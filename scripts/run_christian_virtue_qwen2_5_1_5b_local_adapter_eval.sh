#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

PILOT_LITE_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite"
PILOT_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/pilot"
SMOKE_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/smoke"
if ! ADAPTER_DIR="$(resolve_first_existing_path "${PILOT_LITE_ROOT}/latest" "${PILOT_ROOT}/latest" "${SMOKE_ROOT}/latest")"; then
  echo "Adapter directory not found." >&2
  echo "Expected one of:" >&2
  echo "  ${PILOT_LITE_ROOT}/latest" >&2
  echo "  ${PILOT_ROOT}/latest" >&2
  echo "  ${SMOKE_ROOT}/latest" >&2
  echo "Run the smoke or pilot-lite training first." >&2
  exit 1
fi

DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
DATASET_DIR="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1"
DATASET_SENTINEL="${DATASET_DIR}/all.jsonl"
INFERENCE_CONFIG="configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml"
RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"

init_run_dir "${RUN_DIR}"
ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/generate_christian_virtue_predictions.py" \
  --config \
  "${ROOT_DIR}/${INFERENCE_CONFIG}" \
  --adapter-path \
  "${ADAPTER_DIR}" \
  --output-dir \
  "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/eval_christian_virtue_sft.py" \
  --dataset-dir \
  "${DATASET_DIR}" \
  --predictions \
  "${RUN_DIR}/predictions.jsonl" \
  --splits \
  "test" \
  --report-path \
  "${RUN_DIR}/report.md" \
  --metrics-path \
  "${RUN_DIR}/metrics.json"

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
