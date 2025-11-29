def liquidity_check(
    cash: float,
    rainy_reserve: float,
    price_parity: float,
    engine: dict,
    units_owned: int,
    max_units: int,
) -> tuple[bool, float, float]:
    if units_owned >= max_units:
        return False, 0.0, 0.0

    acq = engine["constants"]["acquisition"]
    banking = engine["banking"]
    dp_pct = float(acq["downPaymentSubsequent"])
    closing_pct = float(acq["closingCostPct"])
    rainy_months = float(banking["rainyCoverageMonths"])

    next_purchase = price_parity * (dp_pct + closing_pct)
    rainy_needed = rainy_months * (price_parity * (units_owned + 1) * 0.05 / 12)  # original proxy
    required = next_purchase + rainy_needed
    available = cash + rainy_reserve

    freeze = available < required
    return freeze, round(required, 2), round(available, 2)