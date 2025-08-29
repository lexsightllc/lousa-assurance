import json, sys
from pathlib import Path
from lousa.assurance import evaluate_claims
from lousa.logs import setup_logging

if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    setup_logging(str(base / "examples" / "logging_config.yaml"))
    cfg = str(base / "examples" / "assurance_case.yaml")
    schema = str(base / "src" / "lousa" / "dsl_schema.json")
    out = evaluate_claims(cfg, schema)
    print(json.dumps(out, indent=2))
