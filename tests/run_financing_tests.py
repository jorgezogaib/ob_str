"""
Simple test runner for financing dashboard tests (no pytest required).
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add paths - need to add parent for relative imports to work
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from ob_str_engine.engine.financing import (
    get_financing_config,
    is_financing_dashboard_enabled,
    calculate_unit_debt_status,
    calculate_months_to_payoff,
    generate_amortization_schedule,
    analyze_refi_opportunity,
    project_payoff_timeline,
    calculate_portfolio_financing_status,
    calculate_interest_savings,
    get_monthly_interest_principal_split,
    validate_financing_config,
    summarize_financing,
    DEFAULT_FINANCING_CONFIG,
    UnitDebtStatus,
    AmortizationEntry,
    RefiOpportunity,
    PayoffProjection,
    PortfolioFinancingStatus,
)


def test_default_financing_config():
    """Default financing config has expected values."""
    assert DEFAULT_FINANCING_CONFIG["enabled"] is True
    assert DEFAULT_FINANCING_CONFIG["track_interest_paid"] is True
    assert DEFAULT_FINANCING_CONFIG["project_payoff_timeline"] is True
    print("OK test_default_financing_config")


def test_get_financing_config_from_config():
    """Get financing config from engine config."""
    config = {
        "financing_dashboard": {
            "enabled": True,
            "track_interest_paid": True,
        }
    }
    fin_cfg = get_financing_config(config)
    assert fin_cfg["enabled"] is True
    assert fin_cfg["track_interest_paid"] is True
    print("OK test_get_financing_config_from_config")


def test_get_financing_config_falls_back_to_defaults():
    """Falls back to defaults when financing not in config."""
    config = {}
    fin_cfg = get_financing_config(config)
    assert fin_cfg["enabled"] is True
    assert fin_cfg["project_payoff_timeline"] is True
    print("OK test_get_financing_config_falls_back_to_defaults")


def test_is_financing_dashboard_enabled():
    """Check if financing dashboard is enabled."""
    config_enabled = {"financing_dashboard": {"enabled": True}}
    config_disabled = {"financing_dashboard": {"enabled": False}}
    config_default = {}

    assert is_financing_dashboard_enabled(config_enabled) is True
    assert is_financing_dashboard_enabled(config_disabled) is False
    assert is_financing_dashboard_enabled(config_default) is True  # Default enabled
    print("OK test_is_financing_dashboard_enabled")


def test_calculate_unit_debt_status():
    """Calculate debt status for a unit."""
    status = calculate_unit_debt_status(
        unit_id=0,
        current_debt=400000,
        current_value=500000,
        monthly_payment=2661.21,
        interest_rate=0.07,
        original_loan=450000,
        interest_paid_to_date=25000,
    )

    assert isinstance(status, UnitDebtStatus)
    assert status.unit_id == 0
    assert status.current_debt == 400000
    assert status.current_ltv == 0.8  # 400k/500k
    assert status.equity == 100000  # 500k - 400k
    assert status.equity_pct == 0.2
    assert status.principal_paid_to_date == 50000  # 450k - 400k
    print("OK test_calculate_unit_debt_status")


def test_calculate_unit_debt_status_paid_off():
    """Debt status for paid off unit."""
    status = calculate_unit_debt_status(
        unit_id=1,
        current_debt=0,
        current_value=600000,
        monthly_payment=0,
        interest_rate=0.07,
    )

    assert status.current_ltv == 0.0
    assert status.equity == 600000
    assert status.equity_pct == 1.0
    assert status.months_remaining == 0
    print("OK test_calculate_unit_debt_status_paid_off")


def test_calculate_months_to_payoff():
    """Calculate months to payoff."""
    # $400k loan at 7% with $2661.21 payment (30-year mortgage)
    months = calculate_months_to_payoff(
        balance=400000,
        monthly_payment=2661.21,
        annual_rate=0.07,
    )

    # Should be around 360 months (30 years)
    assert 350 < months < 370, f"Expected ~360 months, got {months}"
    print("OK test_calculate_months_to_payoff")


def test_calculate_months_to_payoff_with_extra():
    """Extra payments reduce payoff time."""
    base_months = calculate_months_to_payoff(
        balance=400000,
        monthly_payment=2661.21,
        annual_rate=0.07,
    )

    with_extra = calculate_months_to_payoff(
        balance=400000,
        monthly_payment=2661.21,
        annual_rate=0.07,
        extra_payment=500,
    )

    assert with_extra < base_months
    assert with_extra < 300  # Should be significantly faster
    print("OK test_calculate_months_to_payoff_with_extra")


def test_calculate_months_to_payoff_zero_balance():
    """Zero balance returns 0 months."""
    months = calculate_months_to_payoff(0, 2000, 0.07)
    assert months == 0
    print("OK test_calculate_months_to_payoff_zero_balance")


def test_generate_amortization_schedule():
    """Generate amortization schedule."""
    schedule = generate_amortization_schedule(
        balance=100000,
        monthly_payment=665.30,
        annual_rate=0.06,
        months=360,
    )

    assert len(schedule) > 0
    assert isinstance(schedule[0], AmortizationEntry)

    # First payment should have more interest than principal
    first = schedule[0]
    assert first.month == 1
    assert first.interest > first.principal

    # Last payment should have very low interest
    last = schedule[-1]
    assert last.balance == 0 or last.balance < 1
    print("OK test_generate_amortization_schedule")


def test_generate_amortization_schedule_interest_decreases():
    """Interest portion decreases over time."""
    schedule = generate_amortization_schedule(
        balance=100000,
        monthly_payment=665.30,
        annual_rate=0.06,
        months=360,
    )

    # Interest should decrease over time
    assert schedule[0].interest > schedule[len(schedule)//2].interest
    assert schedule[len(schedule)//2].interest > schedule[-1].interest
    print("OK test_generate_amortization_schedule_interest_decreases")


def test_analyze_refi_opportunity_eligible():
    """Analyze refi opportunity for eligible unit."""
    config = {
        "constants": {
            "acquisition": {
                "maxPostRefiLTV": 0.75,
                "refiCooldownYears": 2,
            },
            "financial": {
                "amortizationYears": 30,
            },
            "debt": {
                "refiRate": 0.065,
            },
        },
        "banking": {
            "refiLTVTrigger": 0.75,
            "cashoutCostPct": 0.03,
        },
    }

    opp = analyze_refi_opportunity(
        unit_id=0,
        current_debt=300000,
        current_value=600000,  # 50% LTV - eligible
        current_rate=0.07,
        current_payment=2000,
        months_since_last_refi=36,  # Past cooldown
        config=config,
    )

    assert isinstance(opp, RefiOpportunity)
    assert opp.is_eligible is True
    assert opp.max_cashout > 0  # Can extract equity
    assert opp.months_until_eligible == 0
    print("OK test_analyze_refi_opportunity_eligible")


def test_analyze_refi_opportunity_cooldown():
    """Refi blocked by cooldown."""
    config = {
        "constants": {
            "acquisition": {
                "maxPostRefiLTV": 0.75,
                "refiCooldownYears": 2,
            },
            "financial": {
                "amortizationYears": 30,
            },
            "debt": {
                "refiRate": 0.065,
            },
        },
        "banking": {
            "refiLTVTrigger": 0.75,
            "cashoutCostPct": 0.03,
        },
    }

    opp = analyze_refi_opportunity(
        unit_id=0,
        current_debt=300000,
        current_value=600000,
        current_rate=0.07,
        current_payment=2000,
        months_since_last_refi=12,  # Only 12 months, need 24
        config=config,
    )

    assert opp.is_eligible is False
    assert "Cooldown" in opp.reason
    assert opp.months_until_eligible == 12  # 24 - 12
    print("OK test_analyze_refi_opportunity_cooldown")


def test_analyze_refi_opportunity_ltv_too_high():
    """Refi blocked by high LTV."""
    config = {
        "constants": {
            "acquisition": {
                "maxPostRefiLTV": 0.75,
                "refiCooldownYears": 2,
            },
            "financial": {
                "amortizationYears": 30,
            },
            "debt": {
                "refiRate": 0.065,
            },
        },
        "banking": {
            "refiLTVTrigger": 0.75,
            "cashoutCostPct": 0.03,
        },
    }

    opp = analyze_refi_opportunity(
        unit_id=0,
        current_debt=480000,
        current_value=600000,  # 80% LTV - too high
        current_rate=0.07,
        current_payment=2000,
        months_since_last_refi=36,
        config=config,
    )

    assert opp.is_eligible is False
    assert "LTV too high" in opp.reason
    print("OK test_analyze_refi_opportunity_ltv_too_high")


def test_project_payoff_timeline():
    """Project payoff timeline with extra payment scenarios."""
    proj = project_payoff_timeline(
        unit_id=0,
        current_debt=300000,
        monthly_payment=1996.00,
        annual_rate=0.07,
    )

    assert isinstance(proj, PayoffProjection)
    assert proj.months_to_payoff > 0
    assert proj.years_to_payoff > 0
    assert proj.total_interest_remaining > 0

    # Extra payments should reduce timeline
    assert proj.payoff_with_extra[0] == proj.months_to_payoff
    assert proj.payoff_with_extra[500] < proj.months_to_payoff
    assert proj.payoff_with_extra[1000] < proj.payoff_with_extra[500]
    print("OK test_project_payoff_timeline")


def test_calculate_portfolio_financing_status():
    """Calculate portfolio-wide financing status."""
    units_data = [
        {
            "unit_id": 0,
            "debt": 400000,
            "value": 500000,
            "monthly_payment": 2661.21,
            "rate": 0.07,
            "interest_paid": 25000,
            "principal_paid": 15000,
        },
        {
            "unit_id": 1,
            "debt": 300000,
            "value": 450000,
            "monthly_payment": 1996.00,
            "rate": 0.065,
            "interest_paid": 18000,
            "principal_paid": 12000,
        },
    ]

    status = calculate_portfolio_financing_status(units_data, current_month=36)

    assert isinstance(status, PortfolioFinancingStatus)
    assert status.total_debt == 700000
    assert status.total_value == 950000
    assert 0.7 < status.portfolio_ltv < 0.75
    assert status.total_monthly_debt_service == 2661.21 + 1996.00
    assert status.units_with_debt == 2
    assert status.units_debt_free == 0
    assert status.total_interest_paid_to_date == 43000
    print("OK test_calculate_portfolio_financing_status")


def test_calculate_portfolio_financing_status_empty():
    """Empty portfolio returns zeros."""
    status = calculate_portfolio_financing_status([])

    assert status.total_debt == 0
    assert status.total_value == 0
    assert status.portfolio_ltv == 0
    assert status.units_with_debt == 0
    print("OK test_calculate_portfolio_financing_status_empty")


def test_calculate_portfolio_financing_status_with_paid_off():
    """Portfolio with mixed debt/paid-off units."""
    units_data = [
        {"unit_id": 0, "debt": 400000, "value": 500000, "monthly_payment": 2661.21, "rate": 0.07},
        {"unit_id": 1, "debt": 0, "value": 600000, "monthly_payment": 0, "rate": 0},
    ]

    status = calculate_portfolio_financing_status(units_data)

    assert status.units_with_debt == 1
    assert status.units_debt_free == 1
    assert status.total_equity == 700000  # (500k - 400k) + 600k
    print("OK test_calculate_portfolio_financing_status_with_paid_off")


def test_calculate_interest_savings():
    """Calculate interest savings from extra payments."""
    savings = calculate_interest_savings(
        balance=300000,
        monthly_payment=1996.00,
        annual_rate=0.07,
        extra_payment=500,
    )

    assert savings["base_months"] > savings["new_months"]
    assert savings["months_saved"] > 0
    assert savings["interest_saved"] > 0
    print("OK test_calculate_interest_savings")


def test_get_monthly_interest_principal_split():
    """Get interest/principal split for next payment."""
    interest, principal = get_monthly_interest_principal_split(
        balance=300000,
        monthly_payment=1996.00,
        annual_rate=0.07,
    )

    assert interest > 0
    assert principal > 0
    assert interest + principal <= 1996.00 + 0.01  # Allow small rounding
    print("OK test_get_monthly_interest_principal_split")


def test_get_monthly_interest_principal_split_zero_balance():
    """Zero balance returns zeros."""
    interest, principal = get_monthly_interest_principal_split(0, 2000, 0.07)
    assert interest == 0
    assert principal == 0
    print("OK test_get_monthly_interest_principal_split_zero_balance")


def test_validate_financing_config_valid():
    """Valid config returns no issues."""
    config = {
        "financing_dashboard": {"enabled": True},
        "constants": {
            "debt": {"mortgageRate": 0.07, "refiRate": 0.065},
            "acquisition": {"maxPostRefiLTV": 0.75, "downPaymentFirst": 0.20},
        },
    }
    issues = validate_financing_config(config)
    assert len(issues) == 0
    print("OK test_validate_financing_config_valid")


def test_validate_financing_config_disabled_skips():
    """Disabled config skips validation."""
    config = {
        "financing_dashboard": {"enabled": False},
        "constants": {
            "debt": {"mortgageRate": 999},  # Invalid but should be ignored
        },
    }
    issues = validate_financing_config(config)
    assert len(issues) == 0
    print("OK test_validate_financing_config_disabled_skips")


def test_validate_financing_config_unrealistic_rate():
    """Unrealistic rate is flagged."""
    config = {
        "financing_dashboard": {"enabled": True},
        "constants": {
            "debt": {"mortgageRate": 0.50},  # 50% - unrealistic
        },
    }
    issues = validate_financing_config(config)
    assert len(issues) > 0
    assert any("unrealistic" in issue.lower() for issue in issues)
    print("OK test_validate_financing_config_unrealistic_rate")


def test_summarize_financing():
    """Create comprehensive financing summary."""
    config = {
        "constants": {
            "acquisition": {"maxPostRefiLTV": 0.75, "refiCooldownYears": 2},
            "financial": {"amortizationYears": 30},
            "debt": {"refiRate": 0.065},
        },
        "banking": {"refiLTVTrigger": 0.75, "cashoutCostPct": 0.03},
    }
    units_data = [
        {
            "unit_id": 0,
            "debt": 400000,
            "value": 600000,
            "monthly_payment": 2661.21,
            "rate": 0.07,
            "last_refi_month": 0,
        },
    ]

    summary = summarize_financing(units_data, current_month=36, config=config)

    assert "portfolio" in summary
    assert "units" in summary
    assert "refi_opportunities" in summary
    assert "payoff_projections" in summary
    assert "validation_issues" in summary
    assert isinstance(summary["portfolio"], PortfolioFinancingStatus)
    print("OK test_summarize_financing")


def test_30_year_amortization_totals():
    """Verify 30-year amortization totals match expected."""
    # Standard 30-year mortgage: $500k at 7%
    balance = 500000
    rate = 0.07
    years = 30

    from ob_str_engine.engine.debt import pmt as calc_pmt
    monthly_payment = calc_pmt(rate, years, balance)

    schedule = generate_amortization_schedule(balance, monthly_payment, rate)

    # Should complete in about 360 months
    assert 355 <= len(schedule) <= 365, f"Expected ~360 months, got {len(schedule)}"

    # Total paid should be roughly payment * months
    total_paid = monthly_payment * len(schedule)
    total_interest = schedule[-1].cumulative_interest
    total_principal = schedule[-1].cumulative_principal

    # Principal should approximately equal original balance
    assert abs(total_principal - balance) < 100, "Principal should match original balance"

    # Interest should be roughly payment*months - principal
    assert abs(total_interest - (total_paid - balance)) < 100, "Interest calculation mismatch"
    print("OK test_30_year_amortization_totals")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Financing Dashboard Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_financing_config,
        test_get_financing_config_from_config,
        test_get_financing_config_falls_back_to_defaults,
        test_is_financing_dashboard_enabled,
        test_calculate_unit_debt_status,
        test_calculate_unit_debt_status_paid_off,
        test_calculate_months_to_payoff,
        test_calculate_months_to_payoff_with_extra,
        test_calculate_months_to_payoff_zero_balance,
        test_generate_amortization_schedule,
        test_generate_amortization_schedule_interest_decreases,
        test_analyze_refi_opportunity_eligible,
        test_analyze_refi_opportunity_cooldown,
        test_analyze_refi_opportunity_ltv_too_high,
        test_project_payoff_timeline,
        test_calculate_portfolio_financing_status,
        test_calculate_portfolio_financing_status_empty,
        test_calculate_portfolio_financing_status_with_paid_off,
        test_calculate_interest_savings,
        test_get_monthly_interest_principal_split,
        test_get_monthly_interest_principal_split_zero_balance,
        test_validate_financing_config_valid,
        test_validate_financing_config_disabled_skips,
        test_validate_financing_config_unrealistic_rate,
        test_summarize_financing,
        test_30_year_amortization_totals,
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
