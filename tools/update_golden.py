# tools/update_golden.py
import json, csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from runner.run_suite_full_V23 import simulate

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")
GOLDEN_DIR = Path("golden")

def q2(x):  # two-decimal quantize to stabilize snapshots
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def main():
    e = json.loads(ENGINE.read_text())
    rows = simulate(e, mmax=240)

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    # Save first 12 monthly rows
    head12 = [{k: (q2(v) if isinstance(v, (int, float)) else v) for k, v in r.items()} for r in rows[:12]]
    Path(GOLDEN_DIR / "monthly_first12.json").write_text(json.dumps(head12, indent=2))

    # Roll up to YoY (lightweight – mirrors runner logic enough for snapshot)
    cols = list(rows[0].keys())
    yoy = {}
    for r in rows:
        y = int(str(r["YYYY-MM"]).split("-")[0][1:])
        agg = yoy.setdefault(y, {})
        for k, v in r.items():
            if k in ("YYYY-MM", "UnitID"):
                continue
            if isinstance(v, (int, float)):
                agg[k] = agg.get(k, 0.0) + v
    # Keep only first 3 years
    out = []
    for y in sorted(yoy.keys())[:3]:
        row = {"YYYY-MM": f"Year {y}", "UnitID": "TOTAL"}
        row.update({k: q2(v) for k, v in yoy[y].items()})
        out.append(row)
    Path(GOLDEN_DIR / "yoy_first3.json").write_text(json.dumps(out, indent=2))

    # Manifest for traceability
    manifest = {
        "engine_version": e.get("version"),
        "engine_path": str(ENGINE),
        "rows_captured": {"monthly_first12": len(head12), "yoy_first3": len(out)}
    }
    Path(GOLDEN_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("Golden snapshots updated:", [p.name for p in (GOLDEN_DIR).glob("*.json")])

if __name__ == "__main__":
    main()
