#!/usr/bin/env bash
# Run one local Qwen2.5-1.5B training rung and archive it in a timestamped run directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-pilot}"
case "${MODE}" in
  smoke)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_smoke.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/smoke"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-smoke"
    ;;
  pilot-lite)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-pilot-lite"
    ;;
  pilot)
    TRAIN_CONFIG="configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot.yaml"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/pilot"
    RUN_STEM="christian-virtue-qwen2.5-1.5b-instruct-lora-mps-pilot"
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'smoke', 'pilot-lite', or 'pilot'." >&2
    exit 1
    ;;
esac

DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
DATASET_SENTINEL="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1/all.jsonl"
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"
RUN_ID="$(basename "${RUN_DIR}")"
RUN_NAME="${RUN_STEM}-${RUN_ID}"

init_run_dir "${RUN_DIR}"
ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/train_christian_virtue_qlora.py" \
  --config \
  "${ROOT_DIR}/${TRAIN_CONFIG}" \
  --output-dir \
  "${RUN_DIR}" \
  --run-name \
  "${RUN_NAME}"

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
