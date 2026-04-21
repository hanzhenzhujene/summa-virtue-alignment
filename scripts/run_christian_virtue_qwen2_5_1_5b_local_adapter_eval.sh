#!/usr/bin/env bash
# Generate and evaluate held-out adapter predictions for the latest local training artifact.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-local-baseline}"
ENV_PREFIX=()
LOCAL_BASELINE_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline"
EXTENDED_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/extended"
SMOKE_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/smoke"
CITATION_FRONTIER_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier"
ACCURACY_FIRST_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid"
JUSTICE_GUARDED_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/justice_guarded_citation_repair"

case "${MODE}" in
  local-baseline)
    if ! ADAPTER_DIR="$(resolve_first_existing_path "${LOCAL_BASELINE_ROOT}/latest" "${EXTENDED_ROOT}/latest" "${SMOKE_ROOT}/latest")"; then
      echo "Adapter directory not found." >&2
      echo "Expected one of:" >&2
      echo "  ${LOCAL_BASELINE_ROOT}/latest" >&2
      echo "  ${EXTENDED_ROOT}/latest" >&2
      echo "  ${SMOKE_ROOT}/latest" >&2
      echo "Run the smoke or local-baseline training first." >&2
      exit 1
    fi
    INFERENCE_CONFIG="configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test"
    ;;
  citation-frontier)
    if [[ ! -e "${CITATION_FRONTIER_ROOT}/latest" ]]; then
      echo "Citation-frontier adapter directory not found: ${CITATION_FRONTIER_ROOT}/latest" >&2
      echo "Run the citation-frontier training first." >&2
      exit 1
    fi
    ADAPTER_DIR="${CITATION_FRONTIER_ROOT}/latest"
    INFERENCE_CONFIG="configs/inference/qwen2_5_1_5b_instruct_citation_frontier_adapter_test.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_adapter_test"
    ;;
  accuracy-first)
    if [[ ! -e "${ACCURACY_FIRST_ROOT}/latest" ]]; then
      echo "Accuracy-first adapter directory not found: ${ACCURACY_FIRST_ROOT}/latest" >&2
      echo "Run the accuracy-first training first." >&2
      exit 1
    fi
    ADAPTER_DIR="${ACCURACY_FIRST_ROOT}/latest"
    INFERENCE_CONFIG="configs/inference/qwen2_5_1_5b_instruct_accuracy_first_adapter_test.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid_adapter_test"
    ENV_PREFIX=(
      env
      "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
      "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
    )
    ;;
  justice-guarded)
    if [[ ! -e "${JUSTICE_GUARDED_ROOT}/latest" ]]; then
      echo "Justice-guarded adapter directory not found: ${JUSTICE_GUARDED_ROOT}/latest" >&2
      echo "Run the justice-guarded training first." >&2
      exit 1
    fi
    ADAPTER_DIR="${JUSTICE_GUARDED_ROOT}/latest"
    INFERENCE_CONFIG="configs/inference/qwen2_5_1_5b_instruct_justice_guarded_adapter_test.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/justice_guarded_citation_repair_adapter_test"
    ENV_PREFIX=(
      env
      "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
      "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
    )
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'local-baseline', 'citation-frontier', 'accuracy-first', or 'justice-guarded'." >&2
    exit 1
    ;;
esac

DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
DATASET_DIR="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1"
DATASET_SENTINEL="${DATASET_DIR}/all.jsonl"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"

init_run_dir "${RUN_DIR}"
ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${ENV_PREFIX[@]}" \
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
  "${ENV_PREFIX[@]}" \
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
