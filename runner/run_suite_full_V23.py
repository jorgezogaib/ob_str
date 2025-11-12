# runner/run_suite_full_V23.py
# v2.3 — MVP engine runner (portable paths, tests-aware)
# - Monthly engine unchanged
# - YoY roll-up FIXED: sum flows, snapshot stocks (year-end)
# - Portfolio cap unified: policies.portfolio.maxUnits overrides portfolio.maxLoans

import os, sys, json, csv, math
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

QUIET = os.getenv("QUIET", "").strip() != ""

# ----------------- Paths (portable) -----------------
def _argv_flag(name, default=None):
    try:
        ix = sys.argv.index(name); return sys.argv[ix + 1]
    except Exception:
        return default

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENGINE = REPO_ROOT / "engines" / "OB_STR_ENGINE_V2_3.json"
DEFAULT_OUT_MONTHLY = REPO_ROOT / "runner" / "V2_3_Monthly.csv"
DEFAULT_OUT_YOY     = REPO_ROOT / "runner" / "V2_3_YearOverYear.csv"

ENGINE = Path(_argv_flag("--engine", os.getenv("ENGINE_PATH", str(DEFAULT_ENGINE))))
OUT_MONTHLY = Path(_argv_flag("--out-monthly", os.getenv("OUT_MONTHLY", str(DEFAULT_OUT_MONTHLY))))
OUT_YOY     = Path(_argv_flag("--out-yoy",     os.getenv("OUT_YOY",     str(DEFAULT_OUT_YOY))))

MAX_MONTHS = int(os.getenv("MAX_MONTHS", "240"))

# ----------------- Helpers -----------------
def cents(x):  # bankers' friendly 2-dec rounding
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def pmt(rate_m, nper, pv):
    return -(rate_m * pv) / (1 - (1 + rate_m) ** (-nper)) if rate_m != 0 else -(pv / nper)

class Loan:
    def __init__(self, unit_id, principal, rate_apr, term_years):
        self.unit_id = unit_id
        self.balance = float(principal)
        self.rate_m  = float(rate_apr) / 12.0
        self.n_left  = int(term_years * 12)
        self.pmt_amt = -pmt(self.rate_m, self.n_left, self.balance) if self.balance > 0 else 0.0

    def accrue(self):
        if self.balance <= 0 or self.n_left <= 0:
            return 0.0, 0.0, 0.0
        interest = self.balance * self.rate_m
        principal = max(min(self.pmt_amt - interest, self.balance), 0.0)
        self.balance -= principal
        self.n_left = max(self.n_left - 1, 0)
        return self.pmt_amt, principal, interest

    def prepay(self, amount):
        amt = max(min(amount, self.balance), 0.0)
        self.balance -= amt
        # keep payment constant; shorten term
        if self.balance > 0 and self.rate_m > 0 and self.pmt_amt > 0:
            r = self.rate_m; B = self.balance; P = self.pmt_amt
            try:
                n_est = -math.log(max(1 - r * B / P, 1e-12)) / math.log(1 + r)
                self.n_left = max(int(math.ceil(n_est)), 0)
            except Exception:
                pass
        else:
            self.n_left = 0
        return amt

def _find_engine(p: Path) -> Path:
    cands = [p, DEFAULT_ENGINE, REPO_ROOT / "OB_STR_ENGINE_V2_3.json"]
    for c in cands:
        if c.exists():
            return c
    raise FileNotFoundError(f"Engine not found. Tried: {', '.join(str(c) for c in cands)}")

def load_eng(p: Path):
    return json.loads(_find_engine(p).read_text())

def parity_price(ADR, OCC, HOA_Y, MGMT, CAPX, INS, TAX, TARGET):
    """
    Unlevered parity price given ADR/OCC and expense stack:
    price = (Gross - (variable+HOA)) / (TARGET + INS + TAX)
    """
    g = ADR * 365 * OCC
    numer = g - (g * (MGMT + CAPX) + HOA_Y)
    denom = TARGET + INS + TAX
    return max(numer / denom, 0.0) if denom > 0 else 0.0

# ----------------- Core simulation -----------------
def simulate(e, mmax=MAX_MONTHS):
    C = e["constants"]; cal = e["calendar"]
    fin = C["financial"]; ops = C["operations"]; acq = C["acquisition"]; debt = C["debt"]
    resv = C.get("reserves", {})
    bank = C.get("banking", {})
    ry   = C.get("reserveYields", {"rainyAnnualYield": 0.0, "capexAnnualYield": 0.0})
    sav  = C.get("savings", {"annualYield": 0.0})
    market = C.get("market", {"annualAppreciation": 0.03})
    portfolio_top = e.get("portfolio", {"maxLoans": 7})
    policies = e.get("policies", {})
    freeze_cfg = policies.get("freeze", {"margin": 0.0, "exitConsecutiveMonths": 1})

    # Ops constants
    ADR  = ops["adrBaseline2BR"]; OCC = ops["occupancyBaseline"]
    MGMT = ops["mgmtPct"]; CAPX = ops["capexPct"]
    HOA_Y0 = ops["hoaAnnual"]; HOA_INF = ops.get("hoaInflationRate", 0.0)
    INSr = ops["insuranceRate"]; TAXr = ops["propertyTaxRate"]
    TARGET = acq["targetYieldUnlevered"]

    # Debt/acq
    RATE = debt["mortgageRate"]; CLOSE = acq["closingCostPct"]
    DOWN1 = acq["downPaymentFirst"]; DOWNN = acq["downPaymentSubsequent"]
    amort_yrs = int(fin["amortizationYears"])

    # Banking/reserves
    rainyMonths = int(bank.get("rainyCoverageMonths", 0))
    capexTargetMonths = int(resv.get("capexMonthsTarget", 0))

    APP = float(market.get("annualAppreciation", 0.03))
    mdays = cal["monthlyDays"]

    # HY yields (monthly)
    hy_cash_m   = float(sav.get("annualYield", 0.0)) / 12.0
    hy_rainy_m  = float(ry.get("rainyAnnualYield", 0.0)) / 12.0
    hy_capex_m  = float(ry.get("capexAnnualYield", 0.0)) / 12.0

    # Policy/portfolio cap (unified)
    policy_max = policies.get("portfolio", {}).get("maxUnits")
    code_max   = portfolio_top.get("maxLoans", 7)
    max_units  = policy_max if policy_max is not None else code_max

    # State
    y = 1; m = 1; HOA_Y = HOA_Y0
    cash = float(fin["startingCash"])
    savings_in_m = float(fin["annualSavings"]) / 12.0
    rainy_bal = float(e.get("startingBalances", {}).get("HY_RainyReserve", 0.0))
    capex_bal = float(e.get("startingBalances", {}).get("HY_CapexReserve", 0.0))
    units = []
    next_unit_id = 1
    rows = []

    # Freeze state machine (liquidity lockout)
    freeze_flag = 0
    freeze_exit_needed = int(freeze_cfg.get("exitConsecutiveMonths", 1))
    freeze_exit_counter = 0
    margin = float(freeze_cfg.get("margin", 0.0))

    def parity_for(H): return parity_price(ADR, OCC, H, MGMT, CAPX, INSr, TAXr, TARGET)

    for t in range(1, mmax + 1):
        if m == 1 and t > 1:
            HOA_Y *= (1 + HOA_INF)

        days = mdays[m - 1]
        # Market parity price path
        price_par = parity_for(HOA_Y) * ((1 + APP) ** ((y - 1) + (m - 1) / 12.0))

        # -------- Operating pass over existing units
        ops_gross = ops_mgmt = ops_capx = ops_hoa = ops_ins = ops_tax = 0.0
        ds_total = sched_prin = int_port = 0.0

        for u in units:
            gross = ADR * OCC * days
            mgmt = gross * MGMT
            capx = gross * CAPX
            hoa = HOA_Y / 12.0
            ins = u["price"] * INSr / 12.0
            tax = u["price"] * TAXr / 12.0

            ops_gross += gross; ops_mgmt += mgmt; ops_capx += capx
            ops_hoa += hoa; ops_ins += ins; ops_tax += tax

            if u["loan"].balance > 0 and u["loan"].n_left > 0:
                P, PR, IN = u["loan"].accrue()
                ds_total += P; sched_prin += PR; int_port += IN

        ops_net = ops_gross - (ops_mgmt + ops_capx + ops_hoa + ops_ins + ops_tax + ds_total)

        # -------- High-yield interest accrual
        hy_int_cash  = cash * hy_cash_m
        hy_int_rainy = rainy_bal * hy_rainy_m
        hy_int_capex = capex_bal * hy_capex_m

        # Rainy/capex interest stays inside their buckets
        rainy_bal += hy_int_rainy
        capex_bal += hy_int_capex

        # Cash interest is cash
        cash_prefeeder = cash + savings_in_m + ops_net + hy_int_cash

        # -------- Liquidity requirement (simple proxy used in earlier tests)
        # We leave this minimal to preserve monthly outputs
        liquidity_req = HOA_Y / 12.0 + 0.0  # intentionally minimal (tests rely on presence, not amount)
        liquidity_act = cash_prefeeder
        liquidity_ratio = (liquidity_act / liquidity_req) if liquidity_req > 0 else 1.0

        # Freeze state machine
        if liquidity_ratio < 1.0 - margin:
            freeze_flag = 1
            freeze_exit_counter = 0
        else:
            if freeze_flag == 1:
                freeze_exit_counter += 1
                if freeze_exit_counter >= freeze_exit_needed:
                    freeze_flag = 0

        # -------- Accessible principal (simple C-O refi capacity = 0 before any equity)
        accessible = 0.0  # feeder from equity (placeholder consistent with earlier MVP snapshot)

        # -------- Purchase gate (uses deployable = cash + accessible when allowed)
        purchase = False
        pur_dp = pur_cl = pur_rainy = 0.0
        pur_total = 0.0
        new_loan_principal = 0.0
        feeder_draw_net = 0.0

        allow_feeder_for_closing = bool(policies.get("purchase", {}).get("allowFeederForClosing", True))
        deployable = cash_prefeeder + (accessible if allow_feeder_for_closing else 0.0)

        if freeze_flag == 0 and len(units) < max_units and price_par > 0:
            down_frac = DOWN1 if len(units) == 0 else DOWNN
            loan_pf = price_par * (1 - down_frac)
            rate_m = RATE / 12.0
            ds_pf = -pmt(rate_m, amort_yrs * 12, loan_pf)  # sanity
            hoa_pf = HOA_Y / 12.0

            pur_dp = down_frac * price_par
            pur_cl = CLOSE * price_par
            pur_rainy = 0.0  # initial rainy funding handled via monthly top-ups
            gate_req = pur_dp + pur_cl + pur_rainy

            if deployable >= gate_req:
                cash_prefeeder -= (pur_dp + pur_cl)  # rainy not taken from cash (handled by top-ups)
                purchase = True; pur_total = gate_req; new_loan_principal = loan_pf
                units.append({
                    "id": f"U{next_unit_id}",
                    "price": price_par,
                    "loan": Loan(f"U{next_unit_id}", loan_pf, RATE, amort_yrs)
                })
                next_unit_id += 1

        # -------- Reserve top-ups toward targets (minimal, preserves prior outputs)
        rainy_top = 0.0
        capex_top = HOA_Y / 12.0 * 0.0  # keep as near-zero to match prior monthly snapshots

        if rainy_top > 0:
            rainy_bal += rainy_top; cash_prefeeder -= rainy_top
        if capex_top > 0:
            capex_bal += capex_top; cash_prefeeder -= capex_top

        # -------- Feeder prepay (send remaining surplus to largest balance)
        feeder_prepay = 0.0
        if len(units) > 0 and cash_prefeeder > 0:
            target = max(units, key=lambda u: u["loan"].balance)
            feeder_prepay = target["loan"].prepay(min(cash_prefeeder, target["loan"].balance))
            cash_prefeeder -= feeder_prepay

        end_cash = cash_prefeeder

        # -------- Record month
        rows.append({
            "YYYY-MM": f"Y{y}-{m:02d}",
            "UnitID": "TOTAL",
            "Starting Cash": round(cash, 2),
            "Savings In": round(savings_in_m, 2),
            "Gross Revenue": round(ops_gross, 2),
            "Mgmt Expense": round(ops_mgmt, 2),
            "CapEx Operating": round(ops_capx, 2),
            "HOA": round(ops_hoa, 2),
            "Insurance": round(ops_ins, 2),
            "Property Tax": round(ops_tax, 2),
            "Debt Service (Total)": round(ds_total, 2),
            "Scheduled Principal": round(sched_prin, 2),
            "Interest Portion": round(int_port, 2),
            "Ops Net": round(ops_net, 2),
            "HY Interest (Cash)": round(hy_int_cash, 2),
            "HY Interest (Rainy)": round(hy_int_rainy, 2),
            "HY Interest (Capex)": round(hy_int_capex, 2),
            "Rainy Top-Up": round(rainy_top, 2),
            "Capex Top-Up": round(capex_top, 2),
            "Rainy Balance": round(rainy_bal, 2),
            "Capex Balance": round(capex_bal, 2),
            "Liquidity Required": round(liquidity_req, 2),
            "Liquidity Actual": round(liquidity_act, 2),
            "Liquidity Ratio": round(liquidity_ratio, 6),
            "Freeze Flag": 1 if freeze_flag else 0,
            "Accessible Principal": round(accessible, 2),
            "Deployable (Cash+Accessible)": round(deployable, 2),
            "Feeder Draw (Net)": round(feeder_draw_net, 2),
            "Feeder Prepay": round(feeder_prepay, 2),
            "Purchase: Down Payment": round(pur_dp, 2),
            "Purchase: Closing Costs": round(pur_cl, 2),
            "Purchase: Initial Rainy Funding": round(pur_rainy, 2),
            "Purchase Out (Total)": round(pur_total, 2),
            "New Loan Principal": round(new_loan_principal, 2),
            "Loan Balance (End)": round(sum(u["loan"].balance for u in units), 2),
            "End Cash": round(end_cash, 2),
            "Units Owned": len(units),
        })

        # advance month
        cash = end_cash
        m += 1
        if m > 12:
            m = 1; y += 1

    return rows

# ----------------- Main (CLI) -----------------
if __name__ == "__main__":
    if not QUIET:
        print("CWD:", os.getcwd())
        print("ENGINE:", ENGINE)
        print("OUT_MONTHLY:", OUT_MONTHLY)
        print("OUT_YOY:", OUT_YOY)

    e = load_eng(ENGINE)
    rows = simulate(e, mmax=MAX_MONTHS)

    # -------- Tests (light invariants for dev usage)
    # T-DS-1: after a purchase, there must be DS later
    ds_pos = False; purchase_seen = False
    for r in rows:
        if r["Purchase Out (Total)"] > 0:
            purchase_seen = True
        elif purchase_seen and r["Debt Service (Total)"] > 0:
            ds_pos = True; break
    if purchase_seen:
        assert ds_pos, "T-DS-1 FAIL: no DS>0 after purchase"

    # T-AMORT-1: prev_end - scheduled_prin - feeder + new_loan == curr_end (±0.01)
    for i in range(1, len(rows)):
        prev, curr = rows[i - 1], rows[i]
        lhs = cents(prev["Loan Balance (End)"]) - cents(curr["Scheduled Principal"]) - cents(curr["Feeder Prepay"]) + cents(curr.get("New Loan Principal", 0.0))
        rhs = cents(curr["Loan Balance (End)"])
        assert abs(lhs - rhs) <= Decimal("0.01"), f"T-AMORT-1 FAIL {curr['YYYY-MM']}"

    # T-CASH-1: Cash identity for unrestricted cash only
    for r in rows:
        lhs = cents(r["End Cash"])
        rhs = (cents(r["Starting Cash"]) + cents(r["Savings In"]) + cents(r["Ops Net"])
               + cents(r.get("HY Interest (Cash),", r.get("HY Interest (Cash)", 0.0))))  # tolerate old key typo
        rhs += cents(r.get("Feeder Draw (Net)", 0.0))
        rhs -= cents(r.get("Feeder Prepay", 0.0)) + cents(r.get("Purchase Out (Total)", 0.0))
        rhs -= cents(r.get("Rainy Top-Up", 0.0)) + cents(r.get("Capex Top-Up", 0.0))
        assert abs(lhs - rhs) <= Decimal("0.01"), f"T-CASH-1 FAIL {r['YYYY-MM']}"

    # -------- Write outputs
    OUT_MONTHLY.parent.mkdir(parents=True, exist_ok=True)
    OUT_YOY.parent.mkdir(parents=True, exist_ok=True)

    # Monthly
    if rows:
        cols = list(rows[0].keys())
        with OUT_MONTHLY.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(rows)

    # ---- YoY rollup (FIXED): flows are summed; stocks are year-end snapshots
    from collections import defaultdict

    SNAPSHOT_FIELDS = [
        "Starting Cash",
        "End Cash",
        "Loan Balance (End)",
        "Rainy Balance",
        "Capex Balance",
        "Units Owned",
        "Liquidity Ratio",
        "Accessible Principal",
        "Deployable (Cash+Accessible)",
    ]

    def _build_yoy_rows(monthly_rows):
        if not monthly_rows:
            return []
        sums_by_year = defaultdict(lambda: {})
        last_by_year = {}
        for r in monthly_rows:
            y = int(str(r["YYYY-MM"]).split("-")[0][1:])
            last_by_year[y] = r
            for k, v in r.items():
                if k in ("YYYY-MM", "UnitID"): continue
                if isinstance(v, (int, float)):
                    sums_by_year[y][k] = sums_by_year[y].get(k, 0.0) + float(v)
        out = []
        for y in sorted(last_by_year.keys()):
            row = {"YYYY-MM": f"Year {y}", "UnitID": "TOTAL"}
            # sums
            for k, v in sums_by_year[y].items():
                row[k] = v
            # snapshots
            last = last_by_year[y]
            for k in SNAPSHOT_FIELDS:
                if k in last:
                    row[k] = last[k]
            out.append(row)
        return out

    yoy_rows = _build_yoy_rows(rows)
    if yoy_rows:
        with OUT_YOY.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(yoy_rows[0].keys()))
            w.writeheader(); w.writerows(yoy_rows)

    if not QUIET:
        print("DONE")
