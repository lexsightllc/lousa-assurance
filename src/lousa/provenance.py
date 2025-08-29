"""Provenance capture utilities for Lousa.

Computes SHA-256 for a YAML note, captures git commit, Python version,
package versions, and a compact `pip freeze` list to ensure the evaluation
is reproducible and auditable.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pkg_resources


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> Optional[str]:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return None


def _pip_freeze(max_lines: int = 100) -> List[str]:
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], timeout=10)
        lines = out.decode().splitlines()
        return lines[:max_lines]
    except Exception:
        return []


def capture(note_path: pathlib.Path) -> Dict:
    """Return a provenance dictionary for the given YAML note path."""

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "note_sha256": _sha256(note_path),
        "note_path": str(note_path),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "git_commit": _git_commit(),
        "package_versions": {d.project_name: d.version for d in pkg_resources.working_set},
        "pip_freeze_head": _pip_freeze(),
    }


def dump_json(prov: Dict, out_path: pathlib.Path) -> pathlib.Path:
    out_path.write_text(json.dumps(prov, indent=2, sort_keys=True))
    return out_path
