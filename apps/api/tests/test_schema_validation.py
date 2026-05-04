"""Tests for Pydantic schema validators in app/schemas/domain.py."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.domain import RecommendationRequest


class TestRecommendationRequestValidation:
    """Budget, ZIP, and top_k validation on RecommendationRequest."""

    # --- top_k ---

    def test_top_k_clamped_to_minimum(self):
        req = RecommendationRequest(buyer_id=1, top_k=0)
        assert req.top_k == 1

    def test_top_k_clamped_to_maximum(self):
        req = RecommendationRequest(buyer_id=1, top_k=99)
        assert req.top_k == 10

    def test_top_k_valid_passthrough(self):
        req = RecommendationRequest(buyer_id=1, top_k=5)
        assert req.top_k == 5

    # --- zip_code ---

    def test_valid_zip_accepted(self):
        req = RecommendationRequest(zip_code="94103", budget_min=20000, budget_max=35000)
        assert req.zip_code == "94103"

    def test_zip_with_whitespace_is_stripped(self):
        req = RecommendationRequest(zip_code=" 94103 ", budget_min=20000, budget_max=35000)
        assert req.zip_code == "94103"

    def test_zip_too_short_raises(self):
        with pytest.raises(ValidationError, match="5-digit"):
            RecommendationRequest(zip_code="941", budget_min=20000, budget_max=35000)

    def test_zip_too_long_raises(self):
        with pytest.raises(ValidationError, match="5-digit"):
            RecommendationRequest(zip_code="941030", budget_min=20000, budget_max=35000)

    def test_zip_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="5-digit"):
            RecommendationRequest(zip_code="9410X", budget_min=20000, budget_max=35000)

    def test_zip_none_is_allowed(self):
        req = RecommendationRequest(buyer_id=1)
        assert req.zip_code is None

    # --- budget ---

    def test_budget_min_negative_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            RecommendationRequest(zip_code="94103", budget_min=-100, budget_max=35000)

    def test_budget_max_negative_raises(self):
        with pytest.raises(ValidationError, match="non-negative"):
            RecommendationRequest(zip_code="94103", budget_min=20000, budget_max=-1)

    def test_budget_min_equals_max_raises(self):
        with pytest.raises(ValidationError, match="budget_min must be less than budget_max"):
            RecommendationRequest(zip_code="94103", budget_min=30000, budget_max=30000)

    def test_budget_min_greater_than_max_raises(self):
        with pytest.raises(ValidationError, match="budget_min must be less than budget_max"):
            RecommendationRequest(zip_code="94103", budget_min=40000, budget_max=30000)

    def test_valid_budget_range_accepted(self):
        req = RecommendationRequest(zip_code="94103", budget_min=20000, budget_max=35000)
        assert req.budget_min == 20000
        assert req.budget_max == 35000

    def test_both_budgets_none_is_allowed(self):
        req = RecommendationRequest(buyer_id=1)
        assert req.budget_min is None
        assert req.budget_max is None

    def test_only_budget_min_set_no_cross_field_error(self):
        # Cross-field validation only fires when both are set
        req = RecommendationRequest(buyer_id=1, budget_min=20000)
        assert req.budget_min == 20000
        assert req.budget_max is None
