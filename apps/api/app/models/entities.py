from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    BodyType,
    EventType,
    ExperimentArm,
    ExperimentStatus,
    FinancingPreference,
    InventoryStatus,
    UrgencyLevel,
    UserRole,
    VehicleCondition,
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Dealer(Base, TimestampMixin):
    __tablename__ = "dealers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    average_response_minutes: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    commission_rate: Mapped[float] = mapped_column(Float, default=0.08, nullable=False)
    response_rate: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    inventory_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    close_rate_baseline: Mapped[float] = mapped_column(Float, default=0.18, nullable=False)

    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="dealer", cascade="all, delete-orphan")
    users: Mapped[list["User"]] = relationship(back_populates="dealer")
    events: Mapped[list["Event"]] = relationship(back_populates="dealer")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="dealer")
    conversions: Mapped[list["Conversion"]] = relationship(back_populates="dealer")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    dealer_id: Mapped[int | None] = mapped_column(ForeignKey("dealers.id"), nullable=True)

    dealer: Mapped[Dealer | None] = relationship(back_populates="users")


class Buyer(Base, TimestampMixin):
    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_min: Mapped[float] = mapped_column(Float, nullable=False)
    budget_max: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    preferred_body_type: Mapped[BodyType | None] = mapped_column(Enum(BodyType), nullable=True)
    financing_preference: Mapped[FinancingPreference] = mapped_column(Enum(FinancingPreference), nullable=False)
    urgency: Mapped[UrgencyLevel] = mapped_column(Enum(UrgencyLevel), nullable=False)
    browsing_profile: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    events: Mapped[list["Event"]] = relationship(back_populates="buyer")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="buyer")
    conversions: Mapped[list["Conversion"]] = relationship(back_populates="buyer")
    experiment_assignments: Mapped[list["ExperimentAssignment"]] = relationship(back_populates="buyer")


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dealer_id: Mapped[int] = mapped_column(ForeignKey("dealers.id"), nullable=False, index=True)
    vin: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(120), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    msrp: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    mileage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    body_type: Mapped[BodyType] = mapped_column(Enum(BodyType), nullable=False)
    condition: Mapped[VehicleCondition] = mapped_column(Enum(VehicleCondition), nullable=False)
    financing_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    inventory_status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus), nullable=False)
    projected_margin: Mapped[float] = mapped_column(Float, default=2500.0, nullable=False)
    features: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    dealer: Mapped[Dealer] = relationship(back_populates="vehicles")
    events: Mapped[list["Event"]] = relationship(back_populates="vehicle")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="vehicle")
    conversions: Mapped[list["Conversion"]] = relationship(back_populates="vehicle")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), nullable=False, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False, index=True)
    dealer_id: Mapped[int] = mapped_column(ForeignKey("dealers.id"), nullable=False, index=True)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.id"), nullable=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    experiment_arm: Mapped[ExperimentArm | None] = mapped_column(Enum(ExperimentArm), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    buyer: Mapped[Buyer] = relationship(back_populates="events")
    vehicle: Mapped[Vehicle] = relationship(back_populates="events")
    dealer: Mapped[Dealer] = relationship(back_populates="events")
    recommendation: Mapped["Recommendation | None"] = relationship(back_populates="events")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), nullable=False, index=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False, index=True)
    dealer_id: Mapped[int] = mapped_column(ForeignKey("dealers.id"), nullable=False, index=True)
    experiment_arm: Mapped[ExperimentArm] = mapped_column(Enum(ExperimentArm), nullable=False)
    ranking_strategy: Mapped[str] = mapped_column(String(40), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    distance_miles: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    version: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    buyer: Mapped[Buyer] = relationship(back_populates="recommendations")
    vehicle: Mapped[Vehicle] = relationship(back_populates="recommendations")
    dealer: Mapped[Dealer] = relationship(back_populates="recommendations")
    events: Mapped[list[Event]] = relationship(back_populates="recommendation")
    conversions: Mapped[list["Conversion"]] = relationship(back_populates="recommendation")


class Experiment(Base, TimestampMixin):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(Enum(ExperimentStatus), nullable=False)
    control_arm: Mapped[ExperimentArm] = mapped_column(
        Enum(ExperimentArm), default=ExperimentArm.HEURISTIC, nullable=False
    )
    treatment_arm: Mapped[ExperimentArm] = mapped_column(
        Enum(ExperimentArm), default=ExperimentArm.BAYESIAN, nullable=False
    )
    traffic_split: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    assignments: Mapped[list["ExperimentAssignment"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"
    __table_args__ = (UniqueConstraint("experiment_id", "buyer_id", name="uq_experiment_buyer"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), nullable=False)
    arm: Mapped[ExperimentArm] = mapped_column(Enum(ExperimentArm), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment: Mapped[Experiment] = relationship(back_populates="assignments")
    buyer: Mapped[Buyer] = relationship(back_populates="experiment_assignments")


class Conversion(Base):
    __tablename__ = "conversions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    dealer_id: Mapped[int] = mapped_column(ForeignKey("dealers.id"), nullable=False)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.id"), nullable=True)
    experiment_arm: Mapped[ExperimentArm] = mapped_column(Enum(ExperimentArm), nullable=False)
    sale_price: Mapped[float] = mapped_column(Float, nullable=False)
    commission_revenue: Mapped[float] = mapped_column(Float, nullable=False)
    converted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    buyer: Mapped[Buyer] = relationship(back_populates="conversions")
    vehicle: Mapped[Vehicle] = relationship(back_populates="conversions")
    dealer: Mapped[Dealer] = relationship(back_populates="conversions")
    recommendation: Mapped[Recommendation | None] = relationship(back_populates="conversions")


class BayesianPrior(Base):
    __tablename__ = "bayesian_priors"
    __table_args__ = (UniqueConstraint("segment_type", "segment_key", name="uq_segment_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    segment_type: Mapped[str] = mapped_column(String(80), nullable=False)
    segment_key: Mapped[str] = mapped_column(String(255), nullable=False)
    alpha: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    beta: Mapped[float] = mapped_column(Float, default=8.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

