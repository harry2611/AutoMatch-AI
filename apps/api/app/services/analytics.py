from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.cache import cache_json
from app.models.entities import Conversion, Dealer, Event, Experiment, Recommendation, Vehicle
from app.models.enums import EventType, ExperimentArm
from app.schemas.domain import (
    AnalyticsOverviewResponse,
    ArmMetricSummary,
    DailySeriesPoint,
    DealerDashboardResponse,
    DealerListItem,
    LeadItem,
    MetricCard,
    PricingGapItem,
    ResponseTimeImpactItem,
    TrendPoint,
    VehicleDemandItem,
)


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _recommendation_frame(db: Session) -> pd.DataFrame:
    rows = db.execute(
        select(
            Recommendation.id.label("recommendation_id"),
            Recommendation.rank,
            Recommendation.experiment_arm,
            Recommendation.purchase_probability,
            Recommendation.expected_revenue,
            Recommendation.distance_miles,
            Recommendation.created_at,
            Recommendation.dealer_id,
            Recommendation.buyer_id,
        )
    ).mappings().all()
    return pd.DataFrame(rows)


def _event_frame(db: Session) -> pd.DataFrame:
    rows = db.execute(
        select(
            Event.id.label("event_id"),
            Event.recommendation_id,
            Event.event_type,
            Event.created_at,
            Event.dealer_id,
        )
    ).mappings().all()
    return pd.DataFrame(rows)


def _conversion_frame(db: Session) -> pd.DataFrame:
    rows = db.execute(
        select(
            Conversion.id.label("conversion_id"),
            Conversion.recommendation_id,
            Conversion.experiment_arm,
            Conversion.commission_revenue,
            Conversion.converted_at,
            Conversion.dealer_id,
        )
    ).mappings().all()
    return pd.DataFrame(rows)


def _arm_metrics(
    rec_df: pd.DataFrame,
    event_df: pd.DataFrame,
    conversion_df: pd.DataFrame,
    top_k: int,
) -> list[ArmMetricSummary]:
    if rec_df.empty:
        return []

    summaries: list[ArmMetricSummary] = []
    for arm in [ExperimentArm.HEURISTIC, ExperimentArm.BAYESIAN]:
        arm_recs = rec_df[rec_df["experiment_arm"] == arm]
        if arm_recs.empty:
            summaries.append(
                ArmMetricSummary(
                    arm=arm,
                    ctr=0.0,
                    precision_at_k=0.0,
                    conversion_rate=0.0,
                    total_revenue=0.0,
                    average_distance=0.0,
                    dealer_response_rate=0.0,
                )
            )
            continue

        arm_rec_ids = set(arm_recs["recommendation_id"].tolist())
        arm_events = event_df[event_df["recommendation_id"].isin(arm_rec_ids)] if not event_df.empty else pd.DataFrame()
        arm_conversions = conversion_df[conversion_df["recommendation_id"].isin(arm_rec_ids)] if not conversion_df.empty else pd.DataFrame()

        clicks = len(arm_events[arm_events["event_type"] == EventType.CLICK]) if not arm_events.empty else 0
        test_drives = len(arm_events[arm_events["event_type"] == EventType.TEST_DRIVE_REQUEST]) if not arm_events.empty else 0
        dealer_responses = len(arm_events[arm_events["event_type"] == EventType.DEALER_RESPONSE]) if not arm_events.empty else 0
        top_k_recs = arm_recs[arm_recs["rank"] <= top_k]
        converted_rec_ids = set(arm_conversions["recommendation_id"].dropna().tolist()) if not arm_conversions.empty else set()
        precision_at_k = top_k_recs["recommendation_id"].isin(converted_rec_ids).mean() if not top_k_recs.empty else 0.0

        summaries.append(
            ArmMetricSummary(
                arm=arm,
                ctr=_safe_div(clicks, len(arm_recs)),
                precision_at_k=float(precision_at_k),
                conversion_rate=_safe_div(len(arm_conversions), len(arm_recs)),
                total_revenue=float(arm_conversions["commission_revenue"].sum()) if not arm_conversions.empty else 0.0,
                average_distance=float(arm_recs["distance_miles"].mean()),
                dealer_response_rate=_safe_div(dealer_responses, max(test_drives, 1)),
            )
        )

    return summaries


def analytics_overview(db: Session, top_k: int = 5) -> AnalyticsOverviewResponse:
    rec_df = _recommendation_frame(db)
    event_df = _event_frame(db)
    conversion_df = _conversion_frame(db)

    if rec_df.empty:
        return AnalyticsOverviewResponse(
            headline_metrics=[],
            arms=[],
            conversion_lift=0.0,
            revenue_lift=0.0,
            average_match_distance=0.0,
            daily_series=[],
        )

    arm_summaries = _arm_metrics(rec_df, event_df, conversion_df, top_k)
    arm_lookup = {summary.arm: summary for summary in arm_summaries}
    heuristic = arm_lookup.get(ExperimentArm.HEURISTIC)
    bayesian = arm_lookup.get(ExperimentArm.BAYESIAN)

    conversion_lift = 0.0
    revenue_lift = 0.0
    if heuristic and heuristic.conversion_rate > 0 and bayesian:
        conversion_lift = (bayesian.conversion_rate - heuristic.conversion_rate) / heuristic.conversion_rate
    if heuristic and heuristic.total_revenue > 0 and bayesian:
        revenue_lift = (bayesian.total_revenue - heuristic.total_revenue) / heuristic.total_revenue

    clicks = len(event_df[event_df["event_type"] == EventType.CLICK]) if not event_df.empty else 0
    headline_metrics = [
        MetricCard(name="precision_at_k", value=arm_lookup.get(ExperimentArm.BAYESIAN, ArmMetricSummary(
            arm=ExperimentArm.BAYESIAN,
            ctr=0.0,
            precision_at_k=0.0,
            conversion_rate=0.0,
            total_revenue=0.0,
            average_distance=0.0,
            dealer_response_rate=0.0,
        )).precision_at_k, label="Precision@5"),
        MetricCard(name="ctr", value=_safe_div(clicks, len(rec_df)), label="CTR"),
        MetricCard(name="conversion_lift", value=conversion_lift, label="Conversion Lift"),
        MetricCard(name="revenue_lift", value=revenue_lift, label="Revenue Lift"),
    ]

    merged = rec_df.copy()
    merged["date"] = pd.to_datetime(merged["created_at"]).dt.date
    if not event_df.empty:
        click_df = event_df[event_df["event_type"] == EventType.CLICK].copy()
        click_df["date"] = pd.to_datetime(click_df["created_at"]).dt.date
        click_df = click_df.merge(rec_df[["recommendation_id", "experiment_arm"]], on="recommendation_id", how="left")
    else:
        click_df = pd.DataFrame(columns=["date", "experiment_arm"])

    if not conversion_df.empty:
        conversion_df = conversion_df.copy()
        conversion_df["date"] = pd.to_datetime(conversion_df["converted_at"]).dt.date
    else:
        conversion_df = pd.DataFrame(columns=["date", "experiment_arm"])

    daily_points: list[DailySeriesPoint] = []
    for current_date in sorted(merged["date"].dropna().unique()):
        heuristic_recs = merged[(merged["date"] == current_date) & (merged["experiment_arm"] == ExperimentArm.HEURISTIC)]
        bayesian_recs = merged[(merged["date"] == current_date) & (merged["experiment_arm"] == ExperimentArm.BAYESIAN)]
        heuristic_clicks = len(click_df[(click_df["date"] == current_date) & (click_df["experiment_arm"] == ExperimentArm.HEURISTIC)])
        bayesian_clicks = len(click_df[(click_df["date"] == current_date) & (click_df["experiment_arm"] == ExperimentArm.BAYESIAN)])
        heuristic_conversions = len(conversion_df[(conversion_df["date"] == current_date) & (conversion_df["experiment_arm"] == ExperimentArm.HEURISTIC)])
        bayesian_conversions = len(conversion_df[(conversion_df["date"] == current_date) & (conversion_df["experiment_arm"] == ExperimentArm.BAYESIAN)])

        daily_points.append(
            DailySeriesPoint(
                date=current_date,
                heuristic_ctr=_safe_div(heuristic_clicks, len(heuristic_recs)),
                bayesian_ctr=_safe_div(bayesian_clicks, len(bayesian_recs)),
                heuristic_conversion_rate=_safe_div(heuristic_conversions, len(heuristic_recs)),
                bayesian_conversion_rate=_safe_div(bayesian_conversions, len(bayesian_recs)),
            )
        )

    return AnalyticsOverviewResponse(
        headline_metrics=headline_metrics,
        arms=arm_summaries,
        conversion_lift=float(conversion_lift),
        revenue_lift=float(revenue_lift),
        average_match_distance=float(rec_df["distance_miles"].mean()),
        daily_series=daily_points,
    )


def refresh_dealer_quality_scores(db: Session) -> None:
    rec_df = _recommendation_frame(db)
    conversion_df = _conversion_frame(db)
    dealers = db.execute(select(Dealer)).scalars().all()

    for dealer in dealers:
        dealer_recs = rec_df[rec_df["dealer_id"] == dealer.id] if not rec_df.empty else pd.DataFrame()
        dealer_conversions = conversion_df[conversion_df["dealer_id"] == dealer.id] if not conversion_df.empty else pd.DataFrame()
        close_rate = _safe_div(len(dealer_conversions), len(dealer_recs))
        response_score = clamp(1.0 - (dealer.average_response_minutes / 90.0), 0.1, 1.0)
        dealer.quality_score = float(np.clip((0.45 * close_rate) + (0.35 * dealer.response_rate) + (0.2 * response_score), 0.15, 0.99))
    db.commit()


def cache_analytics_snapshot(db: Session) -> None:
    snapshot = analytics_overview(db).model_dump(mode="json")
    cache_json("analytics:overview", snapshot, ttl_seconds=600)


def dealer_dashboard(db: Session, dealer_id: int) -> DealerDashboardResponse:
    dealer = db.get(Dealer, dealer_id)
    if dealer is None:
        raise ValueError("Dealer not found.")

    lead_rows = db.execute(
        select(Recommendation)
        .options(joinedload(Recommendation.vehicle), joinedload(Recommendation.buyer))
        .where(Recommendation.dealer_id == dealer_id)
        .order_by(Recommendation.purchase_probability.desc(), Recommendation.created_at.desc())
        .limit(6)
    ).scalars().all()
    high_intent_leads = [
        LeadItem(
            buyer_id=row.buyer.id,
            buyer_name=row.buyer.name,
            budget_max=row.buyer.budget_max,
            urgency=row.buyer.urgency,
            vehicle_label=f"{row.vehicle.year} {row.vehicle.brand} {row.vehicle.model}",
            purchase_probability=row.purchase_probability,
            created_at=row.created_at,
        )
        for row in lead_rows
    ]

    demand_rows = db.execute(
        select(Event, Vehicle).join(Vehicle, Vehicle.id == Event.vehicle_id).where(Event.dealer_id == dealer_id)
    ).all()
    demand_df = pd.DataFrame(
        [
            {
                "vehicle_id": vehicle.id,
                "label": f"{vehicle.brand} {vehicle.model}",
                "event_type": event.event_type,
            }
            for event, vehicle in demand_rows
        ]
    )
    vehicle_demand: list[VehicleDemandItem] = []
    if not demand_df.empty:
        for (vehicle_id, label), frame in demand_df.groupby(["vehicle_id", "label"]):
            vehicle_demand.append(
                VehicleDemandItem(
                    vehicle_id=int(vehicle_id),
                    label=str(label),
                    clicks=int((frame["event_type"] == EventType.CLICK).sum()),
                    saves=int((frame["event_type"] == EventType.SAVE).sum()),
                    test_drive_requests=int((frame["event_type"] == EventType.TEST_DRIVE_REQUEST).sum()),
                )
            )
    vehicle_demand.sort(key=lambda item: (item.test_drive_requests, item.saves, item.clicks), reverse=True)

    rec_df = _recommendation_frame(db)
    conv_df = _conversion_frame(db)
    dealer_recs = rec_df[rec_df["dealer_id"] == dealer_id].copy() if not rec_df.empty else pd.DataFrame()
    dealer_convs = conv_df[conv_df["dealer_id"] == dealer_id].copy() if not conv_df.empty else pd.DataFrame()
    trend: list[TrendPoint] = []
    if not dealer_recs.empty:
        dealer_recs["date"] = pd.to_datetime(dealer_recs["created_at"]).dt.date
        dealer_convs["date"] = pd.to_datetime(dealer_convs["converted_at"]).dt.date if not dealer_convs.empty else pd.Series(dtype="object")
        for current_date in sorted(dealer_recs["date"].dropna().unique()):
            rec_count = len(dealer_recs[dealer_recs["date"] == current_date])
            conv_count = len(dealer_convs[dealer_convs["date"] == current_date]) if not dealer_convs.empty else 0
            trend.append(
                TrendPoint(
                    date=current_date,
                    recommendation_count=rec_count,
                    conversion_count=conv_count,
                    close_rate=_safe_div(conv_count, rec_count),
                )
            )

    market_vehicles = db.execute(select(Vehicle)).scalars().all()
    market_frame = pd.DataFrame(
        [
            {
                "vehicle_id": vehicle.id,
                "brand": vehicle.brand,
                "body_type": vehicle.body_type.value,
                "price": float(vehicle.price),
            }
            for vehicle in market_vehicles
        ]
    )
    dealer_vehicles = [vehicle for vehicle in market_vehicles if vehicle.dealer_id == dealer_id]
    pricing_gaps: list[PricingGapItem] = []
    for vehicle in dealer_vehicles:
        segment = market_frame[
            (market_frame["brand"] == vehicle.brand) & (market_frame["body_type"] == vehicle.body_type.value)
        ]
        median_price = float(segment["price"].median()) if not segment.empty else float(vehicle.price)
        pricing_gaps.append(
            PricingGapItem(
                vehicle_id=vehicle.id,
                label=f"{vehicle.brand} {vehicle.model}",
                current_price=float(vehicle.price),
                market_median_price=median_price,
                gap_amount=float(vehicle.price) - median_price,
            )
        )

    response_df = db.execute(
        select(Recommendation.distance_miles, Recommendation.id, Recommendation.dealer_id, Dealer.average_response_minutes)
        .join(Dealer, Dealer.id == Recommendation.dealer_id)
    ).all()
    response_frame = pd.DataFrame(
        [
            {
                "recommendation_id": recommendation_id,
                "dealer_id": dealer_id,
                "response_minutes": response_minutes,
                "bucket": "<20m" if response_minutes < 20 else "20-40m" if response_minutes <= 40 else ">40m",
            }
            for _, recommendation_id, dealer_id, response_minutes in response_df
        ]
    )
    response_time_impact: list[ResponseTimeImpactItem] = []
    if not response_frame.empty:
        converted_ids = set(conv_df["recommendation_id"].dropna().tolist()) if not conv_df.empty else set()
        response_frame["converted"] = response_frame["recommendation_id"].isin(converted_ids)
        for bucket, frame in response_frame.groupby("bucket"):
            response_time_impact.append(
                ResponseTimeImpactItem(
                    bucket=str(bucket),
                    conversion_rate=float(frame["converted"].mean()),
                    recommendation_count=len(frame),
                )
            )

    return DealerDashboardResponse(
        dealer=DealerListItem.model_validate(dealer),
        high_intent_leads=high_intent_leads,
        vehicle_demand=vehicle_demand[:6],
        close_rate_trend=trend[-14:],
        pricing_gaps=pricing_gaps,
        response_time_impact=response_time_impact,
    )


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))

