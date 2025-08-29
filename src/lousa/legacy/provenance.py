import hashlib, platform, importlib.metadata, subprocess, json
from datetime import datetime
from typing import Dict


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
    except Exception:
        return None


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def provenance(meta: Dict[str,str], yaml_text: str) -> Dict:
    deps = {d: importlib.metadata.version(d) for d in [
        "pydantic","PyYAML","numpy","scipy","networkx","graphviz","typer","structlog","nbformat"
    ] if importlib.metadata.version}
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "python": platform.python_version(),
        "git_commit": git_commit(),
        "dependencies": deps,
        "yaml_sha256": digest_bytes(yaml_text.encode("utf-8")),
        "meta": meta
    }
