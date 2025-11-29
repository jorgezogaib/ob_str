import pandas as pd
import numpy as np
from pathlib import Path
from typing import List
from .config import load_engine_config
from .types import Unit, SimulationResult
from .revenue import calculate_gross_revenue, get_adr_for_year
from .expenses import calculate_expenses
from .acquisition import calculate_parity_price, can_purchase
from .debt import pmt, amortize_one_month
from .reserves import update_rainy_day_reserve
from .liquidity import liquidity_check
from .feeder import attempt_refi_cashout, prepay_surplus


def cents(x: float) -> float:
    """Round to cents — exactly like original script."""
    return round(float(x), 2)


def simulate(engine_path: Path, years: int = 30) -> SimulationResult:
    engine = load_engine_config(engine_path)
    const = engine["constants"]
    fin = const["financial"]
    ops = const["operations"]
    acq = const["acquisition"]
    debt_cfg = const["debt"]
    calendar = engine["calendar"]["monthlyDays"]

    # === Constants ===
    starting_cash = float(fin["startingCash"])
    annual_savings = float(fin["annualSavings"])
    amort_years = int(fin["amortizationYears"])

    base_adr = float(ops["adrBaseline2BR"])
    occ = float(ops["occupancyBaseline"])
    mgmt_pct = float(ops["mgmtPct"])
    capex_pct = float(ops["capexPct"])
    hoa_annual_base = float(ops["hoaAnnual"])
    hoa_infl_rate = float(ops["hoaInflationRate"])
    ins_rate = float(ops["insuranceRate"])
    tax_rate = float(ops["propertyTaxRate"])

    dp_first = float(acq["downPaymentFirst"])
    dp_sub = float(acq["downPaymentSubsequent"])
    closing_pct = float(acq["closingCostPct"])

    rate_purchase = float(debt_cfg["mortgageRate"])
    rate_refi = float(debt_cfg["refiRate"])

    appreciation = float(engine["market"]["annualAppreciation"])
    revenue_infl_rate = float(engine["market"].get("revenueInflationRate", 0.04))
    rainy_months = float(engine["banking"]["rainyCoverageMonths"])
    max_units = int(engine["policies"]["portfolio"]["maxUnits"])

    # === State ===
    cash = starting_cash
    rainy_reserve = capex_reserve = 0.0
    units_owned = 0
    units: List[Unit] = []
    pending_cashout = 0.0
    month_global = 0

    rows = []

    for year in range(1, years + 1):
        adr_this_year = get_adr_for_year(base_adr, revenue_infl_rate, year)
        hoa_annual_this_year = hoa_annual_base * (1 + hoa_infl_rate) ** (year - 1)
        price_parity = calculate_parity_price(year, engine)

        for m, days in enumerate(calendar, 1):
            month_global += 1

            # Monthly income
            cash += pending_cashout
            pending_cashout = 0.0
            cash += annual_savings / 12

            gross = calculate_gross_revenue(units_owned, adr_this_year, occ, days)
            total_value = sum(u.value for u in units)

            exp = calculate_expenses(
                gross, units_owned, total_value, hoa_annual_this_year,
                mgmt_pct, capex_pct, ins_rate, tax_rate
            )

            debt_service = sum(u.monthly_payment for u in units)
            noi = gross - exp["mgmt"] - exp["hoa_monthly"] - exp["insurance"] - exp["tax"]
            ops_cashflow = noi - exp["capex_ops"] - debt_service

            capex_reserve += exp["capex_ops"]

            fixed_monthly = exp["hoa_monthly"] + exp["insurance"] + exp["tax"] + debt_service
            rainy_topup, rainy_reserve = update_rainy_day_reserve(
                fixed_monthly, rainy_reserve, ops_cashflow, cash, rainy_months
            )

            cash += ops_cashflow - rainy_topup
            cash = max(0.0, cents(cash))

            freeze, liquidity_req, liquidity_act = liquidity_check(
                cash, rainy_reserve, price_parity, engine, units_owned, max_units
            )

            # Refi cash-out
            feeder_cashout = attempt_refi_cashout(month_global, units, engine, amort_years)
            pending_cashout += feeder_cashout

            # Purchase
            purchase_total = dp = closing = 0.0
            if units_owned < max_units and not freeze:
                can_buy, dp_amt, closing_amt, total = can_purchase(
                    units_owned, cash, price_parity, units_owned == 0, engine
                )
                if can_buy:
                    purchase_total = total
                    dp = dp_amt
                    closing = closing_amt
                    cash -= total
                    loan = price_parity - dp
                    units.append(Unit(
                        value=price_parity,
                        debt=loan,
                        monthly_payment=pmt(rate_purchase, amort_years, loan),
                        rate=rate_purchase,
                        last_refi_month=month_global
                    ))
                    units_owned += 1

            # Amortization + appreciation
            for u in units:
                u.debt = amortize_one_month(u.debt, u.monthly_payment, u.rate)
                u.value *= (1 + appreciation / 12)

            # Surplus prepay
            feeder_prepay = 0.0
            if units_owned >= max_units:
                feeder_prepay, cash = prepay_surplus(cash, liquidity_req, rainy_reserve, units)

            # === RECORD ROW — EXACT ORIGINAL FORMAT ===
            rows.append({
                "Year": year,
                "Month": m,
                "Units": units_owned,
                "PriceParity": cents(price_parity),
                "GrossIncome": gross,
                "Mgmt": exp["mgmt"],
                "CapexOps": exp["capex_ops"],
                "HOA_Monthly_Total": exp["hoa_monthly"],
                "Insurance": exp["insurance"],
                "Tax": exp["tax"],
                "DebtService_Total": cents(debt_service),
                "NOI": noi,
                "SavingsToCash": cents(annual_savings / 12),
                "RainyTarget": cents(rainy_months * fixed_monthly),
                "RainyBalance": cents(rainy_reserve),
                "RainyTopup": cents(rainy_topup),
                "CapexBalance": cents(capex_reserve),
                "LiquidityRequired": cents(liquidity_req),
                "LiquidityActual": cents(liquidity_act),
                "FreezeFlag": int(freeze),
                "Purchase": purchase_total,
                "Purchase_DP": dp,
                "Purchase_Closing": closing,
                "Purchase_Total": purchase_total,
                "FeederDraw_Net": feeder_cashout,
                "FeederPrepay": feeder_prepay,
                "EndCash": cents(cash),
                "TotalValue": cents(sum(u.value for u in units)),
                "TotalDebt": cents(sum(u.debt for u in units)),
            })

    monthly_df = pd.DataFrame(rows)
    return SimulationResult(monthly=monthly_df, yearly=pd.DataFrame())