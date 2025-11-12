# tests/golden/test_golden_outputs.py
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

from runner.run_suite_full_V23 import simulate, _build_yoy_rows

REPO = Path(__file__).resolve().parents[2]
GOLDEN_DIR = REPO / "golden"
ENGINE = REPO / "engines" / "OB_STR_ENGINE_V2_3.json"

def _cents(x):
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _normalize(rows, n=None):
    rows = rows if n is None else rows[:n]
    out=[]
    for r in rows:
        z={}
        for k,v in r.items():
            z[k] = float(_cents(v)) if isinstance(v,(int,float)) else v
        out.append(z)
    return out

def _rows(mmax=240):
    return simulate(json.loads(ENGINE.read_text()), mmax=mmax)

def test_golden_monthly_first12_exists_and_matches():
    p = GOLDEN_DIR / "monthly_first12.json"
    assert p.exists(), "Golden snapshot missing. Run: python tools/update_golden.py"
    golden = json.loads(p.read_text())
    curr = _normalize(_rows(), 12)
    assert curr == golden, "Monthly first12 differs from golden snapshot. If intentional, regenerate golden."

def test_golden_yoy_first3_exists_and_matches():
    p = GOLDEN_DIR / "yoy_first3.json"
    assert p.exists(), "Golden snapshot missing. Run: python tools/update_golden.py"
    golden = json.loads(p.read_text())
    rows = _rows()
    curr = _normalize(_build_yoy_rows(rows), 3)
    assert curr == golden, "YoY first3 differs from golden snapshot. If intentional, regenerate golden."
