from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.domain import RecommendationRequest, RecommendationResponse
from app.services.recommendation import generate_recommendations, latest_recommendations_for_buyer


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/query", response_model=RecommendationResponse)
def query_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)) -> RecommendationResponse:
    try:
        return generate_recommendations(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/buyer/{buyer_id}", response_model=RecommendationResponse)
def get_latest_recommendations(buyer_id: int, db: Session = Depends(get_db)) -> RecommendationResponse:
    try:
        return latest_recommendations_for_buyer(db, buyer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

