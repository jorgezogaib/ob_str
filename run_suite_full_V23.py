import os, json, csv, math
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

ENGINE = Path("/mnt/data/OB_STR_ENGINE_V2_3.json")
OUT_MONTHLY = Path("/mnt/data/V2_3_Monthly.csv")
OUT_YOY     = Path("/mnt/data/V2_3_YearOverYear.csv")
MAX_MONTHS = 240

def cents(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def pmt(rate_m, nper, pv):
    return -(rate_m*pv)/(1-(1+rate_m)**(-nper)) if rate_m!=0 else -(pv/nper)

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
        interest = self.balance * self.rate_m
        principal = max(min(self.pmt_amt - interest, self.balance), 0.0)
        self.balance -= principal
        self.n_left = max(self.n_left - 1, 0)
        return self.pmt_amt, principal, interest

    def prepay(self, amount):
        amt = max(min(amount, self.balance), 0.0)
        self.balance -= amt
        # keep payment constant; shorten term
        if self.balance>0 and self.rate_m>0 and self.pmt_amt>0:
            r = self.rate_m; B = self.balance; P = self.pmt_amt
            try:
                n_est = -math.log(max(1 - r*B/P, 1e-12))/math.log(1+r)
                self.n_left = max(int(math.ceil(n_est)), 0)
            except Exception:
                pass
        else:
            self.n_left = 0
        return amt

def load_eng(p: Path):
    assert p.exists(), f"Engine not found at {p}"
    return json.loads(p.read_text())

def parity_price(ADR,OCC,HOA_Y,MGMT,CAPX,INS,TAX,TARGET):
    g = ADR*365*OCC
    numer = g - (g*(MGMT+CAPX) + HOA_Y)
    denom = TARGET + INS + TAX
    return max(numer/denom, 0.0)

def simulate(e, mmax=MAX_MONTHS):
    C=e["constants"]; cal=e["calendar"]; B=e.get("banking",{})
    fin=C["financial"]; ops=C["operations"]; acq=C["acquisition"]; debt=C["debt"]; res=C["reserves"]
    market = e.get("market", {}); portfolio = e.get("portfolio", {"maxLoans":7})

    ADR=ops["adrBaseline2BR"]; OCC=ops["occupancyBaseline"]; MGMT=ops["mgmtPct"]; CAPX=ops["capexPct"]
    HOA_Y0=ops["hoaAnnual"]; HOA_INF=ops.get("hoaInflationRate",0.0)
    INS=ops["insuranceRate"]; TAX=ops["propertyTaxRate"]; TARGET=acq["targetYieldUnlevered"]
    APP=market.get("annualAppreciation",0.03)

    start_cash=fin["startingCash"]; annual_sav=fin["annualSavings"]; amort_yrs=fin["amortizationYears"]
    RATE=debt["mortgageRate"]; CLOSE=acq["closingCostPct"]; DOWN1=acq["downPaymentFirst"]; DOWNN=acq["downPaymentSubsequent"]
    rainyMonths=B.get("rainyCoverageMonths",0); CAPEX_M=res["capexMonthsTarget"]; mdays=cal["monthlyDays"]

    y=1; m=1; HOA_Y=HOA_Y0
    cash=start_cash; savings_in=annual_sav/12.0
    units=[]; next_unit_id = 1; rows=[]

    def parity(H): return parity_price(ADR,OCC,H,MGMT,CAPX,INS,TAX,TARGET)

    for t in range(1, mmax+1):
        if m==1 and t>1: HOA_Y *= (1+HOA_INF)
        days=mdays[m-1]
        price_par = parity(HOA_Y) * ((1+APP)**((y-1)+(m-1)/12.0))

        ops_gross=ops_mgmt=ops_capex=ops_hoa=ops_ins=ops_tax=0.0
        ds_total=interest_total=principal_total=0.0
        for u in units:
            gross=ADR*OCC*days; mgmt=gross*MGMT; capex_op=gross*CAPX
            hoa=HOA_Y/12.0; ins=u["price"]*INS/12.0; tax=u["price"]*TAX/12.0
            ops_gross+=gross; ops_mgmt+=mgmt; ops_capex+=capex_op; ops_hoa+=hoa; ops_ins+=ins; ops_tax+=tax
            if u["loan"].balance>0 and u["loan"].n_left>0:
                P,PR,IN = u["loan"].accrue()
                ds_total+=P; principal_total+=PR; interest_total+=IN
        ops_net = ops_gross - (ops_mgmt + ops_capex + ops_hoa + ops_ins + ops_tax + ds_total)
        cash_prefeeder = cash + savings_in + ops_net

        # ---- Purchase ----
        purchase=False; pur_dp=pur_cl=pur_rainy=0.0; pur_total=0.0; new_loan_principal=0.0
        if len(units) < portfolio.get("maxLoans",7) and price_par>0:
            down_frac = DOWN1 if len(units)==0 else DOWNN
            loan_pf = price_par*(1 - down_frac)
            rate_m = RATE/12.0
            ds_pf = -pmt(rate_m, amort_yrs*12, loan_pf)
            hoa_pf = HOA_Y/12.0
            pur_dp = down_frac * price_par
            pur_cl = CLOSE * price_par
            pur_rainy = rainyMonths * (ds_pf + hoa_pf)
            gate_req = pur_dp + pur_cl + pur_rainy
            if cash_prefeeder >= gate_req:
                cash_prefeeder -= gate_req
                purchase=True; pur_total=gate_req; new_loan_principal=loan_pf
                units.append({"id":f"U{next_unit_id}","price":price_par,"loan":Loan(f"U{next_unit_id}", loan_pf, RATE, amort_yrs)})
                next_unit_id += 1

        # ---- Feeder ----
        feeder=0.0
        if len(units)>0:
            feeder_eligible = max(cash_prefeeder, 0.0)
            if feeder_eligible>0:
                target = max(units, key=lambda u:u["loan"].balance)
                feeder = target["loan"].prepay(min(feeder_eligible, target["loan"].balance))
                cash_prefeeder -= feeder

        end_cash = cash_prefeeder

        rows.append({
            "YYYY-MM": f"Y{y}-{m:02d}",
            "UnitID": "TOTAL",
            "Starting Cash": round(cash,2),
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
            "Feeder Prepay": round(feeder,2),
            "Purchase: Down Payment": round(pur_dp,2),
            "Purchase: Closing Costs": round(pur_cl,2),
            "Purchase: Initial Rainy Funding": round(pur_rainy,2),
            "Purchase Out (Total)": round(pur_total,2),
            "New Loan Principal": round(new_loan_principal,2),
            "Loan Balance (End)": round(sum(u["loan"].balance for u in units),2),
            "End Cash": round(end_cash,2)
        })

        cash = end_cash
        m += 1
        if m>12: m=1; y+=1
    return rows

if __name__ == "__main__":
    print("CWD:", os.getcwd())
    print("Engine path:", ENGINE, "exists:", ENGINE.exists())
    print("Will write:", OUT_MONTHLY, OUT_YOY)
    e = load_eng(ENGINE)
    rows = simulate(e, mmax=MAX_MONTHS)

    # ---- Tests ----
    # T-DS-1: DS > 0 after purchase
    ds_pos=False; purchase_seen=False
    for r in rows:
        if r["Purchase Out (Total)"]>0: purchase_seen=True
        elif purchase_seen and r["Debt Service (Total)"]>0: ds_pos=True; break
    assert ds_pos, "T-DS-1 FAIL: no DS>0 after purchase"

    # T-AMORT-1: prev_end - principal - feeder + new_loan = curr_end (±0.01)
    for i in range(1,len(rows)):
        prev, curr = rows[i-1], rows[i]
        lhs = cents(prev["Loan Balance (End)"]) - cents(curr["Scheduled Principal"]) - cents(curr["Feeder Prepay"]) + cents(curr.get("New Loan Principal",0.0))
        rhs = cents(curr["Loan Balance (End)"])
        assert abs(lhs - rhs) <= Decimal("0.01"), f"T-AMORT-1 FAIL {curr['YYYY-MM']} lhs={lhs} rhs={rhs}"

    # T-CASH-1: Cash identity
    for r in rows:
        lhs = cents(r["End Cash"])
        rhs = (cents(r["Starting Cash"]) + cents(r["Savings In"]) + cents(r["Ops Net"])
              - cents(r["Feeder Prepay"]) - cents(r["Purchase Out (Total)"]))
        assert abs(lhs - rhs) <= Decimal("0.01"), f"T-CASH-1 FAIL {r['YYYY-MM']}"

    # Write outputs
    if rows:
        cols=list(rows[0].keys())
        with OUT_MONTHLY.open("w",newline="") as f:
            w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
        # simple YOY rollup
        from collections import defaultdict
        agg, last_by_year = defaultdict(lambda:{k:Decimal("0.00") for k in cols}), {}
        for r in rows:
            y=int(r["YYYY-MM"][1:].split("-")[0])
            last_by_year[y]=r
            for k,v in r.items():
                if k in ["YYYY-MM","UnitID"]: continue
                if isinstance(v,(int,float)): agg[y][k]+=Decimal(str(v))
        out=[]
        for y in sorted(agg.keys()):
            a=agg[y]; last=last_by_year[y]
            row={k:(float(a[k]) if isinstance(a[k],Decimal) else a[k]) for k in a}
            row["YYYY-MM"]=f"Year {y}"; row["UnitID"]="TOTAL"
            for k in ["End Cash","Loan Balance (End)"]: row[k]=last[k]
            out.append(row)
        with OUT_YOY.open("w",newline="") as f:
            w=csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
    print("DONE")
