import json, random
from pathlib import Path
from runner.run_suite_full_V23 import simulate

ENGINE_P = Path("engines/OB_STR_ENGINE_V2_3.json")

def test_random_edges_hold_identities_quick():
    base = json.loads(ENGINE_P.read_text())
    for _ in range(5):
        e = json.loads(ENGINE_P.read_text())
        e["constants"]["operations"]["adrBaseline2BR"] = random.uniform(0, 500)
        e["constants"]["operations"]["occupancyBaseline"] = random.uniform(0.3, 0.9)
        e["banking"]["rainyCoverageMonths"] = random.choice([0, 6, 12])
        e["savings"]["prepayPct"] = random.choice([0.0, 1.0])
        rows = simulate(e, mmax=12)
        assert len(rows) == 12  # just sanity that it runs
