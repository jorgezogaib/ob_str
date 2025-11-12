import json
import pandas as pd
from pathlib import Path
from runner.run_suite_full_V23 import simulate
from ui.diagnostics import first_purchase, next_ready, gate_breakdown

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")

def test_diagnostics_basic_paths():
    e = json.loads(ENGINE.read_text())
    rows = simulate(e, mmax=120)
    df = pd.DataFrame(rows)
    fp = first_purchase(df)  # may be None if parity never clears; shouldn't error
    if fp is not None:
        idx, yyyymm, total = fp
        assert isinstance(idx, int) and isinstance(yyyymm, str) and total > 0.0
        nr = next_ready(df, start_idx=idx)
        assert nr is None or (isinstance(nr[0], int) and nr[2] >= 1.0)

def test_gate_breakdown_sums_when_purchase_occurs():
    e = json.loads(ENGINE.read_text())
    rows = simulate(e, mmax=240)
    df = pd.DataFrame(rows)
    fp = first_purchase(df)
    if fp is not None:
        idx = fp[0]
        bd = gate_breakdown(df.loc[idx])
        assert abs(bd["components_sum"] - bd["total"]) < 1e-6
