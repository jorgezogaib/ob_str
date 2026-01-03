"""
Financing Dashboard Module - Phase 1.6

Provides comprehensive financing analytics for the portfolio:
- Per-unit and portfolio debt metrics
- Amortization schedule projections
- Refinance opportunity analysis
- Interest cost tracking
- Principal paydown analysis
- Debt-free timeline projections

This module consolidates debt-related analytics into a single dashboard-ready interface.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from .debt import pmt


# Default financing configuration
DEFAULT_FINANCING_CONFIG = {
    "enabled": True,
    "track_interest_paid": True,
    "project_payoff_timeline": True,
    "analyze_refi_opportunities": True,
}


@dataclass
class UnitDebtStatus:
    """Debt status for a single unit."""
    unit_id: int
    current_debt: float
    current_value: float
    current_ltv: float
    monthly_payment: float
    interest_rate: float
    original_loan: float
    principal_paid_to_date: float
    interest_paid_to_date: float
    months_remaining: int
    equity: float
    equity_pct: float


@dataclass
class AmortizationEntry:
    """Single month in amortization schedule."""
    month: int
    payment: float
    principal: float
    interest: float
    balance: float
    cumulative_interest: float
    cumulative_principal: float


@dataclass
class RefiOpportunity:
    """Refinance opportunity analysis."""
    unit_id: int
    current_debt: float
    current_rate: float
    current_payment: float
    max_cashout: float
    new_debt_at_max_ltv: float
    new_payment_at_max_ltv: float
    monthly_payment_increase: float
    is_eligible: bool
    reason: str
    months_until_eligible: int


@dataclass
class PayoffProjection:
    """Debt payoff timeline projection."""
    unit_id: int
    current_debt: float
    monthly_payment: float
    months_to_payoff: int
    years_to_payoff: float
    total_interest_remaining: float
    payoff_with_extra: Dict[float, int]  # extra_monthly -> months_to_payoff


@dataclass
class PortfolioFinancingStatus:
    """Portfolio-wide financing status."""
    total_debt: float
    total_value: float
    portfolio_ltv: float
    total_monthly_debt_service: float
    annual_debt_service: float
    total_equity: float
    weighted_avg_rate: float
    units_with_debt: int
    units_debt_free: int
    total_interest_paid_to_date: float
    total_principal_paid_to_date: float
    projected_debt_free_month: Optional[int]


def get_financing_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get financing configuration from engine config.

    Args:
        config: Engine configuration

    Returns:
        Financing configuration dict with defaults applied
    """
    fin_cfg = config.get("financing_dashboard", {})

    return {
        "enabled": fin_cfg.get("enabled", DEFAULT_FINANCING_CONFIG["enabled"]),
        "track_interest_paid": fin_cfg.get("track_interest_paid",
                                           DEFAULT_FINANCING_CONFIG["track_interest_paid"]),
        "project_payoff_timeline": fin_cfg.get("project_payoff_timeline",
                                                DEFAULT_FINANCING_CONFIG["project_payoff_timeline"]),
        "analyze_refi_opportunities": fin_cfg.get("analyze_refi_opportunities",
                                                   DEFAULT_FINANCING_CONFIG["analyze_refi_opportunities"]),
    }


def is_financing_dashboard_enabled(config: Dict[str, Any]) -> bool:
    """Check if financing dashboard is enabled."""
    fin_cfg = get_financing_config(config)
    return fin_cfg["enabled"]


def calculate_unit_debt_status(
    unit_id: int,
    current_debt: float,
    current_value: float,
    monthly_payment: float,
    interest_rate: float,
    original_loan: float = 0.0,
    interest_paid_to_date: float = 0.0,
) -> UnitDebtStatus:
    """
    Calculate comprehensive debt status for a unit.

    Args:
        unit_id: Unit identifier
        current_debt: Current outstanding debt
        current_value: Current property value
        monthly_payment: Current monthly payment
        interest_rate: Annual interest rate
        original_loan: Original loan amount (for tracking principal paid)
        interest_paid_to_date: Cumulative interest paid

    Returns:
        UnitDebtStatus with all debt metrics
    """
    # Calculate LTV
    ltv = current_debt / current_value if current_value > 0 else 0.0

    # Calculate equity
    equity = max(0.0, current_value - current_debt)
    equity_pct = 1.0 - ltv

    # Calculate principal paid to date
    if original_loan > 0:
        principal_paid = original_loan - current_debt
    else:
        principal_paid = 0.0

    # Calculate months remaining at current payment
    if current_debt > 0 and monthly_payment > 0 and interest_rate > 0:
        months_remaining = calculate_months_to_payoff(
            current_debt, monthly_payment, interest_rate
        )
    else:
        months_remaining = 0

    return UnitDebtStatus(
        unit_id=unit_id,
        current_debt=round(current_debt, 2),
        current_value=round(current_value, 2),
        current_ltv=round(ltv, 4),
        monthly_payment=round(monthly_payment, 2),
        interest_rate=interest_rate,
        original_loan=round(original_loan, 2),
        principal_paid_to_date=round(principal_paid, 2),
        interest_paid_to_date=round(interest_paid_to_date, 2),
        months_remaining=months_remaining,
        equity=round(equity, 2),
        equity_pct=round(equity_pct, 4),
    )


def calculate_months_to_payoff(
    balance: float,
    monthly_payment: float,
    annual_rate: float,
    extra_payment: float = 0.0
) -> int:
    """
    Calculate months to payoff given current balance and payment.

    Args:
        balance: Current loan balance
        monthly_payment: Regular monthly payment
        annual_rate: Annual interest rate
        extra_payment: Additional monthly payment

    Returns:
        Number of months to full payoff
    """
    if balance <= 0:
        return 0

    total_payment = monthly_payment + extra_payment
    if total_payment <= 0:
        return 999999  # Effectively infinite

    monthly_rate = annual_rate / 12.0

    # If payment doesn't cover interest, loan will never be paid off
    monthly_interest = balance * monthly_rate
    if total_payment <= monthly_interest:
        return 999999

    months = 0
    remaining = balance

    while remaining > 0 and months < 1200:  # Cap at 100 years
        interest = remaining * monthly_rate
        principal = min(total_payment - interest, remaining)
        remaining -= principal
        months += 1

    return months


def generate_amortization_schedule(
    balance: float,
    monthly_payment: float,
    annual_rate: float,
    months: int = 360
) -> List[AmortizationEntry]:
    """
    Generate full amortization schedule.

    Args:
        balance: Starting loan balance
        monthly_payment: Monthly payment amount
        annual_rate: Annual interest rate
        months: Maximum months to project

    Returns:
        List of AmortizationEntry for each month
    """
    schedule = []
    remaining = balance
    cumulative_interest = 0.0
    cumulative_principal = 0.0
    monthly_rate = annual_rate / 12.0

    for month in range(1, months + 1):
        if remaining <= 0:
            break

        interest = remaining * monthly_rate
        principal = min(monthly_payment - interest, remaining)

        if principal < 0:
            # Payment doesn't cover interest
            break

        remaining -= principal
        cumulative_interest += interest
        cumulative_principal += principal

        schedule.append(AmortizationEntry(
            month=month,
            payment=round(monthly_payment, 2),
            principal=round(principal, 2),
            interest=round(interest, 2),
            balance=round(max(0, remaining), 2),
            cumulative_interest=round(cumulative_interest, 2),
            cumulative_principal=round(cumulative_principal, 2),
        ))

    return schedule


def analyze_refi_opportunity(
    unit_id: int,
    current_debt: float,
    current_value: float,
    current_rate: float,
    current_payment: float,
    months_since_last_refi: int,
    config: Dict[str, Any]
) -> RefiOpportunity:
    """
    Analyze refinance opportunity for a unit.

    Args:
        unit_id: Unit identifier
        current_debt: Current outstanding debt
        current_value: Current property value
        current_rate: Current interest rate
        current_payment: Current monthly payment
        months_since_last_refi: Months since last refinance
        config: Engine configuration

    Returns:
        RefiOpportunity analysis
    """
    # Get refi parameters from config
    acq = config.get("constants", {}).get("acquisition", {})
    banking = config.get("banking", {})
    debt_cfg = config.get("constants", {}).get("debt", {})

    max_ltv = float(acq.get("maxPostRefiLTV", 0.75))
    cooldown_years = int(acq.get("refiCooldownYears", 2))
    cooldown_months = cooldown_years * 12
    ltv_trigger = float(banking.get("refiLTVTrigger", 0.75))
    cashout_cost = float(banking.get("cashoutCostPct", 0.03))
    refi_rate = float(debt_cfg.get("refiRate", 0.07))
    amort_years = int(config.get("constants", {}).get("financial", {}).get("amortizationYears", 30))

    current_ltv = current_debt / current_value if current_value > 0 else 1.0

    # Check eligibility
    is_eligible = True
    reason = "Eligible for refinance"
    months_until = 0

    if current_debt <= 0:
        is_eligible = False
        reason = "Loan already paid off"
    elif months_since_last_refi < cooldown_months:
        is_eligible = False
        months_until = cooldown_months - months_since_last_refi
        reason = f"Cooldown: {months_until} months remaining"
    elif current_ltv >= ltv_trigger:
        is_eligible = False
        reason = f"LTV too high: {current_ltv:.1%} >= {ltv_trigger:.1%}"

    # Calculate potential cashout
    new_debt_max = current_value * max_ltv
    gross_cashout = max(0, new_debt_max - current_debt)
    max_cashout = gross_cashout * (1 - cashout_cost)

    # Calculate new payment at max LTV
    new_payment_max = pmt(refi_rate, amort_years, new_debt_max) if new_debt_max > 0 else 0
    payment_increase = new_payment_max - current_payment

    return RefiOpportunity(
        unit_id=unit_id,
        current_debt=round(current_debt, 2),
        current_rate=current_rate,
        current_payment=round(current_payment, 2),
        max_cashout=round(max_cashout, 2),
        new_debt_at_max_ltv=round(new_debt_max, 2),
        new_payment_at_max_ltv=round(new_payment_max, 2),
        monthly_payment_increase=round(payment_increase, 2),
        is_eligible=is_eligible,
        reason=reason,
        months_until_eligible=months_until,
    )


def project_payoff_timeline(
    unit_id: int,
    current_debt: float,
    monthly_payment: float,
    annual_rate: float,
    extra_payment_scenarios: List[float] = None
) -> PayoffProjection:
    """
    Project debt payoff timeline with various extra payment scenarios.

    Args:
        unit_id: Unit identifier
        current_debt: Current debt balance
        monthly_payment: Current monthly payment
        annual_rate: Annual interest rate
        extra_payment_scenarios: List of extra monthly payments to model

    Returns:
        PayoffProjection with timeline projections
    """
    if extra_payment_scenarios is None:
        extra_payment_scenarios = [0, 100, 250, 500, 1000]

    # Base payoff calculation
    base_months = calculate_months_to_payoff(current_debt, monthly_payment, annual_rate)
    base_years = base_months / 12.0

    # Calculate total remaining interest
    schedule = generate_amortization_schedule(
        current_debt, monthly_payment, annual_rate, base_months + 1
    )
    total_interest_remaining = schedule[-1].cumulative_interest if schedule else 0.0

    # Calculate scenarios with extra payments
    payoff_scenarios = {}
    for extra in extra_payment_scenarios:
        if extra == 0:
            payoff_scenarios[extra] = base_months
        else:
            payoff_scenarios[extra] = calculate_months_to_payoff(
                current_debt, monthly_payment, annual_rate, extra
            )

    return PayoffProjection(
        unit_id=unit_id,
        current_debt=round(current_debt, 2),
        monthly_payment=round(monthly_payment, 2),
        months_to_payoff=base_months,
        years_to_payoff=round(base_years, 1),
        total_interest_remaining=round(total_interest_remaining, 2),
        payoff_with_extra=payoff_scenarios,
    )


def calculate_portfolio_financing_status(
    units_data: List[Dict[str, Any]],
    current_month: int = 0,
    config: Dict[str, Any] = None
) -> PortfolioFinancingStatus:
    """
    Calculate portfolio-wide financing status.

    Args:
        units_data: List of unit data dicts with debt info
        current_month: Current simulation month
        config: Engine configuration

    Returns:
        PortfolioFinancingStatus with aggregate metrics
    """
    if not units_data:
        return PortfolioFinancingStatus(
            total_debt=0.0,
            total_value=0.0,
            portfolio_ltv=0.0,
            total_monthly_debt_service=0.0,
            annual_debt_service=0.0,
            total_equity=0.0,
            weighted_avg_rate=0.0,
            units_with_debt=0,
            units_debt_free=0,
            total_interest_paid_to_date=0.0,
            total_principal_paid_to_date=0.0,
            projected_debt_free_month=None,
        )

    total_debt = 0.0
    total_value = 0.0
    total_monthly_service = 0.0
    total_interest_paid = 0.0
    total_principal_paid = 0.0
    units_with_debt = 0
    units_debt_free = 0
    weighted_rate_sum = 0.0

    for unit in units_data:
        debt = float(unit.get("debt", 0))
        value = float(unit.get("value", 0))
        payment = float(unit.get("monthly_payment", 0))
        rate = float(unit.get("rate", 0))
        interest_paid = float(unit.get("interest_paid", 0))
        principal_paid = float(unit.get("principal_paid", 0))

        total_debt += debt
        total_value += value
        total_monthly_service += payment
        total_interest_paid += interest_paid
        total_principal_paid += principal_paid

        if debt > 0:
            units_with_debt += 1
            weighted_rate_sum += debt * rate
        else:
            units_debt_free += 1

    # Calculate portfolio metrics
    portfolio_ltv = total_debt / total_value if total_value > 0 else 0.0
    total_equity = total_value - total_debt
    weighted_avg_rate = weighted_rate_sum / total_debt if total_debt > 0 else 0.0
    annual_debt_service = total_monthly_service * 12

    # Project debt-free timeline (simplified: assuming constant payments)
    projected_debt_free_month = None
    if total_debt > 0 and total_monthly_service > 0 and weighted_avg_rate > 0:
        months_remaining = calculate_months_to_payoff(
            total_debt, total_monthly_service, weighted_avg_rate
        )
        if months_remaining < 999999:
            projected_debt_free_month = current_month + months_remaining

    return PortfolioFinancingStatus(
        total_debt=round(total_debt, 2),
        total_value=round(total_value, 2),
        portfolio_ltv=round(portfolio_ltv, 4),
        total_monthly_debt_service=round(total_monthly_service, 2),
        annual_debt_service=round(annual_debt_service, 2),
        total_equity=round(total_equity, 2),
        weighted_avg_rate=round(weighted_avg_rate, 4),
        units_with_debt=units_with_debt,
        units_debt_free=units_debt_free,
        total_interest_paid_to_date=round(total_interest_paid, 2),
        total_principal_paid_to_date=round(total_principal_paid, 2),
        projected_debt_free_month=projected_debt_free_month,
    )


def calculate_interest_savings(
    balance: float,
    monthly_payment: float,
    annual_rate: float,
    extra_payment: float
) -> Dict[str, float]:
    """
    Calculate interest savings from extra payments.

    Args:
        balance: Current loan balance
        monthly_payment: Regular monthly payment
        annual_rate: Annual interest rate
        extra_payment: Additional monthly payment

    Returns:
        Dict with savings metrics
    """
    # Base scenario
    base_schedule = generate_amortization_schedule(
        balance, monthly_payment, annual_rate
    )
    base_months = len(base_schedule)
    base_interest = base_schedule[-1].cumulative_interest if base_schedule else 0

    # With extra payment
    new_schedule = generate_amortization_schedule(
        balance, monthly_payment + extra_payment, annual_rate
    )
    new_months = len(new_schedule)
    new_interest = new_schedule[-1].cumulative_interest if new_schedule else 0

    return {
        "base_months": base_months,
        "base_interest": round(base_interest, 2),
        "new_months": new_months,
        "new_interest": round(new_interest, 2),
        "months_saved": base_months - new_months,
        "interest_saved": round(base_interest - new_interest, 2),
        "extra_cost": round(extra_payment * new_months, 2),
        "net_savings": round(base_interest - new_interest - (extra_payment * new_months), 2),
    }


def get_monthly_interest_principal_split(
    balance: float,
    monthly_payment: float,
    annual_rate: float
) -> Tuple[float, float]:
    """
    Get interest and principal portions of next payment.

    Args:
        balance: Current loan balance
        monthly_payment: Monthly payment amount
        annual_rate: Annual interest rate

    Returns:
        Tuple of (interest_portion, principal_portion)
    """
    if balance <= 0:
        return 0.0, 0.0

    monthly_rate = annual_rate / 12.0
    interest = balance * monthly_rate
    principal = min(monthly_payment - interest, balance)

    return round(interest, 2), round(max(0, principal), 2)


def validate_financing_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate financing configuration.

    Args:
        config: Engine configuration

    Returns:
        List of validation issues
    """
    issues = []
    fin_cfg = config.get("financing_dashboard", {})

    if not fin_cfg.get("enabled", True):
        return issues  # Skip validation if disabled

    # Check debt configuration
    debt_cfg = config.get("constants", {}).get("debt", {})

    mortgage_rate = debt_cfg.get("mortgageRate", 0)
    if mortgage_rate <= 0 or mortgage_rate > 0.20:
        issues.append(f"Mortgage rate {mortgage_rate:.2%} seems unrealistic")

    refi_rate = debt_cfg.get("refiRate", 0)
    if refi_rate <= 0 or refi_rate > 0.20:
        issues.append(f"Refi rate {refi_rate:.2%} seems unrealistic")

    # Check acquisition config
    acq = config.get("constants", {}).get("acquisition", {})

    max_ltv = acq.get("maxPostRefiLTV", 0)
    if max_ltv <= 0 or max_ltv > 0.95:
        issues.append(f"Max post-refi LTV {max_ltv:.0%} out of typical range")

    down_first = acq.get("downPaymentFirst", 0)
    if down_first < 0.03 or down_first > 0.50:
        issues.append(f"First down payment {down_first:.0%} out of typical range")

    return issues


def summarize_financing(
    units_data: List[Dict[str, Any]],
    current_month: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create comprehensive financing summary.

    Args:
        units_data: List of unit data dicts
        current_month: Current simulation month
        config: Engine configuration

    Returns:
        Dict with complete financing summary
    """
    portfolio_status = calculate_portfolio_financing_status(units_data, current_month, config)

    # Get individual unit statuses
    unit_statuses = []
    for unit in units_data:
        status = calculate_unit_debt_status(
            unit_id=unit.get("unit_id", 0),
            current_debt=unit.get("debt", 0),
            current_value=unit.get("value", 0),
            monthly_payment=unit.get("monthly_payment", 0),
            interest_rate=unit.get("rate", 0),
            original_loan=unit.get("original_loan", 0),
            interest_paid_to_date=unit.get("interest_paid", 0),
        )
        unit_statuses.append(status)

    # Get refi opportunities
    refi_opportunities = []
    for unit in units_data:
        if unit.get("debt", 0) > 0:
            opp = analyze_refi_opportunity(
                unit_id=unit.get("unit_id", 0),
                current_debt=unit.get("debt", 0),
                current_value=unit.get("value", 0),
                current_rate=unit.get("rate", 0),
                current_payment=unit.get("monthly_payment", 0),
                months_since_last_refi=current_month - unit.get("last_refi_month", 0),
                config=config,
            )
            refi_opportunities.append(opp)

    # Get payoff projections
    payoff_projections = []
    for unit in units_data:
        if unit.get("debt", 0) > 0:
            proj = project_payoff_timeline(
                unit_id=unit.get("unit_id", 0),
                current_debt=unit.get("debt", 0),
                monthly_payment=unit.get("monthly_payment", 0),
                annual_rate=unit.get("rate", 0),
            )
            payoff_projections.append(proj)

    return {
        "portfolio": portfolio_status,
        "units": unit_statuses,
        "refi_opportunities": refi_opportunities,
        "payoff_projections": payoff_projections,
        "validation_issues": validate_financing_config(config),
    }
