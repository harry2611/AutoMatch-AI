from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Vehicle
from app.models.enums import BodyType
from app.schemas.domain import VehicleResponse


router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    brand: str | None = None,
    body_type: BodyType | None = None,
    dealer_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[VehicleResponse]:
    query = select(Vehicle).order_by(Vehicle.price.asc())
    if brand:
        query = query.where(Vehicle.brand.ilike(f"%{brand}%"))
    if body_type:
        query = query.where(Vehicle.body_type == body_type)
    if dealer_id:
        query = query.where(Vehicle.dealer_id == dealer_id)

    vehicles = db.execute(query).scalars().all()
    return [VehicleResponse.model_validate(vehicle) for vehicle in vehicles]

