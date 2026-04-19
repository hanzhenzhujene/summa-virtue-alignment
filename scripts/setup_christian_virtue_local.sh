#!/usr/bin/env bash
# Create the pinned local Apple-Silicon environment for the canonical Christian virtue baseline.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
LOCKFILE="${LOCKFILE:-${ROOT_DIR}/requirements/local-mps-py312.lock.txt}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python interpreter not found: ${PYTHON_BIN}" >&2
  echo "Set PYTHON_BIN=python3.12 or another compatible interpreter and retry." >&2
  exit 1
fi

if [[ ! -f "${LOCKFILE}" ]]; then
  echo "Pinned lockfile not found: ${LOCKFILE}" >&2
  exit 1
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${LOCKFILE}"
"${VENV_DIR}/bin/pip" install --no-deps -e "${ROOT_DIR}"

echo "Local environment ready at ${VENV_DIR}"
echo "Next step: make reproduce-christian-virtue-qwen2-5-1-5b-local"
