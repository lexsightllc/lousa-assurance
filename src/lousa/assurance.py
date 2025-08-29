import json, yaml, jsonschema
from pathlib import Path
from typing import Dict, Any, Tuple
from .epistemic import KripkeModel, check_G_implies_F
from .logs import event

def load_yaml(p: str) -> Dict[str, Any]:
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate(schema_path: str, doc: Dict[str, Any]):
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=doc, schema=schema)

def build_kripke(belief_model: Dict[str, Any]) -> Tuple[KripkeModel, Dict[str, list], Dict[str, set]]:
    M = KripkeModel(belief_model["logic"], belief_model["agents"])
    for w in belief_model["worlds"]:
        M.add_world(w["id"], w["facts"])
    for e in belief_model["edges"]:
        M.add_edge(e["agent"], e["frm"], e["to"])
    graph = {}
    label = {}
    for w in belief_model["worlds"]:
        wid = w["id"]
        graph[wid] = []
        label[wid] = set(w["facts"])
    for e in belief_model["edges"]:
        graph.setdefault(e["frm"], []).append(e["to"])
    return M, graph, label

def evaluate_claims(cfg_path: str, schema_path: str) -> Dict[str, Any]:
    doc = load_yaml(cfg_path)
    validate(schema_path, doc)
    event("assurance_case_loaded", system=doc["system"]["name"], revision=doc["system"]["revision"])
    M, graph, label = build_kripke(doc["belief_model"])
    results = []
    for c in doc["claims"]:
        if c["type"] == "temporal":
            p = c["spec"]["temporal"]["p"]; q = c["spec"]["temporal"]["q"]
            ok = check_G_implies_F(graph, label, p, q)
            event("claim_checked", id=c["id"], kind="temporal", p=p, q=q, result=ok)
            results.append({"id": c["id"], "result": ok})
        else:
            op = c["spec"]["epistemic"]["op"]; agent = c["spec"]["epistemic"]["agent"]; prop = c["spec"]["epistemic"]["prop"]
            w0 = next(iter(M.worlds.keys()))
            if op == "B":
                ok = M.believes(agent, prop, w0)
            else:
                ok = M.believes_believes(agent, prop, w0)
            event("claim_checked", id=c["id"], kind="epistemic", op=op, agent=agent, prop=prop, world=w0, result=ok)
            results.append({"id": c["id"], "result": ok})
    return {"system": doc["system"], "results": results}
