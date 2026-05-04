from __future__ import annotations

import logging
import math

logger = logging.getLogger(__name__)

# Coordinates for common California ZIP codes used in seeded demo data and
# likely buyer inputs.  Keys are 5-digit strings.  If a ZIP is not present,
# distance scoring falls back to a configurable default (see zip_to_coordinates).
ZIP_COORDINATES: dict[str, tuple[float, float]] = {
    # Los Angeles area
    "90001": (33.973951, -118.248405),
    "90012": (34.061396, -118.239624),
    "90017": (34.052949, -118.266693),
    "90024": (34.059808, -118.443200),
    "90025": (34.040297, -118.464088),
    "90028": (34.101597, -118.327514),
    "90036": (34.073814, -118.359329),
    "90049": (34.066097, -118.484177),
    "90210": (34.090280, -118.406500),
    "90291": (33.993729, -118.471588),
    "90401": (34.015498, -118.490784),
    "90402": (34.025700, -118.480500),
    # Orange County
    "92618": (33.659523, -117.732498),
    "92627": (33.636299, -117.920502),
    "92651": (33.544800, -117.778900),
    "92660": (33.622101, -117.873901),
    "92701": (33.745800, -117.867401),
    "92705": (33.750301, -117.831200),
    "92843": (33.759399, -117.930900),
    # San Diego
    "92101": (32.724098, -117.165901),
    "92103": (32.745201, -117.162399),
    "92108": (32.773399, -117.131302),
    "92121": (32.900002, -117.209503),
    "92130": (32.952599, -117.223297),
    # San Francisco / Peninsula
    "94016": (37.687924, -122.470207),
    "94025": (37.454201, -122.181999),
    "94027": (37.468399, -122.196899),
    "94063": (37.492596, -122.228455),
    "94065": (37.532902, -122.257698),
    "94103": (37.772640, -122.409915),
    "94105": (37.789101, -122.395302),
    "94107": (37.769722, -122.393301),
    "94110": (37.748501, -122.415298),
    "94117": (37.769699, -122.440102),
    "94122": (37.759800, -122.481903),
    "94132": (37.722599, -122.478302),
    # East Bay / Oakland
    "94501": (37.771599, -122.284103),
    "94601": (37.781700, -122.225800),
    "94607": (37.804363, -122.271111),
    "94609": (37.836201, -122.259598),
    "94611": (37.840599, -122.231201),
    "94618": (37.843899, -122.252502),
    # South Bay / Silicon Valley
    "94041": (37.389198, -122.082497),
    "94043": (37.398899, -122.074303),
    "94085": (37.387501, -122.012901),
    "94086": (37.378601, -122.031799),
    "94301": (37.442699, -122.148399),
    "94306": (37.424301, -122.126801),
    # Sacramento
    "95814": (38.581699, -121.493103),
    "95816": (38.567902, -121.474998),
    "95819": (38.563400, -121.449997),
    "95825": (38.599300, -121.397202),
    "95833": (38.620499, -121.513298),
    # Central Valley / Fresno
    "93701": (36.746601, -119.772598),
    "93710": (36.819302, -119.770203),
    "93720": (36.845001, -119.710503),
}


def zip_to_coordinates(zip_code: str) -> tuple[float, float] | None:
    """Return (latitude, longitude) for a ZIP code, or None if unknown.

    Unknown ZIPs are logged at WARNING level so operators can decide whether to
    expand the lookup table.  Callers should treat None as "distance unknown"
    and apply a sensible fallback (e.g. assume 25 miles).
    """
    coords = ZIP_COORDINATES.get(zip_code)
    if coords is None:
        logger.warning(
            "zip_to_coordinates: ZIP %s not in lookup table — distance will use fallback value.",
            zip_code,
        )
    return coords


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two lat/lon points."""
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

