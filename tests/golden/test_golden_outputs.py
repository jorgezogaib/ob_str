import json
from pathlib import Path
from decimal import Decimal
from runner.run_suite_full_V23 import simulate

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")
GOLDEN_DIR = Path("golden")

def _cents(x):
    return Decimal(str(x)).quantize(Decimal("0.01"))

def _rows(m=240):
    e = json.loads(ENGINE.read_text())
    return simulate(e, mmax=m)

def _normalize(rows, n):
    out = []
    for r in rows[:n]:
        o = {}
        for k, v in r.items():
            if isinstance(v, (int, float)):
                o[k] = float(_cents(v))
            else:
                o[k] = v
        out.append(o)
    return out

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

    # quick re-rollup (reuse update_golden approach)
    rows = _rows()
    yoy = {}
    for r in rows:
        y = int(str(r["YYYY-MM"]).split("-")[0][1:])
        agg = yoy.setdefault(y, {})
        for k, v in r.items():
            if k in ("YYYY-MM", "UnitID"):
                continue
            if isinstance(v, (int, float)):
                agg[k] = agg.get(k, 0.0) + v
    out = []
    for y in sorted(yoy.keys())[:3]:
        row = {"YYYY-MM": f"Year {y}", "UnitID": "TOTAL"}
        for k, v in yoy[y].items():
            row[k] = float(_cents(v))
        out.append(row)

    assert out == golden, "YoY first3 differs from golden snapshot. If intentional, regenerate golden."
