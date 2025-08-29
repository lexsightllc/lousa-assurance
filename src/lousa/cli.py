"""Lousa command-line interface.

Usage::

    lousa validate examples/latency_risk.yaml
    lousa run examples/latency_risk.yaml --out results.json
    lousa schema --out risk_note.schema.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from importlib import resources as importlib_resources

from .eval import evaluate_note
from .models import RiskNote
from .notebook import generate as generate_notebook
from .provenance import capture as capture_provenance, dump_json as dump_prov_json

app = typer.Typer(help="Lousa assurance CLI")


@app.command()
def validate(path: Path):
    """Validate a YAML risk note against the JSON Schema."""
    with path.open() as f:
        data = yaml.safe_load(f)
    RiskNote.model_validate(data)  # raises if invalid
    typer.echo("✓ Validation succeeded", err=True)


@app.command()
def run(path: Path, out: Optional[Path] = typer.Option(None, help="Write JSON result here")):
    """Evaluate a note, save JSON and notebook, print posture."""
    with path.open() as f:
        note_data = yaml.safe_load(f)
    note = RiskNote.model_validate(note_data)

    result = evaluate_note(note)
    if out:
        out.write_text(json.dumps(result, indent=2))
        typer.echo(f"JSON written to {out}", err=True)

    nb_path = generate_notebook(note)
    typer.echo(f"Notebook written to {nb_path}", err=True)

    prov = capture_provenance(path)
    dump_prov_json(prov, Path(f"provenance_{note.id}.json"))

    typer.echo(f"Posture: {result['posture']}")


@app.command()
def schema(out: Optional[Path] = typer.Option(None, help="Path to write the JSON Schema")):
    """Emit the packaged JSON Schema to stdout or a file (portable)."""
    pkg = "lousa"
    name = "schemas/risk_note.schema.json"
    with importlib_resources.files(pkg).joinpath(name).open("r") as f:
        schema_txt = f.read()
    if out:
        out.write_text(schema_txt)
        typer.echo(f"Schema written to {out}", err=True)
    else:
        sys.stdout.write(schema_txt)
