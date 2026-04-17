#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

WITH_OOD=0
for arg in "$@"; do
  case "${arg}" in
    --with-ood)
      WITH_OOD=1
      ;;
    *)
      echo "Unknown argument: ${arg}" >&2
      exit 1
      ;;
  esac
done

MODEL_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen3_0_6b"
init_run_dir "${MODEL_ROOT}"

run_preflight "${MODEL_ROOT}"

run_logged "${MODEL_ROOT}" env SKIP_PREFLIGHT=1 bash "${ROOT_DIR}/scripts/run_christian_virtue_small_train.sh" proto
run_logged "${MODEL_ROOT}" env SKIP_PREFLIGHT=1 bash "${ROOT_DIR}/scripts/run_christian_virtue_small_base_eval.sh" test
run_logged "${MODEL_ROOT}" env SKIP_PREFLIGHT=1 bash "${ROOT_DIR}/scripts/run_christian_virtue_small_adapter_eval.sh" test

COMPARE_TEST_DIR="${MODEL_ROOT}/compare_test"
init_run_dir "${COMPARE_TEST_DIR}"
run_logged \
  "${COMPARE_TEST_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/compare_christian_virtue_runs.py" \
  --baseline-metrics "${MODEL_ROOT}/base_test/metrics.json" \
  --candidate-metrics "${MODEL_ROOT}/adapter_test/metrics.json" \
  --baseline-label "qwen3-0.6b-base-test" \
  --candidate-label "qwen3-0.6b-adapter-test" \
  --output "${COMPARE_TEST_DIR}/report.md"

if [[ "${WITH_OOD}" == "1" ]]; then
  run_logged "${MODEL_ROOT}" env SKIP_PREFLIGHT=1 bash "${ROOT_DIR}/scripts/run_christian_virtue_small_base_eval.sh" ood
  run_logged "${MODEL_ROOT}" env SKIP_PREFLIGHT=1 bash "${ROOT_DIR}/scripts/run_christian_virtue_small_adapter_eval.sh" ood
  COMPARE_OOD_DIR="${MODEL_ROOT}/compare_ood"
  init_run_dir "${COMPARE_OOD_DIR}"
  run_logged \
    "${COMPARE_OOD_DIR}" \
    "${PYTHON_BIN}" \
    "${ROOT_DIR}/scripts/compare_christian_virtue_runs.py" \
    --baseline-metrics "${MODEL_ROOT}/base_ood/metrics.json" \
    --candidate-metrics "${MODEL_ROOT}/adapter_ood/metrics.json" \
    --baseline-label "qwen3-0.6b-base-ood" \
    --candidate-label "qwen3-0.6b-adapter-ood" \
    --output "${COMPARE_OOD_DIR}/report.md"
fi
