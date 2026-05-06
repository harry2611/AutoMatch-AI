from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.db.session import get_db
from app.models.entities import Dealer, User
from app.models.enums import UserRole
from app.schemas.domain import DealerSignupRequest, LoginRequest, TokenResponse, UserSummary
from app.utils.geo import zip_to_coordinates


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(user.email, user.role.value)
    return TokenResponse(access_token=token, user=UserSummary.model_validate(user))


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: DealerSignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing_user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")

    if payload.dealer_id is not None:
        dealer = db.get(Dealer, payload.dealer_id)
        if dealer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected dealership was not found.")
    else:
        coords = zip_to_coordinates(payload.zip_code or "")
        if coords is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That ZIP code is not yet supported for dealership signup. Try one of the seeded California ZIP codes.",
            )

        dealer = Dealer(
            name=payload.dealership_name or "New Dealership",
            email=payload.email,
            zip_code=payload.zip_code or "",
            city=payload.city or "",
            state=(payload.state or "").upper(),
            latitude=coords[0],
            longitude=coords[1],
            average_response_minutes=30.0,
            commission_rate=0.08,
            response_rate=0.5,
            quality_score=0.5,
            inventory_score=0.6,
            close_rate_baseline=0.12,
        )
        db.add(dealer)
        db.flush()

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.DEALER,
        dealer_id=dealer.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.email, user.role.value)
    return TokenResponse(access_token=token, user=UserSummary.model_validate(user))


@router.get("/me", response_model=UserSummary)
def me(current_user=Depends(get_current_user)) -> UserSummary:
    return UserSummary.model_validate(current_user)
