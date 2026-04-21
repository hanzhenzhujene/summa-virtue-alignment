#!/usr/bin/env bash
# Audit the citation frontier for the latest citation-frontier adapter against the shared base run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

BASE_PREDICTIONS="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/predictions.jsonl"
ADAPTER_PREDICTIONS="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_adapter_test/latest/predictions.jsonl"

if [[ ! -f "${BASE_PREDICTIONS}" ]]; then
  echo "Base predictions not found: ${BASE_PREDICTIONS}" >&2
  echo "Run the base evaluation first." >&2
  exit 1
fi

if [[ ! -f "${ADAPTER_PREDICTIONS}" ]]; then
  echo "Citation-frontier adapter predictions not found: ${ADAPTER_PREDICTIONS}" >&2
  echo "Run the citation-frontier adapter evaluation first." >&2
  exit 1
fi

RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_audit"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"

init_run_dir "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/audit_christian_virtue_frontier.py" \
  --base-predictions \
  "${BASE_PREDICTIONS}" \
  --adapter-predictions \
  "${ADAPTER_PREDICTIONS}" \
  --report-path \
  "${RUN_DIR}/report.md" \
  --metrics-path \
  "${RUN_DIR}/metrics.json" \
  --figure-path \
  "${RUN_DIR}/citation_frontier_modes.svg"

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
