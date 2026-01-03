"""
Tax Modeling Module - Phase 1.4

Provides depreciation calculations for STR investment tax planning.
Uses 27.5-year straight-line depreciation on building portion (typically 85% of purchase price).

Per Amendment 1: Simplified implementation - no CPA handoff package, just CSV export capability.
Focus on depreciation tracking for expense accuracy.

Key calculations:
- Depreciation basis = purchase_price * (1 - land_percentage)
- Annual depreciation = depreciation_basis / 27.5
- Accumulated depreciation tracks total depreciation taken
- Estimated tax liability = (rental_income - expenses - depreciation) * marginal_rate

Note: This is for planning purposes only. Consult a tax professional for actual tax filing.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple


# Default tax configuration
DEFAULT_TAX_CONFIG = {
    "enabled": False,
    "marginal_rate": 0.32,
    "land_percentage": 0.15,
    "depreciation_years": 27.5,
}


@dataclass
class DepreciationInfo:
    """Depreciation details for a single unit."""
    depreciation_basis: float
    annual_depreciation: float
    monthly_depreciation: float
    accumulated_depreciation: float
    remaining_basis: float
    years_remaining: float


@dataclass
class TaxEstimate:
    """Estimated tax liability for a period."""
    gross_income: float
    total_expenses: float
    depreciation: float
    taxable_income: float
    estimated_tax: float
    effective_rate: float


def get_tax_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract tax configuration from engine config.
    Falls back to defaults if not present (v2.3 backward compatibility).
    """
    tax_cfg = config.get("tax", {})

    return {
        "enabled": tax_cfg.get("enabled", DEFAULT_TAX_CONFIG["enabled"]),
        "marginal_rate": tax_cfg.get("marginal_rate", DEFAULT_TAX_CONFIG["marginal_rate"]),
        "land_percentage": tax_cfg.get("land_percentage", DEFAULT_TAX_CONFIG["land_percentage"]),
        "depreciation_years": tax_cfg.get("depreciation_years", DEFAULT_TAX_CONFIG["depreciation_years"]),
    }


def is_tax_enabled(config: Dict[str, Any]) -> bool:
    """Check if tax modeling is enabled in config."""
    tax_cfg = get_tax_config(config)
    return tax_cfg["enabled"]


def calculate_depreciation_basis(
    purchase_price: float,
    land_percentage: float = 0.15
) -> float:
    """
    Calculate the depreciable basis for a property.

    Args:
        purchase_price: Total purchase price of the property
        land_percentage: Portion of value attributable to land (not depreciable)

    Returns:
        Depreciable basis (building value only)
    """
    return purchase_price * (1 - land_percentage)


def calculate_annual_depreciation(
    depreciation_basis: float,
    depreciation_years: float = 27.5
) -> float:
    """
    Calculate annual depreciation using straight-line method.

    Residential rental property uses 27.5-year depreciation per IRS rules.

    Args:
        depreciation_basis: Depreciable value (building only)
        depreciation_years: Depreciation period (default 27.5 for residential)

    Returns:
        Annual depreciation amount
    """
    if depreciation_years <= 0:
        return 0.0
    return depreciation_basis / depreciation_years


def calculate_monthly_depreciation(
    depreciation_basis: float,
    depreciation_years: float = 27.5
) -> float:
    """
    Calculate monthly depreciation amount.

    Args:
        depreciation_basis: Depreciable value (building only)
        depreciation_years: Depreciation period (default 27.5 for residential)

    Returns:
        Monthly depreciation amount
    """
    annual = calculate_annual_depreciation(depreciation_basis, depreciation_years)
    return annual / 12


def get_depreciation_info(
    purchase_price: float,
    accumulated_depreciation: float,
    config: Dict[str, Any]
) -> DepreciationInfo:
    """
    Get complete depreciation information for a unit.

    Args:
        purchase_price: Original purchase price
        accumulated_depreciation: Total depreciation taken to date
        config: Engine configuration

    Returns:
        DepreciationInfo with all depreciation details
    """
    tax_cfg = get_tax_config(config)
    land_pct = tax_cfg["land_percentage"]
    dep_years = tax_cfg["depreciation_years"]

    basis = calculate_depreciation_basis(purchase_price, land_pct)
    annual = calculate_annual_depreciation(basis, dep_years)
    monthly = annual / 12

    remaining = max(0.0, basis - accumulated_depreciation)
    years_remaining = remaining / annual if annual > 0 else 0.0

    return DepreciationInfo(
        depreciation_basis=basis,
        annual_depreciation=annual,
        monthly_depreciation=monthly,
        accumulated_depreciation=accumulated_depreciation,
        remaining_basis=remaining,
        years_remaining=years_remaining
    )


def estimate_tax_liability(
    gross_income: float,
    total_expenses: float,
    depreciation: float,
    marginal_rate: float
) -> TaxEstimate:
    """
    Estimate tax liability for a period.

    Args:
        gross_income: Total rental income
        total_expenses: Total deductible expenses (not including depreciation)
        depreciation: Depreciation deduction for the period
        marginal_rate: Investor's marginal tax rate

    Returns:
        TaxEstimate with all tax details
    """
    taxable_income = gross_income - total_expenses - depreciation

    # Tax is only owed on positive taxable income
    # Losses can offset other income but we don't model that here
    if taxable_income > 0:
        estimated_tax = taxable_income * marginal_rate
    else:
        estimated_tax = 0.0

    effective_rate = estimated_tax / gross_income if gross_income > 0 else 0.0

    return TaxEstimate(
        gross_income=gross_income,
        total_expenses=total_expenses,
        depreciation=depreciation,
        taxable_income=taxable_income,
        estimated_tax=estimated_tax,
        effective_rate=effective_rate
    )


def calculate_unit_depreciation(
    unit_purchase_price: float,
    unit_accumulated_depreciation: float,
    months_owned: int,
    config: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Calculate depreciation for a unit for the current month.

    Args:
        unit_purchase_price: Original purchase price of the unit
        unit_accumulated_depreciation: Depreciation already taken
        months_owned: Number of months the unit has been owned
        config: Engine configuration

    Returns:
        Tuple of (monthly_depreciation, new_accumulated_depreciation)
    """
    tax_cfg = get_tax_config(config)
    land_pct = tax_cfg["land_percentage"]
    dep_years = tax_cfg["depreciation_years"]

    basis = calculate_depreciation_basis(unit_purchase_price, land_pct)
    monthly = calculate_monthly_depreciation(basis, dep_years)

    # Check if there's any remaining basis to depreciate
    remaining = basis - unit_accumulated_depreciation

    if remaining <= 0:
        # Fully depreciated
        return 0.0, unit_accumulated_depreciation

    # Don't take more depreciation than remaining
    actual_depreciation = min(monthly, remaining)
    new_accumulated = unit_accumulated_depreciation + actual_depreciation

    return actual_depreciation, new_accumulated


def calculate_portfolio_depreciation(
    units_data: list,
    config: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate total depreciation for the portfolio.

    Args:
        units_data: List of unit data dicts with purchase_price, accumulated_depreciation, months_owned
        config: Engine configuration

    Returns:
        Dict with total depreciation info
    """
    total_monthly = 0.0
    total_annual = 0.0
    total_accumulated = 0.0
    total_remaining_basis = 0.0

    tax_cfg = get_tax_config(config)
    land_pct = tax_cfg["land_percentage"]
    dep_years = tax_cfg["depreciation_years"]

    for unit in units_data:
        price = unit.get("purchase_price", 0)
        accum = unit.get("accumulated_depreciation", 0)

        basis = calculate_depreciation_basis(price, land_pct)
        monthly = calculate_monthly_depreciation(basis, dep_years)
        annual = monthly * 12
        remaining = max(0, basis - accum)

        # Only count depreciation if basis remains
        if remaining > 0:
            total_monthly += min(monthly, remaining)
            total_annual += min(annual, remaining)

        total_accumulated += accum
        total_remaining_basis += remaining

    return {
        "monthly_depreciation": total_monthly,
        "annual_depreciation": total_annual,
        "accumulated_depreciation": total_accumulated,
        "remaining_basis": total_remaining_basis,
    }


def validate_tax_config(config: Dict[str, Any]) -> list:
    """
    Validate tax configuration.

    Args:
        config: Engine configuration

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    tax_cfg = config.get("tax", {})

    if not tax_cfg.get("enabled", False):
        # Tax not enabled, skip validation
        return issues

    # Validate marginal rate
    rate = tax_cfg.get("marginal_rate", 0)
    if rate < 0 or rate > 1:
        issues.append(f"Marginal rate {rate} should be between 0 and 1")

    # Validate land percentage
    land_pct = tax_cfg.get("land_percentage", 0)
    if land_pct < 0 or land_pct > 0.5:
        issues.append(f"Land percentage {land_pct} should be between 0 and 0.5")

    # Validate depreciation years
    dep_years = tax_cfg.get("depreciation_years", 27.5)
    if dep_years <= 0:
        issues.append(f"Depreciation years must be positive, got {dep_years}")
    elif dep_years != 27.5 and dep_years != 39:
        issues.append(f"Non-standard depreciation period {dep_years}. "
                     "Residential is 27.5, commercial is 39.")

    return issues


# Convenience functions for integration with simulator

def init_unit_depreciation(purchase_price: float, config: Dict[str, Any]) -> Dict[str, float]:
    """
    Initialize depreciation tracking for a new unit.

    Args:
        purchase_price: Purchase price of the unit
        config: Engine configuration

    Returns:
        Dict with initial depreciation values
    """
    tax_cfg = get_tax_config(config)
    basis = calculate_depreciation_basis(purchase_price, tax_cfg["land_percentage"])

    return {
        "depreciation_basis": basis,
        "accumulated_depreciation": 0.0,
    }


def process_monthly_depreciation(
    depreciation_basis: float,
    accumulated_depreciation: float,
    config: Dict[str, Any]
) -> Tuple[float, float]:
    """
    Process depreciation for one month.

    Args:
        depreciation_basis: The unit's depreciable basis
        accumulated_depreciation: Depreciation already taken
        config: Engine configuration

    Returns:
        Tuple of (this_month_depreciation, new_accumulated)
    """
    tax_cfg = get_tax_config(config)
    dep_years = tax_cfg["depreciation_years"]

    monthly = calculate_monthly_depreciation(depreciation_basis, dep_years)
    remaining = depreciation_basis - accumulated_depreciation

    if remaining <= 0:
        return 0.0, accumulated_depreciation

    actual = min(monthly, remaining)
    return actual, accumulated_depreciation + actual
