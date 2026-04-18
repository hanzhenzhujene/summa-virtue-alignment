#!/usr/bin/env bash

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

resolve_python_bin() {
  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/.venv/bin/python}"
  else
    PYTHON_BIN="${PYTHON_BIN:-python3}"
  fi
  export PYTHON_BIN
  export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
}

create_timestamped_run_dir() {
  local root_dir="$1"
  mkdir -p "${root_dir}"
  "${PYTHON_BIN}" - "${root_dir}" <<'PY'
from pathlib import Path
import sys

from summa_moral_graph.sft.run_layout import create_timestamped_run_dir

run_dir = create_timestamped_run_dir(Path(sys.argv[1]).resolve())
print(run_dir)
PY
}

link_latest_run() {
  local root_dir="$1"
  local run_dir="$2"
  mkdir -p "${root_dir}"
  ln -sfn "$(basename "${run_dir}")" "${root_dir}/latest"
}

resolve_first_existing_path() {
  local candidate
  for candidate in "$@"; do
    if [[ -e "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

init_run_dir() {
  local run_dir="$1"
  mkdir -p "${run_dir}"
  : > "${run_dir}/stdout.log"
  : > "${run_dir}/stderr.log"
  : > "${run_dir}/command.log"
}

log_command() {
  local run_dir="$1"
  shift
  {
    printf '$ '
    printf '%q ' "$@"
    printf '\n'
  } >> "${run_dir}/command.log"
}

run_logged() {
  local run_dir="$1"
  shift
  log_command "${run_dir}" "$@"
  "$@" \
    > >(tee -a "${run_dir}/stdout.log") \
    2> >(tee -a "${run_dir}/stderr.log" >&2)
}

run_preflight() {
  local run_dir="$1"
  log_command "${run_dir}" "${PYTHON_BIN}" "${ROOT_DIR}/scripts/preflight_christian_virtue_gpu.py"
  if ! "${PYTHON_BIN}" "${ROOT_DIR}/scripts/preflight_christian_virtue_gpu.py" \
    > "${run_dir}/preflight.json"; then
    cat "${run_dir}/preflight.json" >&2 || true
    return 1
  fi
}

ensure_dataset() {
  local dataset_config="$1"
  local dataset_sentinel="$2"
  local run_dir="$3"
  if [[ -f "${dataset_sentinel}" ]]; then
    return 0
  fi
  run_logged \
    "${run_dir}" \
    "${PYTHON_BIN}" \
    "${ROOT_DIR}/scripts/build_christian_virtue_sft_dataset.py" \
    --config \
    "${ROOT_DIR}/${dataset_config}"
}
