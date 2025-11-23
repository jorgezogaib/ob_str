"""
Streamlit UI for OB_STR engine (V2.3)

Minimal, test-aligned app that:

- Loads the canonical engine JSON from `engines/OB_STR_ENGINE_V2_3.json`
- Calls `simulate` from `runner.run_suite_full_V23`
- Builds both monthly and year-over-year DataFrames
- Renders a simple scenario panel without touching test contracts
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import pandas as pd
import streamlit as st

from runner.run_suite_full_V23 import simulate, _build_yoy_rows

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_ENGINE_PATH = PROJECT_ROOT / "engines" / "OB_STR_ENGINE_V2_3.json"


# ---------------------------------------------------------------------------
# Engine loading
# ---------------------------------------------------------------------------

def load_engine(path: Path | str) -> dict:
    """Load an engine JSON file into a dict.

    This is intentionally lightweight – schema validation is handled elsewhere
    (tests + CLI). The UI assumes it is given a known-good engine.
    """
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def _load_engine_cached(path_str: str) -> dict:
    """Streamlit-cached wrapper around `load_engine`.

    `streamlit`'s cache requires hashable arguments, so we take a string path.
    """
    return load_engine(Path(path_str))


def _get_default_horizon_months(engine: dict) -> int:
    cal = engine.get("calendar", {})
    # Fall back to 600 months if the engine ever omits this field.
    return int(cal.get("horizonMonths", 600))


# ---------------------------------------------------------------------------
# Simulation plumbing
# ---------------------------------------------------------------------------

def run_model(
    engine: dict,
    max_months: int | None = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Run the core engine and return (monthly_df, yoy_df).

    This is a thin, UI-oriented wrapper around `simulate` and `_build_yoy_rows`.
    It does **not** mutate the engine.
    """
    mmax = max_months or _get_default_horizon_months(engine)
    rows = simulate(engine, mmax)

    monthly_df = pd.DataFrame(rows)
    yoy_rows = _build_yoy_rows(rows)
    yoy_df = pd.DataFrame(yoy_rows)

    return monthly_df, yoy_df


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _render_kpi_row(monthly_df: pd.DataFrame) -> None:
    """Render a small KPI strip using columns that are guaranteed by tests.

    We only touch columns that are enforced in `tests/io/test_csv_schema.py` to
    avoid coupling the UI to fragile or derived names.
    """
    if monthly_df.empty:
        st.info("No results to display – simulation returned 0 rows.")
        return

    latest = monthly_df.iloc[-1]

    col1, col2, col3, col4 = st.columns(4)

    # End Cash
    if "End Cash" in latest:
        col1.metric("End Cash (last month)", f"{latest['End Cash']:,.0f}")

    # Units Owned
    if "Units Owned" in latest:
        col2.metric("Units Owned", int(latest["Units Owned"]))

    # Net Income (last 12 months approx) – if available
    if "Cash From Ops" in monthly_df.columns:
        trailing = monthly_df["Cash From Ops"].tail(12).sum()
        col3.metric("Trailing 12m Cash From Ops", f"{trailing:,.0f}")

    # DSCR proxy – if we have both NOI and Debt Service style columns
    if {"Cash From Ops", "Debt Service"}.issubset(monthly_df.columns):
        ds = monthly_df["Cash From Ops"].tail(12).sum()
        debt = monthly_df["Debt Service"].tail(12).sum()
        if debt:
            col4.metric("Approx DSCR (T12)", f"{ds / debt:0.2f}")


def scenario_panel() -> None:
    """Top-level Streamlit layout for the scenario runner.

    This keeps to a single-page MVP:
    - Engine selector (today: fixed default engine)
    - Horizon selector
    - Run button
    - KPIs + monthly and YoY tables
    """
    st.title("OB_STR Scenario Runner (V2.3)")

    # Load engine once per session
    with st.sidebar:
        st.header("Engine / Scenario")

        engine_path = st.text_input(
            "Engine JSON path",
            value=str(DEFAULT_ENGINE_PATH),
            help="Path to a valid engine JSON. Default is the canonical V2.3.",
        )

        engine = _load_engine_cached(engine_path)

        max_months_default = _get_default_horizon_months(engine)
        max_months = st.slider(
            "Horizon (months)",
            min_value=60,
            max_value=600,
            value=max_months_default,
            step=12,
            help="Maximum months to simulate.",
        )

        run_clicked = st.button("Run scenario", type="primary")

    if not run_clicked:
        st.info("Adjust options in the sidebar and click **Run scenario**.")
        return

    try:
        monthly_df, yoy_df = run_model(engine, max_months=max_months)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Simulation failed: {exc}")
        st.stop()

    # KPIs
    _render_kpi_row(monthly_df)

    st.subheader("Monthly results")
    st.dataframe(monthly_df, use_container_width=True, height=400)

    st.subheader("Year-over-year rollup")
    st.dataframe(yoy_df, use_container_width=True, height=300)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(
        page_title="OB_STR Scenario Runner",
        layout="wide",
    )
    scenario_panel()


if __name__ == "__main__":
    main()
