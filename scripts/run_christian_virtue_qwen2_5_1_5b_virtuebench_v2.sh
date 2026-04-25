#!/usr/bin/env bash
# Run VirtueBench V2 for the base Qwen2.5-1.5B model or the full-corpus LoRA.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-base}"
BENCHMARK_ROOT="${BENCHMARK_ROOT:-${ROOT_DIR}/runs/_benchmark_sources/virtue-bench-2}"
VIRTUEBENCH_REPO_URL="https://github.com/christian-machine-intelligence/virtue-bench-2.git"
VIRTUEBENCH_COMMIT="410f4069e1277e633edd24962de584c979ac81e5"
EXPECTED_MODEL_NAME="${EXPECTED_MODEL_NAME:-Qwen/Qwen2.5-1.5B-Instruct}"
LIMIT_PER_CELL="${LIMIT_PER_CELL:-25}"
VIRTUEBENCH_RUNS="${VIRTUEBENCH_RUNS:-3}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-48}"
POSITION_MODE="${POSITION_MODE:-random}"
USES_ADAPTER=0
ENV_PREFIX=(
  env
  "PYTHONUNBUFFERED=${PYTHONUNBUFFERED:-1}"
  "PYTORCH_ENABLE_MPS_FALLBACK=${PYTORCH_ENABLE_MPS_FALLBACK:-1}"
  "PYTORCH_MPS_HIGH_WATERMARK_RATIO=${PYTORCH_MPS_HIGH_WATERMARK_RATIO:-0.0}"
  "TOKENIZERS_PARALLELISM=${TOKENIZERS_PARALLELISM:-false}"
)

ensure_virtuebench_source() {
  if [[ ! -d "${BENCHMARK_ROOT}/.git" ]]; then
    mkdir -p "$(dirname "${BENCHMARK_ROOT}")"
    git clone "${VIRTUEBENCH_REPO_URL}" "${BENCHMARK_ROOT}"
  fi
  git -C "${BENCHMARK_ROOT}" fetch --tags --quiet
  git -C "${BENCHMARK_ROOT}" checkout --quiet "${VIRTUEBENCH_COMMIT}"
  local actual_commit
  actual_commit="$(git -C "${BENCHMARK_ROOT}" rev-parse HEAD)"
  if [[ "${actual_commit}" != "${VIRTUEBENCH_COMMIT}" ]]; then
    echo "VirtueBench commit mismatch: expected ${VIRTUEBENCH_COMMIT}, got ${actual_commit}" >&2
    exit 1
  fi
}

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
    if [[ "${POSITION_MODE}" == "paired" ]]; then
      RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/virtuebench_v2_paired_base"
    else
      RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/virtuebench_v2_base"
    fi
    ;;
  full-corpus)
    ADAPTER_DIR="${ADAPTER_PATH:-${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest}"
    if [[ ! -e "${ADAPTER_DIR}" ]]; then
      echo "Full-corpus adapter directory not found: ${ADAPTER_DIR}" >&2
      echo "Pass ADAPTER_PATH=/absolute/path/to/full_corpus/latest." >&2
      exit 1
    fi
    if [[ "${POSITION_MODE}" == "paired" ]]; then
      RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/virtuebench_v2_paired_full_corpus"
    else
      RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/virtuebench_v2_full_corpus"
    fi
    USES_ADAPTER=1
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'base' or 'full-corpus'." >&2
    exit 1
    ;;
esac

ensure_virtuebench_source
RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"
init_run_dir "${RUN_DIR}"

{
  echo "mode=${MODE}"
  echo "benchmark_root=${BENCHMARK_ROOT}"
  echo "virtuebench_commit=${VIRTUEBENCH_COMMIT}"
  echo "limit_per_cell=${LIMIT_PER_CELL}"
  echo "position_mode=${POSITION_MODE}"
  echo "runs=${VIRTUEBENCH_RUNS}"
  git -C "${BENCHMARK_ROOT}" status --short
} > "${RUN_DIR}/source_snapshot.txt"

if [[ "${USES_ADAPTER}" == "1" ]]; then
  verify_adapter_dir "${ADAPTER_DIR}" | tee -a "${RUN_DIR}/stdout.log"
fi
if [[ "${VERIFY_ONLY:-0}" == "1" ]]; then
  link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
  exit 0
fi

COMMON_ARGS=(
  --benchmark-root
  "${BENCHMARK_ROOT}"
  --model-name-or-path
  "${EXPECTED_MODEL_NAME}"
  --output-dir
  "${RUN_DIR}"
  --limit-per-cell
  "${LIMIT_PER_CELL}"
  --position-mode
  "${POSITION_MODE}"
  --runs
  "${VIRTUEBENCH_RUNS}"
  --max-new-tokens
  "${MAX_NEW_TOKENS}"
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
    "${ROOT_DIR}/scripts/run_virtuebench_v2_local.py" \
    "${COMMON_ARGS[@]}" \
    --adapter-path \
    "${ADAPTER_DIR}"
else
  run_logged \
    "${RUN_DIR}" \
    "${ENV_PREFIX[@]}" \
    "${PYTHON_BIN}" \
    "${ROOT_DIR}/scripts/run_virtuebench_v2_local.py" \
    "${COMMON_ARGS[@]}"
fi

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
