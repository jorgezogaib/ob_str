import json, time
from pathlib import Path
from ob_str_engine.compat import simulate

def test_runtime_under_budget():
    engine = json.loads(Path("ob_str_engine/OB_STR_ENGINE_V2_3.json").read_text())
    t0 = time.time()
    simulate(engine, mmax=240)
    dt = time.time() - t0
    assert dt < 2.5  # CI budget
