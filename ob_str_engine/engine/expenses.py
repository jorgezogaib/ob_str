def calculate_expenses(gross: float, units: int, value: float, hoa_annual: float,
                       mgmt: float, capex: float, ins: float, tax: float) -> dict:
    return {
        "mgmt": round(gross * mgmt, 2),
        "capex_ops": round(gross * capex, 2),
        "hoa_monthly": round(hoa_annual / 12 * units, 2),
        "insurance": round(value * ins / 12, 2),
        "tax": round(value * tax / 12, 2),
    }