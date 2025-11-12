import json
import pandas as pd
from pathlib import Path

from runner.run_suite_full_V23 import simulate
from ui.lender_metrics import dscr, icr, cap_rate, breakeven_occupancy

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")

def _rows(m=120):
    e = json.loads(ENGINE.read_text())
    return simulate(e, mmax=m)

def _infer_price_from_row(row, engine):
    """Infer purchase price in a purchase month via down payment fraction."""
    dp = float(row.get("Purchase: Down Payment", 0.0))
    if dp <= 0:
        return None
    # Choose correct down payment rate based on whether it's first unit
    is_first = int(row["Units Owned"]) == 1
    acq = engine["constants"]["acquisition"]
    down_frac = acq["downPaymentFirst"] if is_first else acq["downPaymentSubsequent"]
    if down_frac <= 0:
        return None
    return dp / down_frac

def test_metrics_compute_and_are_bounded():
    e = json.loads(ENGINE.read_text())
    rows = _rows(180)
    df = pd.DataFrame(rows)

    # Use the first month AFTER first purchase to avoid zero DS cases
    purchase_idx = df.index[df["Purchase Out (Total)"] > 0]
    if len(purchase_idx) == 0:
        return  # no purchase in scenario; nothing to assert
    i0 = purchase_idx[0] + 1
    r = df.loc[i0]

    # Build inputs from row
    noi = float(r["Ops Net"]) + float(r["Debt Service (Total)"])  # Ops Net excludes DS
    ds = float(r["Debt Service (Total)"])
    interest = float(r["Interest Portion"])
    hoa = float(r["HOA"]); ins = float(r["Insurance"]); tax = float(r["Property Tax"])
    fixed = hoa + ins + tax

    # Ops settings for breakeven
    ops = e["constants"]["operations"]
    adr = float(ops["adrBaseline2BR"])
    mgmt = float(ops["mgmtPct"])
    capx = float(ops["capexPct"])
    # month length (from actual row index modulo 12)
    month_days = e["calendar"]["monthlyDays"][(i0 % 12)]

    # Assertions
    d = dscr(noi, ds)
    assert d is None or d >= 0.0

    i = icr(noi, interest)
    assert i is None or i >= 0.0

    occ_be = breakeven_occupancy(adr, month_days, mgmt, capx, fixed, ds)
    assert occ_be is None or (0.0 <= occ_be <= 1.0)

    # Cap rate only in a purchase context (infer price)
    price = _infer_price_from_row(df.loc[purchase_idx[0]], e)
    if price:
        c = cap_rate(noi * 12.0, price)
        assert c is None or (0.0 <= c <= 0.5)  # sanity bounds
