from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import BayesianPrior, Buyer, Dealer, Event, Vehicle
from app.models.enums import EventType


DEFAULT_ALPHA = 2.0
DEFAULT_BETA = 8.0
EVENT_IMPACT: dict[EventType, tuple[float, float]] = {
    EventType.CLICK: (0.18, 0.02),
    EventType.SAVE: (0.32, 0.02),
    EventType.REJECT: (0.02, 0.42),
    EventType.TEST_DRIVE_REQUEST: (0.68, 0.03),
    EventType.DEALER_RESPONSE: (0.24, 0.01),
    EventType.CONVERSION: (1.0, 0.02),
}


def _default_mean(alpha: float = DEFAULT_ALPHA, beta: float = DEFAULT_BETA) -> float:
    return alpha / (alpha + beta)


def segment_key(segment_type: str, raw_key: str | int | None) -> tuple[str, str]:
    return segment_type, str(raw_key if raw_key is not None else "unknown")


def get_prior_lookup(db: Session) -> dict[tuple[str, str], BayesianPrior]:
    priors = db.execute(select(BayesianPrior)).scalars().all()
    return {(prior.segment_type, prior.segment_key): prior for prior in priors}


def posterior_mean(
    prior_lookup: dict[tuple[str, str], BayesianPrior],
    segment_type: str,
    raw_key: str | int | None,
    default_alpha: float = DEFAULT_ALPHA,
    default_beta: float = DEFAULT_BETA,
) -> float:
    key = segment_key(segment_type, raw_key)
    prior = prior_lookup.get(key)
    if prior is None:
        return _default_mean(default_alpha, default_beta)
    return prior.alpha / (prior.alpha + prior.beta)


def _get_or_create_prior(db: Session, segment_type: str, raw_key: str | int | None) -> BayesianPrior:
    _, key = segment_key(segment_type, raw_key)
    prior = db.execute(
        select(BayesianPrior).where(
            BayesianPrior.segment_type == segment_type,
            BayesianPrior.segment_key == key,
        )
    ).scalar_one_or_none()
    if prior is None:
        prior = BayesianPrior(segment_type=segment_type, segment_key=key, alpha=DEFAULT_ALPHA, beta=DEFAULT_BETA)
        db.add(prior)
        db.flush()
    return prior


def _segments_for_feedback(buyer: Buyer, vehicle: Vehicle, dealer: Dealer) -> Iterable[tuple[str, str | int | None]]:
    return [
        ("market", "all"),
        ("dealer", dealer.id),
        ("brand", vehicle.brand.lower()),
        ("body_type", vehicle.body_type.value),
        ("financing", buyer.financing_preference.value),
        ("urgency", buyer.urgency.value),
        ("zip_prefix", buyer.zip_code[:3]),
    ]


def apply_event_feedback(db: Session, buyer: Buyer, vehicle: Vehicle, dealer: Dealer, event_type: EventType) -> None:
    delta = EVENT_IMPACT.get(event_type)
    if delta is None:
        return

    alpha_delta, beta_delta = delta
    for segment_type, raw_key in _segments_for_feedback(buyer, vehicle, dealer):
        prior = _get_or_create_prior(db, segment_type, raw_key)
        prior.alpha += alpha_delta
        prior.beta += beta_delta

    db.commit()


def posterior_snapshot(db: Session, buyer: Buyer, vehicle: Vehicle, dealer: Dealer) -> dict[str, float]:
    lookup = get_prior_lookup(db)
    return {
        "market": posterior_mean(lookup, "market", "all"),
        "dealer": posterior_mean(lookup, "dealer", dealer.id),
        "brand": posterior_mean(lookup, "brand", vehicle.brand.lower()),
        "body_type": posterior_mean(lookup, "body_type", vehicle.body_type.value),
        "financing": posterior_mean(lookup, "financing", buyer.financing_preference.value),
        "urgency": posterior_mean(lookup, "urgency", buyer.urgency.value),
    }


def recompute_priors_from_history(db: Session) -> None:
    db.query(BayesianPrior).delete()
    db.flush()

    events = db.execute(select(Event)).scalars().all()
    for event in events:
        delta = EVENT_IMPACT.get(event.event_type)
        if delta is None:
            continue
        for segment_type, raw_key in _segments_for_feedback(event.buyer, event.vehicle, event.dealer):
            prior = _get_or_create_prior(db, segment_type, raw_key)
            prior.alpha += delta[0]
            prior.beta += delta[1]

    db.commit()

