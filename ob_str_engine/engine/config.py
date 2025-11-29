from pathlib import Path
import json

def load_engine_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)