import numpy as np
from .debt import pmt


def attempt_refi_cashout(month: int, units: list, engine: dict, amort_years: int) -> float:
    if not units:
        return 0.0
    banking = engine["banking"]
    acq = engine["constants"]["acquisition"]
    ltv_trigger = float(banking["refiLTVTrigger"])
    max_ltv = float(acq["maxPostRefiLTV"])
    cooldown = int(acq["refiCooldownYears"]) * 12
    cost = float(banking["cashoutCostPct"])
    refi_rate = float(engine["constants"]["debt"]["refiRate"])

    ltvs = [u.debt / u.value for u in units]
    i = int(np.argmin(ltvs))
    if ltvs[i] <= ltv_trigger and month - units[i].last_refi_month >= cooldown:
        new_debt = units[i].value * max_ltv
        gross = max(0.0, new_debt - units[i].debt)
        net = gross * (1 - cost)
        units[i].debt = new_debt
        units[i].monthly_payment = pmt(refi_rate, amort_years, new_debt)
        units[i].rate = refi_rate
        units[i].last_refi_month = month
        return round(net, 2)
    return 0.0


def prepay_surplus(cash: float, liquidity_req: float, rainy_reserve: float, units: list) -> tuple[float, float]:
    surplus = cash - max(0.0, liquidity_req - rainy_reserve)
    if surplus <= 0 or not units:
        return 0.0, cash
    ltvs = [u.debt / u.value for u in units]
    i = int(np.argmin(ltvs))
    prepay = min(surplus, units[i].debt)
    units[i].debt = round(units[i].debt - prepay, 2)
    return round(prepay, 2), round(cash - prepay, 2)