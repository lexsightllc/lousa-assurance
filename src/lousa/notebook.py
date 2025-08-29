import nbformat as nbf
from pathlib import Path


def generate_notebook(yaml_text: str, eval_results: dict, gsn_svg_path: str, out_ipynb: str):
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_markdown_cell("# Lousa Assurance — Reproducible Evaluation"))
    nb.cells.append(nbf.v4.new_code_cell("import json, textwrap\nprint('Frozen environment captured at runtime.')"))
    nb.cells.append(nbf.v4.new_markdown_cell("## Source YAML"))
    nb.cells.append(nbf.v4.new_code_cell(f"yaml_text = '''\\\n{yaml_text}\n'''\nprint(yaml_text)"))
    nb.cells.append(nbf.v4.new_markdown_cell("## Evaluation Results"))
    nb.cells.append(nbf.v4.new_code_cell(f"ev = {eval_results!r}\nimport json\nprint(json.dumps(ev, indent=2))"))
    nb.cells.append(nbf.v4.new_markdown_cell("## GSN Artifact"))
    nb.cells.append(nbf.v4.new_code_cell(
        f"from IPython.display import SVG, display\nsvg_path = '{gsn_svg_path}'\ndisplay(SVG(filename=svg_path))"
    ))
    Path(out_ipynb).parent.mkdir(parents=True, exist_ok=True)
    with open(out_ipynb, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
