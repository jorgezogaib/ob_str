# ui/lender_metrics.py
# Pure, side-effect-free lender metrics.

from typing import Optional

def dscr(noi: float, debt_service: float) -> Optional[float]:
    """Debt Service Coverage Ratio = NOI / DS. None if DS<=0."""
    if debt_service <= 0:
        return None
    return noi / debt_service

def icr(noi: float, interest_only: float) -> Optional[float]:
    """Interest Coverage Ratio = NOI / Interest. None if interest<=0."""
    if interest_only <= 0:
        return None
    return noi / interest_only

def cap_rate(noi_annual: float, price: float) -> Optional[float]:
    """Cap rate = annual NOI / price. None if price<=0."""
    if price <= 0:
        return None
    return noi_annual / price

def breakeven_occupancy(
    adr: float, month_days: float, mgmt_pct: float, capex_pct: float,
    fixed_monthly_costs: float, monthly_debt_service: float
) -> Optional[float]:
    """
    Solve occ for: ADR*days*occ*(1 - mgmt - capex) - fixed - DS = 0
    occ = (fixed + DS) / (ADR*days*(1 - mgmt - capex))
    Returns clamped [0,1], or None if denominator<=0.
    """
    denom = adr * month_days * max(1.0 - (mgmt_pct + capex_pct), 0.0)
    if denom <= 0:
        return None
    occ = (fixed_monthly_costs + monthly_debt_service) / denom
    return max(0.0, min(1.0, occ))
