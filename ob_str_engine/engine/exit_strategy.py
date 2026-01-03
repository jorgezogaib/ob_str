"""
Exit Strategy Modeling Module - Phase 1.7

Provides exit strategy analytics for the portfolio:
- Property sale proceeds calculation
- Capital gains tax estimation
- 1031 exchange modeling
- Depreciation recapture calculation
- Portfolio liquidation scenarios
- Hold vs. sell analysis

This module helps investors evaluate when and how to exit positions.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple


# Default exit strategy configuration
DEFAULT_EXIT_CONFIG = {
    "enabled": True,
    "selling_cost_pct": 0.06,  # 6% broker commission
    "closing_cost_pct": 0.02,  # 2% closing costs
    "capital_gains_rate": 0.15,  # Long-term capital gains rate
    "depreciation_recapture_rate": 0.25,  # Depreciation recapture rate
    "state_tax_rate": 0.05,  # State capital gains tax
    "min_hold_months_ltcg": 12,  # Minimum months for long-term capital gains
}


@dataclass
class SaleProceeds:
    """Net proceeds from a property sale."""
    unit_id: int
    sale_price: float
    selling_costs: float
    closing_costs: float
    mortgage_payoff: float
    gross_proceeds: float
    net_proceeds_before_tax: float
    # Tax calculations
    capital_gain: float
    depreciation_recapture: float
    capital_gains_tax: float
    depreciation_recapture_tax: float
    state_tax: float
    total_tax: float
    net_proceeds_after_tax: float
    # Analysis
    total_return: float
    annualized_return: float
    hold_period_months: int


@dataclass
class Exchange1031:
    """1031 Exchange analysis."""
    relinquished_unit_id: int
    sale_price: float
    adjusted_basis: float
    deferred_gain: float
    boot_received: float  # Cash received (taxable)
    boot_tax: float
    min_replacement_price: float
    min_replacement_debt: float
    exchange_deadline_days: int
    identification_deadline_days: int


@dataclass
class PortfolioLiquidation:
    """Portfolio liquidation scenario."""
    total_sale_value: float
    total_selling_costs: float
    total_mortgage_payoff: float
    total_gross_proceeds: float
    total_capital_gains: float
    total_depreciation_recapture: float
    total_taxes: float
    total_net_proceeds: float
    per_unit_results: List[SaleProceeds]


@dataclass
class HoldVsSellAnalysis:
    """Hold vs. sell decision analysis."""
    unit_id: int
    current_value: float
    net_sale_proceeds: float
    annual_cash_flow: float
    cash_flow_yield: float  # Annual CF / Net Proceeds
    break_even_years: float  # Years of CF to equal sale proceeds
    recommendation: str
    factors: List[str]


def get_exit_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get exit strategy configuration from engine config.

    Args:
        config: Engine configuration

    Returns:
        Exit strategy configuration dict with defaults applied
    """
    exit_cfg = config.get("exit_strategy", {})

    return {
        "enabled": exit_cfg.get("enabled", DEFAULT_EXIT_CONFIG["enabled"]),
        "selling_cost_pct": exit_cfg.get("selling_cost_pct",
                                          DEFAULT_EXIT_CONFIG["selling_cost_pct"]),
        "closing_cost_pct": exit_cfg.get("closing_cost_pct",
                                          DEFAULT_EXIT_CONFIG["closing_cost_pct"]),
        "capital_gains_rate": exit_cfg.get("capital_gains_rate",
                                            DEFAULT_EXIT_CONFIG["capital_gains_rate"]),
        "depreciation_recapture_rate": exit_cfg.get("depreciation_recapture_rate",
                                                     DEFAULT_EXIT_CONFIG["depreciation_recapture_rate"]),
        "state_tax_rate": exit_cfg.get("state_tax_rate",
                                        DEFAULT_EXIT_CONFIG["state_tax_rate"]),
        "min_hold_months_ltcg": exit_cfg.get("min_hold_months_ltcg",
                                              DEFAULT_EXIT_CONFIG["min_hold_months_ltcg"]),
    }


def is_exit_strategy_enabled(config: Dict[str, Any]) -> bool:
    """Check if exit strategy modeling is enabled."""
    exit_cfg = get_exit_config(config)
    return exit_cfg["enabled"]


def calculate_adjusted_basis(
    purchase_price: float,
    capital_improvements: float = 0.0,
    accumulated_depreciation: float = 0.0
) -> float:
    """
    Calculate adjusted cost basis for tax purposes.

    Adjusted Basis = Purchase Price + Capital Improvements - Accumulated Depreciation

    Args:
        purchase_price: Original purchase price
        capital_improvements: Total capital improvements made
        accumulated_depreciation: Total depreciation taken

    Returns:
        Adjusted cost basis
    """
    return purchase_price + capital_improvements - accumulated_depreciation


def calculate_capital_gain(
    sale_price: float,
    selling_costs: float,
    adjusted_basis: float
) -> float:
    """
    Calculate capital gain on sale.

    Capital Gain = Sale Price - Selling Costs - Adjusted Basis

    Args:
        sale_price: Gross sale price
        selling_costs: Broker commission and closing costs
        adjusted_basis: Adjusted cost basis

    Returns:
        Capital gain (can be negative for loss)
    """
    net_sale_price = sale_price - selling_costs
    return net_sale_price - adjusted_basis


def calculate_sale_proceeds(
    unit_id: int,
    sale_price: float,
    purchase_price: float,
    current_debt: float,
    accumulated_depreciation: float,
    hold_period_months: int,
    cash_invested: float,
    config: Dict[str, Any],
    capital_improvements: float = 0.0
) -> SaleProceeds:
    """
    Calculate net proceeds from a property sale.

    Args:
        unit_id: Unit identifier
        sale_price: Expected sale price
        purchase_price: Original purchase price
        current_debt: Outstanding mortgage balance
        accumulated_depreciation: Total depreciation taken
        hold_period_months: Months property has been held
        cash_invested: Original cash invested (down payment + closing)
        config: Engine configuration
        capital_improvements: Total capital improvements made

    Returns:
        SaleProceeds with complete breakdown
    """
    exit_cfg = get_exit_config(config)

    # Calculate selling costs
    selling_cost_pct = exit_cfg["selling_cost_pct"]
    closing_cost_pct = exit_cfg["closing_cost_pct"]
    selling_costs = sale_price * selling_cost_pct
    closing_costs = sale_price * closing_cost_pct
    total_transaction_costs = selling_costs + closing_costs

    # Calculate gross and net proceeds
    gross_proceeds = sale_price - total_transaction_costs
    net_proceeds_before_tax = gross_proceeds - current_debt

    # Calculate adjusted basis and capital gain
    adjusted_basis = calculate_adjusted_basis(
        purchase_price, capital_improvements, accumulated_depreciation
    )
    capital_gain = calculate_capital_gain(sale_price, total_transaction_costs, adjusted_basis)

    # Separate depreciation recapture from regular capital gain
    depreciation_recapture = min(accumulated_depreciation, max(0, capital_gain))
    regular_capital_gain = max(0, capital_gain - depreciation_recapture)

    # Calculate taxes
    capital_gains_rate = exit_cfg["capital_gains_rate"]
    recapture_rate = exit_cfg["depreciation_recapture_rate"]
    state_rate = exit_cfg["state_tax_rate"]
    min_hold_ltcg = exit_cfg["min_hold_months_ltcg"]

    # Use short-term rate (ordinary income) if held less than 12 months
    if hold_period_months < min_hold_ltcg:
        # Short-term gains taxed as ordinary income (using marginal rate estimate)
        effective_cg_rate = 0.32  # Assume 32% marginal rate for short-term
    else:
        effective_cg_rate = capital_gains_rate

    capital_gains_tax = regular_capital_gain * effective_cg_rate
    depreciation_recapture_tax = depreciation_recapture * recapture_rate
    state_tax = max(0, capital_gain) * state_rate

    total_tax = capital_gains_tax + depreciation_recapture_tax + state_tax
    net_proceeds_after_tax = net_proceeds_before_tax - total_tax

    # Calculate returns
    total_return = net_proceeds_after_tax - cash_invested
    if cash_invested > 0 and hold_period_months > 0:
        total_return_pct = total_return / cash_invested
        annualized_return = (1 + total_return_pct) ** (12 / hold_period_months) - 1
    else:
        annualized_return = 0.0

    return SaleProceeds(
        unit_id=unit_id,
        sale_price=round(sale_price, 2),
        selling_costs=round(selling_costs, 2),
        closing_costs=round(closing_costs, 2),
        mortgage_payoff=round(current_debt, 2),
        gross_proceeds=round(gross_proceeds, 2),
        net_proceeds_before_tax=round(net_proceeds_before_tax, 2),
        capital_gain=round(capital_gain, 2),
        depreciation_recapture=round(depreciation_recapture, 2),
        capital_gains_tax=round(capital_gains_tax, 2),
        depreciation_recapture_tax=round(depreciation_recapture_tax, 2),
        state_tax=round(state_tax, 2),
        total_tax=round(total_tax, 2),
        net_proceeds_after_tax=round(net_proceeds_after_tax, 2),
        total_return=round(total_return, 2),
        annualized_return=round(annualized_return, 4),
        hold_period_months=hold_period_months,
    )


def analyze_1031_exchange(
    unit_id: int,
    sale_price: float,
    purchase_price: float,
    current_debt: float,
    accumulated_depreciation: float,
    config: Dict[str, Any],
    capital_improvements: float = 0.0
) -> Exchange1031:
    """
    Analyze 1031 exchange requirements and benefits.

    Args:
        unit_id: Unit identifier
        sale_price: Expected sale price
        purchase_price: Original purchase price
        current_debt: Outstanding mortgage balance
        accumulated_depreciation: Total depreciation taken
        config: Engine configuration
        capital_improvements: Total capital improvements

    Returns:
        Exchange1031 analysis
    """
    exit_cfg = get_exit_config(config)

    # Calculate selling costs
    selling_cost_pct = exit_cfg["selling_cost_pct"]
    closing_cost_pct = exit_cfg["closing_cost_pct"]
    total_costs = sale_price * (selling_cost_pct + closing_cost_pct)

    # Calculate adjusted basis and deferred gain
    adjusted_basis = calculate_adjusted_basis(
        purchase_price, capital_improvements, accumulated_depreciation
    )
    deferred_gain = sale_price - total_costs - adjusted_basis

    # For a fully tax-deferred exchange:
    # 1. Replacement property must be >= relinquished property value
    # 2. Debt on replacement must be >= debt on relinquished
    min_replacement_price = sale_price
    min_replacement_debt = current_debt

    # Boot calculation (cash received = taxable)
    # In a proper 1031, boot should be 0
    boot_received = 0.0
    boot_tax = 0.0

    return Exchange1031(
        relinquished_unit_id=unit_id,
        sale_price=round(sale_price, 2),
        adjusted_basis=round(adjusted_basis, 2),
        deferred_gain=round(max(0, deferred_gain), 2),
        boot_received=round(boot_received, 2),
        boot_tax=round(boot_tax, 2),
        min_replacement_price=round(min_replacement_price, 2),
        min_replacement_debt=round(min_replacement_debt, 2),
        exchange_deadline_days=180,  # IRS requirement
        identification_deadline_days=45,  # IRS requirement
    )


def calculate_portfolio_liquidation(
    units_data: List[Dict[str, Any]],
    current_month: int,
    config: Dict[str, Any]
) -> PortfolioLiquidation:
    """
    Calculate proceeds from liquidating entire portfolio.

    Args:
        units_data: List of unit data dicts
        current_month: Current simulation month
        config: Engine configuration

    Returns:
        PortfolioLiquidation with complete breakdown
    """
    per_unit_results = []
    total_sale_value = 0.0
    total_selling_costs = 0.0
    total_mortgage_payoff = 0.0
    total_gross_proceeds = 0.0
    total_capital_gains = 0.0
    total_depreciation_recapture = 0.0
    total_taxes = 0.0
    total_net_proceeds = 0.0

    for unit in units_data:
        unit_id = unit.get("unit_id", 0)
        sale_price = unit.get("value", 0)
        purchase_price = unit.get("purchase_price", sale_price)
        current_debt = unit.get("debt", 0)
        accumulated_depreciation = unit.get("accumulated_depreciation", 0)
        purchase_month = unit.get("purchase_month", 0)
        cash_invested = unit.get("cash_invested", 0)
        hold_period = current_month - purchase_month

        proceeds = calculate_sale_proceeds(
            unit_id=unit_id,
            sale_price=sale_price,
            purchase_price=purchase_price,
            current_debt=current_debt,
            accumulated_depreciation=accumulated_depreciation,
            hold_period_months=hold_period,
            cash_invested=cash_invested,
            config=config,
        )

        per_unit_results.append(proceeds)
        total_sale_value += proceeds.sale_price
        total_selling_costs += proceeds.selling_costs + proceeds.closing_costs
        total_mortgage_payoff += proceeds.mortgage_payoff
        total_gross_proceeds += proceeds.gross_proceeds
        total_capital_gains += max(0, proceeds.capital_gain)
        total_depreciation_recapture += proceeds.depreciation_recapture
        total_taxes += proceeds.total_tax
        total_net_proceeds += proceeds.net_proceeds_after_tax

    return PortfolioLiquidation(
        total_sale_value=round(total_sale_value, 2),
        total_selling_costs=round(total_selling_costs, 2),
        total_mortgage_payoff=round(total_mortgage_payoff, 2),
        total_gross_proceeds=round(total_gross_proceeds, 2),
        total_capital_gains=round(total_capital_gains, 2),
        total_depreciation_recapture=round(total_depreciation_recapture, 2),
        total_taxes=round(total_taxes, 2),
        total_net_proceeds=round(total_net_proceeds, 2),
        per_unit_results=per_unit_results,
    )


def analyze_hold_vs_sell(
    unit_id: int,
    current_value: float,
    purchase_price: float,
    current_debt: float,
    accumulated_depreciation: float,
    hold_period_months: int,
    cash_invested: float,
    annual_noi: float,
    config: Dict[str, Any]
) -> HoldVsSellAnalysis:
    """
    Analyze whether to hold or sell a property.

    Args:
        unit_id: Unit identifier
        current_value: Current property value
        purchase_price: Original purchase price
        current_debt: Outstanding mortgage balance
        accumulated_depreciation: Total depreciation taken
        hold_period_months: Months property has been held
        cash_invested: Original cash invested
        annual_noi: Annual net operating income
        config: Engine configuration

    Returns:
        HoldVsSellAnalysis with recommendation
    """
    # Calculate net sale proceeds
    proceeds = calculate_sale_proceeds(
        unit_id=unit_id,
        sale_price=current_value,
        purchase_price=purchase_price,
        current_debt=current_debt,
        accumulated_depreciation=accumulated_depreciation,
        hold_period_months=hold_period_months,
        cash_invested=cash_invested,
        config=config,
    )

    net_sale_proceeds = proceeds.net_proceeds_after_tax

    # Calculate cash flow yield on sale proceeds
    # If you sold and reinvested, what yield would you need to match current cash flow?
    annual_cash_flow = annual_noi - (current_debt * 0.07 / 12 * 12)  # Approximate debt service
    cash_flow_yield = annual_cash_flow / net_sale_proceeds if net_sale_proceeds > 0 else 0

    # Calculate break-even years
    if annual_cash_flow > 0:
        break_even_years = net_sale_proceeds / annual_cash_flow
    else:
        break_even_years = 999.0

    # Generate recommendation and factors
    factors = []
    recommendation = "HOLD"

    # Factor 1: Appreciation exhausted
    appreciation_pct = (current_value - purchase_price) / purchase_price if purchase_price > 0 else 0
    if appreciation_pct > 0.50:
        factors.append(f"Strong appreciation ({appreciation_pct:.0%})")

    # Factor 2: Low LTV (lots of equity)
    ltv = current_debt / current_value if current_value > 0 else 0
    if ltv < 0.30:
        factors.append(f"Low leverage (LTV {ltv:.0%}) - consider refi or sell")

    # Factor 3: Tax burden
    if proceeds.total_tax > net_sale_proceeds * 0.15:
        factors.append(f"High tax burden (${proceeds.total_tax:,.0f})")

    # Factor 4: Cash flow yield
    if cash_flow_yield > 0.08:
        factors.append(f"Strong cash flow yield ({cash_flow_yield:.1%})")
        recommendation = "HOLD"
    elif cash_flow_yield < 0.04:
        factors.append(f"Weak cash flow yield ({cash_flow_yield:.1%})")

    # Factor 5: Break-even analysis
    if break_even_years < 10:
        factors.append(f"Quick break-even ({break_even_years:.1f} years)")
    elif break_even_years > 20:
        factors.append(f"Long break-even ({break_even_years:.1f} years)")
        recommendation = "CONSIDER SELLING"

    # Factor 6: 1031 opportunity
    if proceeds.capital_gain > 100000:
        factors.append("Consider 1031 exchange to defer taxes")

    if not factors:
        factors.append("No significant factors identified")

    return HoldVsSellAnalysis(
        unit_id=unit_id,
        current_value=round(current_value, 2),
        net_sale_proceeds=round(net_sale_proceeds, 2),
        annual_cash_flow=round(annual_cash_flow, 2),
        cash_flow_yield=round(cash_flow_yield, 4),
        break_even_years=round(break_even_years, 1),
        recommendation=recommendation,
        factors=factors,
    )


def calculate_optimal_exit_timing(
    current_value: float,
    purchase_price: float,
    current_debt: float,
    monthly_payment: float,
    annual_rate: float,
    accumulated_depreciation: float,
    monthly_depreciation: float,
    annual_appreciation: float,
    hold_period_months: int,
    cash_invested: float,
    config: Dict[str, Any],
    projection_years: int = 10
) -> List[Dict[str, Any]]:
    """
    Project optimal exit timing over future years.

    Args:
        current_value: Current property value
        purchase_price: Original purchase price
        current_debt: Current debt balance
        monthly_payment: Monthly mortgage payment
        annual_rate: Annual interest rate
        accumulated_depreciation: Current accumulated depreciation
        monthly_depreciation: Monthly depreciation amount
        annual_appreciation: Annual appreciation rate
        hold_period_months: Current hold period
        cash_invested: Original cash invested
        config: Engine configuration
        projection_years: Years to project forward

    Returns:
        List of exit scenarios by year
    """
    scenarios = []
    value = current_value
    debt = current_debt
    depreciation = accumulated_depreciation
    hold_months = hold_period_months

    for year in range(projection_years + 1):
        if year > 0:
            # Project forward one year
            value *= (1 + annual_appreciation)

            # Amortize debt for 12 months
            monthly_rate = annual_rate / 12
            for _ in range(12):
                if debt > 0:
                    interest = debt * monthly_rate
                    principal = min(monthly_payment - interest, debt)
                    debt = max(0, debt - principal)

            depreciation += monthly_depreciation * 12
            hold_months += 12

        # Calculate sale proceeds at this point
        proceeds = calculate_sale_proceeds(
            unit_id=0,
            sale_price=value,
            purchase_price=purchase_price,
            current_debt=debt,
            accumulated_depreciation=depreciation,
            hold_period_months=hold_months,
            cash_invested=cash_invested,
            config=config,
        )

        scenarios.append({
            "year": year,
            "hold_months": hold_months,
            "projected_value": round(value, 2),
            "projected_debt": round(debt, 2),
            "equity": round(value - debt, 2),
            "net_proceeds": proceeds.net_proceeds_after_tax,
            "total_tax": proceeds.total_tax,
            "annualized_return": proceeds.annualized_return,
        })

    return scenarios


def validate_exit_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate exit strategy configuration.

    Args:
        config: Engine configuration

    Returns:
        List of validation issues
    """
    issues = []
    exit_cfg = config.get("exit_strategy", {})

    if not exit_cfg.get("enabled", True):
        return issues  # Skip validation if disabled

    selling_cost = exit_cfg.get("selling_cost_pct", 0.06)
    if selling_cost < 0 or selling_cost > 0.15:
        issues.append(f"Selling cost {selling_cost:.0%} outside typical range (0-15%)")

    cg_rate = exit_cfg.get("capital_gains_rate", 0.15)
    if cg_rate < 0 or cg_rate > 0.40:
        issues.append(f"Capital gains rate {cg_rate:.0%} outside typical range (0-40%)")

    recapture_rate = exit_cfg.get("depreciation_recapture_rate", 0.25)
    if recapture_rate != 0.25:
        issues.append(f"Depreciation recapture rate {recapture_rate:.0%} differs from IRS rate (25%)")

    return issues


def summarize_exit_options(
    units_data: List[Dict[str, Any]],
    current_month: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create comprehensive exit strategy summary.

    Args:
        units_data: List of unit data dicts
        current_month: Current simulation month
        config: Engine configuration

    Returns:
        Dict with complete exit strategy analysis
    """
    # Portfolio liquidation
    liquidation = calculate_portfolio_liquidation(units_data, current_month, config)

    # 1031 exchange opportunities
    exchanges = []
    for unit in units_data:
        exchange = analyze_1031_exchange(
            unit_id=unit.get("unit_id", 0),
            sale_price=unit.get("value", 0),
            purchase_price=unit.get("purchase_price", 0),
            current_debt=unit.get("debt", 0),
            accumulated_depreciation=unit.get("accumulated_depreciation", 0),
            config=config,
        )
        exchanges.append(exchange)

    # Hold vs sell for each unit
    hold_vs_sell = []
    for unit in units_data:
        analysis = analyze_hold_vs_sell(
            unit_id=unit.get("unit_id", 0),
            current_value=unit.get("value", 0),
            purchase_price=unit.get("purchase_price", 0),
            current_debt=unit.get("debt", 0),
            accumulated_depreciation=unit.get("accumulated_depreciation", 0),
            hold_period_months=current_month - unit.get("purchase_month", 0),
            cash_invested=unit.get("cash_invested", 0),
            annual_noi=unit.get("annual_noi", 0),
            config=config,
        )
        hold_vs_sell.append(analysis)

    return {
        "liquidation": liquidation,
        "exchanges_1031": exchanges,
        "hold_vs_sell": hold_vs_sell,
        "validation_issues": validate_exit_config(config),
    }
