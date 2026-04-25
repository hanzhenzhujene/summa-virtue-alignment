#!/usr/bin/env bash
# Run the Aquinas grounding probe for the base Qwen2.5-1.5B model or full-corpus LoRA.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-base}"
DATASET_PATH="${DATASET_PATH:-${ROOT_DIR}/data/processed/sft/exports/christian_virtue_v1/test.jsonl}"
EXPECTED_MODEL_NAME="${EXPECTED_MODEL_NAME:-Qwen/Qwen2.5-1.5B-Instruct}"
MAX_EXAMPLES="${MAX_EXAMPLES:-0}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-192}"
PROMPT_MODE="${PROMPT_MODE:-canonical}"
USES_ADAPTER=0
ENV_PREFIX=(
  env
  "PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1}"
  "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
  "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
  "TOKENIZERS_PARALLELISM=${TOKENIZERS_PARALLELISM:-false}"
)

verify_adapter_dir() {
  local adapter_dir="$1"
  local expected_sha="${EXPECTED_ADAPTER_SHA256:-}"
  local expected_run_id="${EXPECTED_ADAPTER_RUN_ID:-}"
  local expected_model="${EXPECTED_MODEL_NAME}"
  "${PYTHON_BIN}" - "${adapter_dir}" "${expected_sha}" "${expected_run_id}" "${expected_model}" <<'PY'
from pathlib import Path
import hashlib
import json
import sys

adapter_dir = Path(sys.argv[1]).resolve()
expected_sha = sys.argv[2]
expected_run_id = sys.argv[3]
expected_model = sys.argv[4]
adapter_model = adapter_dir / "adapter_model.safetensors"
adapter_config = adapter_dir / "adapter_config.json"
train_metadata = adapter_dir / "train_metadata.json"

missing = [str(path) for path in [adapter_model, adapter_config, train_metadata] if not path.exists()]
if missing:
    raise SystemExit(f"Adapter artifact is incomplete. Missing: {', '.join(missing)}")

sha = hashlib.sha256(adapter_model.read_bytes()).hexdigest()
metadata = json.loads(train_metadata.read_text(encoding="utf-8"))
run_id = metadata.get("run_id")
model_name = metadata.get("model_name_or_path")
if expected_sha and sha != expected_sha:
    raise SystemExit(f"Adapter sha256 mismatch: expected {expected_sha}, got {sha}")
if expected_run_id and run_id != expected_run_id:
    raise SystemExit(f"Adapter run_id mismatch: expected {expected_run_id}, got {run_id}")
if model_name != expected_model:
    raise SystemExit(f"Adapter model mismatch: expected {expected_model}, got {model_name}")

summary = {
    "adapter_config": str(adapter_config),
    "adapter_dir": str(adapter_dir),
    "adapter_model": str(adapter_model),
    "adapter_sha256": sha,
    "end_time": metadata.get("end_time"),
    "eval_examples": metadata.get("eval_examples"),
    "event": "adapter_artifact_verified",
    "git_commit": metadata.get("git_commit"),
    "global_step": metadata.get("global_step"),
    "model_name_or_path": model_name,
    "run_id": run_id,
    "train_examples": metadata.get("train_examples"),
}
print(json.dumps(summary, sort_keys=True))
PY
}

case "${MODE}" in
  base)
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/aquinas_grounding_probe_base"
    ;;
  full-corpus)
    ADAPTER_DIR="${ADAPTER_PATH:-${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest}"
    if [[ ! -e "${ADAPTER_DIR}" ]]; then
      echo "Full-corpus adapter directory not found: ${ADAPTER_DIR}" >&2
      echo "Pass ADAPTER_PATH=/absolute/path/to/full_corpus/latest." >&2
      exit 1
    fi
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/aquinas_grounding_probe_full_corpus"
    USES_ADAPTER=1
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'base' or 'full-corpus'." >&2
    exit 1
    ;;
esac

RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"
init_run_dir "${RUN_DIR}"

{
  echo "mode=${MODE}"
  echo "dataset_path=${DATASET_PATH}"
  echo "max_examples=${MAX_EXAMPLES}"
  echo "max_new_tokens=${MAX_NEW_TOKENS}"
  echo "prompt_mode=${PROMPT_MODE}"
} > "${RUN_DIR}/source_snapshot.txt"

if [[ "${USES_ADAPTER}" == "1" ]]; then
  verify_adapter_dir "${ADAPTER_DIR}" | tee -a "${RUN_DIR}/stdout.log"
fi
if [[ "${VERIFY_ONLY:-0}" == "1" ]]; then
  link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
  exit 0
fi

COMMON_ARGS=(
  --dataset-path
  "${DATASET_PATH}"
  --model-name-or-path
  "${EXPECTED_MODEL_NAME}"
  --output-dir
  "${RUN_DIR}"
  --max-examples
  "${MAX_EXAMPLES}"
  --max-new-tokens
  "${MAX_NEW_TOKENS}"
  --prompt-mode
  "${PROMPT_MODE}"
  --runtime-backend
  "mps"
  --torch-dtype
  "float16"
)

if [[ "${USES_ADAPTER}" == "1" ]]; then
  run_logged \
    "${RUN_DIR}" \
    "${ENV_PREFIX[@]}" \
    "${PYTHON_BIN}" \
    "${ROOT_DIR}/scripts/run_aquinas_virtue_grounding_probe.py" \
    "${COMMON_ARGS[@]}" \
    --adapter-path \
    "${ADAPTER_DIR}"
else
  run_logged \
    "${RUN_DIR}" \
    "${ENV_PREFIX[@]}" \
    "${PYTHON_BIN}" \
    "${ROOT_DIR}/scripts/run_aquinas_virtue_grounding_probe.py" \
    "${COMMON_ARGS[@]}"
fi

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
