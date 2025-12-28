"""
Distribution Logic - Calculate investor distributions based on configurable triggers

Supports two modes:
1. SIMPLE MODE (current): One of three trigger types (Year, LTV, or Distributable Amount)
2. COMPLEX MODE (future): Multiple triggers with safety checks (preserved for later use)
"""
from typing import Dict, Tuple


def check_distribution_eligibility(
    config: Dict,
    units_owned: int,
    noi_monthly: float,
    ltv_pct: float,
    total_debt: float,
    total_reserves: float,
    debt_service: float,
    fixed_monthly_costs: float,
    current_year: int = 0,
    distributable_amount: float = 0.0,
) -> Tuple[bool, str]:
    """
    Check if portfolio meets distribution trigger conditions.

    SIMPLE MODE (current default):
    - Checks only ONE trigger type at a time
    - Options: startYear, maxLTV, or minDistributableAmount

    COMPLEX MODE (legacy, for future use):
    - Checks ALL triggers: income, properties, LTV, reserves, DSCR, etc.
    - Enable by setting useComplexTriggers: true in config

    Returns:
        (eligible: bool, reason: str)
    """
    if not config.get("enabled", False):
        return False, "Distributions disabled in config"

    triggers = config.get("triggers", {})

    # Check if using complex multi-trigger mode (legacy)
    use_complex = triggers.get("useComplexTriggers", False)

    if use_complex:
        # COMPLEX MODE: All triggers must be met (original implementation)
        return _check_complex_triggers(
            triggers, units_owned, noi_monthly, ltv_pct, total_debt,
            total_reserves, debt_service, fixed_monthly_costs
        )
    else:
        # SIMPLE MODE: Check only ONE trigger type
        return _check_simple_trigger(
            triggers, ltv_pct, current_year, distributable_amount, units_owned
        )


def _check_simple_trigger(
    triggers: Dict,
    ltv_pct: float,
    current_year: int,
    distributable_amount: float,
    units_owned: int = 0,
) -> Tuple[bool, str]:
    """
    Simple mode: Check ONE trigger type at a time.
    Priority: startYear > maxLTV > minDistributableAmount

    Note: Requires at least 1 property owned to prevent distributing
    all capital before first acquisition.
    """
    # Safety check: Must own at least one property
    if units_owned < 1:
        return False, "No properties owned yet"

    # Trigger 1: Year-Based (highest priority)
    if "startYear" in triggers:
        start_year = triggers.get("startYear", 22)
        if current_year >= start_year:
            return True, f"Distribution start year reached (Year {current_year})"
        else:
            return False, f"Not yet at start year ({current_year} < {start_year})"

    # Trigger 2: LTV-Based (second priority)
    if "maxLTV" in triggers:
        max_ltv = triggers.get("maxLTV", 30.0)
        if ltv_pct <= max_ltv:
            return True, f"LTV threshold met ({ltv_pct:.1f}% <= {max_ltv:.1f}%)"
        else:
            return False, f"LTV too high ({ltv_pct:.1f}% > {max_ltv:.1f}%)"

    # Trigger 3: Distributable Amount-Based (third priority)
    if "minDistributableAmount" in triggers:
        min_amount = triggers.get("minDistributableAmount", 50000.0)
        if distributable_amount >= min_amount:
            return True, f"Distributable amount threshold met (${distributable_amount:,.0f} >= ${min_amount:,.0f})"
        else:
            return False, f"Distributable amount too low (${distributable_amount:,.0f} < ${min_amount:,.0f})"

    # No trigger configured - default to disabled
    return False, "No trigger configured (startYear, maxLTV, or minDistributableAmount required)"


def _check_complex_triggers(
    triggers: Dict,
    units_owned: int,
    noi_monthly: float,
    ltv_pct: float,
    total_debt: float,
    total_reserves: float,
    debt_service: float,
    fixed_monthly_costs: float,
) -> Tuple[bool, str]:
    """
    Complex mode: ALL triggers must be met (legacy implementation, preserved for future).
    """
    # Trigger 1: Minimum properties owned
    min_properties = triggers.get("minPropertiesOwned", 3)
    if units_owned < min_properties:
        return False, f"Properties owned ({units_owned}) < minimum ({min_properties})"

    # Trigger 2: Target annual income
    target_income = triggers.get("targetAnnualIncome", 100000)
    annual_noi = noi_monthly * 12
    if annual_noi < target_income:
        return False, f"Annual NOI (${annual_noi:,.0f}) < target (${target_income:,.0f})"

    # Trigger 3: Portfolio LTV (or debt-free override)
    max_ltv = triggers.get("maxPortfolioLTV", 30.0)
    allow_debt_free_override = triggers.get("allowDebtFreeOverride", True)

    is_debt_free = (total_debt == 0 or ltv_pct == 0)

    if is_debt_free and allow_debt_free_override:
        # Debt-free override: skip LTV check
        pass
    elif ltv_pct > max_ltv:
        return False, f"Portfolio LTV ({ltv_pct:.1f}%) > maximum ({max_ltv:.1f}%)"

    # Trigger 4: Minimum reserve cushion
    min_cushion = triggers.get("minReserveCushion", 200000)
    if total_reserves < min_cushion:
        return False, f"Total reserves (${total_reserves:,.0f}) < minimum (${min_cushion:,.0f})"

    # Trigger 5: Minimum months of fixed costs in reserves
    min_months = triggers.get("minMonthsFixedCostsReserve", 12)
    required_reserves = fixed_monthly_costs * min_months
    if total_reserves < required_reserves:
        return False, f"Reserves (${total_reserves:,.0f}) < {min_months} months fixed costs (${required_reserves:,.0f})"

    # Trigger 6: Minimum DSCR (if debt exists)
    if total_debt > 0 and debt_service > 0:
        min_dscr = triggers.get("minDSCR", 1.5)
        dscr = noi_monthly / debt_service if debt_service > 0 else 999.0
        if dscr < min_dscr:
            return False, f"DSCR ({dscr:.2f}) < minimum ({min_dscr:.2f})"

    return True, "All triggers met"


def check_distribution_safety(
    config: Dict,
    ltv_pct: float,
    total_reserves: float,
    fixed_monthly_costs: float,
    noi_monthly: float,
    debt_service: float,
) -> Tuple[bool, str]:
    """
    Safety checks - can suspend distributions even if triggers are met.
    Only used in COMPLEX MODE. Simple mode has no safety suspensions.

    Returns:
        (safe: bool, reason: str)
    """
    # Simple mode: no safety checks, always pass
    triggers = config.get("triggers", {})
    use_complex = triggers.get("useComplexTriggers", False)

    if not use_complex:
        return True, "Safety checks disabled in simple mode"

    # Complex mode: apply safety checks
    safety = config.get("safety", {})

    # Safety 1: LTV too high
    max_ltv = safety.get("suspendIfLTVExceeds", 50.0)
    if ltv_pct > max_ltv:
        return False, f"LTV ({ltv_pct:.1f}%) exceeds safety limit ({max_ltv:.1f}%)"

    # Safety 2: Reserves too low
    min_months = safety.get("suspendIfReservesBelowMonths", 6)
    required_reserves = fixed_monthly_costs * min_months
    if total_reserves < required_reserves:
        return False, f"Reserves (${total_reserves:,.0f}) below {min_months} month cushion (${required_reserves:,.0f})"

    # Safety 3: DSCR too low
    if debt_service > 0:
        min_dscr = safety.get("suspendIfDSCRBelow", 1.2)
        dscr = noi_monthly / debt_service if debt_service > 0 else 999.0
        if dscr < min_dscr:
            return False, f"DSCR ({dscr:.2f}) below safety limit ({min_dscr:.2f})"

    return True, "All safety checks passed"


def calculate_distribution(
    config: Dict,
    distributable_cash: float,
) -> Tuple[float, str]:
    """
    Calculate distribution amount based on distributable cash.

    SIMPLE MODE: Distributes a percentage of available cash after all obligations.
    COMPLEX MODE: Same as simple, but with reserve top-up priority.

    Args:
        config: Distribution configuration
        distributable_cash: Cash available for distribution after all reserves/obligations

    Returns:
        (distribution_amount, note)
    """
    dist_cfg = config.get("distribution", {})

    if distributable_cash <= 0:
        return 0.0, "No distributable cash available"

    # Apply distribution percentage
    dist_pct = dist_cfg.get("distributionPct", 1.0)  # Default 100% in simple mode
    distribution = distributable_cash * dist_pct

    note = f"Distributing {dist_pct:.0%} of ${distributable_cash:,.0f} available"

    return max(0.0, distribution), note


def process_distribution(
    config: Dict,
    units_owned: int,
    noi_monthly: float,
    ltv_pct: float,
    total_debt: float,
    total_reserves: float,
    debt_service: float,
    fixed_monthly_costs: float,
    current_year: int = 0,
    distributable_cash: float = 0.0,
    reserve_topup_needed: float = 0.0,
) -> Dict:
    """
    Main distribution processing function.

    SIMPLE MODE (current):
    - Uses distributable_cash and current_year parameters
    - Checks ONE trigger type (year, LTV, or distributable amount)
    - No safety suspensions

    COMPLEX MODE (legacy):
    - Uses all parameters for multi-trigger checks
    - Has safety suspension rules

    Returns dict with:
        - enabled: bool
        - eligible: bool
        - safe: bool
        - distribution_amount: float
        - reason: str
    """
    result = {
        "enabled": False,
        "eligible": False,
        "safe": False,
        "distribution_amount": 0.0,
        "reason": "Not processed",
    }

    # Check if enabled
    if not config.get("enabled", False):
        result["reason"] = "Distributions disabled"
        return result

    result["enabled"] = True

    # Check eligibility
    eligible, eligibility_reason = check_distribution_eligibility(
        config, units_owned, noi_monthly, ltv_pct, total_debt,
        total_reserves, debt_service, fixed_monthly_costs,
        current_year, distributable_cash
    )

    if not eligible:
        result["reason"] = f"Not eligible: {eligibility_reason}"
        return result

    result["eligible"] = True

    # Check safety (only applies in complex mode)
    safe, safety_reason = check_distribution_safety(
        config, ltv_pct, total_reserves, fixed_monthly_costs,
        noi_monthly, debt_service
    )

    if not safe:
        result["reason"] = f"Safety suspended: {safety_reason}"
        return result

    result["safe"] = True

    # Calculate distribution
    distribution, note = calculate_distribution(config, distributable_cash)

    result["distribution_amount"] = distribution
    result["reason"] = note

    return result
