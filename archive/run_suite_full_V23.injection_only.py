# see previous cell for full content placeholder; writing again
import csv, json, math
from dataclasses import dataclass
from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
from datetime import date, timedelta

ENGINE = Path("OB_STR_ENGINE_V2_3.MVP.json")
OUT_MONTHLY = Path("V2_3_Monthly.csv")
OUT_YOY     = Path("V2_3_YearOverYear.csv")
MAX_MONTHS = 240

def cents(x): return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

def pmt_act365(rate_yr, n_months, principal):
    rate_m = rate_yr/12.0
    if rate_m == 0: return -(principal/n_months)
    return -(rate_m*principal)/(1-(1+rate_m)**(-n_months))

@dataclass
class Loan:
    id: str
    balance: float
    rate_apr: float
    term_months: int
    start_month_index: int
    payment: float

def load_engine(p: Path):
    return json.loads(Path(p).read_text())

def days_in_month(y,m):
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

    HY_Unres = float(start.get("HY_Unrestricted",0.0))
    HY_Rainy = float(start.get("HY_RainyReserve",0.0))
    HY_Capex = float(start.get("HY_CapexReserve",0.0))
    HY_APY   = float(sav.get("annualYield",0.0))
    savings_pct = float(sav.get("allocationPctToSavings",0.0))

    annual_savings = float(ops.get("annualSavings", 0.0))
    monthly_injection_nominal = annual_savings / 12.0

    units=[]
    next_unit_id = 1

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

    rows=[]
    for t in range(MAX_MONTHS):
        y_now = 1 + (t//12)
        m_now = 1 + (t%12)
        ym = f"Y{y_now:01d}-{m_now:02d}"

        def hy_interest(bal, y, m):
            d = days_in_month(2000+y, m)
            return bal * (HY_APY/365.0) * d
        hy_i_unres = hy_interest(HY_Unres, y_now, m_now)
        hy_i_rainy = hy_interest(HY_Rainy, y_now, m_now)
        hy_i_capex = hy_interest(HY_Capex, y_now, m_now)
        HY_Unres += hy_i_unres; HY_Rainy += hy_i_rainy; HY_Capex += hy_i_capex

        # NEW MONEY INJECTION
        NewMoneyIn = monthly_injection_nominal
        HY_Unres += NewMoneyIn

        ds_total = 0.0
        monthly_HOA = HOA_Y/12.0
        for u in units:
            def act365_interest(balance, apr, y, m):
                from calendar import monthrange
                d = monthrange(2000+y, m)[1]
                return balance * (apr/365.0) * d
            i = act365_interest(u["loan"].balance, u["loan"].rate_apr, y_now, m_now)
            pay = abs(u["loan"].payment) if (t - u["loan"].start_month_index) >= FIRST_PAY_OFFSET else 0.0
            principal = max(pay - i, 0.0)
            principal = min(principal, u["loan"].balance)
            u["loan"].balance -= principal
            ds_total += (i + principal)

        rainy_target_m = rainyMonths * (ds_total + monthly_HOA)

        surplus = 0.0
        prepay_amt = (1.0 - savings_pct) * surplus
        hy_alloc   = savings_pct * surplus
        HY_Unres  += hy_alloc

        liquidity_required = rainy_target_m + (capexAnnualTarget/12.0)
        liquidity_actual = HY_Rainy + HY_Capex
        liq_ratio = (liquidity_actual / liquidity_required) if liquidity_required>0 else 999.0
        freeze = 1 if liq_ratio < 1.0 else 0

        price_par = parity_price()
        down1 = acq.get("downPaymentFirst", 0.2)
        downn = acq.get("downPaymentNext", 0.2)
        down_frac = down1 if len(units)==0 else downn
        loan_pf = price_par * (1 - down_frac)
        payment = -pmt_act365(RATE, TERM, loan_pf)
        initial_rainy = rainyMonths * (payment + monthly_HOA)
        PurchaseKit = down_frac*price_par + acq.get("closingPct",0.03)*price_par + initial_rainy

        accessible = 0.0
        deployable = HY_Unres + accessible
        purchase = 1 if (freeze==0 and deployable >= PurchaseKit) else 0

        row = {
            "YYYY-MM": ym,
            "HY_Unrestricted": float(cents(HY_Unres)),
            "HY_RainyReserve": float(cents(HY_Rainy)),
            "HY_CapexReserve": float(cents(HY_Capex)),
            "HY_Interest_Unres": float(cents(hy_i_unres)),
            "HY_Interest_Rainy": float(cents(hy_i_rainy)),
            "HY_Interest_Capex": float(cents(hy_i_capex)),
            "NewMoneyIn": float(cents(NewMoneyIn)),
            "LiquidityRequired": float(cents(liquidity_required)),
            "LiquidityActual": float(cents(liquidity_actual)),
            "LiquidityRatio": float(cents(liq_ratio)) if liquidity_required>0 else 0.0,
            "FreezeFlag": freeze,
            "AccessiblePrincipal": float(cents(accessible)),
            "PurchaseKit": float(cents(PurchaseKit)),
            "HY_UnresPlusAccessible": float(cents(deployable)),
            "savings_pct": savings_pct,
            "Prepay": float(cents(0.0)),
            "PurchaseEvent": purchase,
        }
        rows.append(row)

    cols = list(rows[0].keys())
    with open(OUT_MONTHLY, "w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    by = {}
    for r in rows:
        y=int(r["YYYY-MM"][1:].split("-")[0])
        agg = by.setdefault(y, {k:0 for k in cols})
        for k,v in r.items():
            if k=="YYYY-MM": continue
            if isinstance(v,(int,float)): agg[k]+=v
        agg["YYYY-MM"]=f"Year {y}"
    out=[by[y] for y in sorted(by.keys())]
    with open(OUT_YOY, "w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)

if __name__ == "__main__":
    simulate()
