"""
Feeder Property Strategy Module

This module implements the "feeder property" acquisition and debt payoff strategy:

PHASE 1 (< max_units): Acquisition Mode
- Select one property as the "feeder" based on lowest LTV past cooldown
- Concentrate all prepayments on the feeder to build equity
- When feeder has sufficient equity (LTV < 75%), refinance to extract cash for next purchase

PHASE 2 (>= max_units): Debt Payoff Mode
- Stop all refinancing (no more cash-out refis)
- Continue feeder strategy for debt elimination
- Target lowest LTV property for concentrated prepayments
- Once a property is fully paid off, select new feeder from remaining mortgaged properties
"""

from typing import Optional, List, Tuple
from .types import Unit
from .debt import pmt


def select_feeder(
    units: List[Unit],
    month_global: int,
    cooldown_months: int,
    for_refi: bool = True
) -> Optional[int]:
    """
    Select the property best positioned to be the feeder.

    Args:
        units: List of owned properties
        month_global: Current simulation month
        cooldown_months: Number of months required since last refi
        for_refi: If True, only consider units past cooldown. If False, consider all with debt.

    Returns:
        Index of the feeder property in the units list, or None if no eligible properties.

    Selection criteria:
        - Must have debt > 0 (not fully paid off)
        - If for_refi=True: must be past refi cooldown
        - Among eligible: choose the one with lowest LTV (most equity)
    """
    if not units:
        return None

    eligible = []
    for i, u in enumerate(units):
        if u.debt <= 0:
            continue  # Skip paid-off properties

        if for_refi:
            months_since_refi = month_global - u.last_refi_month
            if months_since_refi < cooldown_months:
                continue  # Not past cooldown

        # Calculate extractable equity (max 75% LTV refi, minus 3% closing costs)
        max_ltv = 0.75
        extractable = (u.value * max_ltv - u.debt) * 0.97 if u.value > 0 else 0
        eligible.append((i, extractable))

    if not eligible:
        return None

    # Select highest extractable equity (most capital per refi)
    eligible.sort(key=lambda x: x[1], reverse=True)
    return eligible[0][0]


def calculate_potential_refi_cashout(
    unit: Unit,
    max_ltv: float,
    cost_pct: float
) -> float:
    """
    Calculate how much cash could be extracted from a refinance.

    Args:
        unit: The property to potentially refinance
        max_ltv: Maximum LTV after refinance (e.g., 0.75)
        cost_pct: Closing cost percentage (e.g., 0.03)

    Returns:
        Net cash that could be extracted (after closing costs)
    """
    new_debt = unit.value * max_ltv
    gross = max(0.0, new_debt - unit.debt)
    net = gross * (1 - cost_pct)
    return round(net, 2)


def is_feeder_refi_eligible(
    units: List[Unit],
    feeder_index: Optional[int],
    month_global: int,
    ltv_trigger: float,
    cooldown_months: int
) -> Tuple[bool, float]:
    """
    Check if the current feeder is eligible for refinancing.

    Args:
        units: List of owned properties
        feeder_index: Index of current feeder property
        month_global: Current simulation month
        ltv_trigger: LTV threshold for refi eligibility (e.g., 0.75)
        cooldown_months: Months required since last refi

    Returns:
        Tuple of (is_eligible, current_ltv)
    """
    if feeder_index is None or feeder_index >= len(units):
        return False, 0.0

    feeder = units[feeder_index]
    if feeder.debt <= 0:
        return False, 0.0

    ltv = feeder.debt / feeder.value if feeder.value > 0 else 1.0
    months_since_refi = month_global - feeder.last_refi_month

    # Note: use < not <= for LTV comparison (per bug fix)
    is_eligible = ltv < ltv_trigger and months_since_refi >= cooldown_months
    return is_eligible, ltv


def execute_refi_cashout(
    unit: Unit,
    max_ltv: float,
    cost_pct: float,
    refi_rate: float,
    amort_years: int,
    month_global: int,
    target_cashout: float = 0.0,
    strategy: str = "max"
) -> float:
    """
    Execute a cash-out refinance on a property.

    Args:
        unit: The property to refinance (will be modified)
        max_ltv: Maximum LTV after refinance
        cost_pct: Closing cost percentage
        refi_rate: New interest rate for the refinanced loan
        amort_years: Amortization period in years
        month_global: Current simulation month
        target_cashout: Target net cash needed (for "min" strategy)
        strategy: "max" = extract to max LTV, "min" = extract only what's needed

    Returns:
        Net cash extracted (after closing costs)
    """
    if strategy == "min" and target_cashout > 0:
        # Calculate debt needed to extract target cash (accounting for closing costs)
        # target_net = gross * (1 - cost_pct)
        # gross = target_net / (1 - cost_pct)
        gross_needed = target_cashout / (1 - cost_pct)
        new_debt = unit.debt + gross_needed

        # Ensure we don't exceed max LTV
        max_debt = unit.value * max_ltv
        new_debt = min(new_debt, max_debt)

        # Recalculate actual cash out
        gross = max(0.0, new_debt - unit.debt)
        net = gross * (1 - cost_pct)
    else:
        # Max strategy: refinance to maximum LTV
        new_debt = unit.value * max_ltv
        gross = max(0.0, new_debt - unit.debt)
        net = gross * (1 - cost_pct)

    unit.debt = new_debt
    unit.monthly_payment = pmt(refi_rate, amort_years, new_debt)
    unit.rate = refi_rate
    unit.last_refi_month = month_global

    return round(net, 2)


def attempt_refi_cashout(
    month: int,
    units: List[Unit],
    engine: dict,
    amort_years: int,
    feeder_index: Optional[int] = None,
    units_owned: int = 0,
    target_cashout: float = 0.0
) -> Tuple[float, Optional[int]]:
    """
    Attempt to execute a cash-out refinance on the feeder property.

    This is the main entry point for the refi logic, called from simulator.

    Args:
        month: Current simulation month
        units: List of owned properties
        engine: Configuration dictionary
        amort_years: Amortization period in years
        feeder_index: Current feeder property index (if known)
        units_owned: Number of units currently owned
        target_cashout: Target net cash needed (for "min" strategy)

    Returns:
        Tuple of (net_cashout_amount, new_feeder_index)
    """
    if not units:
        return 0.0, None

    banking = engine["banking"]
    acq = engine["constants"]["acquisition"]
    policies = engine.get("policies", {})
    portfolio = policies.get("portfolio", {})

    max_units = int(portfolio.get("maxUnits", 7))
    stop_refi_at_max = bool(portfolio.get("stopRefiAtMaxUnits", True))

    # PHASE 2: Stop refinancing once at max units
    if stop_refi_at_max and units_owned >= max_units:
        # Still need to select a feeder for prepayment targeting
        cooldown = int(acq["refiCooldownYears"]) * 12
        new_feeder = select_feeder(units, month, cooldown, for_refi=False)
        return 0.0, new_feeder

    ltv_trigger = float(banking["refiLTVTrigger"])
    max_ltv = float(acq["maxPostRefiLTV"])
    cooldown = int(acq["refiCooldownYears"]) * 12
    cost = float(banking["cashoutCostPct"])
    refi_rate = float(engine["constants"]["debt"]["refiRate"])

    # Get refi cashout strategy from config (default to "max")
    refi_strategy = acq.get("refiCashoutStrategy", "max")

    # Select feeder if not already set
    if feeder_index is None:
        feeder_index = select_feeder(units, month, cooldown, for_refi=True)

    if feeder_index is None:
        return 0.0, None

    # Check if feeder is eligible
    is_eligible, _ = is_feeder_refi_eligible(
        units, feeder_index, month, ltv_trigger, cooldown
    )

    if not is_eligible:
        return 0.0, feeder_index

    # Execute the refinance
    net_cash = execute_refi_cashout(
        units[feeder_index],
        max_ltv,
        cost,
        refi_rate,
        amort_years,
        month,
        target_cashout,
        refi_strategy
    )

    # After refi, feeder may change - select new one
    new_feeder = select_feeder(units, month, cooldown, for_refi=True)

    return net_cash, new_feeder


def prepay_feeder(
    prepay_amount: float,
    units: List[Unit],
    feeder_index: Optional[int]
) -> Tuple[float, Optional[int]]:
    """
    Apply prepayment to the designated feeder property only.

    Args:
        prepay_amount: Amount to prepay
        units: List of owned properties
        feeder_index: Index of the feeder property

    Returns:
        Tuple of (actual_prepay_amount, updated_feeder_index)
        If feeder is paid off, feeder_index becomes None (needs reselection)
    """
    if prepay_amount <= 0 or not units or feeder_index is None:
        return 0.0, feeder_index

    if feeder_index >= len(units):
        return 0.0, None

    feeder = units[feeder_index]
    if feeder.debt <= 0:
        return 0.0, None  # Feeder already paid off, needs reselection

    actual_prepay = min(prepay_amount, feeder.debt)
    feeder.debt = round(feeder.debt - actual_prepay, 2)

    # Check if feeder is now paid off
    if feeder.debt <= 0:
        feeder.debt = 0.0
        feeder.monthly_payment = 0.0
        return round(actual_prepay, 2), None  # Signal need for new feeder selection

    return round(actual_prepay, 2), feeder_index


def prepay_surplus(
    cash: float,
    liquidity_req: float,
    rainy_reserve: float,
    units: List[Unit],
    fixed_monthly_costs: float,
    feeder_index: Optional[int] = None,
    operating_cash_months: float = 1.0
) -> Tuple[float, float, Optional[int]]:
    """
    Prepay surplus cash to the feeder property.

    This is called in Phase 2 (debt payoff mode) to eliminate debt on one property at a time.

    Args:
        cash: Current operating cash balance
        liquidity_req: Required liquidity reserves
        rainy_reserve: Current rainy-day reserve balance
        units: List of owned properties
        fixed_monthly_costs: Monthly fixed costs for operating cushion
        feeder_index: Current feeder property index
        operating_cash_months: Number of months of fixed costs to maintain in operating cash

    Returns:
        Tuple of (prepay_amount, remaining_cash, updated_feeder_index)
    """
    # Minimum operating cash cushion = configured months of fixed costs
    # Operating cash must maintain its own minimum balance independent of rainy reserve
    min_operating_cash = operating_cash_months * fixed_monthly_costs
    surplus = cash - min_operating_cash

    if surplus <= 0 or not units:
        return 0.0, cash, feeder_index

    prepay, new_feeder_index = prepay_feeder(surplus, units, feeder_index)
    remaining_cash = round(cash - prepay, 2)

    return prepay, remaining_cash, new_feeder_index


def get_feeder_ltv(units: List[Unit], feeder_index: Optional[int]) -> float:
    """Get the current LTV of the feeder property."""
    if feeder_index is None or feeder_index >= len(units):
        return 0.0
    feeder = units[feeder_index]
    if feeder.value <= 0:
        return 0.0
    return round(feeder.debt / feeder.value, 4)
