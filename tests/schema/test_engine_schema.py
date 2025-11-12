import json
from pathlib import Path
from jsonschema import validate, Draft202012Validator

SCHEMA = json.loads(Path("schema/engine_v2_3.json").read_text())
ENGINE = json.loads(Path("engines/OB_STR_ENGINE_V2_3.json").read_text())

def test_engine_schema_validates():
    Draft202012Validator.check_schema(SCHEMA)
    validate(instance=ENGINE, schema=SCHEMA)
