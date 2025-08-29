# Lousa Assurance

This repository provides a minimal framework for evaluating temporal and epistemic assurance claims using a YAML DSL.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
```

## Run demo

```bash
python scripts/run_assurance.py
python scripts/generate_notebook.py
```

The run script emits structured logs and JSON results. The notebook generator produces `notebooks/lousa_demo.ipynb` demonstrating the same evaluation.

## Assurance CLI tests

This repository includes a lightweight CLI defined in `safety_protocol.py` with subcommands for linting, evidence freshness checks, assurance case generation and prioritization. A pytest suite exercises these commands, and the `Makefile` provides a one-shot `assure` target to create a virtual environment, install dependencies and run the tests:

```bash
make assure
```
