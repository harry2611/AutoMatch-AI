from __future__ import annotations

from datetime import date, datetime
from typing import Any

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import BodyType, EventType, ExperimentArm, ExperimentStatus, FinancingPreference, InventoryStatus, UrgencyLevel, UserRole, VehicleCondition


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserSummary(ORMModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    dealer_id: int | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class DealerSignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str
    password: str = Field(min_length=8, max_length=128)
    dealer_id: int | None = None
    dealership_name: str | None = None
    zip_code: str | None = None
    city: str | None = None
    state: str | None = None

    @field_validator("full_name", "email", "dealership_name", "city", "state")
    @classmethod
    def strip_string_fields(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("Enter a valid email address.")
        return normalized

    @field_validator("zip_code")
    @classmethod
    def validate_signup_zip_code(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"\d{5}", value.strip()):
            raise ValueError("zip_code must be a 5-digit US ZIP code.")
        return value.strip() if value else value

    @model_validator(mode="after")
    def validate_dealership_fields(self) -> "DealerSignupRequest":
        if self.dealer_id is not None:
            return self

        missing_fields = [
            label
            for label, value in (
                ("dealership_name", self.dealership_name),
                ("zip_code", self.zip_code),
                ("city", self.city),
                ("state", self.state),
            )
            if not value
        ]
        if missing_fields:
            raise ValueError(
                f"{', '.join(missing_fields)} {'is' if len(missing_fields) == 1 else 'are'} required when creating a new dealership."
            )
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary


class RecommendationRequest(BaseModel):
    buyer_id: int | None = None
    name: str | None = None
    email: str | None = None
    zip_code: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    preferred_brand: str | None = None
    preferred_body_type: BodyType | None = None
    financing_preference: FinancingPreference | None = None
    urgency: UrgencyLevel | None = None
    browsing_events: list[str] = Field(default_factory=list)
    top_k: int = 5
    strategy_override: ExperimentArm | None = None

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"\d{5}", value.strip()):
            raise ValueError("zip_code must be a 5-digit US ZIP code.")
        return value.strip() if value else value

    @field_validator("budget_min", "budget_max")
    @classmethod
    def validate_budget_positive(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("Budget values must be non-negative.")
        return value

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        return min(max(value, 1), 10)

    @model_validator(mode="after")
    def validate_budget_range(self) -> "RecommendationRequest":
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_min >= self.budget_max
        ):
            raise ValueError("budget_min must be less than budget_max.")
        return self


class RecommendationItem(BaseModel):
    recommendation_id: int | None = None
    vehicle_id: int
    dealer_id: int
    rank: int
    experiment_arm: ExperimentArm
    ranking_strategy: str
    brand: str
    model: str
    year: int
    body_type: BodyType
    condition: VehicleCondition
    price: float
    mileage: int
    dealer_name: str
    dealer_city: str
    dealer_state: str
    distance_miles: float
    purchase_probability: float
    ranking_score: float
    expected_revenue: float
    dealer_quality: float
    inventory_score: float
    inventory_status: InventoryStatus
    explanation: list[str]
    explanation_text: str
    features: list[str]
    photo_url: str | None = None


class RecommendationResponse(BaseModel):
    buyer_id: int
    recommendation_version: str
    experiment_name: str | None = None
    experiment_arm: ExperimentArm
    ranking_strategy: str
    recommendations: list[RecommendationItem]


class EventCreate(BaseModel):
    buyer_id: int
    vehicle_id: int
    dealer_id: int | None = None
    recommendation_id: int | None = None
    session_id: str | None = None
    event_type: EventType
    experiment_arm: ExperimentArm | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    rerank: bool = False
    top_k: int = 5


class EventResponse(BaseModel):
    event_id: int
    message: str
    posterior_snapshot: dict[str, float]
    reranked_recommendations: RecommendationResponse | None = None


class DealerListItem(ORMModel):
    id: int
    name: str
    city: str
    state: str
    zip_code: str
    average_response_minutes: float
    quality_score: float
    response_rate: float


class LeadItem(BaseModel):
    buyer_id: int
    buyer_name: str
    budget_max: float
    urgency: UrgencyLevel
    vehicle_label: str
    purchase_probability: float
    created_at: datetime


class VehicleDemandItem(BaseModel):
    vehicle_id: int
    label: str
    clicks: int
    saves: int
    test_drive_requests: int


class TrendPoint(BaseModel):
    date: date
    recommendation_count: int
    conversion_count: int
    close_rate: float


class PricingGapItem(BaseModel):
    vehicle_id: int
    label: str
    current_price: float
    market_median_price: float
    gap_amount: float


class ResponseTimeImpactItem(BaseModel):
    bucket: str
    conversion_rate: float
    recommendation_count: int


class DealerDashboardResponse(BaseModel):
    dealer: DealerListItem
    high_intent_leads: list[LeadItem]
    vehicle_demand: list[VehicleDemandItem]
    close_rate_trend: list[TrendPoint]
    pricing_gaps: list[PricingGapItem]
    response_time_impact: list[ResponseTimeImpactItem]


class VehicleResponse(ORMModel):
    id: int
    brand: str
    model: str
    year: int
    body_type: BodyType
    condition: VehicleCondition
    price: float
    mileage: int
    financing_available: bool
    inventory_status: InventoryStatus
    dealer_id: int
    photo_url: str | None = None


class ExperimentResponse(ORMModel):
    id: int
    name: str
    description: str
    status: ExperimentStatus
    traffic_split: float
    control_arm: ExperimentArm
    treatment_arm: ExperimentArm
    created_at: datetime


class ExperimentCreate(BaseModel):
    name: str
    description: str
    traffic_split: float = 0.5

    @field_validator("traffic_split")
    @classmethod
    def validate_split(cls, value: float) -> float:
        return min(max(value, 0.05), 0.95)


class ExperimentDashboardResponse(BaseModel):
    experiments: list[ExperimentResponse]
    active_experiment: ExperimentResponse | None = None


class MetricCard(BaseModel):
    name: str
    value: float
    label: str


class ArmMetricSummary(BaseModel):
    arm: ExperimentArm
    ctr: float
    precision_at_k: float
    conversion_rate: float
    total_revenue: float
    average_distance: float
    dealer_response_rate: float


class DailySeriesPoint(BaseModel):
    date: date
    heuristic_ctr: float
    bayesian_ctr: float
    heuristic_conversion_rate: float
    bayesian_conversion_rate: float


class AnalyticsOverviewResponse(BaseModel):
    headline_metrics: list[MetricCard]
    arms: list[ArmMetricSummary]
    conversion_lift: float
    revenue_lift: float
    average_match_distance: float
    daily_series: list[DailySeriesPoint]
