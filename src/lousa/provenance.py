"""Provenance capture and management for Lousa risk assessments.

This module provides functionality to capture and manage execution context,
environment details, and dependency information to ensure full reproducibility
and auditability of risk evaluations.

Key Features:
- Captures execution environment (Python version, platform, timestamp)
- Tracks code state via Git commit hashes
- Records package versions and dependencies
- Computes content hashes for input files
- Provides human-readable and machine-readable output formats

Example:
    >>> from pathlib import Path
    >>> from lousa.provenance import capture_provenance, format_provenance
    
    # Capture provenance for a risk note
    prov = capture_provenance(Path("path/to/risk_note.yaml"))
    
    # Get formatted output
    print(format_provenance(prov))
    
    # Save to file
    Path("provenance.json").write_text(json.dumps(prov, indent=2))
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import pathlib
import platform
import re
import socket
import subprocess
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Try to get package versions with fallback for missing packages

def _get_package_versions(packages: list[str]) -> Dict[str, str]:
    """Get version information for a list of packages with graceful fallback."""
    versions = {}
    for pkg in packages:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "not installed"
    return versions


def _get_system_info() -> Dict[str, Any]:
    """Collect system and environment information."""
    return {
        "hostname": socket.gethostname(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
            "executable": sys.executable,
        },
        "environment": {
            "cwd": os.getcwd(),
            "user": os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
            "path": os.environ.get("PATH", "").split(os.pathsep),
        },
    }


def _get_git_info() -> Dict[str, Any]:
    """Collect Git repository information if available."""
    try:
        repo_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        
        return {
            "repository": {
                "root": repo_root,
                "commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip(),
                "branch": subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip(),
                "dirty": bool(
                    subprocess.check_output(
                        ["git", "status", "--porcelain"],
                        stderr=subprocess.DEVNULL,
                    )
                    .decode()
                    .strip()
                ),
                "remote": subprocess.check_output(
                    ["git", "remote", "get-url", "origin"],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip(),
            }
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {"repository": None}


def _get_dependency_info() -> Dict[str, Any]:
    """Collect information about installed packages and dependencies."""
    try:
        # Get installed packages
        installed_packages = {
            pkg.metadata["Name"]: pkg.metadata["Version"]
            for pkg in importlib.metadata.distributions()
            if pkg.metadata["Name"]
        }
        
        # Get direct dependencies
        try:
            deps = importlib.metadata.distribution("lousa").requires or []
        except importlib.metadata.PackageNotFoundError:
            deps = []
            
        return {
            "packages": installed_packages,
            "direct_dependencies": deps,
            "python_path": sys.path,
        }
    except Exception as e:
        return {"error": f"Failed to collect dependency info: {str(e)}"}


def _compute_file_hash(file_path: Union[str, pathlib.Path]) -> Dict[str, str]:
    """Compute hash of a file with multiple algorithms."""
    file_path = pathlib.Path(file_path)
    if not file_path.exists():
        return {"error": "File not found"}
        
    hashes = {
        "sha256": hashlib.sha256(),
        "md5": hashlib.md5(),
    }
    
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                for h in hashes.values():
                    h.update(chunk)
        
        return {name: h.hexdigest() for name, h in hashes.items()}
    except Exception as e:
        return {"error": f"Failed to compute hash: {str(e)}"}


def capture_provenance(
    note_path: Optional[Union[str, pathlib.Path]] = None,
    include_dependencies: bool = True,
    include_system_info: bool = True,
    include_git_info: bool = True,
) -> Dict[str, Any]:
    """Capture comprehensive provenance information for a risk assessment.
    
    Args:
        note_path: Optional path to the risk note file to include in provenance
        include_dependencies: Whether to include package dependency information
        include_system_info: Whether to include system and environment information
        include_git_info: Whether to include Git repository information
        
    Returns:
        A dictionary containing provenance information
    """
    # Try to get package version, fallback to 'development' if not available
    try:
        version = importlib.metadata.version("lousa")
    except importlib.metadata.PackageNotFoundError:
        version = "development"
    
    provenance = {
        "provenance_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": {
            "name": "lousa",
            "version": version,
        },
    }
    
    # Add input file information if provided
    if note_path is not None:
        note_path = pathlib.Path(note_path)
        provenance["input_file"] = {
            "path": str(note_path.absolute()),
            "size": note_path.stat().st_size,
            "modified": datetime.fromtimestamp(note_path.stat().st_mtime, tz=timezone.utc).isoformat(),
            "hashes": _compute_file_hash(note_path),
        }
    
    # Add system information if requested
    if include_system_info:
        provenance["system"] = _get_system_info()
    
    # Add Git information if requested and available
    if include_git_info:
        provenance.update(_get_git_info())
    
    # Add dependency information if requested
    if include_dependencies:
        provenance["dependencies"] = _get_dependency_info()
    
    return provenance


def format_provenance(provenance: Dict[str, Any], format: str = "text") -> str:
    """Format provenance information for human or machine consumption.
    
    Args:
        provenance: The provenance dictionary to format
        format: Output format ('text', 'json', or 'yaml')
        
    Returns:
        Formatted provenance information
        
    Raises:
        ValueError: If an unsupported format is specified
    """
    if format == "json":
        return json.dumps(provenance, indent=2)
    elif format == "yaml":
        try:
            import yaml
            return yaml.dump(provenance, default_flow_style=False)
        except ImportError:
            raise ValueError("PyYAML is required for YAML output")
    elif format == "text":
        lines = [
            "=" * 80,
            f"LOUSA PROVENANCE INFORMATION",
            f"Generated at: {provenance['timestamp']}",
            f"Provenance ID: {provenance['provenance_id']}",
            "=" * 80,
            "",
            "SYSTEM INFORMATION",
            "-" * 40,
        ]
        
        if "system" in provenance:
            sys_info = provenance["system"]
            lines.extend([
                f"Hostname: {sys_info.get('hostname', 'unknown')}",
                f"Platform: {sys_info['platform']['system']} {sys_info['platform']['release']}",
                f"Python: {sys_info['python']['version']} ({sys_info['python']['implementation']})",
                f"Working Directory: {sys_info['environment']['cwd']}",
                "",
            ])
        
        if "repository" in provenance and provenance["repository"]:
            repo = provenance["repository"]
            lines.extend([
                "VERSION CONTROL",
                "-" * 40,
                f"Repository: {repo.get('remote', 'unknown')}",
                f"Branch: {repo.get('branch', 'unknown')}",
                f"Commit: {repo.get('commit', 'unknown')}",
                f"Dirty: {repo.get('dirty', False)}",
                "",
            ])
        
        if "input_file" in provenance:
            file_info = provenance["input_file"]
            lines.extend([
                "INPUT FILE",
                "-" * 40,
                f"Path: {file_info['path']}",
                f"Size: {file_info['size']} bytes",
                f"Modified: {file_info['modified']}",
                f"SHA-256: {file_info['hashes'].get('sha256', 'unknown')}",
                "",
            ])
        
        if "dependencies" in provenance:
            deps = provenance["dependencies"]
            lines.extend([
                "DEPENDENCIES",
                "-" * 40,
                f"Direct Dependencies: {len(deps.get('direct_dependencies', []))}",
                f"Installed Packages: {len(deps.get('packages', {}))}",
                "",
            ])
        
        return "\n".join(lines)
    else:
        raise ValueError(f"Unsupported format: {format}")


def save_provenance(
    provenance: Dict[str, Any],
    output_path: Union[str, pathlib.Path],
    format: str = "json",
) -> None:
    """Save provenance information to a file.
    
    Args:
        provenance: The provenance dictionary to save
        output_path: Path to save the provenance information
        format: Output format ('json' or 'yaml')
        
    Raises:
        ValueError: If an unsupported format is specified
    """
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "json":
        output_path.write_text(json.dumps(provenance, indent=2))
    elif format == "yaml":
        try:
            import yaml
            output_path.write_text(yaml.dump(provenance, default_flow_style=False))
        except ImportError:
            raise ValueError("PyYAML is required for YAML output")
    else:
        raise ValueError(f"Unsupported format: {format}")


# Backward compatibility
def capture(note_path: pathlib.Path) -> Dict:
    """Legacy function for backward compatibility."""
    return capture_provenance(note_path=note_path)


def dump_json(prov: Dict, out_path: pathlib.Path) -> pathlib.Path:
    out_path.write_text(json.dumps(prov, indent=2, sort_keys=True))
    return out_path
