import json
from pathlib import Path
from decimal import Decimal
from runner.run_suite_full_V23 import simulate, cents

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")

def _rows(m=36):
    e = json.loads(ENGINE.read_text())
    return simulate(e, mmax=m)

def test_cash_identity_36m():
    rows = _rows(36)
    for r in rows:
        lhs = cents(r["End Cash"])
        # before (wrong): counted rainy/capex interest as cash inflow
        rhs = (cents(r["Starting Cash"]) + cents(r["Savings In"]) + cents(r["Ops Net"])
               + cents(r.get("HY Interest (Cash)", 0.0))  # keep this
               # remove these two:
               # + cents(r.get("HY Interest (Rainy)", 0.0)) + cents(r.get("HY Interest (Capex)", 0.0))
               + cents(r.get("Feeder Draw (Net)", 0.0))
               - cents(r.get("Feeder Prepay", 0.0)) - cents(r.get("Purchase Out (Total)", 0.0))
               - cents(r.get("Rainy Top-Up", 0.0)) - cents(r.get("Capex Top-Up", 0.0)))

        assert abs(lhs - rhs) <= Decimal("0.01"), f"Cash identity fail {r['YYYY-MM']}"

def test_amortization_identity_36m():
    rows = _rows(36)
    for i in range(1, len(rows)):
        prev, curr = rows[i-1], rows[i]
        lhs = cents(prev["Loan Balance (End)"]) - cents(curr["Scheduled Principal"]) - cents(curr.get("Feeder Prepay", 0.0)) + cents(curr.get("New Loan Principal", 0.0))
        rhs = cents(curr["Loan Balance (End)"])
        assert abs(lhs - rhs) <= Decimal("0.01"), f"Amort identity fail {curr['YYYY-MM']}"
