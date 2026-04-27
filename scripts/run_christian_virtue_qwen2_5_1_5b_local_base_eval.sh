#!/usr/bin/env bash
# Generate and evaluate held-out base-model predictions for the canonical local baseline.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
DATASET_DIR="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1"
DATASET_SENTINEL="${DATASET_DIR}/all.jsonl"
INFERENCE_CONFIG="configs/inference/qwen2_5_1_5b_instruct_base_test.yaml"
RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/base_test"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"
RUN_ID="$(basename "${RUN_DIR}")"

init_run_dir "${RUN_DIR}"
ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/generate_christian_virtue_predictions.py" \
  --config \
  "${ROOT_DIR}/${INFERENCE_CONFIG}" \
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
