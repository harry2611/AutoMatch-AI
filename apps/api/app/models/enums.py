from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    DEALER = "dealer"


class FinancingPreference(str, Enum):
    LOAN = "loan"
    LEASE = "lease"
    CASH = "cash"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BodyType(str, Enum):
    SUV = "suv"
    SEDAN = "sedan"
    TRUCK = "truck"
    EV = "ev"
    COUPE = "coupe"
    WAGON = "wagon"


class VehicleCondition(str, Enum):
    NEW = "new"
    CERTIFIED = "certified"
    USED = "used"


class EventType(str, Enum):
    IMPRESSION = "impression"
    CLICK = "click"
    SAVE = "save"
    REJECT = "reject"
    TEST_DRIVE_REQUEST = "test_drive_request"
    DEALER_RESPONSE = "dealer_response"
    SEARCH = "search"
    CONVERSION = "conversion"


class ExperimentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ExperimentArm(str, Enum):
    HEURISTIC = "heuristic"
    BAYESIAN = "bayesian"


class InventoryStatus(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    LIMITED = "limited"

