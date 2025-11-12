# tools/update_golden.py
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

from runner.run_suite_full_V23 import simulate  # uses default engine on disk
from runner.run_suite_full_V23 import _build_yoy_rows  # YoY = sum flows, snapshot stocks

REPO = Path(__file__).resolve().parents[1]
GOLDEN = REPO / "golden"
GOLDEN.mkdir(exist_ok=True)

def cents(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def normalize_rows(rows):
    out=[]
    for r in rows:
        z={}
        for k,v in r.items():
            if isinstance(v,(int,float)):
                z[k]=cents(v)
            else:
                z[k]=v
        out.append(z)
    return out

def main():
    # 1) monthly (first 12)
    rows = simulate(json.loads((REPO/"engines/OB_STR_ENGINE_V2_3.json").read_text()), mmax=240)
    monthly_first12 = normalize_rows(rows[:12])
    (GOLDEN/"monthly_first12.json").write_text(json.dumps(monthly_first12, indent=2))

    # 2) yoy (first 3) — use runner’s YoY builder to keep definition in one place
    yoy = _build_yoy_rows(rows)[:3]
    yoy = normalize_rows(yoy)
    (GOLDEN/"yoy_first3.json").write_text(json.dumps(yoy, indent=2))

    # 3) manifest
    manifest = {
        "runner": "run_suite_full_V23.py",
        "policy": "YoY: sum flows, snapshot stocks",
        "count_months": len(rows),
        "count_yoy": len(yoy),
    }
    (GOLDEN/"manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Golden snapshots updated:", ["monthly_first12.json","manifest.json","yoy_first3.json"])

if __name__ == "__main__":
    main()
