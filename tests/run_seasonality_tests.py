"""
Simple test runner for seasonality tests (no pytest required).
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add paths
engine_path = str(Path(__file__).parent.parent / "ob_str_engine" / "engine")
sys.path.insert(0, engine_path)

from seasonality import (
    get_default_market_profiles,
    get_market_profile,
    get_default_market_name,
    get_seasonal_factors,
    calculate_seasonal_revenue,
    calculate_annual_seasonal_average,
    validate_market_profile,
    is_seasonality_enabled,
    get_market_baseline,
    get_market_expenses,
    SeasonalFactors,
    ORANGE_BEACH_ADR_MULTIPLIERS,
    ORANGE_BEACH_OCCUPANCY_MULTIPLIERS,
    FLAT_MULTIPLIERS,
)


def test_default_profiles_exist():
    """Default profiles include orange_beach and generic."""
    profiles = get_default_market_profiles()
    assert "orange_beach" in profiles, "orange_beach not in profiles"
    assert "generic" in profiles, "generic not in profiles"
    print("✓ test_default_profiles_exist")


def test_orange_beach_has_seasonality():
    """Orange Beach profile has seasonality enabled."""
    profiles = get_default_market_profiles()
    ob = profiles["orange_beach"]
    assert ob["seasonality_enabled"] is True, "seasonality_enabled should be True"
    print("✓ test_orange_beach_has_seasonality")


def test_generic_flat_seasonality():
    """Generic profile has flat seasonality (disabled)."""
    profiles = get_default_market_profiles()
    generic = profiles["generic"]
    assert generic["seasonality_enabled"] is False, "generic should be disabled"
    print("✓ test_generic_flat_seasonality")


def test_orange_beach_multipliers_length():
    """Orange Beach multipliers have 12 values each."""
    assert len(ORANGE_BEACH_ADR_MULTIPLIERS) == 12, "ADR multipliers should have 12 values"
    assert len(ORANGE_BEACH_OCCUPANCY_MULTIPLIERS) == 12, "Occ multipliers should have 12 values"
    print("✓ test_orange_beach_multipliers_length")


def test_flat_multipliers_all_ones():
    """Flat multipliers are all 1.0."""
    assert all(m == 1.0 for m in FLAT_MULTIPLIERS), "Flat multipliers should all be 1.0"
    assert len(FLAT_MULTIPLIERS) == 12, "Flat multipliers should have 12 values"
    print("✓ test_flat_multipliers_all_ones")


def test_get_profile_from_config():
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
    assert profile is not None, "Profile should not be None"
    assert profile["display_name"] == "Test Market", "Display name should match"
    print("✓ test_get_profile_from_config")


def test_get_profile_falls_back_to_defaults():
    """Falls back to defaults when profile not in config."""
    config = {"market_profiles": {}}
    profile = get_market_profile(config, "orange_beach")
    assert profile is not None, "Profile should not be None"
    assert profile["seasonality_enabled"] is True, "Should have seasonality enabled"
    print("✓ test_get_profile_falls_back_to_defaults")


def test_get_profile_unknown_returns_none():
    """Unknown profile returns None."""
    config = {"market_profiles": {}}
    profile = get_market_profile(config, "unknown_market")
    assert profile is None, "Unknown profile should return None"
    print("✓ test_get_profile_unknown_returns_none")


def test_default_market_name_from_config():
    """Get default market from config policies."""
    config = {
        "policies": {
            "portfolio": {
                "default_market": "custom_market"
            }
        }
    }
    name = get_default_market_name(config)
    assert name == "custom_market", f"Expected custom_market, got {name}"
    print("✓ test_default_market_name_from_config")


def test_default_market_name_fallback():
    """Default market falls back to orange_beach."""
    config = {}
    name = get_default_market_name(config)
    assert name == "orange_beach", f"Expected orange_beach, got {name}"
    print("✓ test_default_market_name_fallback")


def test_peak_season_factors():
    """Peak season (July) has high multipliers."""
    config = {"market_profiles": get_default_market_profiles()}
    factors = get_seasonal_factors(config, "orange_beach", 7)

    assert factors.calendar_month == 7, f"Expected month 7, got {factors.calendar_month}"
    assert factors.adr_multiplier == 1.35, f"Expected 1.35, got {factors.adr_multiplier}"
    assert factors.occupancy_multiplier == 1.15, f"Expected 1.15, got {factors.occupancy_multiplier}"
    assert factors.seasonality_enabled is True, "Should be enabled"
    print("✓ test_peak_season_factors")


def test_off_season_factors():
    """Off-season (January) has low multipliers."""
    config = {"market_profiles": get_default_market_profiles()}
    factors = get_seasonal_factors(config, "orange_beach", 1)

    assert factors.calendar_month == 1, f"Expected month 1, got {factors.calendar_month}"
    assert factors.adr_multiplier == 0.85, f"Expected 0.85, got {factors.adr_multiplier}"
    assert factors.occupancy_multiplier == 0.58, f"Expected 0.58, got {factors.occupancy_multiplier}"
    print("✓ test_off_season_factors")


def test_month_wraparound():
    """Month 13 wraps to January."""
    config = {"market_profiles": get_default_market_profiles()}
    factors = get_seasonal_factors(config, "orange_beach", 13)
    assert factors.calendar_month == 1, f"Expected month 1, got {factors.calendar_month}"
    print("✓ test_month_wraparound")


def test_disabled_seasonality_returns_flat():
    """Disabled seasonality returns 1.0 multipliers."""
    config = {"market_profiles": get_default_market_profiles()}
    factors = get_seasonal_factors(config, "generic", 7)

    assert factors.adr_multiplier == 1.0, f"Expected 1.0, got {factors.adr_multiplier}"
    assert factors.occupancy_multiplier == 1.0, f"Expected 1.0, got {factors.occupancy_multiplier}"
    assert factors.seasonality_enabled is False, "Should be disabled"
    print("✓ test_disabled_seasonality_returns_flat")


def test_unknown_market_returns_flat():
    """Unknown market returns flat multipliers."""
    config = {"market_profiles": {}}
    factors = get_seasonal_factors(config, "unknown", 7)

    assert factors.adr_multiplier == 1.0, f"Expected 1.0, got {factors.adr_multiplier}"
    assert factors.occupancy_multiplier == 1.0, f"Expected 1.0, got {factors.occupancy_multiplier}"
    assert factors.seasonality_enabled is False, "Should be disabled"
    print("✓ test_unknown_market_returns_flat")


def test_peak_season_revenue_higher():
    """Peak season revenue is higher than flat."""
    base_adr = 425.0
    base_occ = 0.78
    days = 31

    peak_factors = SeasonalFactors(
        adr_multiplier=1.35,
        occupancy_multiplier=1.15,
        calendar_month=7,
        market_name="orange_beach",
        seasonality_enabled=True
    )

    revenue, details = calculate_seasonal_revenue(base_adr, base_occ, days, peak_factors)
    flat_revenue = base_adr * base_occ * days

    assert revenue > flat_revenue, f"Seasonal {revenue} should be > flat {flat_revenue}"
    assert details["seasonal_delta"] > 0, "Delta should be positive"
    print("✓ test_peak_season_revenue_higher")


def test_off_season_revenue_lower():
    """Off-season revenue is lower than flat."""
    base_adr = 425.0
    base_occ = 0.78
    days = 31

    off_factors = SeasonalFactors(
        adr_multiplier=0.85,
        occupancy_multiplier=0.58,
        calendar_month=1,
        market_name="orange_beach",
        seasonality_enabled=True
    )

    revenue, details = calculate_seasonal_revenue(base_adr, base_occ, days, off_factors)
    flat_revenue = base_adr * base_occ * days

    assert revenue < flat_revenue, f"Seasonal {revenue} should be < flat {flat_revenue}"
    assert details["seasonal_delta"] < 0, "Delta should be negative"
    print("✓ test_off_season_revenue_lower")


def test_flat_factors_match_baseline():
    """Flat factors produce same revenue as baseline calculation."""
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

    revenue, details = calculate_seasonal_revenue(base_adr, base_occ, days, flat_factors)
    expected = base_adr * base_occ * days

    assert abs(revenue - expected) < 0.01, f"Revenue {revenue} should match expected {expected}"
    assert details["seasonal_delta"] == 0, "Delta should be 0"
    print("✓ test_flat_factors_match_baseline")


def test_seasonal_annual_less_than_flat():
    """Seasonal annual revenue is typically less than flat for OB."""
    config = {"market_profiles": get_default_market_profiles()}
    calendar_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    seasonal_annual, eff_occ = calculate_annual_seasonal_average(
        config, "orange_beach", 425.0, 0.78, calendar_days
    )

    flat_annual = 425.0 * 0.78 * 365
    assert seasonal_annual < flat_annual, f"Seasonal {seasonal_annual} should be < flat {flat_annual}"
    print("✓ test_seasonal_annual_less_than_flat")


def test_effective_occupancy_lower_than_baseline():
    """Effective occupancy is lower than baseline for OB seasonal pattern."""
    config = {"market_profiles": get_default_market_profiles()}
    calendar_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    _, eff_occ = calculate_annual_seasonal_average(
        config, "orange_beach", 425.0, 0.78, calendar_days
    )

    assert eff_occ < 0.78, f"Effective occupancy {eff_occ} should be < 0.78"
    print("✓ test_effective_occupancy_lower_than_baseline")


def test_valid_profile_passes():
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
    assert len(issues) == 0, f"Expected no issues, got {issues}"
    print("✓ test_valid_profile_passes")


def test_missing_baseline_fails():
    """Missing baseline section is flagged."""
    profile = {"seasonality_enabled": True}
    issues = validate_market_profile(profile, "test")
    assert any("baseline" in issue.lower() for issue in issues), f"Should flag missing baseline, got {issues}"
    print("✓ test_missing_baseline_fails")


def test_invalid_multiplier_count_fails():
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
    assert any("12" in issue for issue in issues), f"Should flag wrong count, got {issues}"
    print("✓ test_invalid_multiplier_count_fails")


def test_out_of_range_multiplier_fails():
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
    assert any("out of range" in issue.lower() for issue in issues), f"Should flag out of range, got {issues}"
    print("✓ test_out_of_range_multiplier_fails")


def test_enabled_when_profile_has_seasonality():
    """Returns True when any profile has seasonality enabled."""
    config = {
        "market_profiles": {
            "test": {"seasonality_enabled": True}
        }
    }
    assert is_seasonality_enabled(config) is True, "Should be enabled"
    print("✓ test_enabled_when_profile_has_seasonality")


def test_disabled_when_no_profiles():
    """Returns True when no market profiles exist (falls back to default)."""
    config = {}
    result = is_seasonality_enabled(config)
    assert result is True, "Should be True (orange_beach default has seasonality)"
    print("✓ test_disabled_when_no_profiles")


def test_disabled_when_all_profiles_disabled():
    """Returns False when all profiles have seasonality disabled."""
    config = {
        "market_profiles": {
            "flat1": {"seasonality_enabled": False},
            "flat2": {"seasonality_enabled": False}
        },
        "policies": {"portfolio": {"default_market": "flat1"}}
    }
    assert is_seasonality_enabled(config) is False, "Should be disabled"
    print("✓ test_disabled_when_all_profiles_disabled")


def test_baseline_fallback_to_ops():
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
    assert adr == 500.0, f"Expected 500.0, got {adr}"
    assert occ == 0.80, f"Expected 0.80, got {occ}"
    print("✓ test_baseline_fallback_to_ops")


def test_expenses_fallback_to_ops():
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
    assert expenses["insurance_rate"] == 0.04, f"Expected 0.04, got {expenses['insurance_rate']}"
    assert expenses["property_tax_rate"] == 0.006, f"Expected 0.006, got {expenses['property_tax_rate']}"
    assert expenses["hoa_annual"] == 15000.0, f"Expected 15000.0, got {expenses['hoa_annual']}"
    print("✓ test_expenses_fallback_to_ops")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Seasonality Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_profiles_exist,
        test_orange_beach_has_seasonality,
        test_generic_flat_seasonality,
        test_orange_beach_multipliers_length,
        test_flat_multipliers_all_ones,
        test_get_profile_from_config,
        test_get_profile_falls_back_to_defaults,
        test_get_profile_unknown_returns_none,
        test_default_market_name_from_config,
        test_default_market_name_fallback,
        test_peak_season_factors,
        test_off_season_factors,
        test_month_wraparound,
        test_disabled_seasonality_returns_flat,
        test_unknown_market_returns_flat,
        test_peak_season_revenue_higher,
        test_off_season_revenue_lower,
        test_flat_factors_match_baseline,
        test_seasonal_annual_less_than_flat,
        test_effective_occupancy_lower_than_baseline,
        test_valid_profile_passes,
        test_missing_baseline_fails,
        test_invalid_multiplier_count_fails,
        test_out_of_range_multiplier_fails,
        test_enabled_when_profile_has_seasonality,
        test_disabled_when_no_profiles,
        test_disabled_when_all_profiles_disabled,
        test_baseline_fallback_to_ops,
        test_expenses_fallback_to_ops,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
