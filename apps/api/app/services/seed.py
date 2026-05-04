from __future__ import annotations

from datetime import datetime, timedelta, timezone
from random import Random

from sqlalchemy import func, select

from app.core.security import get_password_hash
from app.db.session import get_session
from app.models.entities import Buyer, Conversion, Dealer, Event, Experiment, User, Vehicle
from app.models.enums import BodyType, EventType, ExperimentArm, ExperimentStatus, FinancingPreference, InventoryStatus, UrgencyLevel, UserRole, VehicleCondition
from app.schemas.domain import RecommendationRequest
from app.services.analytics import cache_analytics_snapshot, refresh_dealer_quality_scores
from app.services.bayesian import recompute_priors_from_history
from app.services.recommendation import generate_recommendations
from app.utils.geo import zip_to_coordinates


DEALER_FIXTURES = [
    {
        "name": "Golden Gate Motors",
        "email": "dealer1@automatch.ai",
        "zip_code": "94107",
        "city": "San Francisco",
        "state": "CA",
        "latitude": 37.769722,
        "longitude": -122.393301,
        "average_response_minutes": 18,
        "commission_rate": 0.082,
        "response_rate": 0.94,
        "quality_score": 0.84,
        "inventory_score": 0.88,
        "close_rate_baseline": 0.22,
    },
    {
        "name": "Peninsula Auto Hub",
        "email": "dealer2@automatch.ai",
        "zip_code": "94063",
        "city": "Redwood City",
        "state": "CA",
        "latitude": 37.492596,
        "longitude": -122.228455,
        "average_response_minutes": 26,
        "commission_rate": 0.075,
        "response_rate": 0.9,
        "quality_score": 0.78,
        "inventory_score": 0.83,
        "close_rate_baseline": 0.19,
    },
    {
        "name": "SoCal EV & SUV",
        "email": "dealer3@automatch.ai",
        "zip_code": "92618",
        "city": "Irvine",
        "state": "CA",
        "latitude": 33.659523,
        "longitude": -117.732498,
        "average_response_minutes": 34,
        "commission_rate": 0.091,
        "response_rate": 0.86,
        "quality_score": 0.79,
        "inventory_score": 0.91,
        "close_rate_baseline": 0.2,
    },
    {
        "name": "Metro Family Cars",
        "email": "dealer4@automatch.ai",
        "zip_code": "90017",
        "city": "Los Angeles",
        "state": "CA",
        "latitude": 34.052949,
        "longitude": -118.266693,
        "average_response_minutes": 43,
        "commission_rate": 0.072,
        "response_rate": 0.79,
        "quality_score": 0.69,
        "inventory_score": 0.74,
        "close_rate_baseline": 0.15,
    },
    # Luxury dealer — Palo Alto
    {
        "name": "Bay Area Luxury",
        "email": "dealer5@automatch.ai",
        "zip_code": "94301",
        "city": "Palo Alto",
        "state": "CA",
        "latitude": 37.442699,
        "longitude": -122.148399,
        "average_response_minutes": 14,
        "commission_rate": 0.095,
        "response_rate": 0.97,
        "quality_score": 0.91,
        "inventory_score": 0.86,
        "close_rate_baseline": 0.25,
    },
    # East Bay all-makes dealer — Oakland
    {
        "name": "East Bay Auto Center",
        "email": "dealer6@automatch.ai",
        "zip_code": "94611",
        "city": "Oakland",
        "state": "CA",
        "latitude": 37.840599,
        "longitude": -122.231201,
        "average_response_minutes": 31,
        "commission_rate": 0.078,
        "response_rate": 0.88,
        "quality_score": 0.76,
        "inventory_score": 0.80,
        "close_rate_baseline": 0.18,
    },
]

# fmt: off
VEHICLE_FIXTURES = [
    # ── Golden Gate Motors (San Francisco) ─────────────────────────────────
    ("Golden Gate Motors", "VIN0001", "Toyota",    "RAV4",         2023, 32900, 35200,  8200, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2800, ["AWD", "lane assist", "apple carplay"]),
    ("Golden Gate Motors", "VIN0002", "Honda",     "CR-V",         2024, 34800, 36500,  3100, BodyType.SUV,   VehicleCondition.NEW,       True, InventoryStatus.MEDIUM,  3000, ["hybrid", "blind spot monitor", "heated seats"]),
    ("Golden Gate Motors", "VIN0013", "Subaru",    "Forester",     2023, 30500, 32800,  6100, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2600, ["eyesight safety", "awd", "starlink"]),
    ("Golden Gate Motors", "VIN0014", "Mazda",     "Mazda3",       2024, 25900, 27500,   800, BodyType.SEDAN, VehicleCondition.NEW,       True, InventoryStatus.HIGH,    2100, ["i-activsense", "bose audio", "soul red crystal"]),
    ("Golden Gate Motors", "VIN0015", "Nissan",    "Leaf",         2023, 27400, 29100,  4700, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  2300, ["propilot assist", "e-pedal", "heat pump"]),

    # ── Peninsula Auto Hub (Redwood City) ──────────────────────────────────
    ("Peninsula Auto Hub", "VIN0003", "Subaru",    "Outback",      2022, 31600, 34100,  9100, BodyType.WAGON, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  2600, ["roof rack", "awd", "adaptive cruise"]),
    ("Peninsula Auto Hub", "VIN0004", "Mazda",     "CX-5",         2023, 29900, 32100,  5600, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2500, ["sunroof", "leather trim", "360 camera"]),
    ("Peninsula Auto Hub", "VIN0005", "Toyota",    "Camry",        2024, 28750, 30150,   900, BodyType.SEDAN, VehicleCondition.NEW,       True, InventoryStatus.HIGH,    2100, ["hybrid", "lane keep", "wireless charging"]),
    ("Peninsula Auto Hub", "VIN0016", "Volkswagen","Tiguan",       2023, 32500, 34800,  7400, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2600, ["awd", "digital cockpit", "third row"]),
    ("Peninsula Auto Hub", "VIN0017", "Volvo",     "V60",          2023, 42000, 45000,  4100, BodyType.WAGON, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3400, ["pilot assist", "harman kardon", "panoramic roof"]),
    ("Peninsula Auto Hub", "VIN0018", "Toyota",    "GR86",         2023, 31500, 33000,  3100, BodyType.COUPE, VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2800, ["manual 6-speed", "track mode", "brembo brakes"]),

    # ── SoCal EV & SUV (Irvine) ────────────────────────────────────────────
    ("SoCal EV & SUV",    "VIN0006", "Tesla",     "Model Y",      2023, 44900, 47100,  6300, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.LIMITED, 3800, ["awd", "full self driving ready", "glass roof"]),
    ("SoCal EV & SUV",    "VIN0007", "Hyundai",   "Ioniq 5",      2023, 39950, 42500,  4100, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3300, ["fast charging", "heads-up display", "heat pump"]),
    ("SoCal EV & SUV",    "VIN0008", "Kia",       "Telluride",    2022, 41200, 44000,  9700, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.LOW,     3200, ["third row", "captain chairs", "tow package"]),
    ("SoCal EV & SUV",    "VIN0019", "Ford",      "Mustang Mach-E",2023,41800, 44200,  3800, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3500, ["extended range", "ford bluecruise", "panoramic sunroof"]),
    ("SoCal EV & SUV",    "VIN0020", "Volkswagen","ID.4",          2023, 38500, 41000,  5100, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    3200, ["pro s trim", "awd", "panoramic roof"]),
    ("SoCal EV & SUV",    "VIN0021", "Jeep",      "Grand Cherokee",2023, 40500, 43000,  6200, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    3500, ["trail rated 4x4", "uconnect 5", "tow package"]),

    # ── Metro Family Cars (Los Angeles) ────────────────────────────────────
    ("Metro Family Cars",  "VIN0009", "Honda",     "Civic",        2023, 24800, 26300,  4000, BodyType.SEDAN, VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    1900, ["sport trim", "apple carplay", "lane assist"]),
    ("Metro Family Cars",  "VIN0010", "Chevrolet", "Bolt EUV",     2023, 28990, 30900,  5200, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  2400, ["super cruise", "heated steering", "one pedal driving"]),
    ("Metro Family Cars",  "VIN0011", "Ford",      "F-150",        2022, 38900, 41750, 11000, BodyType.TRUCK, VehicleCondition.USED,      True, InventoryStatus.LOW,     3600, ["4x4", "tow tech", "bed liner"]),
    ("Metro Family Cars",  "VIN0012", "Hyundai",   "Tucson",       2024, 30100, 32100,  1500, BodyType.SUV,   VehicleCondition.NEW,       True, InventoryStatus.HIGH,    2300, ["hybrid", "panoramic roof", "parking assist"]),
    ("Metro Family Cars",  "VIN0022", "Nissan",    "Altima",       2023, 26800, 28500,  6900, BodyType.SEDAN, VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2200, ["zero gravity seats", "safety shield 360", "sr sport"]),
    ("Metro Family Cars",  "VIN0023", "Toyota",    "Tacoma",       2023, 36800, 39000,  4500, BodyType.TRUCK, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3100, ["trd off road", "crawl control", "bed liner"]),
    ("Metro Family Cars",  "VIN0024", "Ford",      "Mustang",      2022, 38200, 41000,  9800, BodyType.COUPE, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3200, ["gt premium", "performance package", "brembo brakes"]),
    ("Metro Family Cars",  "VIN0025", "Chevrolet", "Camaro",       2022, 34900, 37500, 10200, BodyType.COUPE, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  2900, ["v8 lt1", "magnetic ride control", "brembo brakes"]),

    # ── Bay Area Luxury (Palo Alto) ────────────────────────────────────────
    ("Bay Area Luxury",    "VIN0026", "BMW",       "X3",           2023, 48900, 51500,  2100, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    4200, ["xdrive awd", "panoramic roof", "drive assist"]),
    ("Bay Area Luxury",    "VIN0027", "Audi",      "Q5",           2022, 43500, 46000,  8800, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3800, ["quattro awd", "virtual cockpit", "sunroof"]),
    ("Bay Area Luxury",    "VIN0028", "Mercedes",  "C300",         2023, 45000, 48000,  1200, BodyType.SEDAN, VehicleCondition.NEW,       True, InventoryStatus.HIGH,    4500, ["burmester audio", "heated seats", "ambient lighting"]),
    ("Bay Area Luxury",    "VIN0029", "BMW",       "330i",         2022, 38900, 42000, 11000, BodyType.SEDAN, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3200, ["m sport package", "heads-up display", "lane departure"]),
    ("Bay Area Luxury",    "VIN0030", "Lexus",     "RX 350",       2023, 51500, 54000,  3200, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  4800, ["mark levinson audio", "lexus safety system+", "panoramic roof"]),
    ("Bay Area Luxury",    "VIN0031", "Audi",      "A5",           2022, 44500, 47000,  9200, BodyType.COUPE, VehicleCondition.CERTIFIED, True, InventoryStatus.LOW,     3600, ["s line package", "virtual cockpit", "quattro"]),
    ("Bay Area Luxury",    "VIN0032", "BMW",       "430i",         2022, 47500, 51000,  8700, BodyType.COUPE, VehicleCondition.CERTIFIED, True, InventoryStatus.LOW,     4100, ["m sport package", "adaptive cruise", "harman kardon"]),
    ("Bay Area Luxury",    "VIN0033", "Volvo",     "XC60",         2023, 48200, 51000,  2900, BodyType.SUV,   VehicleCondition.NEW,       True, InventoryStatus.MEDIUM,  4000, ["pilot assist", "crystal white pearl", "360 camera"]),

    # ── East Bay Auto Center (Oakland) ─────────────────────────────────────
    ("East Bay Auto Center","VIN0034","Ram",       "1500",         2022, 42200, 45500, 14000, BodyType.TRUCK, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3700, ["hemi v8", "rambox storage", "blind spot monitor"]),
    ("East Bay Auto Center","VIN0035","Chevrolet", "Silverado",    2023, 46500, 49000,  7200, BodyType.TRUCK, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3900, ["z71 package", "multi-flex tailgate", "bose audio"]),
    ("East Bay Auto Center","VIN0036","Nissan",    "Pathfinder",   2022, 36200, 38500, 12000, BodyType.SUV,   VehicleCondition.CERTIFIED, True, InventoryStatus.HIGH,    2900, ["intelligent awd", "captain chairs", "pro pilot assist"]),
    ("East Bay Auto Center","VIN0037","Rivian",    "R1T",          2023, 67500, 72000,  5800, BodyType.TRUCK, VehicleCondition.CERTIFIED, True, InventoryStatus.LIMITED, 5500, ["quad motor", "camp kitchen", "all terrain tires"]),
    ("East Bay Auto Center","VIN0038","Audi",      "A4",           2022, 40800, 43500, 10400, BodyType.SEDAN, VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3400, ["quattro awd", "virtual cockpit", "sunroof"]),
    ("East Bay Auto Center","VIN0039","Chevrolet", "Camaro ZL1",   2021, 62000, 68000, 14200, BodyType.COUPE, VehicleCondition.USED,      True, InventoryStatus.LIMITED, 5200, ["supercharged lt4", "magnetic ride", "brembo 6-piston"]),
    ("East Bay Auto Center","VIN0040","Kia",       "EV6",          2023, 43200, 45800,  4600, BodyType.EV,    VehicleCondition.CERTIFIED, True, InventoryStatus.MEDIUM,  3600, ["800v charging", "augmented reality hud", "awd"]),
]
# fmt: on

BUYER_FIXTURES = [
    # Existing buyers
    ("Sarah Kim",      "sarah@example.com",  "94103", 26000, 38000, "Honda",   BodyType.SUV,   FinancingPreference.LOAN,  UrgencyLevel.HIGH,   ["search:suv", "click:honda", "save:hybrid"]),
    ("Miguel Alvarez", "miguel@example.com", "90012", 22000, 31000, "Toyota",  BodyType.SEDAN, FinancingPreference.CASH,  UrgencyLevel.MEDIUM, ["search:sedan", "click:camry"]),
    ("Priya Patel",    "priya@example.com",  "94016", 36000, 55000, "Tesla",   BodyType.EV,    FinancingPreference.LEASE, UrgencyLevel.HIGH,   ["search:ev", "save:model-y", "click:ioniq5"]),
    ("Jason Brooks",   "jason@example.com",  "94607", 25000, 34000, None,      BodyType.SUV,   FinancingPreference.LOAN,  UrgencyLevel.LOW,    ["search:suv", "reject:truck"]),
    # New buyers covering coupe, truck, and luxury preferences
    ("Aisha Johnson",  "aisha@example.com",  "94301", 38000, 55000, "BMW",     BodyType.COUPE, FinancingPreference.LOAN,  UrgencyLevel.HIGH,   ["search:coupe", "click:bmw", "save:m-sport"]),
    ("Derek Tran",     "derek@example.com",  "94611", 35000, 50000, "Ford",    BodyType.TRUCK, FinancingPreference.LOAN,  UrgencyLevel.MEDIUM, ["search:truck", "click:f150", "save:4x4"]),
    ("Sofia Reyes",    "sofia@example.com",  "94063", 40000, 58000, "Audi",    BodyType.SEDAN, FinancingPreference.LEASE, UrgencyLevel.HIGH,   ["search:luxury", "click:audi", "save:quattro"]),
    ("Marcus Webb",    "marcus@example.com", "92618", 28000, 42000, "Rivian",  BodyType.EV,    FinancingPreference.LOAN,  UrgencyLevel.MEDIUM, ["search:ev", "click:rivian", "save:range"]),
]


def _seed_users_and_entities() -> None:
    db = get_session()
    try:
        if db.scalar(select(func.count(Dealer.id))) > 0:
            return

        dealers: dict[str, Dealer] = {}
        for payload in DEALER_FIXTURES:
            dealer = Dealer(**payload)
            db.add(dealer)
            dealers[dealer.name] = dealer
        db.flush()

        admin_user = User(
            email="admin@automatch.ai",
            full_name="AutoMatch Admin",
            hashed_password=get_password_hash("demo1234"),
            role=UserRole.ADMIN,
        )
        dealer_user = User(
            email="dealer@automatch.ai",
            full_name="Golden Gate Manager",
            hashed_password=get_password_hash("demo1234"),
            role=UserRole.DEALER,
            dealer_id=dealers["Golden Gate Motors"].id,
        )
        db.add_all([admin_user, dealer_user])

        for dealer_name, vin, brand, model, year, price, msrp, mileage, body_type, condition, financing_available, inventory_status, projected_margin, features in VEHICLE_FIXTURES:
            db.add(
                Vehicle(
                    dealer_id=dealers[dealer_name].id,
                    vin=vin,
                    brand=brand,
                    model=model,
                    year=year,
                    price=price,
                    msrp=msrp,
                    mileage=mileage,
                    body_type=body_type,
                    condition=condition,
                    financing_available=financing_available,
                    inventory_status=inventory_status,
                    projected_margin=projected_margin,
                    features=features,
                )
            )

        for name, email, zip_code, budget_min, budget_max, preferred_brand, preferred_body_type, financing_preference, urgency, events in BUYER_FIXTURES:
            coords = zip_to_coordinates(zip_code)
            db.add(
                Buyer(
                    name=name,
                    email=email,
                    zip_code=zip_code,
                    latitude=coords[0] if coords else None,
                    longitude=coords[1] if coords else None,
                    budget_min=budget_min,
                    budget_max=budget_max,
                    preferred_brand=preferred_brand,
                    preferred_body_type=preferred_body_type,
                    financing_preference=financing_preference,
                    urgency=urgency,
                    browsing_profile={"recent_events": events},
                )
            )

        db.add(
            Experiment(
                name="ranking-strategy-v1",
                description="Compares rule-based heuristic ranking against the live Bayesian posterior ranking.",
                status=ExperimentStatus.ACTIVE,
                control_arm=ExperimentArm.HEURISTIC,
                treatment_arm=ExperimentArm.BAYESIAN,
                traffic_split=0.5,
            )
        )
        db.commit()
    finally:
        db.close()


def _seed_history() -> None:
    db = get_session()
    rng = Random(42)
    try:
        if db.scalar(select(func.count(Event.id))) > 0:
            return

        buyers = db.execute(select(Buyer).order_by(Buyer.id.asc())).scalars().all()
        now = datetime.now(timezone.utc)

        for day_offset in range(14, 0, -1):
            served_at = now - timedelta(days=day_offset)
            for buyer in buyers:
                response = generate_recommendations(
                    db,
                    RecommendationRequest(buyer_id=buyer.id, top_k=5),
                    persist=True,
                    served_at=served_at,
                )
                top_items = response.recommendations[:3]
                for item in top_items:
                    base_details = {"seeded": True, "day_offset": day_offset}
                    click_threshold = 0.44 if response.experiment_arm == ExperimentArm.BAYESIAN else 0.51
                    if item.purchase_probability >= click_threshold or rng.random() < 0.22:
                        db.add(
                            Event(
                                buyer_id=buyer.id,
                                vehicle_id=item.vehicle_id,
                                dealer_id=item.dealer_id,
                                recommendation_id=item.recommendation_id,
                                event_type=EventType.CLICK,
                                experiment_arm=response.experiment_arm,
                                details=base_details,
                                created_at=served_at + timedelta(hours=1, minutes=item.rank * 3),
                            )
                        )

                    if item.rank <= 2 and item.purchase_probability >= 0.58:
                        db.add(
                            Event(
                                buyer_id=buyer.id,
                                vehicle_id=item.vehicle_id,
                                dealer_id=item.dealer_id,
                                recommendation_id=item.recommendation_id,
                                event_type=EventType.SAVE,
                                experiment_arm=response.experiment_arm,
                                details=base_details,
                                created_at=served_at + timedelta(hours=4),
                            )
                        )

                    if item.rank == 1 and buyer.urgency == UrgencyLevel.HIGH and item.purchase_probability >= 0.62:
                        db.add(
                            Event(
                                buyer_id=buyer.id,
                                vehicle_id=item.vehicle_id,
                                dealer_id=item.dealer_id,
                                recommendation_id=item.recommendation_id,
                                event_type=EventType.TEST_DRIVE_REQUEST,
                                experiment_arm=response.experiment_arm,
                                details=base_details,
                                created_at=served_at + timedelta(hours=8),
                            )
                        )
                        db.add(
                            Event(
                                buyer_id=buyer.id,
                                vehicle_id=item.vehicle_id,
                                dealer_id=item.dealer_id,
                                recommendation_id=item.recommendation_id,
                                event_type=EventType.DEALER_RESPONSE,
                                experiment_arm=response.experiment_arm,
                                details={"seeded": True, "response_minutes": 22},
                                created_at=served_at + timedelta(hours=8, minutes=22),
                            )
                        )

                    conversion_threshold = 0.72 if response.experiment_arm == ExperimentArm.BAYESIAN else 0.81
                    conversion_random = 0.48 if response.experiment_arm == ExperimentArm.BAYESIAN else 0.18
                    if item.rank == 1 and item.purchase_probability >= conversion_threshold and rng.random() < conversion_random:
                        vehicle = db.get(Vehicle, item.vehicle_id)
                        sale_price = float(vehicle.price) if vehicle else item.price
                        dealer = db.get(Dealer, item.dealer_id)
                        commission_revenue = sale_price * dealer.commission_rate if dealer else sale_price * 0.08
                        db.add(
                            Event(
                                buyer_id=buyer.id,
                                vehicle_id=item.vehicle_id,
                                dealer_id=item.dealer_id,
                                recommendation_id=item.recommendation_id,
                                event_type=EventType.CONVERSION,
                                experiment_arm=response.experiment_arm,
                                details={"seeded": True, "sale_price": sale_price},
                                created_at=served_at + timedelta(days=1),
                            )
                        )
                        db.add(
                            Conversion(
                                buyer_id=buyer.id,
                                vehicle_id=item.vehicle_id,
                                dealer_id=item.dealer_id,
                                recommendation_id=item.recommendation_id,
                                experiment_arm=response.experiment_arm,
                                sale_price=sale_price,
                                commission_revenue=commission_revenue,
                                converted_at=served_at + timedelta(days=1),
                            )
                        )

                if top_items and rng.random() < 0.2:
                    rejected = top_items[-1]
                    db.add(
                        Event(
                            buyer_id=buyer.id,
                            vehicle_id=rejected.vehicle_id,
                            dealer_id=rejected.dealer_id,
                            recommendation_id=rejected.recommendation_id,
                            event_type=EventType.REJECT,
                            experiment_arm=response.experiment_arm,
                            details={"seeded": True},
                            created_at=served_at + timedelta(hours=2),
                        )
                    )

            db.commit()

        recompute_priors_from_history(db)
        refresh_dealer_quality_scores(db)
        cache_analytics_snapshot(db)
    finally:
        db.close()


def seed_demo_data() -> None:
    _seed_users_and_entities()
    _seed_history()

