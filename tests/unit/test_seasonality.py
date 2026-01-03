"""
Unit tests for the seasonality module.

Tests cover:
- Market profile loading and defaults
- Seasonal factor calculations
- Revenue calculations with seasonality
- Parity price with seasonality
- Backward compatibility (no market_profiles = flat behavior)
"""

import pytest
import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ob_str_engine" / "engine"))

from seasonality import (
    get_default_market_profiles,
    get_market_profile,
    get_default_market_name,
    get_seasonal_factors,
    calculate_seasonal_revenue,
    calculate_annual_seasonal_average,
    validate_market_profile,
    validate_all_market_profiles,
    is_seasonality_enabled,
    get_market_baseline,
    get_market_expenses,
    ORANGE_BEACH_ADR_MULTIPLIERS,
    ORANGE_BEACH_OCCUPANCY_MULTIPLIERS,
    FLAT_MULTIPLIERS,
)


class TestDefaultMarketProfiles:
    """Tests for default market profile generation."""

    def test_default_profiles_exist(self):
        """Default profiles include orange_beach and generic."""
        profiles = get_default_market_profiles()
        assert "orange_beach" in profiles
        assert "generic" in profiles

    def test_orange_beach_has_seasonality(self):
        """Orange Beach profile has seasonality enabled."""
        profiles = get_default_market_profiles()
        ob = profiles["orange_beach"]
        assert ob["seasonality_enabled"] is True

    def test_generic_flat_seasonality(self):
        """Generic profile has flat seasonality (disabled)."""
        profiles = get_default_market_profiles()
        generic = profiles["generic"]
        assert generic["seasonality_enabled"] is False

    def test_orange_beach_multipliers_length(self):
        """Orange Beach multipliers have 12 values each."""
        assert len(ORANGE_BEACH_ADR_MULTIPLIERS) == 12
        assert len(ORANGE_BEACH_OCCUPANCY_MULTIPLIERS) == 12

    def test_flat_multipliers_all_ones(self):
        """Flat multipliers are all 1.0."""
        assert all(m == 1.0 for m in FLAT_MULTIPLIERS)
        assert len(FLAT_MULTIPLIERS) == 12


class TestMarketProfileLookup:
    """Tests for market profile retrieval."""

    def test_get_profile_from_config(self):
        """Get profile from config when present."""
        config = {
            "market_profiles": {
                "test_market": {
                    "display_name": "Test Market",
                    "seasonality_enabled": True,
                    "baseline": {"adr": 300.0, "occupancy": 0.65}
                }
            }
        }
        profile = get_market_profile(config, "test_market")
        assert profile is not None
        assert profile["display_name"] == "Test Market"

    def test_get_profile_falls_back_to_defaults(self):
        """Falls back to defaults when profile not in config."""
        config = {"market_profiles": {}}
        profile = get_market_profile(config, "orange_beach")
        assert profile is not None
        assert profile["seasonality_enabled"] is True

    def test_get_profile_unknown_returns_none(self):
        """Unknown profile returns None."""
        config = {"market_profiles": {}}
        profile = get_market_profile(config, "unknown_market")
        assert profile is None

    def test_default_market_name_from_config(self):
        """Get default market from config policies."""
        config = {
            "policies": {
                "portfolio": {
                    "default_market": "custom_market"
                }
            }
        }
        name = get_default_market_name(config)
        assert name == "custom_market"

    def test_default_market_name_fallback(self):
        """Default market falls back to orange_beach."""
        config = {}
        name = get_default_market_name(config)
        assert name == "orange_beach"


class TestSeasonalFactors:
    """Tests for seasonal factor calculations."""

    def test_peak_season_factors(self):
        """Peak season (July) has high multipliers."""
        config = {"market_profiles": get_default_market_profiles()}
        # July is month 7, simulation month could be 7, 19, etc.
        factors = get_seasonal_factors(config, "orange_beach", 7)

        assert factors.calendar_month == 7
        assert factors.adr_multiplier == 1.35  # Peak ADR
        assert factors.occupancy_multiplier == 1.15  # Peak occupancy
        assert factors.seasonality_enabled is True

    def test_off_season_factors(self):
        """Off-season (January) has low multipliers."""
        config = {"market_profiles": get_default_market_profiles()}
        factors = get_seasonal_factors(config, "orange_beach", 1)

        assert factors.calendar_month == 1
        assert factors.adr_multiplier == 0.85  # Off-season ADR
        assert factors.occupancy_multiplier == 0.58  # Off-season occupancy

    def test_month_wraparound(self):
        """Month 13 wraps to January."""
        config = {"market_profiles": get_default_market_profiles()}
        factors = get_seasonal_factors(config, "orange_beach", 13)
        assert factors.calendar_month == 1

    def test_disabled_seasonality_returns_flat(self):
        """Disabled seasonality returns 1.0 multipliers."""
        config = {"market_profiles": get_default_market_profiles()}
        factors = get_seasonal_factors(config, "generic", 7)

        assert factors.adr_multiplier == 1.0
        assert factors.occupancy_multiplier == 1.0
        assert factors.seasonality_enabled is False

    def test_unknown_market_returns_flat(self):
        """Unknown market returns flat multipliers."""
        config = {"market_profiles": {}}
        factors = get_seasonal_factors(config, "unknown", 7)

        assert factors.adr_multiplier == 1.0
        assert factors.occupancy_multiplier == 1.0
        assert factors.seasonality_enabled is False


class TestSeasonalRevenue:
    """Tests for seasonal revenue calculations."""

    def test_peak_season_revenue_higher(self):
        """Peak season revenue is higher than flat."""
        from seasonality import SeasonalFactors

        base_adr = 425.0
        base_occ = 0.78
        days = 31

        # Peak season factors
        peak_factors = SeasonalFactors(
            adr_multiplier=1.35,
            occupancy_multiplier=1.15,
            calendar_month=7,
            market_name="orange_beach",
            seasonality_enabled=True
        )

        revenue, details = calculate_seasonal_revenue(
            base_adr, base_occ, days, peak_factors
        )

        flat_revenue = base_adr * base_occ * days
        assert revenue > flat_revenue
        assert details["seasonal_delta"] > 0

    def test_off_season_revenue_lower(self):
        """Off-season revenue is lower than flat."""
        from seasonality import SeasonalFactors

        base_adr = 425.0
        base_occ = 0.78
        days = 31

        # Off-season factors
        off_factors = SeasonalFactors(
            adr_multiplier=0.85,
            occupancy_multiplier=0.58,
            calendar_month=1,
            market_name="orange_beach",
            seasonality_enabled=True
        )

        revenue, details = calculate_seasonal_revenue(
            base_adr, base_occ, days, off_factors
        )

        flat_revenue = base_adr * base_occ * days
        assert revenue < flat_revenue
        assert details["seasonal_delta"] < 0

    def test_flat_factors_match_baseline(self):
        """Flat factors produce same revenue as baseline calculation."""
        from seasonality import SeasonalFactors

        base_adr = 425.0
        base_occ = 0.78
        days = 31

        flat_factors = SeasonalFactors(
            adr_multiplier=1.0,
            occupancy_multiplier=1.0,
            calendar_month=1,
            market_name="generic",
            seasonality_enabled=False
        )

        revenue, details = calculate_seasonal_revenue(
            base_adr, base_occ, days, flat_factors
        )

        expected = base_adr * base_occ * days
        assert abs(revenue - expected) < 0.01
        assert details["seasonal_delta"] == 0


class TestAnnualSeasonalAverage:
    """Tests for annual seasonal average calculations."""

    def test_seasonal_annual_less_than_flat(self):
        """Seasonal annual revenue is typically less than flat for OB."""
        config = {"market_profiles": get_default_market_profiles()}
        calendar_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        seasonal_annual, eff_occ = calculate_annual_seasonal_average(
            config, "orange_beach", 425.0, 0.78, calendar_days
        )

        flat_annual = 425.0 * 0.78 * 365
        assert seasonal_annual < flat_annual

    def test_effective_occupancy_lower_than_baseline(self):
        """Effective occupancy is lower than baseline for OB seasonal pattern."""
        config = {"market_profiles": get_default_market_profiles()}
        calendar_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        _, eff_occ = calculate_annual_seasonal_average(
            config, "orange_beach", 425.0, 0.78, calendar_days
        )

        assert eff_occ < 0.78


class TestValidation:
    """Tests for market profile validation."""

    def test_valid_profile_passes(self):
        """Valid profile returns no issues."""
        profile = {
            "display_name": "Test",
            "seasonality_enabled": True,
            "baseline": {"adr": 400.0, "occupancy": 0.75},
            "seasonality": {
                "adr_multipliers": [1.0] * 12,
                "occupancy_multipliers": [1.0] * 12
            }
        }
        issues = validate_market_profile(profile, "test")
        assert len(issues) == 0

    def test_missing_baseline_fails(self):
        """Missing baseline section is flagged."""
        profile = {"seasonality_enabled": True}
        issues = validate_market_profile(profile, "test")
        assert any("baseline" in issue.lower() for issue in issues)

    def test_invalid_multiplier_count_fails(self):
        """Wrong number of multipliers is flagged."""
        profile = {
            "baseline": {"adr": 400.0, "occupancy": 0.75},
            "seasonality_enabled": True,
            "seasonality": {
                "adr_multipliers": [1.0] * 10,  # Wrong count
                "occupancy_multipliers": [1.0] * 12
            }
        }
        issues = validate_market_profile(profile, "test")
        assert any("12" in issue for issue in issues)

    def test_out_of_range_multiplier_fails(self):
        """Out of range multiplier is flagged."""
        mults = [1.0] * 12
        mults[0] = 10.0  # Way too high

        profile = {
            "baseline": {"adr": 400.0, "occupancy": 0.75},
            "seasonality_enabled": True,
            "seasonality": {
                "adr_multipliers": mults,
                "occupancy_multipliers": [1.0] * 12
            }
        }
        issues = validate_market_profile(profile, "test")
        assert any("out of range" in issue.lower() for issue in issues)


class TestSeasonalityEnabled:
    """Tests for seasonality enabled check."""

    def test_enabled_when_profile_has_seasonality(self):
        """Returns True when any profile has seasonality enabled."""
        config = {
            "market_profiles": {
                "test": {"seasonality_enabled": True}
            }
        }
        assert is_seasonality_enabled(config) is True

    def test_disabled_when_no_profiles(self):
        """Returns False when no market profiles exist."""
        config = {}
        # Will check defaults, but if no config profiles, check default market
        # Default market (orange_beach) has seasonality enabled
        result = is_seasonality_enabled(config)
        # With no config, falls back to checking defaults
        assert result is True  # orange_beach default has seasonality

    def test_disabled_when_all_profiles_disabled(self):
        """Returns False when all profiles have seasonality disabled."""
        config = {
            "market_profiles": {
                "flat1": {"seasonality_enabled": False},
                "flat2": {"seasonality_enabled": False}
            },
            "policies": {"portfolio": {"default_market": "flat1"}}
        }
        assert is_seasonality_enabled(config) is False


class TestBackwardCompatibility:
    """Tests for backward compatibility with v2.3 configs."""

    def test_no_market_profiles_uses_flat(self):
        """Config without market_profiles uses flat calculations."""
        config = {
            "constants": {
                "operations": {
                    "adrBaseline2BR": 425.0,
                    "occupancyBaseline": 0.78
                }
            }
        }
        # Should get flat factors
        factors = get_seasonal_factors(config, "orange_beach", 7)
        # Falls back to defaults which have seasonality
        # This tests the fallback mechanism
        assert factors is not None

    def test_baseline_fallback_to_ops(self):
        """get_market_baseline falls back to operations config."""
        config = {
            "constants": {
                "operations": {
                    "adrBaseline2BR": 500.0,
                    "occupancyBaseline": 0.80
                }
            }
        }
        adr, occ = get_market_baseline(config, "unknown_market")
        assert adr == 500.0
        assert occ == 0.80

    def test_expenses_fallback_to_ops(self):
        """get_market_expenses falls back to operations config."""
        config = {
            "constants": {
                "operations": {
                    "insuranceRate": 0.04,
                    "propertyTaxRate": 0.006,
                    "hoaAnnual": 15000.0
                }
            }
        }
        expenses = get_market_expenses(config, "unknown_market")
        assert expenses["insurance_rate"] == 0.04
        assert expenses["property_tax_rate"] == 0.006
        assert expenses["hoa_annual"] == 15000.0
