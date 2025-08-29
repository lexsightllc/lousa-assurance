import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
nb.cells = [
    nbf.v4.new_markdown_cell("# Lousa Assurance Demo Notebook"),
    nbf.v4.new_code_cell("from pathlib import Path\nfrom lousa.assurance import evaluate_claims\nfrom lousa.logs import setup_logging\nbase=Path('.').resolve()\nsetup_logging(str(base/'examples'/'logging_config.yaml'))\nres=evaluate_claims(str(base/'examples'/'assurance_case.yaml'), str(base/'src'/'lousa'/'dsl_schema.json'))\nres"),
    nbf.v4.new_code_cell("res")
]
out = Path("notebooks/lousa_demo.ipynb")
out.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, out)
print(f"Notebook written to {out}")
