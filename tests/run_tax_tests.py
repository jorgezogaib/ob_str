"""
Simple test runner for tax/depreciation tests (no pytest required).
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

from tax import (
    get_tax_config,
    is_tax_enabled,
    calculate_depreciation_basis,
    calculate_annual_depreciation,
    calculate_monthly_depreciation,
    get_depreciation_info,
    estimate_tax_liability,
    calculate_unit_depreciation,
    calculate_portfolio_depreciation,
    validate_tax_config,
    init_unit_depreciation,
    process_monthly_depreciation,
    DEFAULT_TAX_CONFIG,
    DepreciationInfo,
    TaxEstimate,
)


def test_default_tax_config():
    """Default tax config has expected values."""
    assert DEFAULT_TAX_CONFIG["enabled"] is False, "Tax should be disabled by default"
    assert DEFAULT_TAX_CONFIG["marginal_rate"] == 0.32, "Default marginal rate should be 32%"
    assert DEFAULT_TAX_CONFIG["land_percentage"] == 0.15, "Default land percentage should be 15%"
    assert DEFAULT_TAX_CONFIG["depreciation_years"] == 27.5, "Default depreciation should be 27.5 years"
    print("OK test_default_tax_config")


def test_get_tax_config_from_config():
    """Get tax config from engine config."""
    config = {
        "tax": {
            "enabled": True,
            "marginal_rate": 0.35,
            "land_percentage": 0.20,
            "depreciation_years": 27.5
        }
    }
    tax_cfg = get_tax_config(config)
    assert tax_cfg["enabled"] is True
    assert tax_cfg["marginal_rate"] == 0.35
    assert tax_cfg["land_percentage"] == 0.20
    print("OK test_get_tax_config_from_config")


def test_get_tax_config_falls_back_to_defaults():
    """Falls back to defaults when tax not in config."""
    config = {}
    tax_cfg = get_tax_config(config)
    assert tax_cfg["enabled"] is False
    assert tax_cfg["marginal_rate"] == 0.32
    print("OK test_get_tax_config_falls_back_to_defaults")


def test_is_tax_enabled():
    """Check if tax modeling is enabled."""
    config_enabled = {"tax": {"enabled": True}}
    config_disabled = {"tax": {"enabled": False}}
    config_no_tax = {}

    assert is_tax_enabled(config_enabled) is True
    assert is_tax_enabled(config_disabled) is False
    assert is_tax_enabled(config_no_tax) is False
    print("OK test_is_tax_enabled")


def test_calculate_depreciation_basis():
    """Calculate depreciable basis correctly."""
    purchase_price = 700000
    land_pct = 0.15

    basis = calculate_depreciation_basis(purchase_price, land_pct)
    expected = 700000 * 0.85  # $595,000
    assert basis == expected, f"Expected {expected}, got {basis}"
    print("OK test_calculate_depreciation_basis")


def test_calculate_depreciation_basis_custom_land():
    """Calculate depreciable basis with custom land percentage."""
    purchase_price = 1000000
    land_pct = 0.20  # 20% land

    basis = calculate_depreciation_basis(purchase_price, land_pct)
    expected = 1000000 * 0.80  # $800,000
    assert basis == expected, f"Expected {expected}, got {basis}"
    print("OK test_calculate_depreciation_basis_custom_land")


def test_calculate_annual_depreciation():
    """Calculate annual depreciation correctly."""
    basis = 595000  # Building value
    years = 27.5

    annual = calculate_annual_depreciation(basis, years)
    expected = 595000 / 27.5  # ~$21,636.36
    assert abs(annual - expected) < 0.01, f"Expected {expected}, got {annual}"
    print("OK test_calculate_annual_depreciation")


def test_calculate_monthly_depreciation():
    """Calculate monthly depreciation correctly."""
    basis = 595000
    years = 27.5

    monthly = calculate_monthly_depreciation(basis, years)
    annual = 595000 / 27.5
    expected = annual / 12  # ~$1,803.03
    assert abs(monthly - expected) < 0.01, f"Expected {expected}, got {monthly}"
    print("OK test_calculate_monthly_depreciation")


def test_get_depreciation_info():
    """Get complete depreciation info for a unit."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.15,
            "depreciation_years": 27.5
        }
    }
    purchase_price = 700000
    accumulated = 10000

    info = get_depreciation_info(purchase_price, accumulated, config)

    assert isinstance(info, DepreciationInfo)
    assert info.depreciation_basis == 700000 * 0.85  # $595,000
    assert info.accumulated_depreciation == 10000
    assert info.remaining_basis == 595000 - 10000  # $585,000
    assert info.annual_depreciation > 0
    assert info.monthly_depreciation > 0
    assert info.years_remaining > 0
    print("OK test_get_depreciation_info")


def test_estimate_tax_liability_positive_income():
    """Estimate tax liability for positive taxable income."""
    gross = 100000
    expenses = 40000
    depreciation = 20000
    rate = 0.32

    result = estimate_tax_liability(gross, expenses, depreciation, rate)

    assert isinstance(result, TaxEstimate)
    assert result.taxable_income == 40000  # 100k - 40k - 20k
    assert result.estimated_tax == 40000 * 0.32  # $12,800
    assert result.effective_rate > 0
    print("OK test_estimate_tax_liability_positive_income")


def test_estimate_tax_liability_loss():
    """Estimate tax liability when there's a loss."""
    gross = 50000
    expenses = 40000
    depreciation = 20000  # Creates a $10k loss
    rate = 0.32

    result = estimate_tax_liability(gross, expenses, depreciation, rate)

    assert result.taxable_income == -10000  # Loss
    assert result.estimated_tax == 0  # No tax on losses
    print("OK test_estimate_tax_liability_loss")


def test_calculate_unit_depreciation():
    """Calculate depreciation for a single unit."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.15,
            "depreciation_years": 27.5
        }
    }
    purchase_price = 700000
    accumulated = 0
    months_owned = 12

    monthly_dep, new_accumulated = calculate_unit_depreciation(
        purchase_price, accumulated, months_owned, config
    )

    assert monthly_dep > 0
    assert new_accumulated == monthly_dep
    print("OK test_calculate_unit_depreciation")


def test_calculate_unit_depreciation_fully_depreciated():
    """Don't take more depreciation than remaining basis."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.15,
            "depreciation_years": 27.5
        }
    }
    purchase_price = 700000
    basis = purchase_price * 0.85  # $595,000
    accumulated = basis - 100  # Only $100 remaining

    monthly_dep, new_accumulated = calculate_unit_depreciation(
        purchase_price, accumulated, 1, config
    )

    # Should only take the remaining $100
    assert monthly_dep == 100, f"Should only depreciate remaining $100, got {monthly_dep}"
    assert new_accumulated == basis, f"Should be fully depreciated, got {new_accumulated}"
    print("OK test_calculate_unit_depreciation_fully_depreciated")


def test_calculate_portfolio_depreciation():
    """Calculate total depreciation for a portfolio."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.15,
            "depreciation_years": 27.5
        }
    }
    units_data = [
        {"purchase_price": 700000, "accumulated_depreciation": 10000, "months_owned": 12},
        {"purchase_price": 800000, "accumulated_depreciation": 5000, "months_owned": 6},
    ]

    result = calculate_portfolio_depreciation(units_data, config)

    assert result["monthly_depreciation"] > 0
    assert result["annual_depreciation"] > 0
    assert result["accumulated_depreciation"] == 15000  # 10k + 5k
    assert result["remaining_basis"] > 0
    print("OK test_calculate_portfolio_depreciation")


def test_validate_tax_config_valid():
    """Valid tax config returns no issues."""
    config = {
        "tax": {
            "enabled": True,
            "marginal_rate": 0.32,
            "land_percentage": 0.15,
            "depreciation_years": 27.5
        }
    }
    issues = validate_tax_config(config)
    assert len(issues) == 0, f"Expected no issues, got {issues}"
    print("OK test_validate_tax_config_valid")


def test_validate_tax_config_disabled_skips_validation():
    """Disabled tax config skips validation."""
    config = {
        "tax": {
            "enabled": False,
            "marginal_rate": 999,  # Invalid but should be ignored
        }
    }
    issues = validate_tax_config(config)
    assert len(issues) == 0, "Should skip validation when disabled"
    print("OK test_validate_tax_config_disabled_skips_validation")


def test_validate_tax_config_invalid_rate():
    """Invalid marginal rate is flagged."""
    config = {
        "tax": {
            "enabled": True,
            "marginal_rate": 1.5,  # Invalid: > 1
        }
    }
    issues = validate_tax_config(config)
    assert len(issues) > 0, "Should flag invalid rate"
    assert any("rate" in issue.lower() for issue in issues)
    print("OK test_validate_tax_config_invalid_rate")


def test_validate_tax_config_invalid_land_pct():
    """Invalid land percentage is flagged."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.60,  # Invalid: > 0.5
        }
    }
    issues = validate_tax_config(config)
    assert len(issues) > 0, "Should flag invalid land percentage"
    assert any("land" in issue.lower() for issue in issues)
    print("OK test_validate_tax_config_invalid_land_pct")


def test_validate_tax_config_nonstandard_depreciation():
    """Non-standard depreciation years is flagged (warning)."""
    config = {
        "tax": {
            "enabled": True,
            "depreciation_years": 20,  # Non-standard
        }
    }
    issues = validate_tax_config(config)
    assert len(issues) > 0, "Should flag non-standard depreciation"
    assert any("non-standard" in issue.lower() for issue in issues)
    print("OK test_validate_tax_config_nonstandard_depreciation")


def test_init_unit_depreciation():
    """Initialize depreciation tracking for new unit."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.15,
        }
    }
    purchase_price = 700000

    result = init_unit_depreciation(purchase_price, config)

    assert result["depreciation_basis"] == 700000 * 0.85
    assert result["accumulated_depreciation"] == 0.0
    print("OK test_init_unit_depreciation")


def test_process_monthly_depreciation():
    """Process monthly depreciation correctly."""
    config = {
        "tax": {
            "enabled": True,
            "depreciation_years": 27.5
        }
    }
    basis = 595000
    accumulated = 0

    monthly, new_accum = process_monthly_depreciation(basis, accumulated, config)

    expected_monthly = basis / 27.5 / 12
    assert abs(monthly - expected_monthly) < 0.01
    assert abs(new_accum - monthly) < 0.01
    print("OK test_process_monthly_depreciation")


def test_process_monthly_depreciation_fully_depreciated():
    """Returns 0 when fully depreciated."""
    config = {
        "tax": {
            "enabled": True,
            "depreciation_years": 27.5
        }
    }
    basis = 595000
    accumulated = basis  # Fully depreciated

    monthly, new_accum = process_monthly_depreciation(basis, accumulated, config)

    assert monthly == 0, "Should return 0 when fully depreciated"
    assert new_accum == basis, "Accumulated should stay at basis"
    print("OK test_process_monthly_depreciation_fully_depreciated")


def test_27_5_year_depreciation_schedule():
    """Verify 27.5 year schedule results in full depreciation."""
    config = {
        "tax": {
            "enabled": True,
            "land_percentage": 0.15,
            "depreciation_years": 27.5
        }
    }
    purchase_price = 700000
    basis = purchase_price * 0.85  # $595,000
    accumulated = 0

    # Simulate 330 months (27.5 years)
    for month in range(330):
        monthly, accumulated = process_monthly_depreciation(basis, accumulated, config)

    # Should be fully depreciated (or very close)
    remaining = basis - accumulated
    assert remaining < 100, f"Should be nearly fully depreciated, remaining: {remaining}"
    print("OK test_27_5_year_depreciation_schedule")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Tax/Depreciation Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_tax_config,
        test_get_tax_config_from_config,
        test_get_tax_config_falls_back_to_defaults,
        test_is_tax_enabled,
        test_calculate_depreciation_basis,
        test_calculate_depreciation_basis_custom_land,
        test_calculate_annual_depreciation,
        test_calculate_monthly_depreciation,
        test_get_depreciation_info,
        test_estimate_tax_liability_positive_income,
        test_estimate_tax_liability_loss,
        test_calculate_unit_depreciation,
        test_calculate_unit_depreciation_fully_depreciated,
        test_calculate_portfolio_depreciation,
        test_validate_tax_config_valid,
        test_validate_tax_config_disabled_skips_validation,
        test_validate_tax_config_invalid_rate,
        test_validate_tax_config_invalid_land_pct,
        test_validate_tax_config_nonstandard_depreciation,
        test_init_unit_depreciation,
        test_process_monthly_depreciation,
        test_process_monthly_depreciation_fully_depreciated,
        test_27_5_year_depreciation_schedule,
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
