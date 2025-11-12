
import csv, json, math
from dataclasses import dataclass
from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import date, timedelta

ENGINE = Path("OB_STR_ENGINE_V2_3.MVP.json")  # local path (same dir) after install
OUT_MONTHLY = Path("V2_3_Monthly.csv")
OUT_YOY     = Path("V2_3_YearOverYear.csv")
MAX_MONTHS = 240

def cents(x): return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

def pmt_act365(rate_yr, n_months, principal):
    # approximate fixed monthly payment under ACT/365 by solving constant M with daily accrual per average month length
    rate_m = rate_yr/12.0
    if rate_m == 0: return -(principal/n_months)
    return -(rate_m*principal)/(1-(1+rate_m)**(-n_months))

@dataclass
class Loan:
    id: str
    balance: float
    rate_apr: float
    term_months: int
    start_month_index: int  # first accrual month index (0-based), first payment at +1
    payment: float

def load_engine(p: Path):
    e=json.loads(Path(p).read_text())
    return e

def days_in_month(y,m):
    if m==12: return 31
    from calendar import monthrange
    return monthrange(y,m)[1]

def act365_interest(balance, apr, y, m):
    d = days_in_month(y,m)
    return balance * (apr/365.0) * d

def simulate():
    e = load_engine(ENGINE)
    C=e["constants"]; cal=e["calendar"]
    ops=C.get("operations",{}); acq=C.get("acquisition",{}); debt=C.get("debt",{})
    res=C.get("reserves",{}); lend=C.get("lending",{}); sav=C.get("savings",{})
    pol=e.get("policies",{})
    pol_pur=pol.get("purchase",{}); pol_pre=pol.get("prepay",{}); pol_fz=pol.get("freeze",{}); pol_debt=pol.get("debt",{})
    start=e.get("startingBalances",{})
    rainyMonths = res.get("rainyMonths",6)
    capexAnnualTarget = res.get("capexAnnualTarget",0.0)

    # High-yield sub-ledgers
    HY_Unres = float(start.get("HY_Unrestricted",0.0))
    HY_Rainy = float(start.get("HY_RainyReserve",0.0))
    HY_Capex = float(start.get("HY_CapexReserve",0.0))
    HY_APY   = float(sav.get("annualYield",0.0))
    savings_pct = float(sav.get("allocationPctToSavings",0.0))

    # Portfolio
    units=[]  # each: {"id":, "price":, "age_m":, "loan": Loan}
    next_unit_id = 1

    # Inputs for first unit parity
    ADR = ops.get("ADR", 0.0); OCC=ops.get("occupancy",0.0); MGMT=ops.get("mgmtPct",0.0); CAPX=ops.get("capexPct",0.0)
    HOA_Y = ops.get("hoaAnnual",0.0); INS=ops.get("insPct",0.0); TAX=ops.get("taxPct",0.0)
    TARGET = acq.get("targetYield",0.06)

    RATE = debt.get("apr",0.0)
    TERM = int(debt.get("termYears",30))*12
    FIRST_PAY_OFFSET = 1

    ADV=lend.get("advanceRate",0.75)
    T_LTV=lend.get("targetLTV",0.75)
    COST=lend.get("cashoutCostPct",0.03)
    SEASON=lend.get("seasoningMonths",6)

    def parity_price():
        g = ADR*365*OCC
        numer = g - (g*(MGMT+CAPX) + HOA_Y)
        denom = TARGET + INS + TAX
        return max(numer/denom, 0.0)

    # Calendar
    start_ym = cal.get("start","Y1-01")  # format Y#-MM
    y_now = 1; m_now=1

    # Freeze state
    freeze=False; freeze_enter=None; freeze_exit=None
    margin=float(pol_fz.get("margin",0.0)); exitN=int(pol_fz.get("exitConsecutiveMonths",1)); exit_run=0

    rows=[]
    for t in range(MAX_MONTHS):
        y_now = 1 + (t//12)
        m_now = 1 + (t%12)
        ym = f"Y{y_now:01d}-{m_now:02d}"

        # === 1) Accrue HY interest ACT/365 on prior balances (credit at month start for simplicity) ===
        def hy_interest(bal):
            d = 30 if m_now not in [1,3,5,7,8,10,12] else 31
            if m_now==2: d = 29 if (y_now%4==0) else 28
            return bal * (HY_APY/365.0) * d

        hy_i_unres = hy_interest(HY_Unres)
        hy_i_rainy = hy_interest(HY_Rainy)
        hy_i_capex = hy_interest(HY_Capex)
        HY_Unres += hy_i_unres; HY_Rainy += hy_i_rainy; HY_Capex += hy_i_capex

        # === 2) Ops and reserve top-ups (simplified ops net) ===
        # For MVP we assume ops net provided/zero. Top-ups to target (monthly capex target and rainy to coverage)
        monthly_HOA = HOA_Y/12.0
        # Debt service from active loans
        ds_total = 0.0
        for u in units:
            # ACT/365 interest
            i = act365_interest(u["loan"].balance, u["loan"].rate_apr, 2000+y_now, m_now)
            pay = abs(u["loan"].payment) if (t - u["loan"].start_month_index) >= FIRST_PAY_OFFSET else 0.0
            principal = max(pay - i, 0.0)
            principal = min(principal, u["loan"].balance)
            u["loan"].balance = u["loan"].balance - principal
            ds_total += (i + principal)

        # Rainy target sized on current month costs (portfolio-wide)
        rainy_target_m = rainyMonths * (ds_total + monthly_HOA)  # insurance/tax % omitted if not provided numerically
        # Top-up rainy/capex from unrestricted cash (here, HY_Unres represents holdings; "cash" bucket is zero)
        # In this simplified runner, assume ops cash surplus is zero; top-ups not executed unless you add ops cash

        # === 3) Surplus split ===
        surplus = 0.0  # placeholder; if upstream feeds cash in, it appears here
        prepay_amt = (1.0 - savings_pct) * surplus
        hy_alloc   = savings_pct * surplus
        HY_Unres  += hy_alloc

        # === 4) Liquidity calculation and freeze ===
        liquidity_required = rainy_target_m + (capexAnnualTarget/12.0)
        liquidity_actual = HY_Rainy + HY_Capex
        liq_ratio = (liquidity_actual / liquidity_required) if liquidity_required>0 else 999.0
        # State machine
        if not freeze and liq_ratio < 1.0:
            freeze=True; freeze_enter=ym; exit_run=0
        elif freeze:
            if liq_ratio >= (1.0 + margin):
                exit_run += 1
                if exit_run >= exitN:
                    freeze=False; freeze_exit = ym; exit_run=0
            else:
                exit_run = 0

        # === 5) Purchase gate (blocked if frozen) ===
        purchase=False; PurchaseKit=0.0; accessible=0.0
        price_par = parity_price()
        down1 = acq.get("downPaymentFirst", 0.2)
        downn = acq.get("downPaymentNext", 0.2)
        down_frac = down1 if len(units)==0 else downn
        loan_pf = price_par * (1 - down_frac)
        payment = -pmt_act365(RATE, TERM, loan_pf)
        monthly_HOA_new = monthly_HOA
        initial_rainy = rainyMonths * (payment + monthly_HOA_new)
        PurchaseKit = down_frac*price_par + acq.get("closingPct",0.03)*price_par + initial_rainy

        # Accessible principal (prev-year valuation proxy = price_par for MVP)
        prev_year_val = price_par
        equity_room = max(T_LTV*prev_year_val - sum([u["loan"].balance for u in units]), 0.0)
        accessible = max(ADV*equity_room*(1.0 - COST), 0.0)

        deployable = HY_Unres + accessible
        if (not freeze) and (len(units) < pol.get("portfolio",{}).get("maxUnits", 7)) and deployable >= PurchaseKit:
            purchase=True
            # draw from HY first
            draw_hy = min(HY_Unres, PurchaseKit)
            HY_Unres -= draw_hy
            need = PurchaseKit - draw_hy
            if need > 0 and pol_pur.get("allowFeederForClosing", True):
                # conceptually from accessible principal: no explicit balance to track
                pass
            # add the new loan
            units.append({"id":f"U{len(units)+1}",
                          "price":price_par,
                          "age_m":0,
                          "loan":Loan(id=f"L{len(units)+1}", balance=loan_pf, rate_apr=RATE, term_months=TERM, start_month_index=t, payment=payment)})

        # === 6) Prepay (blocked if frozen); simple tie-break: largest balance among lowest LTV ===
        prepay_executed = 0.0
        if (not freeze) and prepay_amt>0 and len(units)>0:
            # compute LTV per unit via prev_year_val proxy
            lv = []
            for u in units:
                val = prev_year_val
                ltv = (u["loan"].balance / (val*T_LTV)) if (val*T_LTV)>0 else 999.0
                lv.append((ltv, u["loan"].balance, u))
            lv.sort(key=lambda x:(x[0], -x[1]))
            target = lv[0][2]
            amt = min(prepay_amt, target["loan"].balance)
            target["loan"].balance -= amt
            prepay_executed = amt

        row = {
            "YYYY-MM": ym,
            "HY_Unrestricted": float(cents(HY_Unres)),
            "HY_RainyReserve": float(cents(HY_Rainy)),
            "HY_CapexReserve": float(cents(HY_Capex)),
            "HY_Interest_Unres": float(cents(hy_i_unres)),
            "HY_Interest_Rainy": float(cents(hy_i_rainy)),
            "HY_Interest_Capex": float(cents(hy_i_capex)),
            "LiquidityRequired": float(cents(liquidity_required)),
            "LiquidityActual": float(cents(liquidity_actual)),
            "LiquidityRatio": float(cents(liquidity_actual / liquidity_required)) if liquidity_required>0 else 0.0,
            "FreezeFlag": 1 if freeze else 0,
            "AccessiblePrincipal": float(cents(accessible)),
            "PurchaseKit": float(cents(PurchaseKit)),
            "HY_UnresPlusAccessible": float(cents(deployable)),
            "savings_pct": savings_pct,
            "Prepay": float(cents(prepay_executed)),
            "PurchaseEvent": int(purchase),
        }
        rows.append(row)

    # write CSVs
    cols = list(rows[0].keys())
    with OUT_MONTHLY.open("w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    # Year over Year aggregate
    by = {}
    for r in rows:
        y=int(r["YYYY-MM"][1:].split("-")[0])
        by.setdefault(y, r.copy())
        for k in cols:
            if k in ["YYYY-MM","FreezeFlag","PurchaseEvent"]: continue
            if isinstance(r[k], (int,float)):
                by[y][k] += r[k] if isinstance(by[y][k], (int,float)) else 0

    out=[]
    for y in sorted(by.keys()):
        rr = {"YYYY-MM": f"Year {y}"}
        rr.update({k:by[y][k] for k in cols if k!="YYYY-MM"})
        out.append(rr)

    with OUT_YOY.open("w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)

if __name__ == "__main__":
    simulate()
