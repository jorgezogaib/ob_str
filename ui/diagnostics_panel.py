# ui/diagnostics_panel.py
import json
import pandas as pd
from pathlib import Path
from ui.lender_metrics import dscr, icr, cap_rate, breakeven_occupancy

def _first_purchase_index(df: pd.DataFrame):
    idx = df.index[df["Purchase Out (Total)"] > 0.0]
    return int(idx[0]) if len(idx) else None

def _next_ready_index(df: pd.DataFrame, start_idx: int):
    # Heuristic: first month after purchase where Liquidity Ratio >= 1.0
    if start_idx is None:
        return None
    post = df.iloc[start_idx+1:]
    idx = post.index[post["Liquidity Ratio"] >= 1.0]
    return int(idx[0]) if len(idx) else None

def _gate_breakdown(df_row: pd.Series):
    return {
        "Down Payment": float(df_row.get("Purchase: Down Payment", 0.0)),
        "Closing Costs": float(df_row.get("Purchase: Closing Costs", 0.0)),
        "Initial Rainy Funding": float(df_row.get("Purchase: Initial Rainy Funding", 0.0)),
        "Gate Total": float(df_row.get("Purchase Out (Total)", 0.0)),
    }

def _infer_price_at_purchase(purchase_row: pd.Series, engine: dict) -> float | None:
    dp = float(purchase_row.get("Purchase: Down Payment", 0.0))
    if dp <= 0:
        return None
    units_owned = int(purchase_row.get("Units Owned", 0))
    is_first = units_owned == 1
    acq = engine["constants"]["acquisition"]
    down_frac = acq["downPaymentFirst"] if is_first else acq["downPaymentSubsequent"]
    if down_frac <= 0:
        return None
    return dp / down_frac

def _metrics_at_row(r: pd.Series, engine: dict, purchase_price: float | None):
    # NOI here = Ops Net + DS (since Ops Net already subtracted DS)
    noi_m = float(r["Ops Net"]) + float(r["Debt Service (Total)"])
    ds_m = float(r["Debt Service (Total)"])
    int_m = float(r["Interest Portion"])
    adr = float(engine["constants"]["operations"]["adrBaseline2BR"])
    mgmt = float(engine["constants"]["operations"]["mgmtPct"])
    capx = float(engine["constants"]["operations"]["capexPct"])
    # fixed monthly costs (non-DS)
    fixed = float(r["HOA"]) + float(r["Insurance"]) + float(r["Property Tax"])
    # pick month length from calendar using month index
    # fallback: if not supplied by UI, assume 30
    monthly_days = 30.0

    return {
        "DSCR": dscr(noi_m, ds_m),
        "ICR": icr(noi_m, int_m),
        "Breakeven Occ": breakeven_occupancy(adr, monthly_days, mgmt, capx, fixed, ds_m),
        "Cap Rate (if price known)": (cap_rate(noi_m * 12.0, purchase_price) if purchase_price else None),
    }

def render(st, engine_path="engines/OB_STR_ENGINE_V2_3.json", csv_path="runner/V2_3_Monthly.csv"):
    st.header("Diagnostics")

    engine = json.loads(Path(engine_path).read_text())
    df = pd.read_csv(csv_path)

    fp_idx = _first_purchase_index(df)
    nr_idx = _next_ready_index(df, fp_idx) if fp_idx is not None else None

    st.subheader("Acquisitions Timeline")
    if fp_idx is None:
        st.info("No purchase occurred in current run.")
        return

    fp_row = df.loc[fp_idx]
    st.write(f"**First Purchase:** {fp_row['YYYY-MM']}  |  Units Owned: {int(fp_row['Units Owned'])}")

    gate = _gate_breakdown(fp_row)
    st.json(gate)

    # Metrics: month after purchase to avoid DS=0 edge cases
    after_idx = fp_idx + 1 if (fp_idx + 1) in df.index else fp_idx
    m_row = df.loc[after_idx]
    purchase_price = _infer_price_at_purchase(fp_row, engine)
    metrics = _metrics_at_row(m_row, engine, purchase_price)

    st.subheader("Lender Metrics (Month after purchase)")
    st.json(metrics)

    if nr_idx is not None:
        nr_row = df.loc[nr_idx]
        st.subheader("Next-Ready Month (Liquidity)")
        st.write(f"**Next Ready:** {nr_row['YYYY-MM']}  |  Liquidity Ratio: {round(float(nr_row['Liquidity Ratio']), 3)}")
    else:
        st.info("Next-ready month not met within timeline.")
