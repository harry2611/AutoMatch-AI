"""Unit tests for the recommendation scoring helpers in app/services/recommendation.py."""
from __future__ import annotations

import pytest

from app.models.enums import BodyType, InventoryStatus
from app.services.recommendation import (
    INVENTORY_FACTORS,
    _body_fit,
    _brand_fit,
    _affinity_score,
)
from app.utils.math_utils import clamp
from app.utils.geo import haversine_miles, zip_to_coordinates


# ---------------------------------------------------------------------------
# clamp
# ---------------------------------------------------------------------------

class TestClamp:
    def test_within_range(self):
        assert clamp(0.5) == 0.5

    def test_below_min(self):
        assert clamp(-1.0) == 0.0

    def test_above_max(self):
        assert clamp(2.0) == 1.0

    def test_at_min_boundary(self):
        assert clamp(0.0) == 0.0

    def test_at_max_boundary(self):
        assert clamp(1.0) == 1.0

    def test_custom_range(self):
        assert clamp(5.0, 1.0, 10.0) == 5.0
        assert clamp(0.0, 1.0, 10.0) == 1.0
        assert clamp(15.0, 1.0, 10.0) == 10.0


# ---------------------------------------------------------------------------
# _body_fit
# ---------------------------------------------------------------------------

class TestBodyFit:
    def test_exact_match(self):
        assert _body_fit(BodyType.SUV, BodyType.SUV) == 1.0

    def test_mismatch(self):
        score = _body_fit(BodyType.SUV, BodyType.SEDAN)
        assert score == 0.34

    def test_none_preference_returns_neutral(self):
        score = _body_fit(None, BodyType.SEDAN)
        assert score == 0.78

    def test_all_body_types_produce_valid_scores(self):
        for body_type in BodyType:
            score = _body_fit(BodyType.SUV, body_type)
            assert 0.0 <= score <= 1.0, f"Score out of range for {body_type}"


# ---------------------------------------------------------------------------
# _brand_fit
# ---------------------------------------------------------------------------

class TestBrandFit:
    def test_exact_match_case_insensitive(self):
        assert _brand_fit("Honda", "Honda") == 1.0
        assert _brand_fit("honda", "Honda") == 1.0
        assert _brand_fit("HONDA", "honda") == 1.0

    def test_mismatch(self):
        score = _brand_fit("Honda", "Toyota")
        assert score == 0.32

    def test_none_preference_returns_neutral(self):
        score = _brand_fit(None, "Toyota")
        assert score == 0.75

    def test_empty_string_preference_returns_neutral(self):
        score = _brand_fit("", "Toyota")
        assert score == 0.75


# ---------------------------------------------------------------------------
# _affinity_score
# ---------------------------------------------------------------------------

class TestAffinityScore:
    def test_neutral_when_no_history(self):
        score = _affinity_score({}, "suv")
        assert abs(score - 0.5) < 1e-9

    def test_positive_interactions_increase_score(self):
        profile = {"suv": 3}
        score = _affinity_score(profile, "suv")
        assert score > 0.5

    def test_negative_interactions_decrease_score(self):
        profile = {"sedan": -2}
        score = _affinity_score(profile, "sedan")
        assert score < 0.5

    def test_result_clamped_between_0_05_and_0_95(self):
        # Extreme positive
        score_high = _affinity_score({"suv": 100}, "suv")
        assert score_high <= 0.95

        # Extreme negative
        score_low = _affinity_score({"suv": -100}, "suv")
        assert score_low >= 0.05


# ---------------------------------------------------------------------------
# INVENTORY_FACTORS
# ---------------------------------------------------------------------------

class TestInventoryFactors:
    def test_high_inventory_is_1(self):
        assert INVENTORY_FACTORS[InventoryStatus.HIGH] == 1.0

    def test_factors_decrease_with_scarcity(self):
        assert (
            INVENTORY_FACTORS[InventoryStatus.HIGH]
            > INVENTORY_FACTORS[InventoryStatus.MEDIUM]
            > INVENTORY_FACTORS[InventoryStatus.LOW]
            > INVENTORY_FACTORS[InventoryStatus.LIMITED]
        )

    def test_all_factors_between_0_and_1(self):
        for status, factor in INVENTORY_FACTORS.items():
            assert 0.0 <= factor <= 1.0, f"Factor out of range for {status}"


# ---------------------------------------------------------------------------
# geo utilities
# ---------------------------------------------------------------------------

class TestHaversineMiles:
    def test_same_point_is_zero(self):
        assert haversine_miles(37.77, -122.41, 37.77, -122.41) == pytest.approx(0.0, abs=1e-6)

    def test_sf_to_la_roughly_337_miles(self):
        # SFO area to LAX area
        distance = haversine_miles(37.619, -122.374, 33.942, -118.408)
        assert 320 < distance < 360

    def test_symmetric(self):
        d1 = haversine_miles(37.77, -122.41, 34.05, -118.24)
        d2 = haversine_miles(34.05, -118.24, 37.77, -122.41)
        assert abs(d1 - d2) < 0.001


class TestZipToCoordinates:
    def test_known_zip_returns_coords(self):
        coords = zip_to_coordinates("94103")
        assert coords is not None
        lat, lon = coords
        assert 37.0 < lat < 38.0
        assert -123.0 < lon < -122.0

    def test_unknown_zip_returns_none(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="app.utils.geo"):
            result = zip_to_coordinates("00000")
        assert result is None
        assert "00000" in caplog.text

    def test_all_seeded_zips_resolve(self):
        seeded = ["94103", "94107", "94016", "94063", "94607", "92618", "90001", "90012", "90017"]
        for z in seeded:
            assert zip_to_coordinates(z) is not None, f"Seeded ZIP {z} not in lookup"
