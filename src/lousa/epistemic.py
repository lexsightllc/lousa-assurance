from dataclasses import dataclass
from typing import Dict, Set, List

@dataclass(frozen=True)
class World:
    id: str
    facts: Set[str]

class KripkeModel:
    def __init__(self, logic: str, agents: List[str]):
        self.logic = logic
        self.agents = set(agents)
        self.worlds: Dict[str, World] = {}
        self.rel: Dict[str, Dict[str, Set[str]]] = {a:{} for a in self.agents}

    def add_world(self, world_id: str, facts: List[str]):
        self.worlds[world_id] = World(world_id, set(facts))

    def add_edge(self, agent: str, frm: str, to: str):
        if agent not in self.rel: self.rel[agent] = {}
        self.rel[agent].setdefault(frm, set()).add(to)

    def successors(self, agent: str, w: str) -> Set[str]:
        return self.rel.get(agent, {}).get(w, set())

    def holds(self, prop: str, w: str) -> bool:
        return prop in self.worlds[w].facts

    def believes(self, agent: str, prop: str, w: str) -> bool:
        for v in self.successors(agent, w):
            if not self.holds(prop, v):
                return False
        return True

    def believes_believes(self, agent: str, prop: str, w: str) -> bool:
        for v in self.successors(agent, w):
            if not self.believes(agent, prop, v):
                return False
        return True

def check_G_implies_F(graph: Dict[str, List[str]], label: Dict[str, Set[str]], p: str, q: str) -> bool:
    from collections import deque
    for node in graph:
        if p in label.get(node, set()):
            visited = set([node])
            dq = deque([node])
            reachable_q = False
            while dq:
                u = dq.popleft()
                if q in label.get(u, set()):
                    reachable_q = True
                    break
                for v in graph.get(u, []):
                    if v not in visited:
                        visited.add(v)
                        dq.append(v)
            if not reachable_q:
                return False
    return True
