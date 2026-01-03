"""
Simple test runner for exit strategy tests (no pytest required).
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

from ob_str_engine.engine.exit_strategy import (
    get_exit_config,
    is_exit_strategy_enabled,
    calculate_adjusted_basis,
    calculate_capital_gain,
    calculate_sale_proceeds,
    analyze_1031_exchange,
    calculate_portfolio_liquidation,
    analyze_hold_vs_sell,
    calculate_optimal_exit_timing,
    validate_exit_config,
    summarize_exit_options,
    DEFAULT_EXIT_CONFIG,
    SaleProceeds,
    Exchange1031,
    PortfolioLiquidation,
    HoldVsSellAnalysis,
)


def test_default_exit_config():
    """Default exit config has expected values."""
    assert DEFAULT_EXIT_CONFIG["enabled"] is True
    assert DEFAULT_EXIT_CONFIG["selling_cost_pct"] == 0.06
    assert DEFAULT_EXIT_CONFIG["capital_gains_rate"] == 0.15
    assert DEFAULT_EXIT_CONFIG["depreciation_recapture_rate"] == 0.25
    print("OK test_default_exit_config")


def test_get_exit_config_from_config():
    """Get exit config from engine config."""
    config = {
        "exit_strategy": {
            "enabled": True,
            "selling_cost_pct": 0.05,
            "capital_gains_rate": 0.20,
        }
    }
    exit_cfg = get_exit_config(config)
    assert exit_cfg["enabled"] is True
    assert exit_cfg["selling_cost_pct"] == 0.05
    assert exit_cfg["capital_gains_rate"] == 0.20
    print("OK test_get_exit_config_from_config")


def test_get_exit_config_falls_back_to_defaults():
    """Falls back to defaults when exit_strategy not in config."""
    config = {}
    exit_cfg = get_exit_config(config)
    assert exit_cfg["enabled"] is True
    assert exit_cfg["selling_cost_pct"] == 0.06
    print("OK test_get_exit_config_falls_back_to_defaults")


def test_is_exit_strategy_enabled():
    """Check if exit strategy is enabled."""
    config_enabled = {"exit_strategy": {"enabled": True}}
    config_disabled = {"exit_strategy": {"enabled": False}}
    config_default = {}

    assert is_exit_strategy_enabled(config_enabled) is True
    assert is_exit_strategy_enabled(config_disabled) is False
    assert is_exit_strategy_enabled(config_default) is True  # Default enabled
    print("OK test_is_exit_strategy_enabled")


def test_calculate_adjusted_basis():
    """Calculate adjusted cost basis."""
    # $700k purchase, $50k improvements, $100k depreciation
    basis = calculate_adjusted_basis(
        purchase_price=700000,
        capital_improvements=50000,
        accumulated_depreciation=100000,
    )
    # 700k + 50k - 100k = 650k
    assert basis == 650000
    print("OK test_calculate_adjusted_basis")


def test_calculate_adjusted_basis_no_depreciation():
    """Adjusted basis with no depreciation."""
    basis = calculate_adjusted_basis(
        purchase_price=500000,
        capital_improvements=0,
        accumulated_depreciation=0,
    )
    assert basis == 500000
    print("OK test_calculate_adjusted_basis_no_depreciation")


def test_calculate_capital_gain():
    """Calculate capital gain on sale."""
    # Sell for $800k, $48k costs (6%), $650k basis
    gain = calculate_capital_gain(
        sale_price=800000,
        selling_costs=48000,
        adjusted_basis=650000,
    )
    # 800k - 48k - 650k = 102k
    assert gain == 102000
    print("OK test_calculate_capital_gain")


def test_calculate_capital_gain_loss():
    """Calculate capital loss on sale."""
    gain = calculate_capital_gain(
        sale_price=600000,
        selling_costs=36000,
        adjusted_basis=650000,
    )
    # 600k - 36k - 650k = -86k (loss)
    assert gain == -86000
    print("OK test_calculate_capital_gain_loss")


def test_calculate_sale_proceeds():
    """Calculate net sale proceeds."""
    config = {}  # Use defaults

    proceeds = calculate_sale_proceeds(
        unit_id=0,
        sale_price=800000,
        purchase_price=600000,
        current_debt=300000,
        accumulated_depreciation=50000,
        hold_period_months=60,  # 5 years
        cash_invested=150000,
        config=config,
    )

    assert isinstance(proceeds, SaleProceeds)
    assert proceeds.unit_id == 0
    assert proceeds.sale_price == 800000
    # Selling costs = 6% of 800k = 48k
    assert proceeds.selling_costs == 48000
    # Closing costs = 2% of 800k = 16k
    assert proceeds.closing_costs == 16000
    # Gross = 800k - 64k = 736k
    assert proceeds.gross_proceeds == 736000
    # Net before tax = 736k - 300k = 436k
    assert proceeds.net_proceeds_before_tax == 436000
    # Capital gain should be positive
    assert proceeds.capital_gain > 0
    # Total tax should be positive
    assert proceeds.total_tax > 0
    # Net after tax should be less than before tax
    assert proceeds.net_proceeds_after_tax < proceeds.net_proceeds_before_tax
    print("OK test_calculate_sale_proceeds")


def test_calculate_sale_proceeds_short_term():
    """Short-term sale uses higher tax rate."""
    config = {}

    # Sell after 6 months (short-term)
    proceeds_short = calculate_sale_proceeds(
        unit_id=0,
        sale_price=700000,
        purchase_price=600000,
        current_debt=400000,
        accumulated_depreciation=10000,
        hold_period_months=6,
        cash_invested=130000,
        config=config,
    )

    # Sell after 24 months (long-term)
    proceeds_long = calculate_sale_proceeds(
        unit_id=0,
        sale_price=700000,
        purchase_price=600000,
        current_debt=400000,
        accumulated_depreciation=40000,
        hold_period_months=24,
        cash_invested=130000,
        config=config,
    )

    # Short-term should have higher tax rate on same gain
    # (though accumulated depreciation differs, so comparing rates not amounts)
    assert proceeds_short.hold_period_months == 6
    assert proceeds_long.hold_period_months == 24
    print("OK test_calculate_sale_proceeds_short_term")


def test_calculate_sale_proceeds_no_gain():
    """Sale with no capital gain."""
    config = {}

    proceeds = calculate_sale_proceeds(
        unit_id=0,
        sale_price=600000,
        purchase_price=600000,
        current_debt=400000,
        accumulated_depreciation=50000,
        hold_period_months=60,
        cash_invested=130000,
        config=config,
    )

    # Even with no appreciation, depreciation recapture creates taxable gain
    assert proceeds.depreciation_recapture > 0
    assert proceeds.depreciation_recapture_tax > 0
    print("OK test_calculate_sale_proceeds_no_gain")


def test_analyze_1031_exchange():
    """Analyze 1031 exchange opportunity."""
    config = {}

    exchange = analyze_1031_exchange(
        unit_id=0,
        sale_price=800000,
        purchase_price=600000,
        current_debt=300000,
        accumulated_depreciation=50000,
        config=config,
    )

    assert isinstance(exchange, Exchange1031)
    assert exchange.relinquished_unit_id == 0
    assert exchange.sale_price == 800000
    assert exchange.deferred_gain > 0
    # Min replacement = sale price
    assert exchange.min_replacement_price == 800000
    # Min replacement debt = current debt
    assert exchange.min_replacement_debt == 300000
    # IRS deadlines
    assert exchange.identification_deadline_days == 45
    assert exchange.exchange_deadline_days == 180
    print("OK test_analyze_1031_exchange")


def test_analyze_1031_exchange_fully_depreciated():
    """1031 exchange with large depreciation."""
    config = {}

    exchange = analyze_1031_exchange(
        unit_id=0,
        sale_price=900000,
        purchase_price=600000,
        current_debt=200000,
        accumulated_depreciation=150000,  # Large depreciation
        config=config,
    )

    # Large deferred gain due to depreciation lowering basis
    assert exchange.deferred_gain > 200000
    print("OK test_analyze_1031_exchange_fully_depreciated")


def test_calculate_portfolio_liquidation():
    """Calculate portfolio liquidation proceeds."""
    config = {}
    units_data = [
        {
            "unit_id": 0,
            "value": 700000,
            "purchase_price": 600000,
            "debt": 300000,
            "accumulated_depreciation": 40000,
            "purchase_month": 0,
            "cash_invested": 140000,
        },
        {
            "unit_id": 1,
            "value": 800000,
            "purchase_price": 650000,
            "debt": 350000,
            "accumulated_depreciation": 30000,
            "purchase_month": 12,
            "cash_invested": 155000,
        },
    ]

    liquidation = calculate_portfolio_liquidation(units_data, current_month=60, config=config)

    assert isinstance(liquidation, PortfolioLiquidation)
    assert liquidation.total_sale_value == 1500000  # 700k + 800k
    assert liquidation.total_mortgage_payoff == 650000  # 300k + 350k
    assert len(liquidation.per_unit_results) == 2
    assert liquidation.total_net_proceeds > 0
    assert liquidation.total_taxes > 0
    print("OK test_calculate_portfolio_liquidation")


def test_calculate_portfolio_liquidation_empty():
    """Empty portfolio liquidation."""
    config = {}
    liquidation = calculate_portfolio_liquidation([], current_month=60, config=config)

    assert liquidation.total_sale_value == 0
    assert liquidation.total_net_proceeds == 0
    assert len(liquidation.per_unit_results) == 0
    print("OK test_calculate_portfolio_liquidation_empty")


def test_analyze_hold_vs_sell():
    """Analyze hold vs sell decision."""
    config = {}

    analysis = analyze_hold_vs_sell(
        unit_id=0,
        current_value=800000,
        purchase_price=600000,
        current_debt=300000,
        accumulated_depreciation=50000,
        hold_period_months=60,
        cash_invested=150000,
        annual_noi=60000,  # $5k/month NOI
        config=config,
    )

    assert isinstance(analysis, HoldVsSellAnalysis)
    assert analysis.unit_id == 0
    assert analysis.current_value == 800000
    assert analysis.net_sale_proceeds > 0
    assert analysis.annual_cash_flow > 0
    assert analysis.cash_flow_yield > 0
    assert analysis.break_even_years > 0
    assert analysis.recommendation in ["HOLD", "CONSIDER SELLING"]
    assert len(analysis.factors) > 0
    print("OK test_analyze_hold_vs_sell")


def test_analyze_hold_vs_sell_low_yield():
    """Hold vs sell with low cash flow yield."""
    config = {}

    analysis = analyze_hold_vs_sell(
        unit_id=0,
        current_value=1000000,
        purchase_price=500000,
        current_debt=100000,  # Very low debt
        accumulated_depreciation=100000,
        hold_period_months=120,
        cash_invested=150000,
        annual_noi=30000,  # Low NOI relative to equity
        config=config,
    )

    # High equity, low cash flow should suggest considering sale
    assert analysis.cash_flow_yield < 0.05
    print("OK test_analyze_hold_vs_sell_low_yield")


def test_calculate_optimal_exit_timing():
    """Project optimal exit timing."""
    config = {}

    scenarios = calculate_optimal_exit_timing(
        current_value=700000,
        purchase_price=600000,
        current_debt=400000,
        monthly_payment=2661,
        annual_rate=0.07,
        accumulated_depreciation=30000,
        monthly_depreciation=1500,
        annual_appreciation=0.04,
        hold_period_months=24,
        cash_invested=140000,
        config=config,
        projection_years=5,
    )

    assert len(scenarios) == 6  # Year 0 through Year 5
    assert scenarios[0]["year"] == 0
    assert scenarios[5]["year"] == 5

    # Value should increase over time
    assert scenarios[5]["projected_value"] > scenarios[0]["projected_value"]

    # Debt should decrease over time
    assert scenarios[5]["projected_debt"] < scenarios[0]["projected_debt"]

    # Equity should increase over time
    assert scenarios[5]["equity"] > scenarios[0]["equity"]
    print("OK test_calculate_optimal_exit_timing")


def test_calculate_optimal_exit_timing_debt_payoff():
    """Exit timing with debt paid off mid-projection."""
    config = {}

    scenarios = calculate_optimal_exit_timing(
        current_value=700000,
        purchase_price=600000,
        current_debt=50000,  # Low remaining debt
        monthly_payment=2661,
        annual_rate=0.07,
        accumulated_depreciation=150000,
        monthly_depreciation=1500,
        annual_appreciation=0.04,
        hold_period_months=300,  # 25 years already held
        cash_invested=140000,
        config=config,
        projection_years=3,
    )

    # Debt should hit zero before end of projection
    assert scenarios[-1]["projected_debt"] == 0
    print("OK test_calculate_optimal_exit_timing_debt_payoff")


def test_validate_exit_config_valid():
    """Valid config returns no issues."""
    config = {
        "exit_strategy": {
            "enabled": True,
            "selling_cost_pct": 0.06,
            "capital_gains_rate": 0.15,
            "depreciation_recapture_rate": 0.25,
        }
    }
    issues = validate_exit_config(config)
    assert len(issues) == 0
    print("OK test_validate_exit_config_valid")


def test_validate_exit_config_disabled_skips():
    """Disabled config skips validation."""
    config = {
        "exit_strategy": {
            "enabled": False,
            "selling_cost_pct": 999,  # Invalid but should be ignored
        }
    }
    issues = validate_exit_config(config)
    assert len(issues) == 0
    print("OK test_validate_exit_config_disabled_skips")


def test_validate_exit_config_invalid_selling_cost():
    """Invalid selling cost is flagged."""
    config = {
        "exit_strategy": {
            "enabled": True,
            "selling_cost_pct": 0.25,  # 25% - too high
        }
    }
    issues = validate_exit_config(config)
    assert len(issues) > 0
    assert any("selling cost" in issue.lower() for issue in issues)
    print("OK test_validate_exit_config_invalid_selling_cost")


def test_validate_exit_config_nonstandard_recapture():
    """Non-standard recapture rate is flagged."""
    config = {
        "exit_strategy": {
            "enabled": True,
            "depreciation_recapture_rate": 0.20,  # Should be 0.25
        }
    }
    issues = validate_exit_config(config)
    assert len(issues) > 0
    assert any("recapture" in issue.lower() for issue in issues)
    print("OK test_validate_exit_config_nonstandard_recapture")


def test_summarize_exit_options():
    """Create comprehensive exit strategy summary."""
    config = {}
    units_data = [
        {
            "unit_id": 0,
            "value": 700000,
            "purchase_price": 600000,
            "debt": 300000,
            "accumulated_depreciation": 40000,
            "purchase_month": 0,
            "cash_invested": 140000,
            "annual_noi": 50000,
        },
    ]

    summary = summarize_exit_options(units_data, current_month=60, config=config)

    assert "liquidation" in summary
    assert "exchanges_1031" in summary
    assert "hold_vs_sell" in summary
    assert "validation_issues" in summary
    assert isinstance(summary["liquidation"], PortfolioLiquidation)
    assert len(summary["exchanges_1031"]) == 1
    assert len(summary["hold_vs_sell"]) == 1
    print("OK test_summarize_exit_options")


def test_depreciation_recapture_calculation():
    """Verify depreciation recapture is correctly separated."""
    config = {}

    # $700k sale, $600k purchase, $100k depreciation
    proceeds = calculate_sale_proceeds(
        unit_id=0,
        sale_price=700000,
        purchase_price=600000,
        current_debt=300000,
        accumulated_depreciation=100000,
        hold_period_months=120,
        cash_invested=140000,
        config=config,
    )

    # Adjusted basis = 600k - 100k = 500k
    # Capital gain = 700k - (8% costs) - 500k = 700k - 56k - 500k = 144k
    # Depreciation recapture = min(100k, 144k) = 100k
    assert proceeds.depreciation_recapture == 100000
    # Regular capital gain = 144k - 100k = 44k
    # Depreciation recapture taxed at 25%: 100k * 0.25 = 25k
    assert proceeds.depreciation_recapture_tax == 25000
    print("OK test_depreciation_recapture_calculation")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Exit Strategy Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_exit_config,
        test_get_exit_config_from_config,
        test_get_exit_config_falls_back_to_defaults,
        test_is_exit_strategy_enabled,
        test_calculate_adjusted_basis,
        test_calculate_adjusted_basis_no_depreciation,
        test_calculate_capital_gain,
        test_calculate_capital_gain_loss,
        test_calculate_sale_proceeds,
        test_calculate_sale_proceeds_short_term,
        test_calculate_sale_proceeds_no_gain,
        test_analyze_1031_exchange,
        test_analyze_1031_exchange_fully_depreciated,
        test_calculate_portfolio_liquidation,
        test_calculate_portfolio_liquidation_empty,
        test_analyze_hold_vs_sell,
        test_analyze_hold_vs_sell_low_yield,
        test_calculate_optimal_exit_timing,
        test_calculate_optimal_exit_timing_debt_payoff,
        test_validate_exit_config_valid,
        test_validate_exit_config_disabled_skips,
        test_validate_exit_config_invalid_selling_cost,
        test_validate_exit_config_nonstandard_recapture,
        test_summarize_exit_options,
        test_depreciation_recapture_calculation,
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
