"""Minimal Goal-Structuring-Notation renderer for a `RiskNote`.

Produces an SVG via Graphviz, annotating each claim node by computed posture
(ACCEPTABLE / CONDITIONAL / BLOCKING / EXPIRED).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from graphviz import Digraph

from .models import Posture, RiskNote
from .eval import evaluate_note


_STYLE_BY_POSTURE = {
    Posture.ACCEPTABLE: {"fillcolor": "#b7e1cd", "fontcolor": "#000000"},
    Posture.CONDITIONAL: {"fillcolor": "#fff2cc", "fontcolor": "#000000"},
    Posture.BLOCKING: {"fillcolor": "#f4c7c3", "fontcolor": "#000000"},
    Posture.EXPIRED: {"fillcolor": "#d0cece", "fontcolor": "#7f7f7f"},
}


def _hash(text: str, length: int = 8) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:length]


def render(note: RiskNote, *, out_path: Optional[Path] = None) -> Path:
    """Render the note as an SVG and return the output path.

    If `out_path` is None a deterministic filename in the current working
    directory is generated based on the note id.
    """

    evaluation = evaluate_note(note)
    g = Digraph("GSN", graph_attr={"rankdir": "TB", "bgcolor": "white"})
    g.attr("node", shape="box", style="filled,rounded", fontsize="10", fontname="Helvetica")

    note_id = note.id
    g.node(note_id, label=f"Note: {note.title}")

    for claim in note.claims:
        claim_id = claim.id
        res = next(c for c in evaluation["claims"] if c["id"] == claim_id)
        style = _STYLE_BY_POSTURE[Posture(res["posture"])]
        g.node(claim_id, label=f"Claim: {claim.title}\nposture={res['posture']}", **style)
        g.edge(note_id, claim_id)

        for ev in claim.evidence:
            ev_id = _hash(ev.id)
            label = f"{ev.kind}: {ev.title or ev.id}"
            edge_style = {"color": "green" if ev.supports else "red"}
            g.node(ev_id, label=label, shape="ellipse", fontsize="9")
            g.edge(claim_id, ev_id, **edge_style)

    out_path = out_path or Path(f"gsn_{_hash(note_id)}.svg")
    g.format = "svg"
    g.render(out_path.with_suffix(""), cleanup=True)  # graphviz adds .svg
    return out_path.with_suffix(".svg")
