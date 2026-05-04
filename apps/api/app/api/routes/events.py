from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.cache import get_redis_client
from app.db.session import get_db
from app.models.entities import Buyer, Conversion, Dealer, Event, Recommendation, Vehicle
from app.models.enums import EventType, ExperimentArm
from app.schemas.domain import EventCreate, EventResponse, RecommendationRequest
from app.services.bayesian import apply_event_feedback, posterior_snapshot
from app.services.recommendation import generate_recommendations

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse)
def track_event(payload: EventCreate, db: Session = Depends(get_db)) -> EventResponse:
    buyer = db.get(Buyer, payload.buyer_id)
    vehicle = db.get(Vehicle, payload.vehicle_id)
    dealer = db.get(Dealer, payload.dealer_id or (vehicle.dealer_id if vehicle else None))
    if buyer is None or vehicle is None or dealer is None:
        raise HTTPException(status_code=404, detail="Buyer, vehicle, or dealer not found.")

    event = Event(
        buyer_id=buyer.id,
        vehicle_id=vehicle.id,
        dealer_id=dealer.id,
        recommendation_id=payload.recommendation_id,
        session_id=payload.session_id,
        event_type=payload.event_type,
        experiment_arm=payload.experiment_arm,
        details=payload.details,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    logger.info(
        "Event tracked: type=%s buyer=%d vehicle=%d dealer=%d",
        payload.event_type.value,
        buyer.id,
        vehicle.id,
        dealer.id,
    )

    apply_event_feedback(db, buyer, vehicle, dealer, payload.event_type)

    if payload.event_type == EventType.CONVERSION:
        recommendation_id = payload.recommendation_id
        experiment_arm = payload.experiment_arm
        if recommendation_id is None:
            latest_rec = db.execute(
                select(Recommendation)
                .where(Recommendation.buyer_id == buyer.id, Recommendation.vehicle_id == vehicle.id)
                .order_by(Recommendation.created_at.desc())
            ).scalar_one_or_none()
            recommendation_id = latest_rec.id if latest_rec else None
            if latest_rec is not None and experiment_arm is None:
                experiment_arm = latest_rec.experiment_arm
        sale_price = float(payload.details.get("sale_price", float(vehicle.price)))
        db.add(
            Conversion(
                buyer_id=buyer.id,
                vehicle_id=vehicle.id,
                dealer_id=dealer.id,
                recommendation_id=recommendation_id,
                experiment_arm=experiment_arm or ExperimentArm.BAYESIAN,
                sale_price=sale_price,
                commission_revenue=sale_price * dealer.commission_rate,
            )
        )
        db.commit()
        logger.info(
            "Conversion recorded: buyer=%d vehicle=%d sale_price=%.2f",
            buyer.id,
            vehicle.id,
            sale_price,
        )

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            redis_client.hincrby("events:counts", payload.event_type.value, 1)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to increment event counter in Redis: %s", exc)

    reranked = None
    if payload.rerank:
        reranked = generate_recommendations(
            db,
            RecommendationRequest(buyer_id=buyer.id, top_k=payload.top_k),
            persist=True,
        )

    return EventResponse(
        event_id=event.id,
        message="Event tracked and posterior updated.",
        posterior_snapshot=posterior_snapshot(db, buyer, vehicle, dealer),
        reranked_recommendations=reranked,
    )
