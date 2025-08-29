import graphviz
from .models import RiskNote


def gsn_dot(note: RiskNote, eval_results: dict) -> graphviz.Digraph:
    dot = graphviz.Digraph("GSN", graph_attr={"rankdir": "TB"})
    dot.node("G0", f"Goal: {note.title}")
    for r in eval_results["claims"]:
        cid = r["claim_id"]
        posture = r["posture"]
        goal_id = f"G_{cid}"
        dot.node(goal_id, f"Goal: {cid}\nposture={posture}")
        dot.edge("G0", goal_id)
        strat_id = f"S_{cid}"
        dot.node(strat_id, "Strategy: Argue via evidence and thresholds")
        dot.edge(goal_id, strat_id)
        for c in r["contributions"]:
            ev_id = f"Sn_{c['evidence_id']}"
            delta = round(c["delta_logodds"], 3)
            dot.node(ev_id, f"Solution: Evidence {c['evidence_id']}\nΔlogodds={delta}")
            dot.edge(strat_id, ev_id)
    return dot


def export_svg(note: RiskNote, eval_results: dict, out_path: str) -> str:
    dot = gsn_dot(note, eval_results)
    svg_path = dot.render(out_path, format="svg", cleanup=True)
    return svg_path
