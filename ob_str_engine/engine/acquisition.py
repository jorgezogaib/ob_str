"""
Acquisition module for property purchase calculations.

Provides parity price calculation (what price yields target unlevered return)
and purchase affordability checks.
"""

from typing import Dict, Any, Tuple, Optional
from .revenue import get_adr_for_year


def calculate_parity_price(
    year: int,
    engine: dict,
    market_profile_name: Optional[str] = None
) -> float:
    """
    Calculates the correct parity purchase price for the given year.

    With seasonality enabled, uses seasonal average annual revenue instead of
    flat assumptions. This typically results in a lower parity price (more
    realistic for seasonal markets).

    Args:
        year: Simulation year (1-indexed)
        engine: Engine configuration dictionary
        market_profile_name: Optional market profile to use (defaults to portfolio default)

    Returns:
        Parity price for target unlevered yield
    """
    ops = engine["constants"]["operations"]
    acq = engine["constants"]["acquisition"]

    mgmt_pct = float(ops["mgmtPct"])
    capex_pct = float(ops["capexPct"])
    target_yield = float(acq["targetYieldUnlevered"])

    # Check if we should use seasonal calculations
    market_profiles = engine.get("market_profiles", {})
    use_seasonal = bool(market_profiles)

    if use_seasonal:
        return _calculate_parity_price_seasonal(
            year, engine, market_profile_name, mgmt_pct, capex_pct, target_yield
        )
    else:
        return _calculate_parity_price_flat(
            year, engine, mgmt_pct, capex_pct, target_yield
        )


def _calculate_parity_price_flat(
    year: int,
    engine: dict,
    mgmt_pct: float,
    capex_pct: float,
    target_yield: float
) -> float:
    """
    Calculate parity price using flat assumptions (v2.3 behavior).

    Args:
        year: Simulation year
        engine: Engine configuration
        mgmt_pct: Management fee percentage
        capex_pct: CapEx percentage
        target_yield: Target unlevered yield

    Returns:
        Parity price
    """
    ops = engine["constants"]["operations"]

    base_adr = float(ops["adrBaseline2BR"])
    occ = float(ops["occupancyBaseline"])
    hoa_annual_base = float(ops["hoaAnnual"])
    hoa_inflation_rate = float(ops["hoaInflationRate"])
    ins_rate = float(ops["insuranceRate"])
    tax_rate = float(ops["propertyTaxRate"])
    revenue_infl_rate = float(engine["market"].get("revenueInflationRate", 0.04))

    # Revenue grows with inflation
    adr_this_year = get_adr_for_year(base_adr, revenue_infl_rate, year)

    # HOA must also be inflated
    hoa_this_year = hoa_annual_base * (1 + hoa_inflation_rate) ** (year - 1)

    gross_one_unit = adr_this_year * occ * 365
    noi_one_unit = gross_one_unit * (1 - mgmt_pct - capex_pct) - hoa_this_year

    price_parity = noi_one_unit / (target_yield + ins_rate + tax_rate)
    return round(max(0.0, price_parity), 2)


def _calculate_parity_price_seasonal(
    year: int,
    engine: dict,
    market_profile_name: Optional[str],
    mgmt_pct: float,
    capex_pct: float,
    target_yield: float
) -> float:
    """
    Calculate parity price using seasonal revenue averages.

    Args:
        year: Simulation year
        engine: Engine configuration
        market_profile_name: Market profile to use
        mgmt_pct: Management fee percentage
        capex_pct: CapEx percentage
        target_yield: Target unlevered yield

    Returns:
        Parity price based on seasonal average revenue
    """
    from .seasonality import (
        get_market_profile,
        get_default_market_name,
        get_market_expenses,
        calculate_annual_seasonal_average,
        get_market_baseline
    )

    # Determine market to use
    if market_profile_name is None:
        market_profile_name = get_default_market_name(engine)

    market = get_market_profile(engine, market_profile_name)
    if market is None:
        # Fall back to flat calculation
        return _calculate_parity_price_flat(
            year, engine, mgmt_pct, capex_pct, target_yield
        )

    # Get market-specific parameters
    base_adr, base_occupancy = get_market_baseline(engine, market_profile_name)
    expenses = get_market_expenses(engine, market_profile_name)

    ins_rate = expenses["insurance_rate"]
    tax_rate = expenses["property_tax_rate"]
    hoa_annual_base = expenses["hoa_annual"]

    # HOA inflation
    ops = engine["constants"]["operations"]
    hoa_inflation_rate = float(ops.get("hoaInflationRate", 0.04))
    hoa_this_year = hoa_annual_base * (1 + hoa_inflation_rate) ** (year - 1)

    # Get calendar days from config
    calendar = engine.get("calendar", {})
    calendar_days = calendar.get("monthlyDays", [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

    # Apply revenue inflation
    revenue_infl_rate = float(engine["market"].get("revenueInflationRate", 0.04))
    adr_inflated = get_adr_for_year(base_adr, revenue_infl_rate, year)

    # Calculate seasonal annual revenue
    gross_annual, _ = calculate_annual_seasonal_average(
        engine, market_profile_name, adr_inflated, base_occupancy, calendar_days
    )

    # NOI calculation
    noi_one_unit = gross_annual * (1 - mgmt_pct - capex_pct) - hoa_this_year

    # Parity price for target yield
    price_parity = noi_one_unit / (target_yield + ins_rate + tax_rate)
    return round(max(0.0, price_parity), 2)


def can_purchase(
    units_owned: int,
    cash: float,
    price_parity: float,
    is_first: bool,
    engine: dict,
) -> Tuple[bool, float, float, float]:
    """
    Check if a purchase is affordable.

    Args:
        units_owned: Current number of units owned
        cash: Available cash
        price_parity: Target purchase price
        is_first: Whether this is the first property
        engine: Engine configuration

    Returns:
        Tuple of (can_afford, down_payment, closing_costs, total_needed)
    """
    acq = engine["constants"]["acquisition"]
    dp_pct = float(acq["downPaymentFirst"] if is_first else acq["downPaymentSubsequent"])
    closing_pct = float(acq["closingCostPct"])
    needed = price_parity * (dp_pct + closing_pct)

    if cash >= needed:
        dp_amount = price_parity * dp_pct
        closing_amount = price_parity * closing_pct
        return True, dp_amount, closing_amount, needed

    return False, 0.0, 0.0, 0.0


def get_default_market_for_acquisition(engine: dict) -> str:
    """
    Get the default market profile for new acquisitions.

    Args:
        engine: Engine configuration

    Returns:
        Market profile name
    """
    from .seasonality import get_default_market_name
    return get_default_market_name(engine)
