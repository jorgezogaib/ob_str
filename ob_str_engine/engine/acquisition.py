from .revenue import get_adr_for_year

def calculate_parity_price(year: int, engine: dict) -> float:
    """
    Calculates the correct parity purchase price for the given year.
    Critical fix: HOA must be inflated here (same as running portfolio).
    """
    ops = engine["constants"]["operations"]
    acq = engine["constants"]["acquisition"]

    base_adr = float(ops["adrBaseline2BR"])
    occ = float(ops["occupancyBaseline"])
    mgmt_pct = float(ops["mgmtPct"])
    capex_pct = float(ops["capexPct"])
    hoa_annual_base = float(ops["hoaAnnual"])
    hoa_inflation_rate = float(ops["hoaInflationRate"])
    ins_rate = float(ops["insuranceRate"])
    tax_rate = float(ops["propertyTaxRate"])
    target_yield = float(acq["targetYieldUnlevered"])
    revenue_infl_rate = float(engine["market"].get("revenueInflationRate", 0.04))

    # Revenue grows with inflation
    adr_this_year = get_adr_for_year(base_adr, revenue_infl_rate, year)

    # HOA must also be inflated — this was the bug
    hoa_this_year = hoa_annual_base * (1 + hoa_inflation_rate) ** (year - 1)

    gross_one_unit = adr_this_year * occ * 365
    noi_one_unit = gross_one_unit * (1 - mgmt_pct - capex_pct) - hoa_this_year

    price_parity = noi_one_unit / (target_yield + ins_rate + tax_rate)
    return round(max(0.0, price_parity), 2)


def can_purchase(
    units_owned: int,
    cash: float,
    price_parity: float,
    is_first: bool,
    engine: dict,
) -> tuple[bool, float, float, float]:
    acq = engine["constants"]["acquisition"]
    dp_pct = float(acq["downPaymentFirst"] if is_first else acq["downPaymentSubsequent"])
    closing_pct = float(acq["closingCostPct"])
    needed = price_parity * (dp_pct + closing_pct)

    if cash >= needed:
        dp_amount = price_parity * dp_pct
        closing_amount = price_parity * closing_pct
        return True, dp_amount, closing_amount, needed

    return False, 0.0, 0.0, 0.0