from __future__ import annotations

import math


ZIP_COORDINATES: dict[str, tuple[float, float]] = {
    "90001": (33.973951, -118.248405),
    "90012": (34.061396, -118.239624),
    "90017": (34.052949, -118.266693),
    "92618": (33.659523, -117.732498),
    "94016": (37.687924, -122.470207),
    "94063": (37.492596, -122.228455),
    "94103": (37.772640, -122.409915),
    "94107": (37.769722, -122.393301),
    "94607": (37.804363, -122.271111),
}


def zip_to_coordinates(zip_code: str) -> tuple[float, float] | None:
    return ZIP_COORDINATES.get(zip_code)


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_miles * c

