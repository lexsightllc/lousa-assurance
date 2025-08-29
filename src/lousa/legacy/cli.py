import json, pathlib
from datetime import datetime
import typer, structlog, yaml
from .dsl import load_risknote
from .eval import evaluate
from .gsn import export_svg
from .notebook import generate_notebook
from .provenance import provenance

app = typer.Typer()
log = structlog.get_logger()


@app.command()
def run(yaml_path: str, outdir: str = "runs"):
    note = load_risknote(yaml_path)
    now = datetime.utcnow()
    results = evaluate(note, now)
    with open(yaml_path, "r", encoding="utf-8") as f:
        ytxt = f.read()
    prov = provenance({"note_id": note.id}, ytxt)
    out = {"provenance": prov, "results": results}
    out_dir = pathlib.Path(outdir) / note.id
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "assurance.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    svg_path = export_svg(note, results, str(out_dir / "gsn"))
    generate_notebook(ytxt, results, svg_path, str(out_dir / "lousa_demo.ipynb"))
    log.info("assurance_complete", note_id=note.id, posture=results["posture"], json=str(json_path), gsn=svg_path)


@app.command()
def validate(yaml_path: str):
    _ = load_risknote(yaml_path)
    typer.echo("YAML is valid against the DSL schema.")


if __name__ == "__main__":
    app()
