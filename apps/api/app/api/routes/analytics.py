from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.domain import AnalyticsOverviewResponse
from app.services.analytics import analytics_overview


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def overview(
    top_k: int = 5,
    _: object = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> AnalyticsOverviewResponse:
    return analytics_overview(db, top_k=top_k)

