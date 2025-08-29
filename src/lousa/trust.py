from typing import Dict, List
from math import tanh

def propagate_trust(adj: Dict[str, List[str]], base: Dict[str, float], damping: float = 0.85, iters: int = 20) -> Dict[str, float]:
    nodes = list({*adj.keys(), *[v for vs in adj.values() for v in vs]})
    trust = {n: base.get(n, 0.5) for n in nodes}
    for _ in range(iters):
        new = {}
        for n in nodes:
            incoming = [u for u, outs in adj.items() if n in outs]
            s = sum(trust[u] for u in incoming) / max(1, len(incoming))
            new[n] = (1 - damping) * base.get(n, 0.5) + damping * s
        trust = new
    return {k: 0.5 * (tanh(3*(v-0.5)) + 1) for k, v in trust.items()}
