#!/usr/bin/env bash
# Generate and evaluate held-out adapter predictions for the smaller remote-GPU path.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-test}"
ADAPTER_DIR="${ROOT_DIR}/runs/christian_virtue/qwen3_0_6b/proto"
if [[ ! -d "${ADAPTER_DIR}" ]]; then
  echo "Adapter directory not found: ${ADAPTER_DIR}" >&2
  exit 1
fi

case "${MODE}" in
  test)
    DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
    DATASET_DIR="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1"
    DATASET_SENTINEL="${DATASET_DIR}/all.jsonl"
    INFERENCE_CONFIG="configs/inference/qwen3_0_6b_adapter_test.yaml"
    RUN_DIR="${ROOT_DIR}/runs/christian_virtue/qwen3_0_6b/adapter_test"
    SPLIT_NAME="test"
    ;;
  ood)
    DATASET_CONFIG="configs/sft/christian_virtue_v1_ood.yaml"
    DATASET_DIR="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1_ood"
    DATASET_SENTINEL="${DATASET_DIR}/all.jsonl"
    INFERENCE_CONFIG="configs/inference/qwen3_0_6b_adapter_ood.yaml"
    RUN_DIR="${ROOT_DIR}/runs/christian_virtue/qwen3_0_6b/adapter_ood"
    SPLIT_NAME="ood_test"
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'test' or 'ood'." >&2
    exit 1
    ;;
esac

init_run_dir "${RUN_DIR}"

if [[ "${SKIP_PREFLIGHT:-0}" != "1" ]]; then
  run_preflight "${RUN_DIR}"
fi

ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/generate_christian_virtue_predictions.py" \
  --config \
  "${ROOT_DIR}/${INFERENCE_CONFIG}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/eval_christian_virtue_sft.py" \
  --dataset-dir \
  "${DATASET_DIR}" \
  --predictions \
  "${RUN_DIR}/predictions.jsonl" \
  --splits \
  "${SPLIT_NAME}" \
  --report-path \
  "${RUN_DIR}/report.md" \
  --metrics-path \
  "${RUN_DIR}/metrics.json"
