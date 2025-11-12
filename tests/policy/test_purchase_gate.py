import json
from pathlib import Path
from runner.run_suite_full_V23 import simulate

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")

def test_max_units_cap():
    e = json.loads(ENGINE.read_text())
    # force easy buying: reduce down payments and closing costs
    e["constants"]["acquisition"]["downPaymentFirst"] = 0.05
    e["constants"]["acquisition"]["downPaymentSubsequent"] = 0.05
    e["constants"]["acquisition"]["closingCostPct"] = 0.0
    e["policies"]["portfolio"]["maxUnits"] = 1  # hard cap 1
    rows = simulate(e, mmax=240)
    assert rows[-1]["Units Owned"] <= 1

def test_freeze_blocks_purchase_and_prepay_when_ratio_below_1():
    e = json.loads(ENGINE.read_text())
    # make rainy requirement huge to keep ratio < 1 for a while
    e["banking"]["rainyCoverageMonths"] = 12
    rows = simulate(e, mmax=12)
    for r in rows:
        if r["Liquidity Ratio"] < 1.0:
            assert r.get("Feeder Prepay", 0.0) == 0.0
            assert r.get("Purchase Out (Total)", 0.0) == 0.0
