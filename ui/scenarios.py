"""
Scenario helpers for the OB_STR UI.

The current Streamlit app (`app.py`) is self-contained and does **not** depend
on this module, but we keep a light-weight set of helpers here so other tools,
notebooks or future UIs can share a common structure without touching the core
engine or tests.

Nothing in this file is imported by the test suite; it is safe to refactor as
long as public names remain stable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Tuple

import json
import pandas as pd

from runner.run_suite_full_V23 import simulate, _build_yoy_rows


@dataclass
class ScenarioParams:
    """High-level knobs for a single scenario.

    These deliberately map to *stable* parts of the engine:

    - `starting_cash`  -> constants.financial.startingCash
    - `max_months`     -> simulation horizon (mmax)
    """

    name: str = "Base case"
    starting_cash: float | None = None
    max_months: int | None = None

    def apply_overrides(self, engine: Dict[str, Any]) -> Dict[str, Any]:
        """Return a *copy* of `engine` with this scenario's overrides applied.

        Only touches a narrow, well-understood subset of fields to avoid
        accidental divergence from the schema.
        """
        # Deep copy via JSON round-trip keeps it schema-like and simple.
        e = json.loads(json.dumps(engine))

        if self.starting_cash is not None:
            e.setdefault("constants", {}).setdefault("financial", {})[
                "startingCash"
            ] = float(self.starting_cash)

        # `max_months` is applied at simulate-call time, not into the engine.
        return e


def load_engine(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_scenario(
    engine: Dict[str, Any],
    params: ScenarioParams,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Apply `params` to `engine`, run `simulate`, and return DataFrames.

    This mirrors the behaviour in `app.py` but is UI-agnostic so it can be used
    from tests, notebooks, or other front-ends.
    """
    e = params.apply_overrides(engine)

    cal = e.get("calendar", {})
    default_horizon = int(cal.get("horizonMonths", 600))
    mmax = params.max_months or default_horizon

    rows = simulate(e, mmax)
    monthly_df = pd.DataFrame(rows)
    yoy_df = pd.DataFrame(_build_yoy_rows(rows))
    return monthly_df, yoy_df


def summarize_scenario(
    monthly_df: pd.DataFrame,
) -> Dict[str, Any]:
    """Return a light-weight summary dict for display or logging.

    This is intentionally simple and only uses columns guaranteed by
    `tests/io/test_csv_schema.py`.
    """
    if monthly_df.empty:
        return {
            "units": 0,
            "end_cash": 0.0,
            "t12_cash_from_ops": 0.0,
        }

    latest = monthly_df.iloc[-1]

    units = int(latest["Units Owned"]) if "Units Owned" in latest else 0
    end_cash = float(latest["End Cash"]) if "End Cash" in latest else 0.0

    if "Cash From Ops" in monthly_df.columns:
        t12 = float(monthly_df["Cash From Ops"].tail(12).sum())
    else:
        t12 = 0.0

    return {
        "units": units,
        "end_cash": end_cash,
        "t12_cash_from_ops": t12,
    }


__all__ = [
    "ScenarioParams",
    "load_engine",
    "run_scenario",
    "summarize_scenario",
]
