from typing import Dict

TRAIT_WEIGHTS = {
    "O": 0.20,
    "C": 0.25,
    "E": 0.10,
    "A": 0.15,
    "N": -0.10
}

def trait_weighted_reasoning(traits: Dict[str, float]) -> float:
    s = 0.0
    for k, w in TRAIT_WEIGHTS.items():
        s += w * traits.get(k, 0.5)
    lo, hi = -0.10*1.0 + 0.20*0.0, 0.25*1.0 + 0.20*1.0 + 0.15*1.0 + 0.10*1.0
    val = (s - lo) / (hi - lo)
    return max(0.0, min(1.0, val))
