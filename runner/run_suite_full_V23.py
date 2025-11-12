# run_suite_full_V23.py — MVP engine runner (clean)
# - ACT/365 HY accrual for cash, rainy, capex
# - Prepay split control (savings.prepayPct)
# - Accessible Principal (C1) with seasoning, advance rate, draw cost
# - Deterministic CSV columns
# - Cash/Amortization tests (incl. reserves, feeder, HY interest)

import os, sys, json, csv, math
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

# Quiet mode (suppresses banners and trailing DONE)
QUIET = os.getenv("QUIET", "0") == "1"

def _argv_flag(name, default=None):
    try:
        ix = sys.argv.index(name)
        return sys.argv[ix + 1]
    except Exception:
        return default

REPO_ROOT = Path(__file__).resolve().parent.parent  # …/ob_str
DEFAULT_ENGINE = REPO_ROOT / "engines" / "OB_STR_ENGINE_V2_3.json"
DEFAULT_OUT_MONTHLY = REPO_ROOT / "runner" / "V2_3_Monthly.csv"
DEFAULT_OUT_YOY     = REPO_ROOT / "runner" / "V2_3_YearOverYear.csv"

ENGINE = Path(_argv_flag("--engine", os.getenv("ENGINE_PATH", str(DEFAULT_ENGINE))))
OUT_MONTHLY = Path(_argv_flag("--out-monthly", os.getenv("OUT_MONTHLY", str(DEFAULT_OUT_MONTHLY))))
OUT_YOY     = Path(_argv_flag("--out-yoy", os.getenv("OUT_YOY", str(DEFAULT_OUT_YOY))))
MAX_MONTHS  = int(os.getenv("MAX_MONTHS", "240"))

COLS = [
    "YYYY-MM","UnitID",
    "Starting Cash","Savings In","Gross Revenue","Mgmt Expense","CapEx Operating",
    "HOA","Insurance","Property Tax","Debt Service (Total)","Scheduled Principal",
    "Interest Portion","Ops Net",
    "HY Interest (Cash)","HY Interest (Rainy)","HY Interest (Capex)",
    "Rainy Top-Up","Capex Top-Up","Rainy Balance","Capex Balance",
    "Liquidity Required","Liquidity Actual","Liquidity Ratio","Freeze Flag",
    "Accessible Principal","Deployable (Cash+Accessible)","Feeder Draw (Net)",
    "Feeder Prepay",
    "Purchase: Down Payment","Purchase: Closing Costs","Purchase: Initial Rainy Funding",
    "Purchase Out (Total)","New Loan Principal",
    "Loan Balance (End)","End Cash","Units Owned"
]

def cents(x): return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
def pmt(rate_m, nper, pv): return -(rate_m*pv)/(1-(1+rate_m)**(-nper)) if rate_m!=0 else -(pv/nper)

class Loan:
    def __init__(self, unit_id, principal, rate_apr, term_years):
        self.unit_id = unit_id
        self.balance = float(principal)
        self.rate_m  = float(rate_apr)/12.0
        self.n_left  = int(term_years*12)
        self.pmt_amt = -pmt(self.rate_m, self.n_left, self.balance) if self.balance>0 else 0.0
    def accrue(self):
        if self.balance <= 0 or self.n_left<=0:
            return 0.0, 0.0, 0.0
        interest  = self.balance * self.rate_m
        principal = max(min(self.pmt_amt - interest, self.balance), 0.0)
        self.balance -= principal
        self.n_left = max(self.n_left - 1, 0)
        return self.pmt_amt, principal, interest
    def prepay(self, amount):
        amt = max(min(amount, self.balance), 0.0)
        self.balance -= amt
        # keep payment constant; shorten term
        if self.balance>0 and self.rate_m>0 and self.pmt_amt>0:
            r=self.rate_m; B=self.balance; P=self.pmt_amt
            try:
                n_est = -math.log(max(1 - r*B/P, 1e-12))/math.log(1+r)
                self.n_left = max(int(math.ceil(n_est)), 0)
            except Exception:
                pass
        else:
            self.n_left = 0
        return amt

def _find_engine(p: Path) -> Path:
    for c in [p, DEFAULT_ENGINE, REPO_ROOT / "OB_STR_ENGINE_V2_3.json"]:
        if c.exists(): return c
    raise FileNotFoundError(f"Engine not found. Tried: {p}, {DEFAULT_ENGINE}, REPO/OB_STR_ENGINE_V2_3.json")

def load_eng(p: Path): return json.loads(_find_engine(p).read_text())

def parity_price(ADR,OCC,HOA_Y,MGMT,CAPX,INS,TAX,TARGET):
    # Price = (Gross - (Mgmt+Capex% of Gross) - HOA_annual) / (TARGET + INS + TAX)
    g = ADR*365*OCC
    numer = g - (g*(MGMT+CAPX) + HOA_Y)
    denom = TARGET + INS + TAX
    return max(numer/denom, 0.0)

def simulate(e, mmax=MAX_MONTHS):
    C=e["constants"]; cal=e["calendar"]
    # Top-level optional blocks
    B_top = e.get("banking", {})
    L_top = e.get("lending", {})
    P     = e.get("policies", {})
    S     = e.get("savings", {"annualYield":0.0, "prepayPct":1.0})
    market_top    = e.get("market", {})
    portfolio_top = e.get("portfolio", {"maxLoans":7})

    # Core constants
    fin=C["financial"]; ops=C["operations"]; acq=C["acquisition"]; debt=C["debt"]
    # runner still expects this key to exist (we only need capexMonthsTarget for structure)
    res=C.get("reserves", {"capexMonthsTarget": 6})

    ADR=ops["adrBaseline2BR"]; OCC=ops["occupancyBaseline"]; MGMT=ops["mgmtPct"]; CAPX=ops["capexPct"]
    HOA_Y0=ops["hoaAnnual"]; HOA_INF=ops.get("hoaInflationRate",0.0)
    INS=ops["insuranceRate"]; TAX=ops["propertyTaxRate"]; TARGET=acq["targetYieldUnlevered"]
    APP=(market_top or e.get("market", {})).get("annualAppreciation", 0.03)

    start_cash=fin["startingCash"]; annual_sav=fin["annualSavings"]; amort_yrs=fin["amortizationYears"]
    RATE=debt["mortgageRate"]; CLOSE=acq["closingCostPct"]; DOWN1=acq["downPaymentFirst"]; DOWNN=acq["downPaymentSubsequent"]
    rainyMonths=(B_top or {}).get("rainyCoverageMonths", 0)
    mdays=cal["monthlyDays"]

    # Lending/draw params (prefer top-level explicit)
    ADV=float(L_top.get("advanceRate", 0.75))
    T_LTV=float(L_top.get("targetLTV", 0.75))
    COST=float(L_top.get("cashoutCostPct", 0.03))
    SEAS=int(L_top.get("seasoningMonths", 6))

    allow_feeder_for_closing = bool((P.get("purchase") or {}).get("allowFeederForClosing", True))

    # HY savings controls
    hy_apr=float(S.get("annualYield", 0.0))
    prepay_pct=float(S.get("prepayPct", 1.0))
    prepay_pct = min(max(prepay_pct,0.0),1.0)

    rainy_bal=0.0; capex_bal=0.0
    y=1; m=1; HOA_Y=HOA_Y0
    cash=start_cash; savings_in=annual_sav/12.0
    units=[]; next_unit_id=1; rows=[]

    app_m = (1.0 + APP) ** (1.0/12.0)
    def parity(H): return parity_price(ADR,OCC,H,MGMT,CAPX,INS,TAX,TARGET)

    for t in range(1, mmax+1):
        # capture BOP cash for cash-identity
        start_bop_cash = cash

        if m==1 and t>1:
            HOA_Y *= (1+HOA_INF)

        # Parity price path with continuous appreciation
        price_par = parity(HOA_Y) * ((1+APP)**((y-1)+(m-1)/12.0))
        days      = mdays[m-1]
        hy_factor = (hy_apr/365.0) * days  # ACT/365

        # Ops + DS across owned units
        ops_gross=ops_mgmt=ops_capex=ops_hoa=ops_ins=ops_tax=0.0
        ds_total=interest_total=principal_total=0.0
        for u in units:
            gross=ADR*OCC*days
            mgmt=gross*MGMT
            capex_op=gross*CAPX
            hoa=HOA_Y/12.0
            ins=u["valuation"]*INS/12.0
            tax=u["valuation"]*TAX/12.0

            ops_gross+=gross; ops_mgmt+=mgmt; ops_capex+=capex_op
            ops_hoa+=hoa; ops_ins+=ins; ops_tax+=tax

            if u["loan"].balance>0 and u["loan"].n_left>0:
                Pmt,PR,IN = u["loan"].accrue()
                ds_total+=Pmt; principal_total+=PR; interest_total+=IN

            # monthly appreciation
            u["valuation"] *= app_m
            u["months_owned"] += 1
            if m==12:
                u["val_yend"][y] = u["valuation"]

        # HY interest accrues on starting balances BEFORE flows
        hy_int_cash  = cash      * hy_factor
        hy_int_rainy = rainy_bal * hy_factor
        hy_int_capex = capex_bal * hy_factor
        cash      += hy_int_cash
        rainy_bal += hy_int_rainy
        capex_bal += hy_int_capex

        # Operations net of expenses + debt service
        ops_net = ops_gross - (ops_mgmt + ops_capex + ops_hoa + ops_ins + ops_tax + ds_total)

        # Pre-feeder cash (after ops and savings in)
        cash_prefeeder = cash + savings_in + ops_net

        # Reserve targets
        gross_revenue_annual = ADR * 365 * OCC
        capex_target_m = (CAPX * gross_revenue_annual) / 12.0

        fixed_costs_m = ds_total + ops_hoa + ops_ins + ops_tax
        rainy_target_m  = rainyMonths * fixed_costs_m

        # Top-ups to reserves (order: rainy → capex)
        gap_rainy  = max(0.0, rainy_target_m - rainy_bal)
        rainy_top  = min(cash_prefeeder, gap_rainy); cash_prefeeder -= rainy_top; rainy_bal += rainy_top

        gap_capex  = max(0.0, capex_target_m - capex_bal)
        capex_top  = min(cash_prefeeder, gap_capex); cash_prefeeder -= capex_top; capex_bal += capex_top

        # Liquidity status (ironclad lockout)
        liquidity_required = rainy_target_m + capex_target_m
        liquidity_actual   = rainy_bal + capex_bal
        freeze_flag = 1 if (liquidity_required>0 and liquidity_actual < liquidity_required) else 0

        # Accessible principal (C1) using prior-year values (seasoned)
        accessible = 0.0
        prior_year = y - 1
        if allow_feeder_for_closing and prior_year>=1:
            for u in units:
                if u["months_owned"]>=SEAS and prior_year in u["val_yend"]:
                    val_prev = u["val_yend"][prior_year]
                    headroom = T_LTV*val_prev - u["loan"].balance
                    if headroom>0:
                        gross_draw = ADV*headroom
                        accessible += max(gross_draw*(1.0-COST), 0.0)

        # Purchase gate (uses deployable = cash + accessible when allowed)
        purchase=False; pur_dp=pur_cl=pur_rainy=0.0; pur_total=0.0; new_loan_principal=0.0
        feeder_draw_net=0.0
        deployable = cash_prefeeder + (accessible if allow_feeder_for_closing else 0.0)

        if freeze_flag==0 and len(units) < (portfolio_top.get("maxLoans",7)) and price_par>0:
            down_frac = DOWN1 if len(units)==0 else DOWNN
            loan_pf  = price_par*(1 - down_frac)
            rate_m   = RATE/12.0
            ds_pf    = -pmt(rate_m, amort_yrs*12, loan_pf)  # scheduled DS after purchase (sanity)
            hoa_pf   = HOA_Y/12.0
            pur_dp   = down_frac * price_par
            pur_cl   = CLOSE * price_par
            pur_rainy= 0.0  # initial rainy funding is handled via monthly target top-ups
            gate_req = pur_dp + pur_cl + pur_rainy

            if deployable >= gate_req:
                shortage = max(0.0, gate_req - cash_prefeeder)
                feeder_draw_net = min(accessible, shortage)
                cash_prefeeder += feeder_draw_net

                cash_prefeeder -= gate_req
                purchase=True; pur_total=gate_req; new_loan_principal=loan_pf
                units.append({
                    "id": f"U{next_unit_id}",
                    "price": price_par,
                    "valuation": price_par,
                    "months_owned": 0,
                    "val_yend": {},
                    "loan": Loan(f"U{next_unit_id}", loan_pf, RATE, amort_yrs)
                })
                next_unit_id += 1

        # Surplus split: prepay vs. stay in HY cash
        feeder_prepay = 0.0
        if freeze_flag==0 and len(units)>0 and cash_prefeeder>0:
            prepay_eligible = prepay_pct * cash_prefeeder
            if prepay_eligible>0:
                target = max(units, key=lambda u:u["loan"].balance)
                feeder_prepay = target["loan"].prepay(min(prepay_eligible, target["loan"].balance))
                cash_prefeeder -= feeder_prepay
            # remainder (1-prepay_pct) remains as cash (already HY-accruing next month)

        end_cash = cash_prefeeder

        # Row
        rows.append({
            "YYYY-MM": f"Y{y}-{m:02d}",
            "UnitID": "TOTAL",
            "Starting Cash": round(start_bop_cash,2),
            "Savings In": round(savings_in,2),
            "Gross Revenue": round(ops_gross,2),
            "Mgmt Expense": round(ops_mgmt,2),
            "CapEx Operating": round(ops_capex,2),
            "HOA": round(ops_hoa,2),
            "Insurance": round(ops_ins,2),
            "Property Tax": round(ops_tax,2),
            "Debt Service (Total)": round(ds_total,2),
            "Scheduled Principal": round(principal_total,2),
            "Interest Portion": round(interest_total,2),
            "Ops Net": round(ops_net,2),
            "HY Interest (Cash)": round(hy_int_cash,2),
            "HY Interest (Rainy)": round(hy_int_rainy,2),
            "HY Interest (Capex)": round(hy_int_capex,2),
            "Rainy Top-Up": round(rainy_top,2),
            "Capex Top-Up": round(capex_top,2),
            "Rainy Balance": round(rainy_bal,2),
            "Capex Balance": round(capex_bal,2),
            "Liquidity Required": round(liquidity_required,2),
            "Liquidity Actual": round(liquidity_actual,2),
            "Liquidity Ratio": round((liquidity_actual/liquidity_required) if liquidity_required>0 else 0.0, 6),
            "Freeze Flag": freeze_flag,
            "Accessible Principal": round(accessible,2),
            "Deployable (Cash+Accessible)": round(deployable,2),
            "Feeder Draw (Net)": round(feeder_draw_net,2),
            "Feeder Prepay": round(feeder_prepay,2),
            "Purchase: Down Payment": round(pur_dp,2),
            "Purchase: Closing Costs": round(pur_cl,2),
            "Purchase: Initial Rainy Funding": round(pur_rainy,2),
            "Purchase Out (Total)": round(pur_total,2),
            "New Loan Principal": round(new_loan_principal,2),
            "Loan Balance (End)": round(sum(u["loan"].balance for u in units),2),
            "End Cash": round(end_cash,2),
            "Units Owned": len(units)
        })

        cash = end_cash
        m += 1
        if m>12: m=1; y+=1

    return rows

if __name__ == "__main__":
    if not QUIET:
        print("CWD:", os.getcwd())
        print("ENGINE:", ENGINE)
        print("OUT_MONTHLY:", OUT_MONTHLY)
        print("OUT_YOY:", OUT_YOY)

    e = load_eng(ENGINE)
    rows = simulate(e, mmax=MAX_MONTHS)

    # ---- Tests ----
    # T-DS-1: If any purchase occurred, DS must be > 0 afterwards
    ds_pos=False; purchase_seen=False
    for r in rows:
        if r["Purchase Out (Total)"]>0: purchase_seen=True
        elif purchase_seen and r["Debt Service (Total)"]>0:
            ds_pos=True; break
    if purchase_seen:
        assert ds_pos, "T-DS-1 FAIL: no DS>0 after purchase"

    # T-AMORT-1: prev_end - principal - feeder + new_loan == curr_end (±0.01)
    for i in range(1,len(rows)):
        prev, curr = rows[i-1], rows[i]
        lhs = cents(prev["Loan Balance (End)"]) - cents(curr["Scheduled Principal"]) - cents(curr["Feeder Prepay"]) + cents(curr.get("New Loan Principal",0.0))
        rhs = cents(curr["Loan Balance (End)"])
        assert abs(lhs - rhs) <= Decimal("0.01"), f"T-AMORT-1 FAIL {curr['YYYY-MM']} lhs={lhs} rhs={rhs}"

    # T-CASH-1: Cash identity including HY interest, reserve top-ups, feeder draw, prepay split
    for r in rows:
        lhs = cents(r["End Cash"])
        start   = cents(r.get("Starting Cash", 0.0))
        sav_in  = cents(r.get("Savings In", 0.0))
        ops_net = cents(r.get("Ops Net", 0.0))
        hy_cash     = cents(r.get("HY Interest (Cash)", 0.0))
        feeder_draw = cents(r.get("Feeder Draw (Net)", 0.0))
        prepay      = cents(r.get("Feeder Prepay", 0.0))
        purchase    = cents(r.get("Purchase Out (Total)", 0.0))
        rainy       = cents(r.get("Rainy Top-Up", 0.0))
        capex       = cents(r.get("Capex Top-Up", 0.0))
        rhs = (start + sav_in + ops_net + hy_cash + feeder_draw
               - prepay - purchase - rainy - capex)
        assert abs(lhs - rhs) <= Decimal("0.01"), f"T-CASH-1 FAIL {r['YYYY-MM']} (lhs={lhs}, rhs={rhs})"

    # ---- Write outputs ----
    OUT_MONTHLY.parent.mkdir(parents=True, exist_ok=True)
    OUT_YOY.parent.mkdir(parents=True, exist_ok=True)

    if rows:
        with OUT_MONTHLY.open("w", newline="") as f:
            w=csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, 0.0) for k in COLS})

        # YOY rollup: sum flows; carry end-of-year states
        from collections import defaultdict
        agg, last_by_year = defaultdict(lambda:{k:Decimal("0.00") for k in COLS}), {}
        for r in rows:
            y=int(r["YYYY-MM"][1:].split("-")[0])
            last_by_year[y]=r
            for k,v in r.items():
                if k in ["YYYY-MM","UnitID"]: continue
                if isinstance(v,(int,float)): agg[y][k]+=Decimal(str(v))
        out=[]
        carry = ["End Cash","Loan Balance (End)","Rainy Balance","Capex Balance",
                 "Liquidity Required","Liquidity Actual","Liquidity Ratio","Freeze Flag",
                 "Accessible Principal","Deployable (Cash+Accessible)","Units Owned"]
        for y in sorted(agg.keys()):
            a=agg[y]; last=last_by_year[y]
            row={k:(float(a[k]) if isinstance(a[k],Decimal) else a[k]) for k in a}
            row["YYYY-MM"]=f"Year {y}"; row["UnitID"]="TOTAL"
            for k in carry:
                row[k]=last[k]
            out.append(row)
        with OUT_YOY.open("w", newline="") as f:
            w=csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            for r in out:
                w.writerow({k: r.get(k, 0.0) for k in COLS})

    if not QUIET:
        print("DONE")
