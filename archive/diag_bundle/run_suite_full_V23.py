import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def cents(x: float) -> float:
    """Round to cents to keep identities tight."""
    return float(np.round(x, 2))


def load_engine(engine_path: Path) -> Dict[str, Any]:
    with engine_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def apply_engine_overrides(base_engine: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply ENGINE_OVERRIDE-style nested overrides onto the base engine.
    Supports:
      - direct scalar replacement
      - nested dict walking
    """
    if not overrides:
        return base_engine

    def _apply(d: Dict[str, Any], o: Dict[str, Any]) -> None:
        for k, v in o.items():
            if isinstance(v, dict) and isinstance(d.get(k), dict):
                _apply(d[k], v)
            else:
                d[k] = v

    engine = json.loads(json.dumps(base_engine))
    _apply(engine, overrides)
    return engine


def simulate(
    engine: Dict[str, Any],
    years: int = 30,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Core simulation.
    Returns:
      - monthly_df
      - yoy_df
    """
    const = engine["constants"]
    fin = const["financial"]
    ops = const["operations"]
    acq = const["acquisition"]
    debt_cfg = const["debt"]
    reserves_cfg = const["reserves"]

    calendar = engine["calendar"]
    monthly_days = calendar["monthlyDays"]

    # --- Inputs and baseline parameters ---
    starting_cash = float(fin["startingCash"])
    annual_savings = float(fin["annualSavings"])
    amort_years = int(fin["amortizationYears"])

    adr_baseline_2br = float(ops["adrBaseline2BR"])
    occ_baseline = float(ops["occupancyBaseline"])
    mgmt_pct = float(ops["mgmtPct"])
    capex_pct = float(ops["capexPct"])
    hoa_annual = float(ops["hoaAnnual"])
    hoa_infl_rate = float(ops["hoaInflationRate"])
    ins_rate = float(ops["insuranceRate"])
    tax_rate = float(ops["propertyTaxRate"])

    dp_first = float(acq["downPaymentFirst"])
    dp_sub = float(acq["downPaymentSubsequent"])
    closing_cost_pct = float(acq["closingCostPct"])
    target_yield_unlev = float(acq["targetYieldUnlevered"])

    rate = float(debt_cfg["mortgageRate"])
    capex_months_target = int(reserves_cfg["capexMonthsTarget"])

    annual_appreciation = float(engine["market"]["annualAppreciation"])

    max_units = int(engine["portfolio"]["maxLoans"])
    purchase_max_units = int(engine["policies"]["portfolio"]["maxUnits"])

    # --- Mortgage helper ---
    def pmt(r_annual: float, n_years: int, principal: float) -> float:
        r = r_annual / 12.0
        n = n_years * 12
        if r == 0:
            return principal / n
        return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    # --- State tracking ---
    rows: List[Dict[str, Any]] = []
    yoy_rows: List[Dict[str, Any]] = []

    cash = starting_cash
    units_owned = 0

    # We track per-unit state in lists
    unit_values: List[float] = []
    unit_debts: List[float] = []
    unit_pmt: List[float] = []

    # For simplicity: assume 1st purchase at a parity price derived from target yield
    # Then re-use derived price for subsequent purchases.
    price_per_unit = None

    # --- Main loop ---
    total_months = years * 12
    month_index = 0

    # Annual accumulators for YoY
    def _reset_yoy_accum() -> Dict[str, float]:
        return dict(
            GrossIncome=0.0,
            Mgmt=0.0,
            CapexOps=0.0,
            HOA=0.0,
            Insurance=0.0,
            Tax=0.0,
            DebtService=0.0,
            NOI=0.0,
        )

    yoy_accum = _reset_yoy_accum()

    for year in range(1, years + 1):
        for m in range(1, 13):
            month_index += 1
            days = monthly_days[m - 1]

            # Simple "savings to cash" model (no HY detail in this runner)
            # Spread annual savings evenly across 12 months
            savings_in = annual_savings / 12.0
            cash += savings_in

            # --- Derive ADR and gross income for current portfolio ---
            if units_owned > 0:
                # simple appreciation on ADR as well? keep flat for now, appreciation only on asset price
                adr = adr_baseline_2br
                occ = occ_baseline
                gross = adr * occ * days * units_owned
            else:
                adr = adr_baseline_2br
                occ = 0.0
                gross = 0.0

            gross = cents(gross)
            mgmt = cents(gross * mgmt_pct)
            capex_ops = cents(gross * capex_pct)

            # HOA: annual, inflated by year, then pro-rated monthly
            hoa_annual_this_year = hoa_annual * ((1 + hoa_infl_rate) ** (year - 1))
            hoa_m = cents(hoa_annual_this_year / 12.0 * units_owned)

            # Insurance & tax as a rate on property value
            total_property_value = sum(unit_values) if unit_values else 0.0
            ins_annual = total_property_value * ins_rate
            tax_annual = total_property_value * tax_rate
            ins = cents(ins_annual / 12.0)
            tax = cents(tax_annual / 12.0)

            # Debt service: sum of payments across all units
            debt_service_total = cents(sum(unit_pmt)) if unit_pmt else 0.0

            # --- NOI definition (Institutional) ---
            # Institutional-style NOI: before capex reserves and before debt service
            noi = gross - mgmt - hoa_m - ins - tax

            # Cash movement from operations before any new purchase
            cash_ops = gross - mgmt - capex_ops - hoa_m - ins - tax - debt_service_total
            cash_ops = cents(cash_ops)
            cash_prefeeder = cash + cash_ops

            # --- Purchase logic (very simplified) ---
            purchase_flag = 0
            purchase_dp = 0.0
            purchase_closing = 0.0
            purchase_total = 0.0

            if units_owned < purchase_max_units:
                # If we haven't fixed price yet, derive a parity price for 1st purchase
                if price_per_unit is None and adr_baseline_2br > 0 and occ_baseline > 0:
                    # Simple parity: Annual unlevered NOI / target_yield
                    # Using single-unit economics
                    annual_days = 365
                    unit_gross_annual = adr_baseline_2br * occ_baseline * annual_days
                    unit_mgmt_annual = unit_gross_annual * mgmt_pct
                    unit_capex_annual = unit_gross_annual * capex_pct
                    unit_hoa_annual = hoa_annual
                    # As a placeholder, assume insurance+tax as a fraction of price and solve iteratively
                    # For MVP, we approximate ignoring tax/ins in the parity solve.
                    approx_noi_unlev = unit_gross_annual - unit_mgmt_annual - unit_capex_annual - unit_hoa_annual
                    if approx_noi_unlev > 0 and target_yield_unlev > 0:
                        price_per_unit = approx_noi_unlev / target_yield_unlev
                    else:
                        price_per_unit = 350_000.0  # fallback

                # Very blunt gate: if we can cover a simple DP+closing with cash_prefeeder, buy one unit
                if price_per_unit is not None and price_per_unit > 0:
                    dp_pct = dp_first if units_owned == 0 else dp_sub
                    dp = price_per_unit * dp_pct
                    closing = price_per_unit * closing_cost_pct
                    purchase_need = dp + closing
                    if cash_prefeeder >= purchase_need:
                        purchase_flag = 1
                        purchase_dp = cents(dp)
                        purchase_closing = cents(closing)
                        purchase_total = cents(purchase_dp + purchase_closing)

                        units_owned += 1
                        # New loan
                        principal = price_per_unit - purchase_dp
                        monthly_pmt = pmt(rate, amort_years, principal)
                        unit_values.append(price_per_unit)
                        unit_debts.append(principal)
                        unit_pmt.append(monthly_pmt)

                        # Deduct from cash
                        cash_prefeeder -= purchase_total

            # Update debt balances via simple amortization
            if unit_debts:
                new_unit_debts = []
                new_unit_values = []
                new_unit_pmt = []
                for v, bal, pmt_i in zip(unit_values, unit_debts, unit_pmt):
                    r_m = rate / 12.0
                    interest = bal * r_m
                    principal = pmt_i - interest
                    new_bal = bal - principal
                    if new_bal < 0:
                        new_bal = 0.0
                    new_unit_debts.append(new_bal)
                    new_unit_values.append(v * (1 + annual_appreciation / 12.0))
                    new_unit_pmt.append(pmt_i)
                unit_values = new_unit_values
                unit_debts = new_unit_debts
                unit_pmt = new_unit_pmt

            # End cash after all flows this month
            cash = cash_prefeeder
            end_cash = cents(cash)

            total_value = cents(sum(unit_values)) if unit_values else 0.0
            total_debt = cents(sum(unit_debts)) if unit_debts else 0.0

            # Record monthly
            row = dict(
                Year=year,
                Month=m,
                Units=units_owned,
                HOA_Annual=cents(hoa_annual_this_year * units_owned),
                PriceParity=cents(price_per_unit or 0.0),
                GrossIncome=gross,
                Mgmt=mgmt,
                CapexOps=capex_ops,
                HOA_Monthly_Total=hoa_m,
                Insurance=ins,
                Tax=tax,
                DebtService_Total=debt_service_total,
                Debt_Principal=0.0,  # We are not breaking out principal/interest here (MVP).
                Debt_Interest=0.0,
                NOI=noi,
                SavingsToCash=cents(savings_in),
                SavingsToHY=0.0,
                HY_Savings=0.0,
                RainyTarget=0.0,
                RainyBalance=0.0,
                RainyTopup=0.0,
                CapexTarget=0.0,
                CapexBalance=0.0,
                CapexTopup=0.0,
                LiquidityRequired=0.0,
                LiquidityActual=end_cash,
                LiquidityRatio=1.0,
                FreezeFlag=0,
                AccessiblePrincipal=0.0,
                Deployable=end_cash,
                Purchase=purchase_flag,
                Purchase_DP=purchase_dp,
                Purchase_Closing=purchase_closing,
                Purchase_Rainy=0.0,
                Purchase_Total=purchase_total,
                FeederDraw_Net=0.0,
                FeederPrepay=0.0,
                EndCash=end_cash,
                TotalValue=total_value,
                TotalDebt=total_debt,
            )
            rows.append(row)

            # YoY accumulation
            yoy_accum["GrossIncome"] += gross
            yoy_accum["Mgmt"] += mgmt
            yoy_accum["CapexOps"] += capex_ops
            yoy_accum["HOA"] += hoa_m
            yoy_accum["Insurance"] += ins
            yoy_accum["Tax"] += tax
            yoy_accum["DebtService"] += debt_service_total
            yoy_accum["NOI"] += noi

        # End of year: push YoY
        yoy_rows.append(
            dict(
                Year=year,
                Units=units_owned,
                GrossIncome=cents(yoy_accum["GrossIncome"]),
                Mgmt=cents(yoy_accum["Mgmt"]),
                CapexOps=cents(yoy_accum["CapexOps"]),
                HOA=cents(yoy_accum["HOA"]),
                Insurance=cents(yoy_accum["Insurance"]),
                Tax=cents(yoy_accum["Tax"]),
                DebtService=cents(yoy_accum["DebtService"]),
                NOI=cents(yoy_accum["NOI"]),
                TotalValue=cents(sum(unit_values)) if unit_values else 0.0,
                TotalDebt=cents(sum(unit_debts)) if unit_debts else 0.0,
                EndCash=cents(cash),
            )
        )
        yoy_accum = _reset_yoy_accum()

    monthly_df = pd.DataFrame(rows)
    yoy_df = pd.DataFrame(yoy_rows)
    return monthly_df, yoy_df


def compute_parity_prices(
    engine: Dict[str, Any],
    adr_candidates: List[float],
    yield_model: Dict[str, Any],
    target_year_yield: float,
) -> pd.DataFrame:
    """
    Take a range of ADRs and compute parity prices given the target yield curve.

    This is for strategy exploration, not the core runner.
    """
    const = engine["constants"]
    fin = const["financial"]
    ops = const["operations"]
    acq = const["acquisition"]

    occ = float(ops["occupancyBaseline"])
    mgmt_pct = float(ops["mgmtPct"])
    capex_pct = float(ops["capexPct"])
    hoa_annual = float(ops["hoaAnnual"])

    closing_cost_pct = float(acq["closingCostPct"])
    dp_first = float(acq["downPaymentFirst"])

    annual_days = 365

    rows = []
    for adr in adr_candidates:
        gross_annual = adr * occ * annual_days
        mgmt_annual = gross_annual * mgmt_pct
        capex_annual = gross_annual * capex_pct
        noi_unlev = gross_annual - mgmt_annual - capex_annual - hoa_annual

        if noi_unlev <= 0 or target_year_yield <= 0:
            price = 0.0
        else:
            price = noi_unlev / target_year_yield

        dp = price * dp_first
        closing = price * closing_cost_pct
        total_cash_in = dp + closing

        rows.append(
            dict(
                ADR=adr,
                Occupancy=occ,
                GrossAnnual=cents(gross_annual),
                NOI_Unlevered=cents(noi_unlev),
                TargetYield=target_year_yield,
                ParityPrice=cents(price),
                DP_First=cents(dp),
                ClosingCosts=cents(closing),
                TotalCashIn=cents(total_cash_in),
            )
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="OB_STR V2.3 full suite runner")
    parser.add_argument(
        "--engine",
        type=str,
        required=True,
        help="Path to engine JSON (e.g., engines/OB_STR_ENGINE_V2_3.json)",
    )
    parser.add_argument(
        "--out-prefix",
        type=str,
        required=True,
        help="Output prefix for CSVs (e.g., out/V2_3)",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=30,
        help="Number of years to simulate",
    )
    parser.add_argument(
        "--engine-override",
        type=str,
        default=None,
        help="Optional path to ENGINE_OVERRIDE JSON to apply on top of engine.",
    )
    args = parser.parse_args()

    engine_path = Path(args.engine)
    engine = load_engine(engine_path)

    if args.engine_override:
        override_path = Path(args.engine_override)
        with override_path.open("r", encoding="utf-8") as f:
            overrides = json.load(f)
        engine = apply_engine_overrides(engine, overrides)

    monthly_df, yoy_df = simulate(engine, years=args.years)

    out_prefix = Path(args.out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)

    monthly_path = out_prefix.with_name(out_prefix.name + "_Monthly.csv")
    yoy_path = out_prefix.with_name(out_prefix.name + "_YearOverYear.csv")

    monthly_df.to_csv(monthly_path, index=False)
    yoy_df.to_csv(yoy_path, index=False)

    print(f"Wrote monthly to {monthly_path}")
    print(f"Wrote YoY to {yoy_path}")


if __name__ == "__main__":
    main()
