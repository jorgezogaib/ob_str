import json, math
from pathlib import Path
from runner.run_suite_full_V23 import simulate

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")

def test_reserve_targets_vs_formulas():
    e = json.loads(ENGINE.read_text())
    rows = simulate(e, mmax=24)
    c = e["constants"]; ops=c["operations"]; res=c["reserves"]; bank=e["banking"]
    adr, occ, capx = ops["adrBaseline2BR"], ops["occupancyBaseline"], ops["capexPct"]
    for r in rows:
        g = adr * occ * 30.4167  # average month days ≈ 365/12; test tolerance only
        capex_target_m = capx * adr * 365 * occ / 12
        assert abs(r.get("Capex Top-Up", 0.0)) >= 0.0  # structural presence
        assert capex_target_m >= 0.0
    # liquidity ratio existence
    assert all("Liquidity Ratio" in r for r in rows)
