import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def cents(x: float) -> float:
    return float(np.round(x, 2))


def load_engine(engine_path: Path) -> Dict[str, Any]:
    with engine_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def simulate(engine: Dict[str, Any], years: int = 30) -> Tuple[pd.DataFrame, pd.DataFrame]:
    const = engine["constants"]
    fin = const["financial"]
    ops = const["operations"]
    acq = const["acquisition"]
    debt_cfg = const["debt"]

    calendar = engine["calendar"]["monthlyDays"]

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
    target_yield = float(acq["targetYieldUnlevered"])
    max_post_ltv = float(acq["maxPostRefiLTV"])
    refi_cooldown_y = float(acq["refiCooldownYears"])

    rate_purchase = float(debt_cfg["mortgageRate"])
    rate_refi = float(debt_cfg["refiRate"])

    rainy_months = float(engine["banking"]["rainyCoverageMonths"])
    refi_ltv_trigger = float(engine["banking"]["refiLTVTrigger"])
    cashout_cost_pct = float(engine["banking"]["cashoutCostPct"])
    appreciation = float(engine["market"]["annualAppreciation"])
    max_units = int(engine["policies"]["portfolio"]["maxUnits"])
    revenue_infl_rate = float(engine.get("market", {}).get("revenueInflationRate", 0.04))

    def pmt(r_annual: float, n_years: int, principal: float) -> float:
        r = r_annual / 12.0
        n = n_years * 12
        if r == 0:
            return principal / n
        return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    # State
    cash = starting_cash
    rainy_reserve = capex_reserve = 0.0
    units_owned = 0

    unit_values = []
    unit_debts = []
    unit_pmt = []
    unit_rate = []
    unit_last_refi_month = []

    pending_cashout = 0.0

    rows = []
    yoy_rows = []
    yoy_accum = {k: 0.0 for k in ["GrossIncome", "Mgmt", "CapexOps", "HOA", "Insurance", "Tax", "DebtService", "NOI"]}

    month = 0

    for year in range(1, years + 1):
        adr_this_year = base_adr * (1 + revenue_infl_rate) ** (year - 1)
        hoa_annual_this_year = hoa_annual_base * (1 + hoa_infl_rate) ** (year - 1)

        # FINAL CORRECT parity price — TODAY's costs only
        gross_one = base_adr * occ * 365
        noi_one = (
            gross_one * (1 - mgmt_pct - capex_pct)
            - hoa_annual_base
            - 650000 * ins_rate
            - 650000 * tax_rate
        )
        price_parity = max(0, noi_one / target_yield) if target_yield > 0 else 650000

        for m in range(1, 13):
            month += 1
            days = calendar[m - 1]

            cash += pending_cashout
            pending_cashout = 0.0
            cash += annual_savings / 12

            gross = cents(adr_this_year * occ * days * units_owned) if units_owned else 0.0
            mgmt = cents(gross * mgmt_pct)
            capex_ops = cents(gross * capex_pct)
            hoa_m = cents(hoa_annual_this_year / 12 * units_owned)
            ins = cents(sum(unit_values or [0]) * ins_rate / 12)
            tax = cents(sum(unit_values or [0]) * tax_rate / 12)
            debt_service = cents(sum(unit_pmt or [0]))

            noi = gross - mgmt - hoa_m - ins - tax
            ops_cashflow = noi - capex_ops - debt_service

            capex_reserve += capex_ops
            fixed_monthly = hoa_m + ins + tax + debt_service
            rainy_target = rainy_months * fixed_monthly
            rainy_topup = min(max(0, rainy_target - rainy_reserve), max(0, ops_cashflow + cash))
            cash += ops_cashflow - rainy_topup
            rainy_reserve += rainy_topup
            cash = max(0, cents(cash))

            liquidity_req = rainy_target + price_parity * (dp_sub + closing_pct)
            liquidity_act = cash + rainy_reserve
            freeze = liquidity_act < liquidity_req

            feeder_cashout = 0.0
            if units_owned > 0 and not freeze and unit_debts:
                ltvs = [d / v for d, v in zip(unit_debts, unit_values)]
                i = int(np.argmin(ltvs))
                if (unit_debts[i] / unit_values[i] <= refi_ltv_trigger and
                    month - unit_last_refi_month[i] >= refi_cooldown_y * 12):
                    new_debt = unit_values[i] * max_post_ltv
                    gross_out = max(0, new_debt - unit_debts[i])
                    net = gross_out * (1 - cashout_cost_pct)
                    feeder_cashout = cents(net)
                    pending_cashout += feeder_cashout
                    unit_debts[i] = new_debt
                    unit_pmt[i] = pmt(rate_refi, amort_years, new_debt)
                    unit_rate[i] = rate_refi
                    unit_last_refi_month[i] = month

            purchase = dp = closing = total = 0.0
            if units_owned < max_units and not freeze:
                dp_pct = dp_first if units_owned == 0 else dp_sub
                needed = price_parity * (dp_pct + closing_pct)
                if cash >= needed:
                    total = needed
                    dp = price_parity * dp_pct
                    closing = price_parity * closing_pct
                    cash -= total
                    loan = price_parity - dp
                    units_owned += 1
                    unit_values.append(price_parity)
                    unit_debts.append(loan)
                    unit_pmt.append(pmt(rate_purchase, amort_years, loan))
                    unit_rate.append(rate_purchase)
                    unit_last_refi_month.append(month)

            # Amortization + appreciation
            for i in range(len(unit_debts)):
                r_m = unit_rate[i] / 12
                interest = unit_debts[i] * r_m
                principal = unit_pmt[i] - interest
                unit_debts[i] = max(0, unit_debts[i] - principal)
                unit_values[i] *= (1 + appreciation / 12)

            # Post-cap feeder prepay
            feeder_prepay = 0.0
            if units_owned >= max_units and cash > (liquidity_req - rainy_reserve):
                surplus = cash - (liquidity_req - rainy_reserve)
                if surplus > 0 and unit_debts:
                    ltvs = [d / v for d, v in zip(unit_debts, unit_values)]
                    i = int(np.argmin(ltvs))
                    prepay = min(surplus, unit_debts[i])
                    unit_debts[i] -= prepay
                    feeder_prepay = prepay
                    cash -= prepay

            row = {
                "Year": year, "Month": m, "Units": units_owned,
                "PriceParity": cents(price_parity),
                "GrossIncome": gross, "Mgmt": mgmt, "CapexOps": capex_ops,
                "HOA_Monthly_Total": hoa_m, "Insurance": ins, "Tax": tax,
                "DebtService_Total": debt_service, "NOI": noi,
                "SavingsToCash": cents(annual_savings / 12),
                "RainyTarget": cents(rainy_target), "RainyBalance": cents(rainy_reserve),
                "RainyTopup": cents(rainy_topup), "CapexBalance": cents(capex_reserve),
                "LiquidityRequired": cents(liquidity_req), "LiquidityActual": cents(liquidity_act),
                "FreezeFlag": int(freeze), "Purchase": total,
                "Purchase_DP": dp, "Purchase_Closing": closing, "Purchase_Total": total,
                "FeederDraw_Net": feeder_cashout, "FeederPrepay": feeder_prepay,
                "EndCash": cents(cash),
                "TotalValue": cents(sum(unit_values or [0])),
                "TotalDebt": cents(sum(unit_debts or [0])),
            }
            rows.append(row)

            for k in yoy_accum:
                yoy_accum[k] += row.get(k, 0) if k != "NOI" else noi

        yoy_rows.append({**{k: cents(v) for k, v in yoy_accum.items()},
                         "Year": year, "Units": units_owned,
                         "TotalValue": cents(sum(unit_values or [0])),
                         "TotalDebt": cents(sum(unit_debts or [0])),
                         "EndCash": cents(cash)})
        yoy_accum = {k: 0.0 for k in yoy_accum}

    return pd.DataFrame(rows), pd.DataFrame(yoy_rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--years", type=int, default=30)
    parser.add_argument("--out-prefix", type=str, default="out/OB_STR_V2_3")
    args = parser.parse_args()

    engine = load_engine(args.engine)
    monthly_df, yoy_df = simulate(engine, years=args.years)

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    monthly_df.to_csv(out_prefix.with_name(out_prefix.name + "_Monthly.csv"), index=False)
    yoy_df.to_csv(out_prefix.with_name(out_prefix.name + "_YearOverYear.csv"), index=False)
    print("Done – check out/ folder")


if __name__ == "__main__":
    main()