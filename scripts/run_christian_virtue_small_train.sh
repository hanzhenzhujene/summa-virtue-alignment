#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-proto}"
case "${MODE}" in
  smoke)
    TRAIN_CONFIG="configs/train/qwen3_0_6b_qlora_smoke.yaml"
    RUN_DIR="${ROOT_DIR}/runs/christian_virtue/qwen3_0_6b/smoke"
    ;;
  proto)
    TRAIN_CONFIG="configs/train/qwen3_0_6b_qlora.yaml"
    RUN_DIR="${ROOT_DIR}/runs/christian_virtue/qwen3_0_6b/proto"
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'smoke' or 'proto'." >&2
    exit 1
    ;;
esac

DATASET_CONFIG="configs/sft/christian_virtue_v1.yaml"
DATASET_SENTINEL="${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1/all.jsonl"

init_run_dir "${RUN_DIR}"

if [[ "${SKIP_PREFLIGHT:-0}" != "1" ]]; then
  run_preflight "${RUN_DIR}"
fi

ensure_dataset "${DATASET_CONFIG}" "${DATASET_SENTINEL}" "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/train_christian_virtue_qlora.py" \
  --config \
  "${ROOT_DIR}/${TRAIN_CONFIG}"
