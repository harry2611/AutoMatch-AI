"""Unit tests for the Bayesian prior engine (app/services/bayesian.py)."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from app.models.entities import BayesianPrior, Buyer, Dealer, Vehicle
from app.models.enums import (
    BodyType,
    EventType,
    FinancingPreference,
    InventoryStatus,
    UrgencyLevel,
    VehicleCondition,
)
from app.services.bayesian import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    EVENT_IMPACT,
    posterior_mean,
    segment_key,
    _default_mean,
    _segments_for_feedback,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prior(segment_type: str, key: str, alpha: float, beta: float) -> BayesianPrior:
    prior = BayesianPrior()
    prior.segment_type = segment_type
    prior.segment_key = key
    prior.alpha = alpha
    prior.beta = beta
    return prior


def _make_lookup(*priors: BayesianPrior) -> dict:
    return {(p.segment_type, p.segment_key): p for p in priors}


def _make_buyer(
    zip_code: str = "94103",
    financing: FinancingPreference = FinancingPreference.LOAN,
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM,
) -> Buyer:
    b = Buyer()
    b.zip_code = zip_code
    b.financing_preference = financing
    b.urgency = urgency
    return b


def _make_dealer(dealer_id: int = 1) -> Dealer:
    d = Dealer()
    d.id = dealer_id
    return d


def _make_vehicle(brand: str = "Toyota", body_type: BodyType = BodyType.SUV) -> Vehicle:
    v = Vehicle()
    v.brand = brand
    v.body_type = body_type
    return v


# ---------------------------------------------------------------------------
# segment_key
# ---------------------------------------------------------------------------

class TestSegmentKey:
    def test_returns_tuple(self):
        assert segment_key("dealer", 7) == ("dealer", "7")

    def test_none_becomes_unknown(self):
        assert segment_key("market", None) == ("market", "unknown")

    def test_string_key(self):
        assert segment_key("brand", "toyota") == ("brand", "toyota")


# ---------------------------------------------------------------------------
# _default_mean
# ---------------------------------------------------------------------------

class TestDefaultMean:
    def test_default_params(self):
        result = _default_mean()
        assert abs(result - DEFAULT_ALPHA / (DEFAULT_ALPHA + DEFAULT_BETA)) < 1e-9

    def test_custom_params(self):
        result = _default_mean(alpha=1.0, beta=9.0)
        assert abs(result - 0.1) < 1e-9

    def test_result_between_zero_and_one(self):
        for alpha in [0.5, 1.0, 2.0, 10.0]:
            for beta in [0.5, 1.0, 5.0, 20.0]:
                assert 0 < _default_mean(alpha, beta) < 1


# ---------------------------------------------------------------------------
# posterior_mean
# ---------------------------------------------------------------------------

class TestPosteriorMean:
    def test_known_prior(self):
        prior = _make_prior("dealer", "1", alpha=5.0, beta=5.0)
        lookup = _make_lookup(prior)
        result = posterior_mean(lookup, "dealer", 1)
        assert abs(result - 0.5) < 1e-9

    def test_missing_prior_returns_default(self):
        lookup: dict = {}
        result = posterior_mean(lookup, "dealer", 999)
        expected = DEFAULT_ALPHA / (DEFAULT_ALPHA + DEFAULT_BETA)
        assert abs(result - expected) < 1e-9

    def test_high_alpha_gives_high_probability(self):
        prior = _make_prior("brand", "honda", alpha=20.0, beta=2.0)
        lookup = _make_lookup(prior)
        result = posterior_mean(lookup, "brand", "honda")
        assert result > 0.85

    def test_high_beta_gives_low_probability(self):
        prior = _make_prior("brand", "ford", alpha=1.0, beta=19.0)
        lookup = _make_lookup(prior)
        result = posterior_mean(lookup, "brand", "ford")
        assert result < 0.1

    def test_none_key_uses_unknown_segment(self):
        prior = _make_prior("market", "unknown", alpha=3.0, beta=7.0)
        lookup = _make_lookup(prior)
        result = posterior_mean(lookup, "market", None)
        assert abs(result - 0.3) < 1e-9


# ---------------------------------------------------------------------------
# EVENT_IMPACT
# ---------------------------------------------------------------------------

class TestEventImpact:
    def test_conversion_has_highest_alpha_delta(self):
        conversion_alpha, _ = EVENT_IMPACT[EventType.CONVERSION]
        for event_type, (alpha_delta, _) in EVENT_IMPACT.items():
            if event_type != EventType.CONVERSION:
                assert conversion_alpha >= alpha_delta, (
                    f"Conversion alpha {conversion_alpha} < {event_type} alpha {alpha_delta}"
                )

    def test_reject_has_highest_beta_delta(self):
        _, reject_beta = EVENT_IMPACT[EventType.REJECT]
        for event_type, (_, beta_delta) in EVENT_IMPACT.items():
            if event_type != EventType.REJECT:
                assert reject_beta >= beta_delta, (
                    f"Reject beta {reject_beta} < {event_type} beta {beta_delta}"
                )

    def test_all_deltas_positive(self):
        for event_type, (alpha_delta, beta_delta) in EVENT_IMPACT.items():
            assert alpha_delta > 0, f"{event_type} alpha_delta not positive"
            assert beta_delta > 0, f"{event_type} beta_delta not positive"


# ---------------------------------------------------------------------------
# _segments_for_feedback
# ---------------------------------------------------------------------------

class TestSegmentsForFeedback:
    def test_returns_expected_segment_types(self):
        buyer = _make_buyer()
        dealer = _make_dealer()
        vehicle = _make_vehicle()
        segments = list(_segments_for_feedback(buyer, vehicle, dealer))
        types = [s[0] for s in segments]
        assert "market" in types
        assert "dealer" in types
        assert "brand" in types
        assert "body_type" in types
        assert "financing" in types
        assert "urgency" in types
        assert "zip_prefix" in types

    def test_zip_prefix_uses_first_three_digits(self):
        buyer = _make_buyer(zip_code="94103")
        dealer = _make_dealer()
        vehicle = _make_vehicle()
        segments = dict(_segments_for_feedback(buyer, vehicle, dealer))
        assert segments["zip_prefix"] == "941"

    def test_market_key_is_all(self):
        buyer = _make_buyer()
        dealer = _make_dealer()
        vehicle = _make_vehicle()
        segments = dict(_segments_for_feedback(buyer, vehicle, dealer))
        assert segments["market"] == "all"
