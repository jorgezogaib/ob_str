def update_rainy_day_reserve(
    fixed_monthly_costs: float,
    current_reserve: float,
    cashflow_available: float,
    cash: float,
    rainy_months_target: float,
) -> tuple[float, float]:
    """
    Exact logic from original script.
    Returns (topup_amount, new_reserve_balance) both rounded to cents.
    """
    target = rainy_months_target * fixed_monthly_costs
    shortfall = max(0.0, target - current_reserve)
    topup = min(shortfall, cashflow_available + cash)
    new_reserve = current_reserve + topup
    return round(topup, 2), round(new_reserve, 2)