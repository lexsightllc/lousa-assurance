import logging, logging.config, yaml, time, json
from pathlib import Path

def setup_logging(cfg_path: str):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logging.config.dictConfig(cfg)

def event(name: str, **fields):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": name, **fields}
    logging.getLogger("lousa").info(json.dumps(rec))
    return rec
