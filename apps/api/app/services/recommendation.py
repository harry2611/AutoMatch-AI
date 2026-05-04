from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math

import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import BayesianPrior, Buyer, Dealer, Event, Recommendation, Vehicle
from app.models.enums import BodyType, EventType, ExperimentArm, FinancingPreference, InventoryStatus, UrgencyLevel, VehicleCondition
from app.schemas.domain import RecommendationItem, RecommendationRequest, RecommendationResponse
from app.services.bayesian import get_prior_lookup, posterior_mean
from app.services.experiments import assign_experiment_arm, get_active_experiment
from app.utils.geo import haversine_miles, zip_to_coordinates
from app.utils.math_utils import clamp


POSITIVE_EVENTS = {EventType.CLICK, EventType.SAVE, EventType.TEST_DRIVE_REQUEST, EventType.CONVERSION}
NEGATIVE_EVENTS = {EventType.REJECT}
INVENTORY_FACTORS = {
    InventoryStatus.HIGH: 1.0,
    InventoryStatus.MEDIUM: 0.82,
    InventoryStatus.LOW: 0.6,
    InventoryStatus.LIMITED: 0.45,
}


@dataclass
class CandidateScore:
    vehicle: Vehicle
    dealer: Dealer
    purchase_probability: float
    raw_rank_score: float
    expected_revenue_raw: float
    distance_miles: float
    dealer_quality: float
    inventory_score: float
    explanation: list[str]



def _price_as_float(vehicle: Vehicle) -> float:
    return float(vehicle.price)


def _body_fit(preferred: BodyType | None, actual: BodyType) -> float:
    if preferred is None:
        return 0.78
    return 1.0 if preferred == actual else 0.34


def _brand_fit(preferred: str | None, actual: str) -> float:
    if not preferred:
        return 0.75
    return 1.0 if preferred.lower() == actual.lower() else 0.32


def _behavior_profile(db: Session, buyer_id: int) -> dict[str, dict[str, int]]:
    profile = {"brand": {}, "body_type": {}}
    rows = db.execute(
        select(Event.event_type, Vehicle.brand, Vehicle.body_type)
        .join(Vehicle, Vehicle.id == Event.vehicle_id)
        .where(Event.buyer_id == buyer_id)
    ).all()

    for event_type, brand, body_type in rows:
        if event_type in POSITIVE_EVENTS:
            delta = 1
        elif event_type in NEGATIVE_EVENTS:
            delta = -1
        else:
            continue

        profile["brand"][brand.lower()] = profile["brand"].get(brand.lower(), 0) + delta
        profile["body_type"][body_type.value] = profile["body_type"].get(body_type.value, 0) + delta

    return profile


def _affinity_score(profile: dict[str, int], key: str) -> float:
    value = profile.get(key, 0)
    return clamp(0.5 + (value * 0.12), 0.05, 0.95)


def _resolve_buyer(db: Session, request: RecommendationRequest) -> Buyer:
    buyer: Buyer | None = None
    if request.buyer_id is not None:
        buyer = db.get(Buyer, request.buyer_id)
        if buyer is None:
            raise ValueError("Buyer not found.")

    if buyer is None:
        if request.zip_code is None or request.budget_min is None or request.budget_max is None:
            raise ValueError("zip_code, budget_min, and budget_max are required for a new buyer.")

        coords = zip_to_coordinates(request.zip_code)
        buyer = Buyer(
            name=request.name or "Marketplace Buyer",
            email=request.email,
            zip_code=request.zip_code,
            latitude=coords[0] if coords else None,
            longitude=coords[1] if coords else None,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            preferred_brand=request.preferred_brand,
            preferred_body_type=request.preferred_body_type,
            financing_preference=request.financing_preference or FinancingPreference.LOAN,
            urgency=request.urgency or UrgencyLevel.MEDIUM,
            browsing_profile={"recent_events": request.browsing_events},
        )
        db.add(buyer)
        db.commit()
        db.refresh(buyer)
        return buyer

    if request.zip_code:
        coords = zip_to_coordinates(request.zip_code)
        buyer.zip_code = request.zip_code
        buyer.latitude = coords[0] if coords else buyer.latitude
        buyer.longitude = coords[1] if coords else buyer.longitude
    if request.budget_min is not None:
        buyer.budget_min = request.budget_min
    if request.budget_max is not None:
        buyer.budget_max = request.budget_max
    if request.preferred_brand is not None:
        buyer.preferred_brand = request.preferred_brand
    if request.preferred_body_type is not None:
        buyer.preferred_body_type = request.preferred_body_type
    if request.name:
        buyer.name = request.name
    if request.financing_preference is not None:
        buyer.financing_preference = request.financing_preference
    if request.urgency is not None:
        buyer.urgency = request.urgency
    buyer.browsing_profile = {"recent_events": request.browsing_events}
    db.commit()
    db.refresh(buyer)
    return buyer


def _candidate_inventory(db: Session, buyer: Buyer) -> list[tuple[Vehicle, Dealer]]:
    target_budget = (buyer.budget_min + buyer.budget_max) / 2
    floor = max(8000.0, buyer.budget_min * 0.7)
    ceiling = max(buyer.budget_max * 1.45, target_budget * 1.25)

    rows = db.execute(
        select(Vehicle, Dealer)
        .join(Dealer, Dealer.id == Vehicle.dealer_id)
        .where(Vehicle.price >= floor, Vehicle.price <= ceiling)
        .order_by(Vehicle.price.asc())
    ).all()
    return list(rows)


def _score_candidate(
    buyer: Buyer,
    vehicle: Vehicle,
    dealer: Dealer,
    strategy: ExperimentArm,
    prior_lookup: dict[tuple[str, str], BayesianPrior],
    behavior_profile: dict[str, dict[str, int]],
) -> CandidateScore:
    vehicle_price = _price_as_float(vehicle)
    budget_target = (buyer.budget_min + buyer.budget_max) / 2
    budget_span = max(5000.0, buyer.budget_max - buyer.budget_min, budget_target * 0.22)

    if buyer.budget_min <= vehicle_price <= buyer.budget_max:
        budget_fit = 1.0
    elif vehicle_price < buyer.budget_min:
        budget_fit = clamp(1 - ((buyer.budget_min - vehicle_price) / budget_span), 0.2, 1.0)
    else:
        budget_fit = clamp(1 - ((vehicle_price - buyer.budget_max) / budget_span), 0.05, 1.0)

    brand_fit = _brand_fit(buyer.preferred_brand, vehicle.brand)
    body_fit = _body_fit(buyer.preferred_body_type, vehicle.body_type)
    financing_fit = 1.0 if buyer.financing_preference.value == "cash" or vehicle.financing_available else 0.25

    if buyer.latitude is None or buyer.longitude is None:
        buyer_coords = zip_to_coordinates(buyer.zip_code)
        if buyer_coords:
            buyer.latitude, buyer.longitude = buyer_coords

    distance_miles = (
        haversine_miles(buyer.latitude, buyer.longitude, dealer.latitude, dealer.longitude)
        if buyer.latitude is not None and buyer.longitude is not None
        else 25.0
    )
    distance_score = clamp(math.exp(-distance_miles / 60.0), 0.08, 1.0)

    dealer_posterior = posterior_mean(prior_lookup, "dealer", dealer.id)
    brand_posterior = posterior_mean(prior_lookup, "brand", vehicle.brand.lower())
    body_posterior = posterior_mean(prior_lookup, "body_type", vehicle.body_type.value)
    financing_posterior = posterior_mean(prior_lookup, "financing", buyer.financing_preference.value)
    urgency_posterior = posterior_mean(prior_lookup, "urgency", buyer.urgency.value)
    market_posterior = posterior_mean(prior_lookup, "market", "all")

    behavior_brand = _affinity_score(behavior_profile["brand"], vehicle.brand.lower())
    behavior_body = _affinity_score(behavior_profile["body_type"], vehicle.body_type.value)
    behavior_score = float(np.mean([behavior_brand, behavior_body]))

    inventory_score = clamp(
        0.58 * INVENTORY_FACTORS[vehicle.inventory_status] + 0.42 * dealer.inventory_score,
        0.1,
        1.0,
    )
    dealer_quality = clamp(
        0.45 * dealer_posterior
        + 0.2 * dealer.response_rate
        + 0.2 * dealer.quality_score
        + 0.15 * clamp(1 - dealer.average_response_minutes / 90.0, 0.1, 1.0),
        0.1,
        0.99,
    )

    if strategy == ExperimentArm.BAYESIAN:
        bayes_signal = float(
            np.mean(
                [
                    market_posterior,
                    dealer_posterior,
                    brand_posterior,
                    body_posterior,
                    financing_posterior,
                    urgency_posterior,
                    behavior_score,
                ]
            )
        )
        purchase_probability = clamp(
            0.04
            + (0.17 * budget_fit)
            + (0.08 * brand_fit)
            + (0.08 * body_fit)
            + (0.07 * financing_fit)
            + (0.11 * distance_score)
            + (0.14 * dealer_quality)
            + (0.1 * inventory_score)
            + (0.13 * bayes_signal)
            + (0.08 * behavior_score),
            0.03,
            0.97,
        )
        raw_rank_score = (
            0.48 * purchase_probability
            + 0.18 * dealer_quality
            + 0.12 * distance_score
            + 0.1 * inventory_score
            + 0.12 * budget_fit
        )
    else:
        purchase_probability = clamp(
            0.05
            + (0.27 * budget_fit)
            + (0.14 * brand_fit)
            + (0.14 * body_fit)
            + (0.12 * distance_score)
            + (0.14 * dealer.close_rate_baseline)
            + (0.14 * inventory_score),
            0.03,
            0.9,
        )
        raw_rank_score = (
            0.57 * purchase_probability
            + 0.18 * distance_score
            + 0.15 * inventory_score
            + 0.1 * budget_fit
        )

    expected_revenue_raw = vehicle_price * dealer.commission_rate * (0.7 + (0.3 * inventory_score))
    explanation = [
        f"Budget fit is {budget_fit * 100:.0f}%.",
        f"Dealer distance is {distance_miles:.1f} miles.",
        f"{vehicle.body_type.value.upper()} preference strength is {body_fit * 100:.0f}%.",
        f"Dealer close quality is {dealer_quality * 100:.0f}%.",
    ]

    return CandidateScore(
        vehicle=vehicle,
        dealer=dealer,
        purchase_probability=purchase_probability,
        raw_rank_score=raw_rank_score,
        expected_revenue_raw=expected_revenue_raw,
        distance_miles=distance_miles,
        dealer_quality=dealer_quality,
        inventory_score=inventory_score,
        explanation=explanation,
    )


def _serialize_recommendation(record: Recommendation) -> RecommendationItem:
    vehicle = record.vehicle
    dealer = record.dealer
    return RecommendationItem(
        recommendation_id=record.id,
        vehicle_id=vehicle.id,
        dealer_id=dealer.id,
        rank=record.rank,
        experiment_arm=record.experiment_arm,
        ranking_strategy=record.ranking_strategy,
        brand=vehicle.brand,
        model=vehicle.model,
        year=vehicle.year,
        body_type=vehicle.body_type,
        condition=vehicle.condition,
        price=float(vehicle.price),
        mileage=vehicle.mileage,
        dealer_name=dealer.name,
        dealer_city=dealer.city,
        dealer_state=dealer.state,
        distance_miles=record.distance_miles,
        purchase_probability=record.purchase_probability,
        ranking_score=record.score,
        expected_revenue=record.expected_revenue,
        dealer_quality=dealer.quality_score,
        inventory_score=dealer.inventory_score,
        inventory_status=vehicle.inventory_status,
        explanation=record.explanation,
        explanation_text=" ".join(record.explanation),
        features=vehicle.features,
        photo_url=vehicle.photo_url,
    )


def generate_recommendations(
    db: Session,
    request: RecommendationRequest,
    persist: bool = True,
    served_at: datetime | None = None,
) -> RecommendationResponse:
    buyer = _resolve_buyer(db, request)
    experiment = get_active_experiment(db)
    strategy = request.strategy_override or assign_experiment_arm(db, buyer.id, experiment)

    prior_lookup = get_prior_lookup(db)
    behavior_profile = _behavior_profile(db, buyer.id)
    candidates = [
        _score_candidate(buyer, vehicle, dealer, strategy, prior_lookup, behavior_profile)
        for vehicle, dealer in _candidate_inventory(db, buyer)
    ]
    if not candidates:
        return RecommendationResponse(
            buyer_id=buyer.id,
            recommendation_version=f"empty-{buyer.id}",
            experiment_name=experiment.name if experiment else None,
            experiment_arm=strategy,
            ranking_strategy=strategy.value,
            recommendations=[],
        )

    revenue_scaler = MinMaxScaler(feature_range=(0.2, 1.0))
    revenue_scores = revenue_scaler.fit_transform(
        np.array([[candidate.expected_revenue_raw] for candidate in candidates], dtype=float)
    ).flatten()

    ranked_payload: list[tuple[CandidateScore, float, float]] = []
    for candidate, revenue_score in zip(candidates, revenue_scores, strict=True):
        revenue_weight = 0.15 if strategy == ExperimentArm.BAYESIAN else 0.08
        ranking_score = clamp(candidate.raw_rank_score + (revenue_weight * float(revenue_score)), 0.01, 0.999)
        expected_revenue = candidate.purchase_probability * candidate.expected_revenue_raw
        ranked_payload.append((candidate, ranking_score, expected_revenue))

    ranked_payload.sort(key=lambda item: item[1], reverse=True)
    top_candidates = ranked_payload[: request.top_k]
    version = f"{(served_at or datetime.now(timezone.utc)).strftime('%Y%m%d%H%M%S')}-{buyer.id}"

    records: list[Recommendation] = []
    if persist:
        for rank, (candidate, ranking_score, expected_revenue) in enumerate(top_candidates, start=1):
            record = Recommendation(
                buyer_id=buyer.id,
                vehicle_id=candidate.vehicle.id,
                dealer_id=candidate.dealer.id,
                experiment_arm=strategy,
                ranking_strategy=strategy.value,
                rank=rank,
                score=ranking_score,
                purchase_probability=candidate.purchase_probability,
                expected_revenue=expected_revenue,
                distance_miles=candidate.distance_miles,
                explanation=candidate.explanation,
                version=version,
                created_at=served_at or datetime.now(timezone.utc),
            )
            db.add(record)
            records.append(record)
        db.flush()
        db.commit()

        persisted = db.execute(
            select(Recommendation)
            .options(joinedload(Recommendation.vehicle), joinedload(Recommendation.dealer))
            .where(Recommendation.version == version)
            .order_by(Recommendation.rank.asc())
        ).scalars().all()
        items = [_serialize_recommendation(record) for record in persisted]
    else:
        items = []
        for rank, (candidate, ranking_score, expected_revenue) in enumerate(top_candidates, start=1):
            item = RecommendationItem(
                recommendation_id=None,
                vehicle_id=candidate.vehicle.id,
                dealer_id=candidate.dealer.id,
                rank=rank,
                experiment_arm=strategy,
                ranking_strategy=strategy.value,
                brand=candidate.vehicle.brand,
                model=candidate.vehicle.model,
                year=candidate.vehicle.year,
                body_type=candidate.vehicle.body_type,
                condition=candidate.vehicle.condition,
                price=float(candidate.vehicle.price),
                mileage=candidate.vehicle.mileage,
                dealer_name=candidate.dealer.name,
                dealer_city=candidate.dealer.city,
                dealer_state=candidate.dealer.state,
                distance_miles=candidate.distance_miles,
                purchase_probability=candidate.purchase_probability,
                ranking_score=ranking_score,
                expected_revenue=expected_revenue,
                dealer_quality=candidate.dealer_quality,
                inventory_score=candidate.inventory_score,
                inventory_status=candidate.vehicle.inventory_status,
                explanation=candidate.explanation,
                explanation_text=" ".join(candidate.explanation),
                features=candidate.vehicle.features,
                photo_url=candidate.vehicle.photo_url,
            )
            items.append(item)

    return RecommendationResponse(
        buyer_id=buyer.id,
        recommendation_version=version,
        experiment_name=experiment.name if experiment else None,
        experiment_arm=strategy,
        ranking_strategy=strategy.value,
        recommendations=items,
    )


def latest_recommendations_for_buyer(db: Session, buyer_id: int) -> RecommendationResponse:
    latest = db.execute(
        select(Recommendation)
        .options(joinedload(Recommendation.vehicle), joinedload(Recommendation.dealer))
        .where(Recommendation.buyer_id == buyer_id)
        .order_by(Recommendation.created_at.desc(), Recommendation.rank.asc())
    ).scalars().all()

    if not latest:
        raise ValueError("No recommendations found for buyer.")

    version = latest[0].version
    rows = [record for record in latest if record.version == version]
    rows.sort(key=lambda item: item.rank)
    return RecommendationResponse(
        buyer_id=buyer_id,
        recommendation_version=version,
        experiment_name=None,
        experiment_arm=rows[0].experiment_arm,
        ranking_strategy=rows[0].ranking_strategy,
        recommendations=[_serialize_recommendation(record) for record in rows],
    )
