from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import authenticate_user, create_access_token, get_current_user
from app.db.session import get_db
from app.schemas.domain import LoginRequest, TokenResponse, UserSummary


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(user.email, user.role.value)
    return TokenResponse(access_token=token, user=UserSummary.model_validate(user))


@router.get("/me", response_model=UserSummary)
def me(current_user=Depends(get_current_user)) -> UserSummary:
    return UserSummary.model_validate(current_user)

