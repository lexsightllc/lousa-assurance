import subprocess, shutil, tempfile, os
from pathlib import Path
from typing import Optional
from .logs import event

def nuXmv_available() -> bool:
    return shutil.which("nuXmv") is not None

def run_nuxmv(model_path: str) -> Optional[str]:
    if not nuXmv_available():
        event("nuxmv_skipped", reason="nuXmv not found on PATH")
        return None
    cmd = ["nuXmv", "-source", "-"]
    script = f'read_model -i {model_path}\ngo\ncheck_ltlspec\nquit\n'
    with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as p:
        out, _ = p.communicate(script)
    event("nuxmv_ran", model=model_path)
    return out
