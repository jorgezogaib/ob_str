"""
Revenue calculation module.

Provides functions for calculating gross rental revenue, with support for
both flat (v2.3) and seasonal (v2.4+) calculations.
"""

from typing import Dict, Any, List, Tuple, Optional
from .types import Unit


def calculate_gross_revenue(units: int, adr: float, occ: float, days: int) -> float:
    """
    Calculate gross revenue using flat assumptions (v2.3 behavior).

    Args:
        units: Number of units
        adr: Average daily rate
        occ: Occupancy rate (0-1)
        days: Days in month

    Returns:
        Gross monthly revenue
    """
    return round(adr * occ * days * units, 2)


def get_adr_for_year(base_adr: float, infl: float, year: int) -> float:
    """
    Calculate inflated ADR for a given year.

    Args:
        base_adr: Base ADR (year 1)
        infl: Annual inflation rate (e.g., 0.04 for 4%)
        year: Simulation year (1-indexed)

    Returns:
        Inflated ADR for the year
    """
    return base_adr * (1 + infl) ** (year - 1)


def calculate_gross_revenue_seasonal(
    units_list: List[Unit],
    config: Dict[str, Any],
    year: int,
    simulation_month: int,
    days_in_month: int
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate gross revenue with seasonal adjustments per unit.

    Each unit's revenue is calculated based on its assigned market profile
    and that market's seasonal multipliers for the current month.

    Args:
        units_list: List of Unit objects
        config: Engine configuration dictionary
        year: Simulation year (1-indexed)
        simulation_month: Global simulation month (1-360)
        days_in_month: Number of days in the current month

    Returns:
        Tuple of (total_gross_revenue, details_dict)
    """
    # Import here to avoid circular imports
    from .seasonality import (
        get_seasonal_factors,
        calculate_seasonal_revenue,
        get_market_baseline,
        get_default_market_name
    )

    if not units_list:
        return 0.0, {
            "total_revenue": 0.0,
            "flat_revenue": 0.0,
            "seasonal_delta": 0.0,
            "units_breakdown": [],
            "by_market": {},
            "seasonality_enabled": False
        }

    # Get inflation rate
    market_cfg = config.get("market", {})
    revenue_infl_rate = float(market_cfg.get("revenueInflationRate", 0.04))

    total_revenue = 0.0
    total_flat_revenue = 0.0
    units_breakdown = []
    by_market = {}

    for unit in units_list:
        market_name = getattr(unit, 'market_profile', get_default_market_name(config))

        # Get baseline for this market
        base_adr, base_occupancy = get_market_baseline(config, market_name)

        # Apply inflation
        adr_inflated = get_adr_for_year(base_adr, revenue_infl_rate, year)

        # Get seasonal factors
        factors = get_seasonal_factors(config, market_name, simulation_month)

        # Calculate seasonal revenue
        unit_revenue, details = calculate_seasonal_revenue(
            adr_inflated, base_occupancy, days_in_month, factors
        )

        total_revenue += unit_revenue
        total_flat_revenue += details["flat_revenue"]

        # Store unit breakdown
        unit_details = {
            "unit_id": unit.unit_id,
            "market": market_name,
            **details
        }
        units_breakdown.append(unit_details)

        # Aggregate by market
        if market_name not in by_market:
            by_market[market_name] = {
                "units": 0,
                "revenue": 0.0,
                "flat_revenue": 0.0,
                "seasonal_delta": 0.0
            }
        by_market[market_name]["units"] += 1
        by_market[market_name]["revenue"] += unit_revenue
        by_market[market_name]["flat_revenue"] += details["flat_revenue"]
        by_market[market_name]["seasonal_delta"] += details["seasonal_delta"]

    # Overall summary
    any_seasonal = any(u.get("seasonality_enabled", False) for u in units_breakdown)

    result_details = {
        "total_revenue": round(total_revenue, 2),
        "flat_revenue": round(total_flat_revenue, 2),
        "seasonal_delta": round(total_revenue - total_flat_revenue, 2),
        "units_breakdown": units_breakdown,
        "by_market": by_market,
        "seasonality_enabled": any_seasonal
    }

    return round(total_revenue, 2), result_details


def calculate_annual_revenue_seasonal(
    config: Dict[str, Any],
    market_name: str,
    year: int,
    calendar_days: List[int]
) -> Tuple[float, float]:
    """
    Calculate annual revenue for a market using seasonal averages.

    Used for parity price calculations.

    Args:
        config: Engine configuration dictionary
        market_name: Name of the market profile
        year: Simulation year (1-indexed)
        calendar_days: List of days per month [31, 28, 31, ...]

    Returns:
        Tuple of (annual_revenue, effective_annual_occupancy)
    """
    from .seasonality import (
        get_seasonal_factors,
        calculate_seasonal_revenue,
        get_market_baseline
    )

    if len(calendar_days) != 12:
        calendar_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Get baseline for market
    base_adr, base_occupancy = get_market_baseline(config, market_name)

    # Get inflation rate
    market_cfg = config.get("market", {})
    revenue_infl_rate = float(market_cfg.get("revenueInflationRate", 0.04))

    # Apply inflation
    adr_inflated = get_adr_for_year(base_adr, revenue_infl_rate, year)

    total_revenue = 0.0
    total_occupied_days = 0.0
    total_days = sum(calendar_days)

    for month_index in range(12):
        simulation_month = month_index + 1  # 1-12
        days = calendar_days[month_index]

        factors = get_seasonal_factors(config, market_name, simulation_month)
        revenue, details = calculate_seasonal_revenue(
            adr_inflated, base_occupancy, days, factors
        )
        total_revenue += revenue

        # Track effective occupancy
        occupancy_effective = details["occupancy_effective"]
        total_occupied_days += occupancy_effective * days

    effective_annual_occupancy = total_occupied_days / total_days if total_days > 0 else 0.0

    return round(total_revenue, 2), round(effective_annual_occupancy, 4)
