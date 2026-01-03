"""
Seasonality Engine & Market Profiles

This module provides market-specific seasonal revenue patterns, replacing flat
occupancy/ADR assumptions with realistic monthly curves.

Phase 1 Implementation:
- Market profiles with seasonal multipliers (12 ADR, 12 occupancy)
- Orange Beach defaults based on Gulf Coast patterns
- Generic fallback profile (flat seasonality)
- Backward compatible: works without market_profiles config section
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Default Orange Beach seasonal multipliers
# Based on Gulf Coast STR patterns:
# - Peak (Jun-Aug): 90% occupancy, +35% ADR
# - Shoulder (Mar-May, Sep-Oct): 70% occupancy, +10% ADR
# - Off-season (Nov-Feb): 45% occupancy, -15% ADR

ORANGE_BEACH_ADR_MULTIPLIERS = [
    0.85, 0.85,  # Jan, Feb (off-season)
    1.10, 1.10, 1.10,  # Mar, Apr, May (shoulder)
    1.35, 1.35, 1.35,  # Jun, Jul, Aug (peak)
    1.10, 1.10,  # Sep, Oct (shoulder)
    0.85, 0.85,  # Nov, Dec (off-season)
]

ORANGE_BEACH_OCCUPANCY_MULTIPLIERS = [
    0.58, 0.58,  # Jan, Feb (45% / 78% baseline)
    0.90, 0.90, 0.90,  # Mar, Apr, May (70% / 78%)
    1.15, 1.15, 1.15,  # Jun, Jul, Aug (90% / 78%)
    0.90, 0.90,  # Sep, Oct (70% / 78%)
    0.58, 0.58,  # Nov, Dec (45% / 78%)
]

# Flat multipliers for generic/disabled seasonality
FLAT_MULTIPLIERS = [1.0] * 12


@dataclass
class SeasonalFactors:
    """Container for seasonal adjustment factors for a given month."""
    adr_multiplier: float
    occupancy_multiplier: float
    calendar_month: int  # 1-12
    market_name: str
    seasonality_enabled: bool


def get_default_market_profiles() -> Dict[str, Any]:
    """
    Return default market profiles configuration.

    Used when no market_profiles section exists in config.
    Provides Orange Beach and generic profiles.
    """
    return {
        "orange_beach": {
            "display_name": "Orange Beach, AL",
            "description": "Gulf Coast 2BR condo STR market",
            "seasonality_enabled": True,
            "baseline": {
                "adr": 425.0,
                "occupancy": 0.78,
                "notes": "Annual averages - actual monthly varies per curves below"
            },
            "seasonality": {
                "adr_multipliers": ORANGE_BEACH_ADR_MULTIPLIERS.copy(),
                "occupancy_multipliers": ORANGE_BEACH_OCCUPANCY_MULTIPLIERS.copy(),
                "notes": "Index 0 = January, 11 = December"
            },
            "expenses": {
                "insurance_rate": 0.04,
                "property_tax_rate": 0.0055,
                "hoa_annual": 12800.0,
                "insurance_inflation_rate": 0.07,
                "notes": "Coastal insurance higher than generic"
            },
            "market": {
                "appreciation_rate": 0.03,
                "revenue_inflation_rate": 0.04
            }
        },
        "generic": {
            "display_name": "Generic Market (Flat)",
            "description": "Default market with no seasonal variation",
            "seasonality_enabled": False,
            "baseline": {
                "adr": 200.0,
                "occupancy": 0.70
            },
            "seasonality": {
                "adr_multipliers": FLAT_MULTIPLIERS.copy(),
                "occupancy_multipliers": FLAT_MULTIPLIERS.copy()
            },
            "expenses": {
                "insurance_rate": 0.033,
                "property_tax_rate": 0.0055,
                "hoa_annual": 8000.0,
                "insurance_inflation_rate": 0.03
            },
            "market": {
                "appreciation_rate": 0.03,
                "revenue_inflation_rate": 0.04
            }
        }
    }


def get_market_profile(config: Dict[str, Any], market_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a market profile by name from config.

    Falls back to default profiles if not in config.

    Args:
        config: Engine configuration dictionary
        market_name: Name of the market profile to retrieve

    Returns:
        Market profile dict, or None if not found
    """
    # Check config first
    market_profiles = config.get("market_profiles", {})
    if market_name in market_profiles:
        return market_profiles[market_name]

    # Fall back to defaults
    defaults = get_default_market_profiles()
    return defaults.get(market_name)


def get_default_market_name(config: Dict[str, Any]) -> str:
    """
    Get the default market name for new acquisitions.

    Args:
        config: Engine configuration dictionary

    Returns:
        Default market name (defaults to "orange_beach")
    """
    policies = config.get("policies", {})
    portfolio = policies.get("portfolio", {})
    return portfolio.get("default_market", "orange_beach")


def get_seasonal_factors(
    config: Dict[str, Any],
    market_name: str,
    simulation_month: int
) -> SeasonalFactors:
    """
    Get seasonal adjustment factors for a specific month.

    Args:
        config: Engine configuration dictionary
        market_name: Name of the market profile
        simulation_month: Global simulation month (1-360)

    Returns:
        SeasonalFactors with ADR and occupancy multipliers
    """
    # Convert simulation month to calendar month (1-12)
    calendar_month = ((simulation_month - 1) % 12) + 1
    month_index = calendar_month - 1  # 0-indexed for array access

    market = get_market_profile(config, market_name)

    if market is None:
        # Unknown market - use flat multipliers
        return SeasonalFactors(
            adr_multiplier=1.0,
            occupancy_multiplier=1.0,
            calendar_month=calendar_month,
            market_name=market_name,
            seasonality_enabled=False
        )

    seasonality_enabled = market.get("seasonality_enabled", False)

    if not seasonality_enabled:
        return SeasonalFactors(
            adr_multiplier=1.0,
            occupancy_multiplier=1.0,
            calendar_month=calendar_month,
            market_name=market_name,
            seasonality_enabled=False
        )

    seasonality = market.get("seasonality", {})
    adr_multipliers = seasonality.get("adr_multipliers", FLAT_MULTIPLIERS)
    occ_multipliers = seasonality.get("occupancy_multipliers", FLAT_MULTIPLIERS)

    # Validate multiplier arrays
    if len(adr_multipliers) != 12:
        adr_multipliers = FLAT_MULTIPLIERS
    if len(occ_multipliers) != 12:
        occ_multipliers = FLAT_MULTIPLIERS

    return SeasonalFactors(
        adr_multiplier=adr_multipliers[month_index],
        occupancy_multiplier=occ_multipliers[month_index],
        calendar_month=calendar_month,
        market_name=market_name,
        seasonality_enabled=True
    )


def calculate_seasonal_revenue(
    base_adr: float,
    base_occupancy: float,
    days_in_month: int,
    seasonal_factors: SeasonalFactors
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate revenue for a single unit with seasonal adjustments.

    Args:
        base_adr: Base ADR (after inflation adjustment)
        base_occupancy: Base occupancy rate (0-1)
        days_in_month: Number of days in the month
        seasonal_factors: SeasonalFactors for this month

    Returns:
        Tuple of (gross_revenue, details_dict)
    """
    adr_effective = base_adr * seasonal_factors.adr_multiplier
    occupancy_effective = base_occupancy * seasonal_factors.occupancy_multiplier

    # Cap occupancy at 100%
    occupancy_effective = min(occupancy_effective, 1.0)

    gross_revenue = adr_effective * occupancy_effective * days_in_month

    # Calculate what flat revenue would have been (for comparison)
    flat_revenue = base_adr * base_occupancy * days_in_month
    seasonal_delta = gross_revenue - flat_revenue

    details = {
        "adr_base": base_adr,
        "adr_multiplier": seasonal_factors.adr_multiplier,
        "adr_effective": round(adr_effective, 2),
        "occupancy_base": base_occupancy,
        "occupancy_multiplier": seasonal_factors.occupancy_multiplier,
        "occupancy_effective": round(occupancy_effective, 4),
        "days_in_month": days_in_month,
        "gross_revenue": round(gross_revenue, 2),
        "flat_revenue": round(flat_revenue, 2),
        "seasonal_delta": round(seasonal_delta, 2),
        "calendar_month": seasonal_factors.calendar_month,
        "market_name": seasonal_factors.market_name,
        "seasonality_enabled": seasonal_factors.seasonality_enabled
    }

    return round(gross_revenue, 2), details


def calculate_annual_seasonal_average(
    config: Dict[str, Any],
    market_name: str,
    base_adr: float,
    base_occupancy: float,
    calendar_days: List[int]
) -> Tuple[float, float]:
    """
    Calculate annual revenue using seasonal averages.

    Used for parity price calculations to get accurate annual projections.

    Args:
        config: Engine configuration dictionary
        market_name: Name of the market profile
        base_adr: Base ADR (for year 1, before inflation)
        base_occupancy: Base occupancy rate
        calendar_days: List of days per month [31, 28, 31, ...]

    Returns:
        Tuple of (annual_revenue, effective_annual_occupancy)
    """
    if len(calendar_days) != 12:
        calendar_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    total_revenue = 0.0
    total_occupied_days = 0.0
    total_days = sum(calendar_days)

    for month_index in range(12):
        simulation_month = month_index + 1  # 1-12
        factors = get_seasonal_factors(config, market_name, simulation_month)

        days = calendar_days[month_index]
        revenue, _ = calculate_seasonal_revenue(
            base_adr, base_occupancy, days, factors
        )
        total_revenue += revenue

        # Track effective occupancy for reporting
        occupancy_effective = base_occupancy * factors.occupancy_multiplier
        total_occupied_days += occupancy_effective * days

    effective_annual_occupancy = total_occupied_days / total_days if total_days > 0 else 0.0

    return round(total_revenue, 2), round(effective_annual_occupancy, 4)


def validate_market_profile(market: Dict[str, Any], market_name: str) -> List[str]:
    """
    Validate a market profile configuration.

    Args:
        market: Market profile dictionary
        market_name: Name of the market (for error messages)

    Returns:
        List of validation error/warning messages (empty if valid)
    """
    issues = []

    if not market:
        issues.append(f"{market_name}: Market profile is empty")
        return issues

    # Check baseline
    baseline = market.get("baseline", {})
    if not baseline:
        issues.append(f"{market_name}: Missing baseline section")
    else:
        adr = baseline.get("adr")
        if adr is None or adr <= 0:
            issues.append(f"{market_name}: Invalid or missing baseline ADR")

        occ = baseline.get("occupancy")
        if occ is None or occ <= 0 or occ > 1:
            issues.append(f"{market_name}: Invalid or missing baseline occupancy (must be 0-1)")

    # Check seasonality if enabled
    if market.get("seasonality_enabled", False):
        seasonality = market.get("seasonality", {})

        adr_mults = seasonality.get("adr_multipliers", [])
        if len(adr_mults) != 12:
            issues.append(f"{market_name}: adr_multipliers must have 12 values, got {len(adr_mults)}")
        else:
            for i, mult in enumerate(adr_mults):
                if mult < 0.1 or mult > 5.0:
                    issues.append(f"{market_name}: adr_multipliers[{i}] = {mult} out of range (0.1-5.0)")

        occ_mults = seasonality.get("occupancy_multipliers", [])
        if len(occ_mults) != 12:
            issues.append(f"{market_name}: occupancy_multipliers must have 12 values, got {len(occ_mults)}")
        else:
            for i, mult in enumerate(occ_mults):
                if mult < 0.1 or mult > 2.0:
                    issues.append(f"{market_name}: occupancy_multipliers[{i}] = {mult} out of range (0.1-2.0)")

    return issues


def validate_all_market_profiles(config: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate all market profiles in configuration.

    Args:
        config: Engine configuration dictionary

    Returns:
        Dict mapping market_name to list of issues (empty lists = valid)
    """
    results = {}

    market_profiles = config.get("market_profiles", {})

    # If no market profiles, that's OK - will use defaults
    if not market_profiles:
        return results

    for market_name, market in market_profiles.items():
        issues = validate_market_profile(market, market_name)
        if issues:
            results[market_name] = issues

    return results


def is_seasonality_enabled(config: Dict[str, Any]) -> bool:
    """
    Check if any market profile has seasonality enabled.

    Args:
        config: Engine configuration dictionary

    Returns:
        True if at least one market has seasonality enabled
    """
    market_profiles = config.get("market_profiles", {})

    for market in market_profiles.values():
        if market.get("seasonality_enabled", False):
            return True

    # Check defaults
    defaults = get_default_market_profiles()
    default_market = get_default_market_name(config)

    if default_market in defaults:
        return defaults[default_market].get("seasonality_enabled", False)

    return False


def get_market_baseline(config: Dict[str, Any], market_name: str) -> Tuple[float, float]:
    """
    Get baseline ADR and occupancy for a market.

    Falls back to v2.3 config values if market not found.

    Args:
        config: Engine configuration dictionary
        market_name: Name of the market profile

    Returns:
        Tuple of (base_adr, base_occupancy)
    """
    market = get_market_profile(config, market_name)

    if market:
        baseline = market.get("baseline", {})
        adr = baseline.get("adr")
        occ = baseline.get("occupancy")

        if adr is not None and occ is not None:
            return float(adr), float(occ)

    # Fall back to v2.3 config
    ops = config.get("constants", {}).get("operations", {})
    return (
        float(ops.get("adrBaseline2BR", 425.0)),
        float(ops.get("occupancyBaseline", 0.78))
    )


def get_market_expenses(config: Dict[str, Any], market_name: str) -> Dict[str, float]:
    """
    Get expense rates for a market.

    Falls back to v2.3 config values if market not found.

    Args:
        config: Engine configuration dictionary
        market_name: Name of the market profile

    Returns:
        Dict with insurance_rate, property_tax_rate, hoa_annual, etc.
    """
    market = get_market_profile(config, market_name)

    # Start with v2.3 defaults
    ops = config.get("constants", {}).get("operations", {})
    defaults = {
        "insurance_rate": float(ops.get("insuranceRate", 0.033)),
        "property_tax_rate": float(ops.get("propertyTaxRate", 0.0055)),
        "hoa_annual": float(ops.get("hoaAnnual", 12800.0)),
        "insurance_inflation_rate": 0.03
    }

    if market:
        expenses = market.get("expenses", {})
        # Override with market-specific values
        for key in defaults:
            if key in expenses:
                defaults[key] = float(expenses[key])

    return defaults
