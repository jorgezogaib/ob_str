import io, json
from copy import deepcopy

import pandas as pd
import streamlit as st

# Import simulator without triggering __main__
import runner.run_suite_full_V23 as simmod

st.set_page_config(page_title="OB STR – MVP Runner (V2_3)", layout="wide")

st.title("OB STR – MVP Runner (V2_3)")
st.caption("Edit engine constants → Run → Review monthly & YoY → Download results")

# ============ Engine loader ============

col1, col2 = st.columns([1,1], gap="large")
with col1:
    src_mode = st.radio(
        "Engine source",
        ["Use file path", "Upload JSON"],
        index=0,
        horizontal=True,
    )
with col2:
    default_path = "engines/OB_STR_ENGINE_V2_3.json"
    engine_path = st.text_input("Engine file path", default_path, disabled=(src_mode=="Upload JSON"))

uploaded = None
engine_obj = None
load_ok = False
load_err = None

if src_mode == "Upload JSON":
    uploaded = st.file_uploader("Upload engine JSON", type=["json"])
    if uploaded:
        try:
            engine_obj = json.load(uploaded)
            load_ok = True
            st.success("Engine loaded from upload.")
        except Exception as e:
            load_err = str(e)
            st.error(f"Invalid JSON: {e}")
else:
    try:
        engine_obj = simmod.load_eng(simmod.Path(engine_path))
        load_ok = True
        st.success(f"Loaded engine from: {engine_path}")
    except AssertionError as ae:
        load_err = str(ae)
        st.error(load_err)
    except Exception as e:
        load_err = str(e)
        st.error(f"Failed to load: {e}")

if not load_ok:
    st.stop()

# Work on a mutable copy
e = deepcopy(engine_obj)

# ============ Editable constants UI ============
st.divider()
st.subheader("Edit engine constants")

def numeric_editor_dict(section_name: str, d: dict, help_map=None):
    """
    Render number inputs for numeric leaf fields in dict d.
    Returns updated dict.
    """
    if help_map is None:
        help_map = {}
    changed = False
    out = deepcopy(d)
    for k, v in d.items():
        key_label = f"{section_name}.{k}"
        if isinstance(v, (int, float)):
            # Decide sensible step
            step = 0.01
            if abs(v) >= 1000:
                step = 10.0
            elif 0 < abs(v) < 1:
                step = 0.001
            new_v = st.number_input(
                key_label,
                value=float(v),
                step=step,
                help=help_map.get(k, None)
            )
            if new_v != v:
                out[k] = float(new_v)
                changed = True
        elif isinstance(v, dict):
            with st.expander(f"{key_label} (nested)", expanded=False):
                out[k] = numeric_editor_dict(f"{section_name}.{k}", v, help_map=help_map.get(k, {}))
        else:
            # Non-numeric leaves are shown but not edited here
            st.text(f"{key_label}: {v}")
    return out

# Known editable sections (present in your engine)
sections = []
for name in ["constants","calendar","banking","market","portfolio"]:
    if name in e:
        sections.append(name)

colA, colB = st.columns(2, gap="large")
left, right = colA, colB

# Helpers for tooltips if you want (optional)
HELP = {
    "constants": {
        "operations": {
            "adrBaseline2BR": "Average daily rate assumption.",
            "occupancyBaseline": "Occupancy (0-1).",
            "mgmtPct": "Management % of gross.",
            "capexPct": "CapEx % of gross.",
            "hoaAnnual": "Annual HOA per unit.",
            "hoaInflationRate": "Annual HOA inflator."
        },
        "acquisition": {
            "targetYieldUnlevered": "Unlevered target yield used in parity price.",
            "downPaymentFirst": "Down % on first purchase.",
            "downPaymentSubsequent": "Down % on later purchases.",
            "closingCostPct": "Closing costs as % of price."
        },
        "debt": {
            "mortgageRate": "APR (decimal).",
            "amortizationYears": "Amort term in years."
        },
        "financial": {
            "startingCash": "Initial cash.",
            "annualSavings": "New cash each year."
        },
        "reserves": {
            "capexMonthsTarget": "Months of capex target held."
        }
    },
    "banking": {
        "rainyCoverageMonths": "Months of DS+HOA for rainy-day.",
        "seasoningMonths": "Months before refi/advance allowed.",
        "advanceRate": "Advance rate on accessible principal.",
        "cashoutCostPct": "Refi/cash-out friction as %.",
        "initialBufferMonths": "Extra rainy buffer months at purchase.",
        "initialCapExBufferMonths": "Capex buffer months at purchase.",
        "opsCashFloorMonths": "Ops floor = months of (DS+HOA).",
        "refiLTVTrigger": "LTV threshold to enable accessibility."
    },
    "market": {
        "annualAppreciation": "Annual appreciation used to grow parity price."
    },
    "portfolio": {
        "maxLoans": "Cap for number of concurrent loans."
    }
}

# constants sub-sections laid out nicely
if "constants" in e:
    st.markdown("### constants")
    c = e["constants"]
    subcols = st.columns(2, gap="large")

    with subcols[0]:
        if "financial" in c:
            st.markdown("**constants.financial**")
            c["financial"] = numeric_editor_dict("constants.financial", c["financial"], HELP["constants"].get("financial", {}))
        if "operations" in c:
            st.markdown("**constants.operations**")
            c["operations"] = numeric_editor_dict("constants.operations", c["operations"], HELP["constants"].get("operations", {}))

    with subcols[1]:
        if "acquisition" in c:
            st.markdown("**constants.acquisition**")
            c["acquisition"] = numeric_editor_dict("constants.acquisition", c["acquisition"], HELP["constants"].get("acquisition", {}))
        if "debt" in c:
            st.markdown("**constants.debt**")
            c["debt"] = numeric_editor_dict("constants.debt", c["debt"], HELP["constants"].get("debt", {}))
        if "reserves" in c:
            st.markdown("**constants.reserves**")
            c["reserves"] = numeric_editor_dict("constants.reserves", c["reserves"], HELP["constants"].get("reserves", {}))

# banking / market / portfolio
st.markdown("### other sections")
two = st.columns(2, gap="large")
with two[0]:
    if "banking" in e:
        st.markdown("**banking**")
        e["banking"] = numeric_editor_dict("banking", e["banking"], HELP.get("banking", {}))
    if "market" in e:
        st.markdown("**market**")
        e["market"] = numeric_editor_dict("market", e["market"], HELP.get("market", {}))
with two[1]:
    if "portfolio" in e:
        st.markdown("**portfolio**")
        e["portfolio"] = numeric_editor_dict("portfolio", e["portfolio"], HELP.get("portfolio", {}))

st.divider()

# ============ Run controls ============
st.subheader("Run controls")
rcol1, rcol2, rcol3 = st.columns([1,1,2])
with rcol1:
    max_months = st.number_input("Max months", 1, 600, value=240, step=1)
with rcol2:
    # Your simulate currently stops only via mmax; readiness stop handled internally in V2_3.
    stop_note = st.caption("Readiness stop is enforced inside your simulator when present.")

run_btn = st.button("▶ Run with edited constants", type="primary")

# ============ Run + Show ============
monthly_df_slot = st.empty()
yoy_df_slot = st.empty()
dl_cols = st.columns(2)

def rollup_yoy(rows):
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["_Year"] = df["YYYY-MM"].str.extract(r"Y(\d+)-", expand=False).astype(int)

    # fields to take the last value of within the year
    snapshot_fields = ["End Cash", "Loan Balance (End)", "Units Owned"]   # <- include Units Owned

    # sum everything numeric except helper + snapshot fields
    sum_cols = df.select_dtypes(include=["number"]).columns.tolist()
    for c in ["_Year"] + snapshot_fields:
        if c in sum_cols:
            sum_cols.remove(c)

    agg = df.groupby("_Year")[sum_cols].sum()
    last_vals = (
        df.sort_values(["_Year", "YYYY-MM"])
          .groupby("_Year")[snapshot_fields]
          .last()
    )

    out = pd.concat([agg, last_vals], axis=1).reset_index()
    out.insert(0, "YYYY-MM", out["_Year"].apply(lambda y: f"Year {y}"))
    out.insert(1, "UnitID", "TOTAL")
    out.drop(columns=["_Year"], inplace=True)

    # Optional: ensure Units Owned is int
    if "Units Owned" in out.columns:
        out["Units Owned"] = out["Units Owned"].astype(int)

    # Column order (put Units Owned near the front)
    monthly_cols = list(rows[0].keys())
    preferred = ["YYYY-MM", "UnitID", "Units Owned"]
    order = preferred + [c for c in monthly_cols if c not in preferred]
    out = out.reindex(columns=[c for c in order if c in out.columns])
    return out

if run_btn:
    try:
        # Respect max months
        simmod.MAX_MONTHS = int(max_months)
        rows = simmod.simulate(e, mmax=int(max_months))

        if not rows:
            st.warning("Simulation returned no rows.")
        else:
            monthly_df = pd.DataFrame(rows)
            yoy_df = rollup_yoy(rows)

            st.subheader("Monthly timeline")
            monthly_df_slot.dataframe(monthly_df, use_container_width=True, height=430)

            st.subheader("Year-over-Year (rolled up)")
            yoy_df_slot.dataframe(yoy_df, use_container_width=True, height=360)

            with dl_cols[0]:
                buf = io.StringIO()
                monthly_df.to_csv(buf, index=False)
                st.download_button("⬇ Download Monthly CSV", buf.getvalue(), "V2_3_Monthly.csv", "text/csv")

            with dl_cols[1]:
                buf2 = io.StringIO()
                yoy_df.to_csv(buf2, index=False)
                st.download_button("⬇ Download YoY CSV", buf2.getvalue(), "V2_3_YearOverYear.csv", "text/csv")

            st.success("Run complete.")
    except AssertionError as ae:
        st.error(f"Assertion failed: {ae}")
    except Exception as ex:
        st.exception(ex)

st.divider()
# ============ Save/Download edited engine ============
st.subheader("Save edited engine")
save_cols = st.columns(2)
with save_cols[0]:
    if st.button("💾 Write to engines/OB_STR_ENGINE_V2_3_EDITED.json"):
        outp = "engines/OB_STR_ENGINE_V2_3_EDITED.json"
        try:
            simmod.Path(outp).write_text(json.dumps(e, indent=2))
            st.success(f"Wrote: {outp}")
        except Exception as ex:
            st.error(f"Write failed: {ex}")
with save_cols[1]:
    as_text = json.dumps(e, indent=2)
    st.download_button("⬇ Download edited engine.json", as_text, file_name="OB_STR_ENGINE_V2_3_EDITED.json", mime="application/json")

# app.py snippet
import streamlit as st
from ui.diagnostics_panel import render as render_diagnostics

st.sidebar.header("Panels")
if st.sidebar.checkbox("Diagnostics", value=True):
    render_diagnostics(st, "engines/OB_STR_ENGINE_V2_3.json", "runner/V2_3_Monthly.csv")
