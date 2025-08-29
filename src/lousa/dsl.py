import yaml
from .models import RiskNote

def load_risknote(path: str) -> RiskNote:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RiskNote.model_validate(raw)
