import json, time
from pathlib import Path
from runner.run_suite_full_V23 import simulate

def test_runtime_under_budget():
    engine = json.loads(Path("engines/OB_STR_ENGINE_V2_3.json").read_text())
    t0 = time.time()
    simulate(engine, mmax=240)
    dt = time.time() - t0
    assert dt < 2.5  # CI budget
