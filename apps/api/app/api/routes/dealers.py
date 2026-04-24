from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models.entities import Dealer
from app.models.enums import UserRole
from app.schemas.domain import DealerDashboardResponse, DealerListItem
from app.services.analytics import dealer_dashboard


router = APIRouter(prefix="/dealers", tags=["dealers"])


@router.get("", response_model=list[DealerListItem])
def list_dealers(db: Session = Depends(get_db)) -> list[DealerListItem]:
    dealers = db.execute(select(Dealer).order_by(Dealer.quality_score.desc())).scalars().all()
    return [DealerListItem.model_validate(dealer) for dealer in dealers]


@router.get("/me/dashboard", response_model=DealerDashboardResponse)
def my_dashboard(current_user=Depends(require_roles(UserRole.DEALER, UserRole.ADMIN)), db: Session = Depends(get_db)) -> DealerDashboardResponse:
    dealer_id = current_user.dealer_id
    if current_user.role == UserRole.ADMIN and dealer_id is None:
        dealer = db.execute(select(Dealer).order_by(Dealer.quality_score.desc())).scalar_one_or_none()
        dealer_id = dealer.id if dealer else None
    if dealer_id is None:
        raise HTTPException(status_code=404, detail="Dealer account is not linked to a dealership.")
    try:
        return dealer_dashboard(db, dealer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{dealer_id}/dashboard", response_model=DealerDashboardResponse)
def get_dashboard(
    dealer_id: int,
    current_user=Depends(require_roles(UserRole.DEALER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> DealerDashboardResponse:
    if current_user.role == UserRole.DEALER and current_user.dealer_id != dealer_id:
        raise HTTPException(status_code=403, detail="Dealer users can only access their own dashboard.")
    try:
        return dealer_dashboard(db, dealer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

