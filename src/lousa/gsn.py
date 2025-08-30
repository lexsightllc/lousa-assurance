"""Goal-Structuring-Notation (GSN) renderer for RiskNote.

This module provides functionality to generate visual representations of risk notes
using the Goal Structuring Notation (GSN). The generated diagrams show the
hierarchical relationship between claims, evidence, and investigations, with
visual indicators for risk postures and evidence strength.

Example:
    >>> from lousa.models import RiskNote
    >>> from lousa.gsn import generate_gsn_diagram
    >>> note = RiskNote.model_validate_yaml("path/to/risk_note.yaml")
    >>> output_path = generate_gsn_diagram(note, output_dir="./diagrams")

Dependencies:
    - graphviz: Python interface to Graphviz
    - pydot: Required for Graphviz Python interface
    - System installation of Graphviz (e.g., `brew install graphviz` on macOS)
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from graphviz import Digraph, Graph

from .models import EvidenceItem, Investigation, Posture, RiskNote, Claim
from .eval import evaluate_note, NoteEvaluationResult, ClaimResult

# Configure logging
logger = logging.getLogger(__name__)

# Constants for graph styling
DEFAULT_NODE_STYLE = {
    "fontname": "Helvetica",
    "fontsize": "10",
    "fontcolor": "#000000",
    "margin": "0.1,0.1",
    "width": "0",
    "height": "0",
}

# Colors from a colorblind-friendly palette
COLORS = {
    "background": "#FFFFFF",
    "border": "#000000",
    "evidence_weak": "#E1EDF5",  # Light blue
    "evidence_strong": "#4E98D1",  # Blue
    "investigation": "#F8D7A3",  # Light orange
    "assumption": "#F0F0F0",  # Light gray
    "note": "#F5F5F5",  # Off-white
}


# Style definitions for different node types
_STYLE_BY_POSTURE = {
    Posture.ACCEPTABLE: {
        "fillcolor": "#B7E1CD",  # Light green
        "fontcolor": "#0A5C36",  # Dark green
        "color": "#0A5C36",
        "penwidth": "1.5",
    },
    Posture.CONDITIONAL: {
        "fillcolor": "#FFF2CC",  # Light yellow
        "fontcolor": "#8C6B0A",  # Dark yellow
        "color": "#8C6B0A",
        "penwidth": "1.5",
    },
    Posture.BLOCKING: {
        "fillcolor": "#F4C7C3",  # Light red
        "fontcolor": "#8B0000",  # Dark red
        "color": "#8B0000",
        "penwidth": "2.0",
    },
    Posture.EXPIRED: {
        "fillcolor": "#F0F0F0",  # Light gray
        "fontcolor": "#666666",  # Medium gray
        "color": "#999999",
        "penwidth": "1.0",
        "style": "filled,dashed",
    },
}

# Style for evidence nodes based on strength
_EVIDENCE_STRENGTH_STYLES = {
    "weak": {
        "fillcolor": COLORS["evidence_weak"],
        "color": COLORS["border"],
        "style": "filled,rounded",
    },
    "strong": {
        "fillcolor": COLORS["evidence_strong"],
        "color": COLORS["border"],
        "style": "filled,rounded,bold",
        "penwidth": "1.5",
    },
}

# Style for investigation nodes
_INVESTIGATION_STYLE = {
    "shape": "octagon",
    "fillcolor": COLORS["investigation"],
    "style": "filled,rounded",
    "color": "#8B5A2B",  # Brown
    "fontcolor": "#000000",
}

# Style for assumption nodes
_ASSUMPTION_STYLE = {
    "shape": "note",
    "fillcolor": COLORS["assumption"],
    "style": "filled,rounded,dashed",
    "color": "#666666",
    "fontcolor": "#333333",
}


class GraphDirection(str, Enum):
    """Supported graph directions for GSN diagrams."""
    TOP_DOWN = "TB"  # Top to bottom (default)
    BOTTOM_UP = "BT"  # Bottom to top
    LEFT_RIGHT = "LR"  # Left to right
    RIGHT_LEFT = "RL"  # Right to left


def _hash(text: str, length: int = 8) -> str:
    """Generate a deterministic hash from a string.
    
    Args:
        text: Input string to hash
        length: Length of the hash to return (max 64 for SHA-256)
        
    Returns:
        A hexadecimal string of the specified length
    """
    return hashlib.sha256(text.encode()).hexdigest()[:length]


def _format_text(text: str, max_length: int = 40) -> str:
    """Format text for display in graph nodes.
    
    Args:
        text: The text to format
        max_length: Maximum length before truncation
        
    Returns:
        Formatted text with newlines and truncation
    """
    if not text:
        return ""
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if necessary
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text


def _format_evidence_strength(lr_plus: float, lr_minus: float) -> str:
    """Determine the strength of evidence based on likelihood ratios."""
    # Calculate the weight of evidence (log-odds)
    weight = abs((1 - lr_minus) / lr_minus) * lr_plus
    
    if weight > 10:  # Strong evidence
        return "strong"
    return "weak"  # Weak or neutral evidence


def generate_gsn_diagram(
    note: RiskNote,
    output_dir: Union[str, Path] = ".",
    format: str = "svg",
    direction: GraphDirection = GraphDirection.TOP_DOWN,
    show_evidence: bool = True,
    show_investigations: bool = True,
    show_metadata: bool = True,
    now: Optional[datetime] = None,
) -> Path:
    """Generate a GSN diagram from a RiskNote.
    
    Args:
        note: The risk note to visualize
        output_dir: Directory to save the output file
        format: Output format (e.g., 'svg', 'png', 'pdf')
        direction: Direction of the graph layout
        show_evidence: Whether to include evidence nodes
        show_investigations: Whether to include investigation nodes
        show_metadata: Whether to include metadata in the graph
        now: Reference time for temporal calculations
        
    Returns:
        Path to the generated diagram file
        
    Raises:
        FileNotFoundError: If output directory doesn't exist
        RuntimeError: If Graphviz fails to render the diagram
    """
    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    elif not output_dir.is_dir():
        raise FileNotFoundError(f"Output path is not a directory: {output_dir}")
    
    # Evaluate the note to get current postures
    evaluation = evaluate_note(note, now=now)
    
    # Create a new directed graph
    graph_attrs = {
        "rankdir": direction.value,
        "bgcolor": COLORS["background"],
        "fontname": "Helvetica",
        "fontsize": "12",
        "ranksep": "0.5",
        "nodesep": "0.3",
    }
    
    g = Digraph(
        name="GSN",
        graph_attr=graph_attrs,
        node_attr={
            "shape": "box",
            "style": "filled,rounded",
            "fontname": "Helvetica",
            "fontsize": "10",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "arrowsize": "0.7",
        },
    )
    
    # Add a title/subgraph for better layout control
    with g.subgraph(name="cluster_title") as c:
        c.attr(
            style="invis",  # Hide the subgraph border
            margin="20",
        )
        title_id = f"note_{_hash(note.id)}"
        c.node(
            title_id,
            label=f"{note.title}\n{note.id}",
            shape="box",
            style="filled,rounded,bold",
            fillcolor=COLORS["note"],
            fontsize="14",
            margin="0.2,0.1",
        )
    
    # Add claims
    for claim in note.claims:
        _add_claim_to_graph(g, claim, evaluation, show_evidence, show_investigations)
    
    # Add metadata if requested
    if show_metadata:
        _add_metadata(g, note, evaluation, now)
    
    # Render the graph to a file
    output_path = output_dir / f"{note.id}_gsn"
    try:
        rendered_path = g.render(
            filename=output_path,
            format=format,
            cleanup=True,
            view=False,
        )
        return Path(rendered_path)
    except Exception as e:
        raise RuntimeError(f"Failed to render GSN diagram: {e}")


def _add_claim_to_graph(
    graph: Digraph,
    claim: Claim,
    evaluation: NoteEvaluationResult,
    show_evidence: bool = True,
    show_investigations: bool = True,
) -> None:
    """Add a claim and its supporting elements to the graph."""
    # Find the evaluation result for this claim
    claim_result = next((c for c in evaluation["claims"] if c.id == claim.id), None)
    if not claim_result:
        logger.warning(f"No evaluation result found for claim: {claim.id}")
        return
    
    # Add the claim node
    posture = claim_result.posture
    style = _STYLE_BY_POSTURE.get(posture, {})
    
    # Format the label with HTML for better formatting
    label = (
        f'<<table border="0" cellborder="0" cellspacing="2">'
        f'<tr><td align="left" border="1" bgcolor="{style.get("fillcolor", "white")}" '
        f'color="{style.get("color", "black")}" port="port1">'
        f'<font point-size="12"><b>{_format_text(claim.title)}</b></font>'
    )
    
    # Add posterior probability if available
    if hasattr(claim_result, 'posterior'):
        label += f'</td></tr><tr><td align="left">Posterior: {claim_result.posterior:.1%}</td></tr>'
    
    # Add threshold information
    if claim.threshold_conditional is not None and claim.threshold_blocking is not None:
        label += (
            f'</td></tr><tr><td align="left">'
            f'Thresholds: Cond={claim.threshold_conditional:.1%}, Block={claim.threshold_blocking:.1%}'
            f'</td></tr>'
        )
    
    label += "</table>>"
    
    # Add the claim node with HTML label
    graph.node(
        claim.id,
        label=label,
        shape="box",
        style=style.get("style", "filled,rounded"),
        fillcolor=style.get("fillcolor", "white"),
        color=style.get("color", "black"),
        fontcolor=style.get("fontcolor", "black"),
        penwidth=style.get("penwidth", "1.0"),
    )
    
    # Add evidence if enabled
    if show_evidence and claim.evidence:
        _add_evidence_to_graph(graph, claim, claim_result)
    
    # Add investigations if enabled
    if show_investigations and claim.investigations:
        _add_investigations_to_graph(graph, claim, claim_result)

        for ev in claim.evidence:
            ev_id = _hash(ev.id)

def _add_evidence_to_graph(
    graph: Digraph,
    claim: Claim,
    claim_result: ClaimResult,
) -> None:
    """Add evidence nodes and edges to the graph for a claim."""
    if not claim.evidence:
        return
    
    # Group evidence by kind
    evidence_by_kind: Dict[str, List[EvidenceItem]] = {}
    for evidence in claim.evidence:
        evidence_by_kind.setdefault(evidence.kind, []).append(evidence)
    
    # Add evidence groups as subgraphs
    for kind, evidence_items in evidence_by_kind.items():
        with graph.subgraph(name=f"cluster_{claim.id}_{kind}") as c:
            c.attr(
                label=f"{kind.upper()} Evidence",
                style="rounded,filled",
                color="#CCCCCC",
                bgcolor="#F9F9F9",
                fontname="Helvetica",
                fontsize="9",
                margin="10",
            )
            
            for evidence in evidence_items:
                # Find this evidence's contribution in the evaluation
                contribution = next(
                    (cont for cont in claim_result.contributions 
                     if cont.evidence_id == evidence.id),
                    None
                )
                
                # Determine evidence strength
                strength = _format_evidence_strength(
                    evidence.lr_plus,
                    evidence.lr_minus,
                )
                style = _EVIDENCE_STRENGTH_STYLES.get(strength, {})
                
                # Format the evidence label
                label = f"{_format_text(evidence.description, 30)}"
                if contribution:
                    label += f"\nΔlog-odds: {contribution.delta_log_odds:+.2f}"
                
                # Add the evidence node
                evidence_id = f"{claim.id}_evidence_{_hash(evidence.id)}"
                c.node(
                    evidence_id,
                    label=label,
                    shape="box",
                    **style,
                )
                
                # Add edge from evidence to claim
                graph.edge(evidence_id, claim.id, style="solid")


def _add_investigations_to_graph(
    graph: Digraph,
    claim: Claim,
    claim_result: ClaimResult,
) -> None:
    """Add investigation nodes and edges to the graph for a claim."""
    if not claim.investigations:
        return
    
    with graph.subgraph(name=f"cluster_{claim.id}_investigations") as c:
        c.attr(
            label="Investigations",
            style="rounded,filled,dashed",
            color="#999999",
            bgcolor="#F5F5F5",
            fontname="Helvetica",
            fontsize="9",
            margin="10",
        )
        
        for inv in claim.investigations:
            inv_id = f"{claim.id}_investigation_{_hash(inv.id)}"
            
            # Format the investigation label
            label = (
                f"{_format_text(inv.title, 30)}\n"
                f"Cost: {inv.cost_hours}h | "
                f"Expected Δp: {inv.expected_delta:+.2f}"
            )
            
            # Add the investigation node
            c.node(
                inv_id,
                label=label,
                **_INVESTIGATION_STYLE,
            )
            
            # Add edge from claim to investigation
            graph.edge(claim.id, inv_id, style="dashed")


def _add_metadata(
    graph: Digraph,
    note: RiskNote,
    evaluation: NoteEvaluationResult,
    now: Optional[datetime] = None,
) -> None:
    """Add metadata to the graph as a footer."""
    now = now or datetime.now().astimezone()
    
    # Create a timestamp string
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # Add a footer with metadata
    footer_id = "footer"
    graph.node(
        footer_id,
        label=(
            f"Generated: {timestamp}\n"
            f"Overall Posture: {evaluation['overall_posture'].name}"
        ),
        shape="box",
        style="filled,rounded",
        fillcolor="#F0F0F0",
        fontsize="8",
        margin="0.1,0.05",
    )
    
    # Make sure the footer is at the bottom
    if graph.body:
        last_node = graph.body[-1].split(' ')[1].strip('[]')
        graph.edge(last_node, footer_id, style="invis")
