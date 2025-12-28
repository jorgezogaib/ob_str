"""
Compatibility layer for legacy test imports.

This module provides backward-compatible function signatures that match
the old runner.run_suite_full_V23 API, allowing existing tests to work
without modification while using the new modular engine.
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from .engine.simulator import simulate as _simulate, cents as _cents
from .engine.acquisition import calculate_parity_price
from .engine.debt import pmt as _pmt


def simulate(engine: Dict[str, Any], mmax: int = 600) -> List[Dict[str, Any]]:
    """
    Legacy simulate() function that accepts a dict and mmax parameter.

    Wraps the new simulate(Path, years) function by:
    1. Writing the engine dict to a temp JSON file
    2. Calling the new simulate() function
    3. Converting SimulationResult to list of row dicts

    Args:
        engine: Engine configuration dictionary
        mmax: Maximum months to simulate (converted to years)

    Returns:
        List of monthly row dictionaries
    """
    # Convert months to years (round up)
    years = (mmax + 11) // 12

    # Write engine dict to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(engine, f)
        temp_path = Path(f.name)

    try:
        # Call new simulate function
        result = _simulate(temp_path, years=years)

        # Convert DataFrame to list of dicts (matching old format)
        rows = result.monthly.to_dict('records')

        # Limit to mmax months
        return rows[:mmax]
    finally:
        # Clean up temp file
        temp_path.unlink()


def parity_price(
    adr: float,
    occ: float,
    hoa_annual: float,
    mgmt_pct: float,
    capex_pct: float,
    ins_rate: float,
    tax_rate: float,
    target_yield: float
) -> float:
    """
    Legacy parity_price() function with individual parameters.

    Calculates parity price using the same formula as the old implementation.
    Note: This is for testing only. The actual engine uses calculate_parity_price()
    which handles inflation correctly.

    Args:
        adr: Average daily rate
        occ: Occupancy rate (0-1)
        hoa_annual: Annual HOA costs
        mgmt_pct: Management fee percentage (0-1)
        capex_pct: CapEx percentage (0-1)
        ins_rate: Insurance rate (0-1)
        tax_rate: Property tax rate (0-1)
        target_yield: Target unlevered yield (0-1)

    Returns:
        Parity purchase price
    """
    gross_one_unit = adr * occ * 365
    noi_one_unit = gross_one_unit * (1 - mgmt_pct - capex_pct) - hoa_annual
    price = noi_one_unit / (target_yield + ins_rate + tax_rate)
    return max(0.0, price)


def pmt(annual_rate: float, years: int, principal: float) -> float:
    """
    Legacy pmt() function - direct passthrough to debt.pmt().

    Calculate monthly payment for a loan.

    Args:
        annual_rate: Annual interest rate (e.g., 0.0685 for 6.85%)
        years: Loan term in years
        principal: Loan principal amount

    Returns:
        Monthly payment amount (positive value)
    """
    return _pmt(annual_rate, years, principal)


def cents(x: float) -> float:
    """
    Legacy cents() function - direct passthrough to simulator.cents().

    Round to cents (2 decimal places).

    Args:
        x: Value to round

    Returns:
        Value rounded to cents
    """
    return _cents(x)


def _build_yoy_rows(monthly_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Legacy _build_yoy_rows() function.

    Build year-over-year summary rows from monthly data.
    Note: Currently returns empty list as YoY aggregation is not implemented
    in the new engine's compat layer. Tests using this should be updated.

    Args:
        monthly_rows: List of monthly row dictionaries

    Returns:
        List of year-over-year summary dictionaries (currently empty)
    """
    # TODO: Implement YoY aggregation if needed by tests
    # For now, return empty to match current engine behavior
    return []


# Export all legacy functions
__all__ = [
    'simulate',
    'parity_price',
    'pmt',
    'cents',
    '_build_yoy_rows',
]
