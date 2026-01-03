"""
Simple test runner for insurance tests (no pytest required).
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

from insurance import (
    get_insurance_config,
    is_insurance_enhanced,
    calculate_base_premium,
    apply_insurance_inflation,
    calculate_flood_insurance,
    calculate_surcharge,
    calculate_deductible,
    calculate_unit_insurance,
    calculate_monthly_insurance,
    process_insurance_claim,
    calculate_portfolio_insurance,
    validate_insurance_config,
    estimate_annual_insurance_trend,
    DEFAULT_INSURANCE_CONFIG,
    MARKET_INSURANCE_DEFAULTS,
    InsurancePremium,
    InsuranceClaim,
)


def test_default_insurance_config():
    """Default insurance config has expected values."""
    assert DEFAULT_INSURANCE_CONFIG["enabled"] is False
    assert DEFAULT_INSURANCE_CONFIG["base_rate"] == 0.033
    assert DEFAULT_INSURANCE_CONFIG["inflation_rate"] == 0.03
    assert DEFAULT_INSURANCE_CONFIG["named_storm_deductible_pct"] == 0.02
    print("OK test_default_insurance_config")


def test_market_insurance_defaults():
    """Market-specific defaults exist."""
    assert "orange_beach" in MARKET_INSURANCE_DEFAULTS
    assert "generic" in MARKET_INSURANCE_DEFAULTS

    ob = MARKET_INSURANCE_DEFAULTS["orange_beach"]
    assert ob["base_rate"] == 0.04  # 4% for coastal
    assert ob["inflation_rate"] == 0.07  # 7% for coastal
    print("OK test_market_insurance_defaults")


def test_get_insurance_config_from_market_profile():
    """Get insurance config from market profile."""
    config = {
        "market_profiles": {
            "orange_beach": {
                "expenses": {
                    "insurance_rate": 0.045,
                    "insurance_inflation_rate": 0.08
                }
            }
        }
    }
    ins_cfg = get_insurance_config(config, "orange_beach")
    assert ins_cfg["base_rate"] == 0.045
    assert ins_cfg["inflation_rate"] == 0.08
    print("OK test_get_insurance_config_from_market_profile")


def test_get_insurance_config_falls_back_to_market_defaults():
    """Falls back to market defaults when not in profile."""
    config = {"market_profiles": {}}
    ins_cfg = get_insurance_config(config, "orange_beach")
    assert ins_cfg["base_rate"] == 0.04  # OB default
    assert ins_cfg["inflation_rate"] == 0.07  # OB default
    print("OK test_get_insurance_config_falls_back_to_market_defaults")


def test_get_insurance_config_falls_back_to_global_default():
    """Falls back to global default for unknown market."""
    config = {}
    ins_cfg = get_insurance_config(config, "unknown_market")
    assert ins_cfg["base_rate"] == 0.033  # Global default
    print("OK test_get_insurance_config_falls_back_to_global_default")


def test_is_insurance_enhanced():
    """Check if enhanced insurance is enabled."""
    config_enhanced = {
        "market_profiles": {
            "test": {"expenses": {"insurance_rate": 0.04}}
        }
    }
    config_not_enhanced = {"market_profiles": {}}

    assert is_insurance_enhanced(config_enhanced) is True
    assert is_insurance_enhanced(config_not_enhanced) is False
    print("OK test_is_insurance_enhanced")


def test_calculate_base_premium():
    """Calculate base insurance premium."""
    value = 700000
    rate = 0.04

    premium = calculate_base_premium(value, rate)
    expected = 700000 * 0.04  # $28,000
    assert premium == expected
    print("OK test_calculate_base_premium")


def test_apply_insurance_inflation_year_1():
    """No inflation in year 1."""
    base = 28000
    years = 1
    rate = 0.07

    result = apply_insurance_inflation(base, years, rate)
    assert result == base
    print("OK test_apply_insurance_inflation_year_1")


def test_apply_insurance_inflation_year_5():
    """Inflation compounds over years."""
    base = 28000
    years = 5
    rate = 0.07

    result = apply_insurance_inflation(base, years, rate)
    expected = base * (1.07 ** 4)  # 4 years of inflation
    assert abs(result - expected) < 0.01
    print("OK test_apply_insurance_inflation_year_5")


def test_calculate_flood_insurance_in_zone():
    """Flood insurance applies in flood zone."""
    result = calculate_flood_insurance(True, 2500, 1, 0.03)
    assert result == 2500
    print("OK test_calculate_flood_insurance_in_zone")


def test_calculate_flood_insurance_not_in_zone():
    """No flood insurance outside flood zone."""
    result = calculate_flood_insurance(False, 2500, 1, 0.03)
    assert result == 0.0
    print("OK test_calculate_flood_insurance_not_in_zone")


def test_calculate_surcharge_with_recent_claim():
    """Surcharge applies after claim."""
    base = 28000
    has_claim = True
    months_since = 12  # 1 year
    surcharge_pct = 0.20
    surcharge_months = 60  # 5 years

    result = calculate_surcharge(base, has_claim, months_since, surcharge_pct, surcharge_months)
    expected = 28000 * 0.20  # $5,600
    assert result == expected
    print("OK test_calculate_surcharge_with_recent_claim")


def test_calculate_surcharge_expired():
    """No surcharge after expiration."""
    base = 28000
    has_claim = True
    months_since = 72  # 6 years
    surcharge_pct = 0.20
    surcharge_months = 60  # 5 years

    result = calculate_surcharge(base, has_claim, months_since, surcharge_pct, surcharge_months)
    assert result == 0.0
    print("OK test_calculate_surcharge_expired")


def test_calculate_surcharge_no_claim():
    """No surcharge without claim."""
    result = calculate_surcharge(28000, False, 0, 0.20, 60)
    assert result == 0.0
    print("OK test_calculate_surcharge_no_claim")


def test_calculate_deductible_named_storm():
    """Named storm deductible is percentage-based."""
    value = 700000
    deductible_pct = 0.02

    result = calculate_deductible(value, deductible_pct, is_named_storm=True)
    expected = 700000 * 0.02  # $14,000
    assert result == expected
    print("OK test_calculate_deductible_named_storm")


def test_calculate_deductible_standard():
    """Standard deductible is capped."""
    value = 700000
    deductible_pct = 0.02

    result = calculate_deductible(value, deductible_pct, is_named_storm=False)
    # Standard is min(1% of value, $2500) = min($7000, $2500) = $2500
    assert result == 2500
    print("OK test_calculate_deductible_standard")


def test_calculate_unit_insurance():
    """Calculate complete insurance for a unit."""
    config = {
        "market_profiles": {
            "orange_beach": {
                "expenses": {
                    "insurance_rate": 0.04,
                    "insurance_inflation_rate": 0.07
                }
            }
        }
    }

    premium = calculate_unit_insurance(
        property_value=700000,
        years_owned=1,
        in_flood_zone=False,
        has_claim=False,
        months_since_claim=0,
        config=config,
        market_name="orange_beach"
    )

    assert isinstance(premium, InsurancePremium)
    assert premium.base_premium == 700000 * 0.04  # $28,000
    assert premium.flood_insurance == 0  # Not in flood zone
    assert premium.surcharge_amount == 0  # No claim
    assert premium.total_premium == premium.adjusted_premium
    print("OK test_calculate_unit_insurance")


def test_calculate_unit_insurance_with_flood():
    """Unit with flood insurance."""
    config = {}  # Will use OB defaults

    premium = calculate_unit_insurance(
        property_value=700000,
        years_owned=1,
        in_flood_zone=True,
        has_claim=False,
        months_since_claim=0,
        config=config,
        market_name="orange_beach"
    )

    assert premium.flood_insurance == 2500  # Default flood premium
    assert premium.total_premium == premium.adjusted_premium + premium.flood_insurance
    print("OK test_calculate_unit_insurance_with_flood")


def test_calculate_unit_insurance_with_claim():
    """Unit with recent insurance claim."""
    config = {}

    premium = calculate_unit_insurance(
        property_value=700000,
        years_owned=3,
        in_flood_zone=False,
        has_claim=True,
        months_since_claim=24,  # 2 years ago
        config=config,
        market_name="orange_beach"
    )

    assert premium.surcharge_amount > 0
    assert premium.total_premium > premium.adjusted_premium
    print("OK test_calculate_unit_insurance_with_claim")


def test_calculate_monthly_insurance():
    """Convert annual to monthly."""
    premium = InsurancePremium(
        base_premium=28000,
        inflation_adjustment=0,
        adjusted_premium=28000,
        flood_insurance=0,
        surcharge_amount=0,
        total_premium=28000,
        deductible_amount=14000
    )

    monthly = calculate_monthly_insurance(premium)
    expected = 28000 / 12  # ~$2,333.33
    assert abs(monthly - expected) < 0.01
    print("OK test_calculate_monthly_insurance")


def test_process_insurance_claim():
    """Process an insurance claim."""
    config = {}

    claim = process_insurance_claim(
        claim_amount=50000,
        property_value=700000,
        is_named_storm=True,
        current_month=36,
        config=config,
        market_name="orange_beach",
        coverage_pct=0.90,
        payout_delay_months=4
    )

    assert isinstance(claim, InsuranceClaim)
    assert claim.claim_month == 36
    assert claim.claim_amount == 50000
    assert claim.deductible_paid == 700000 * 0.02  # $14,000
    assert claim.payout_amount == (50000 * 0.90) - 14000  # $31,000
    assert claim.payout_delay_months == 4
    assert claim.surcharge_until_month == 36 + (5 * 12)  # 5 years
    print("OK test_process_insurance_claim")


def test_calculate_portfolio_insurance():
    """Calculate insurance for portfolio."""
    config = {}
    units_data = [
        {
            "value": 700000,
            "years_owned": 1,
            "in_flood_zone": False,
            "has_claim": False,
            "months_since_claim": 0,
            "market_name": "orange_beach"
        },
        {
            "value": 800000,
            "years_owned": 2,
            "in_flood_zone": True,
            "has_claim": False,
            "months_since_claim": 0,
            "market_name": "orange_beach"
        },
    ]

    result = calculate_portfolio_insurance(units_data, config)

    assert result["base_premium"] > 0, f"Base premium should be > 0, got {result['base_premium']}"
    # Total should include adjusted premium + flood
    assert result["total_premium"] >= result["adjusted_premium"], f"Total {result['total_premium']} should >= adjusted {result['adjusted_premium']}"
    # Flood insurance for year 2 is 2500 * 1.03 = 2575
    assert result["flood_insurance"] >= 2500, f"Flood insurance should be >= 2500, got {result['flood_insurance']}"
    assert abs(result["monthly_cost"] - result["total_premium"] / 12) < 0.01, "Monthly cost should be total/12"
    print("OK test_calculate_portfolio_insurance")


def test_validate_insurance_config_valid():
    """Valid config returns no issues."""
    config = {
        "market_profiles": {
            "test": {
                "expenses": {
                    "insurance_rate": 0.04,
                    "insurance_inflation_rate": 0.07
                }
            }
        }
    }
    issues = validate_insurance_config(config)
    assert len(issues) == 0
    print("OK test_validate_insurance_config_valid")


def test_validate_insurance_config_unusual_rate():
    """Unusual rate is flagged."""
    config = {
        "market_profiles": {
            "test": {
                "expenses": {
                    "insurance_rate": 0.20  # 20% is unusual
                }
            }
        }
    }
    issues = validate_insurance_config(config)
    assert len(issues) > 0
    assert any("unusual" in issue.lower() for issue in issues)
    print("OK test_validate_insurance_config_unusual_rate")


def test_estimate_annual_insurance_trend():
    """Estimate insurance over time."""
    config = {}
    result = estimate_annual_insurance_trend(
        initial_value=700000,
        years=5,
        appreciation_rate=0.03,
        config=config,
        market_name="orange_beach"
    )

    assert len(result) == 5
    assert result[0]["year"] == 1
    assert result[4]["year"] == 5
    # Premiums should increase due to inflation + appreciation
    assert result[4]["adjusted_premium"] > result[0]["adjusted_premium"]
    print("OK test_estimate_annual_insurance_trend")


def test_coastal_vs_inland_insurance():
    """Coastal insurance is higher than inland."""
    config = {}

    coastal = calculate_unit_insurance(
        property_value=700000,
        years_owned=5,
        in_flood_zone=False,
        has_claim=False,
        months_since_claim=0,
        config=config,
        market_name="orange_beach"
    )

    inland = calculate_unit_insurance(
        property_value=700000,
        years_owned=5,
        in_flood_zone=False,
        has_claim=False,
        months_since_claim=0,
        config=config,
        market_name="generic"
    )

    # Coastal has higher base rate and inflation
    assert coastal.total_premium > inland.total_premium
    print("OK test_coastal_vs_inland_insurance")


def test_insurance_inflation_impact_10_years():
    """Insurance inflation significantly increases costs over time."""
    config = {}

    year_1 = calculate_unit_insurance(
        property_value=700000,
        years_owned=1,
        in_flood_zone=False,
        has_claim=False,
        months_since_claim=0,
        config=config,
        market_name="orange_beach"
    )

    year_10 = calculate_unit_insurance(
        property_value=700000,
        years_owned=10,
        in_flood_zone=False,
        has_claim=False,
        months_since_claim=0,
        config=config,
        market_name="orange_beach"
    )

    # 7% annual inflation for 9 years = ~1.84x
    ratio = year_10.adjusted_premium / year_1.adjusted_premium
    expected_ratio = 1.07 ** 9  # ~1.84
    assert abs(ratio - expected_ratio) < 0.01, f"Expected {expected_ratio}, got {ratio}"
    print("OK test_insurance_inflation_impact_10_years")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Insurance Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_insurance_config,
        test_market_insurance_defaults,
        test_get_insurance_config_from_market_profile,
        test_get_insurance_config_falls_back_to_market_defaults,
        test_get_insurance_config_falls_back_to_global_default,
        test_is_insurance_enhanced,
        test_calculate_base_premium,
        test_apply_insurance_inflation_year_1,
        test_apply_insurance_inflation_year_5,
        test_calculate_flood_insurance_in_zone,
        test_calculate_flood_insurance_not_in_zone,
        test_calculate_surcharge_with_recent_claim,
        test_calculate_surcharge_expired,
        test_calculate_surcharge_no_claim,
        test_calculate_deductible_named_storm,
        test_calculate_deductible_standard,
        test_calculate_unit_insurance,
        test_calculate_unit_insurance_with_flood,
        test_calculate_unit_insurance_with_claim,
        test_calculate_monthly_insurance,
        test_process_insurance_claim,
        test_calculate_portfolio_insurance,
        test_validate_insurance_config_valid,
        test_validate_insurance_config_unusual_rate,
        test_estimate_annual_insurance_trend,
        test_coastal_vs_inland_insurance,
        test_insurance_inflation_impact_10_years,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
