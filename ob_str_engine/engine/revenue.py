def calculate_gross_revenue(units: int, adr: float, occ: float, days: int) -> float:
    return round(adr * occ * days * units, 2)

def get_adr_for_year(base_adr: float, infl: float, year: int) -> float:
    return base_adr * (1 + infl) ** (year - 1)