#!/usr/bin/env bash
# Run one local Qwen2.5-1.5B training rung and archive it in a timestamped run directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-local-baseline}"
ENV_PREFIX=()
case "${MODE}" in
  smoke)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_smoke.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/smoke"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-smoke"
    ;;
  local-baseline)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_local_baseline.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-local-baseline"
    ;;
  full-corpus)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_full_corpus.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-full-corpus"
    ENV_PREFIX=(
      env
      "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
      "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
    )
    ;;
  citation-frontier)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-citation-frontier"
    ;;
  accuracy-first)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_accuracy_first_hybrid.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-accuracy-first-hybrid"
    ENV_PREFIX=(
      env
      "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
      "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
    )
    ;;
  justice-guarded)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_justice_guarded_citation_repair.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/justice_guarded_citation_repair"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-justice-guarded-citation-repair"
    ENV_PREFIX=(
      env
      "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
      "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
    )
    ;;
  extended)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_extended.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/extended"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-extended"
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'smoke', 'local-baseline', 'full-corpus', 'citation-frontier', 'accuracy-first', 'justice-guarded', or 'extended'." >&2
    exit 1
    ;;
esac

DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
DATASET_SENTINEL="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1/all.jsonl"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"
RUN_ID="$(basename "${RUN_DIR}")"
RUN_NAME="${RUN_STEM}-${RUN_ID}"

init_run_dir "${RUN_DIR}"
link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
{
  echo "Run directory: ${RUN_DIR}"
  echo "Latest symlink: ${RUN_ROOT}/latest"
} | tee -a "${RUN_DIR}/stdout.log"
ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${ENV_PREFIX[@]}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/train_christian_virtue_qlora.py" \
  --config \
  "${ROOT_DIR}/${TRAIN_CONFIG}" \
  --output-dir \
  "${RUN_DIR}" \
  --run-name \
  "${RUN_NAME}"
