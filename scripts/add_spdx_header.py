#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Ensure files contain the MPL-2.0 SPDX header."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HEADER_TEXT = "SPDX-License-Identifier: MPL-2.0"
HTML_HEADER = f"<!-- {HEADER_TEXT} -->"

COMMENT_STYLES = {
    ".py": "#",
    ".pyi": "#",
    ".sh": "#",
    ".bash": "#",
    ".zsh": "#",
    ".ps1": "#",
    ".psm1": "#",
    ".yml": "#",
    ".yaml": "#",
    ".toml": "#",
    ".ini": "#",
    ".cfg": "#",
    ".env": "#",
    ".sample": "#",
    ".txt": "#",
    ".mk": "#",
}

NAME_BASED_STYLES = {
    "Makefile": "#",
    ".gitignore": "#",
    ".gitmodules": "#",
    ".gitattributes": "#",
    ".editorconfig": "#",
    ".pre-commit-config.yaml": "#",
    ".env.example": "#",
    ".tool-versions": "#",
    "Dockerfile": "#",
    "CODEOWNERS": "#",
}

MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdx"}


def iter_target_files(args: list[str]) -> list[Path]:
    if args:
        return [Path(arg) for arg in args]
    git_files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    return [Path(name) for name in git_files]


def has_header(lines: list[str], needle: str) -> bool:
    return any(needle in line for line in lines[:5])


def apply_hash_header(path: Path, lines: list[str]) -> list[str]:
    if has_header(lines, HEADER_TEXT):
        return lines

    shebang = lines[0] if lines and lines[0].startswith("#!") else None
    insertion_index = 1 if shebang else 0

    if shebang and insertion_index < len(lines) and HEADER_TEXT in lines[insertion_index]:
        return lines

    new_lines = lines.copy()
    new_lines.insert(insertion_index, f"# {HEADER_TEXT}\n")
    return new_lines


def apply_markdown_header(path: Path, lines: list[str]) -> list[str]:
    if has_header(lines, HEADER_TEXT):
        return lines

    stripped = path.read_text(encoding="utf-8").lstrip()
    if stripped.startswith("<!--") and HEADER_TEXT in stripped.split("-->", 1)[0]:
        return lines

    new_lines = lines.copy()
    new_lines.insert(0, f"{HTML_HEADER}\n")
    return new_lines


def determine_style(path: Path) -> str | None:
    if path.suffix in MARKDOWN_EXTENSIONS:
        return "markdown"
    if path.name in NAME_BASED_STYLES:
        return NAME_BASED_STYLES[path.name]
    if path.suffix in COMMENT_STYLES:
        return COMMENT_STYLES[path.suffix]
    return None


def process_file(path: Path) -> None:
    if not path.exists() or path.is_dir():
        return

    try:
        original = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return

    style = determine_style(path)
    if style is None and original and original[0].startswith("#!"):
        style = "#"
    if style is None:
        return

    if style == "markdown":
        updated = apply_markdown_header(path, original)
    else:
        updated = apply_hash_header(path, original)

    if updated != original:
        path.write_text("".join(updated), encoding="utf-8")


def main(args: list[str]) -> int:
    files = iter_target_files(args)
    for file in files:
        process_file(file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
