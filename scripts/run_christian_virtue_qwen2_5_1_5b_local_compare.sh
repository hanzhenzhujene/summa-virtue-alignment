#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

BASE_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/base_test"
ADAPTER_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test"
BASE_METRICS="${BASE_ROOT}/latest/metrics.json"
ADAPTER_METRICS="${ADAPTER_ROOT}/latest/metrics.json"

if [[ ! -f "${BASE_METRICS}" ]]; then
  echo "Base metrics not found: ${BASE_METRICS}" >&2
  echo "Run the base evaluation first." >&2
  exit 1
fi

if [[ ! -f "${ADAPTER_METRICS}" ]]; then
  echo "Adapter metrics not found: ${ADAPTER_METRICS}" >&2
  echo "Run the adapter evaluation first." >&2
  exit 1
fi

RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/compare_test"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"

init_run_dir "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/compare_christian_virtue_runs.py" \
  --baseline-metrics \
  "${BASE_METRICS}" \
  --candidate-metrics \
  "${ADAPTER_METRICS}" \
  --baseline-label \
  "qwen2.5-1.5b-base-test" \
  --candidate-label \
  "qwen2.5-1.5b-pilot-lite-adapter-test" \
  --output \
  "${RUN_DIR}/report.md"

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
