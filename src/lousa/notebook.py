"""Generate a reproducible Jupyter notebook that walks through evaluation results."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import nbformat as nbf

from .eval import evaluate_note
from .gsn import render as render_gsn
from .models import RiskNote


_TEMPLATE_INTRO = """# Lousa Assurance Notebook\n\nThis notebook is auto-generated and walks through the evaluation of a risk note.\n"""


def generate(note: RiskNote, *, out_path: Optional[Path] = None) -> Path:
    """Create the notebook and return its path."""

    nb = nbf.v4.new_notebook()
    nb["cells"].append(nbf.v4.new_markdown_cell(_TEMPLATE_INTRO))

    # evaluation cell
    evaluation = evaluate_note(note)
    nb["cells"].append(
        nbf.v4.new_code_cell(
            """from lousa import eval as lousa_eval, models as M\n"""
            """from pathlib import Path, read_text\n"""
        )
    )
    nb["cells"].append(
        nbf.v4.new_markdown_cell("## Evaluation JSON")
    )
    nb["cells"].append(nbf.v4.new_code_cell(f"evaluation = {json.dumps(evaluation, indent=2)}\nevaluation"))

    # GSN rendering
    svg_path = render_gsn(note)
    nb["cells"].append(nbf.v4.new_markdown_cell("## Goal-Structuring Notation"))
    nb["cells"].append(
        nbf.v4.new_markdown_cell(f"<img src='{svg_path}' width='800px'>")  # noqa: S608
    )

    out_path = out_path or Path(f"lousa_{note.id}.ipynb")
    nbf.write(nb, out_path)
    return out_path
