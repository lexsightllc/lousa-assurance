#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${VENV_PATH:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${VENV_PATH}/bin/python"
PIP_BIN="${VENV_PATH}/bin/pip"
PIP_OPTIONS=${PIP_OPTIONS:-}

export PIP_DISABLE_PIP_VERSION_CHECK=1

ensure_venv() {
    if [[ ! -d "${VENV_PATH}" ]]; then
        python -m venv "${VENV_PATH}"
    fi
}

install_dev_dependencies() {
    ensure_venv
    local opts=()
    if [[ -n "${PIP_OPTIONS}" ]]; then
        # shellcheck disable=SC2206
        opts=(${PIP_OPTIONS})
    fi
    "${PIP_BIN}" install "${opts[@]}" --upgrade pip
    "${PIP_BIN}" install "${opts[@]}" -e ".[dev]"
}

run_in_venv() {
    ensure_venv
    "${PYTHON_BIN}" "$@"
}

ensure_bootstrap() {
    install_dev_dependencies
    "${VENV_PATH}/bin/pre-commit" install --install-hooks
    "${VENV_PATH}/bin/pre-commit" install --hook-type commit-msg
    git config commit.template ".github/commit_template.txt"
}

has_py_files() {
    shopt -s nullglob
    local files=("$1"/*.py)
    if (( ${#files[@]} > 0 )); then
        return 0
    fi
    return 1
}
