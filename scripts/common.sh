#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHON_VERSION_FILE="${ROOT_DIR}/.tool-versions"
REQUESTED_PYTHON_VERSION=""
if [[ -f "${PYTHON_VERSION_FILE}" ]]; then
    REQUESTED_PYTHON_VERSION="$(grep '^python ' "${PYTHON_VERSION_FILE}" | awk '{print $2}')"
fi

PYTHON_EXE="${PYTHON_EXE:-}"
if [[ -z "${PYTHON_EXE}" && -n "${REQUESTED_PYTHON_VERSION}" ]]; then
    # Prefer an interpreter that matches the requested version.
    CANDIDATES=("python${REQUESTED_PYTHON_VERSION}" "python${REQUESTED_PYTHON_VERSION%.*}" python3 python)
    for candidate in "${CANDIDATES[@]}"; do
        if command -v "${candidate}" >/dev/null 2>&1; then
            PYTHON_EXE="${candidate}"
            break
        fi
    done
fi

PYTHON_EXE="${PYTHON_EXE:-python3}"

VENV_PATH="${VENV_PATH:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${VENV_PATH}/bin/python"
PIP_BIN="${VENV_PATH}/bin/pip"
PYTEST_BIN="${VENV_PATH}/bin/pytest"
COVERAGE_BIN="${VENV_PATH}/bin/coverage"
PIP_OPTIONS=${PIP_OPTIONS:-}

export PIP_DISABLE_PIP_VERSION_CHECK=1

ensure_venv() {
    if [[ ! -d "${VENV_PATH}" ]]; then
        "${PYTHON_EXE}" -m venv "${VENV_PATH}"
    fi
}

install_dev_dependencies() {
    ensure_venv
    if [[ "${LOUSA_SKIP_INSTALL:-0}" == "1" ]]; then
        echo "LOUSA_SKIP_INSTALL=1 detected; skipping dependency installation" >&2
        return 0
    fi
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
