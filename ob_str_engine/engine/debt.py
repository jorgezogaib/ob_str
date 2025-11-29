def pmt(annual_rate: float, years: int, principal: float) -> float:
    """Exact PMT formula from original script."""
    if principal <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = years * 12
    if r == 0:
        return principal / n
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def amortize_one_month(debt: float, monthly_payment: float, annual_rate: float) -> float:
    """
    Amortizes one month and returns the new debt balance.
    Exactly matches original script behavior.
    """
    if debt <= 0:
        return 0.0
    monthly_rate = annual_rate / 12.0
    interest = debt * monthly_rate
    principal = min(monthly_payment - interest, debt)
    new_debt = debt - principal
    return round(new_debt, 2)