import json, subprocess, sys, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
CLI = str(ROOT / "safety_protocol.py")
SCHEMA = str(ROOT / "risk_note.schema.json")
NOTE = str(ROOT / "risk-note-47.yaml")  # the repository has this file at the root

def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, CLI, *args], cwd=ROOT, text=True, capture_output=True)

def test_lint_against_schema_succeeds():
    cp = run("lint", NOTE, "--schema", SCHEMA)
    assert cp.returncode == 0, cp.stderr + cp.stdout

def test_evidence_freshness_with_lenient_policy_passes():
    cp = run("check-evidence", NOTE, "--max-age", "P365D")
    assert cp.returncode == 0, cp.stderr + cp.stdout

def test_generate_assurance_case_outputs_graph_text():
    cp = run("generate-assurance-case", NOTE)
    assert cp.returncode == 0, cp.stderr + cp.stdout
    # The README shows a graph with "Goal:" as the prefix of the main node; check for it.
    assert "Goal:" in cp.stdout or "Goal" in cp.stdout

def test_prioritize_runs_with_budget_flag():
    # The README demonstrates "prioritize" with --budget in ISO-8601 hours; we use the existing risk note.
    cp = run("prioritize", ".", "--budget", "PT40H")
    assert cp.returncode == 0, cp.stderr + cp.stdout
