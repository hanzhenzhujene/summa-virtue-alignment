#!/usr/bin/env bash
# Run the full canonical local Qwen2.5-1.5B publication loop from dataset build through verify.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${ROOT_DIR}/.venv/bin/python"
REPORT_PATH="${ROOT_DIR}/docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md"
PACKAGE_DIR="${ROOT_DIR}/artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter"
TRAIN_LATEST="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline/latest"
BASE_LATEST="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest"
ADAPTER_LATEST="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Pinned local environment not found at ${VENV_PYTHON}." >&2
  echo "Run 'make setup-christian-virtue-local' first, then retry this command." >&2
  exit 1
fi

run_step() {
  local label="$1"
  shift
  echo
  echo "==> ${label}"
  "$@"
}

run_step "Build Christian virtue dataset" make -C "${ROOT_DIR}" build-christian-virtue-sft
run_step "Run local smoke train" make -C "${ROOT_DIR}" train-christian-virtue-qwen2-5-1-5b-local-smoke
run_step "Run canonical local-baseline train" make -C "${ROOT_DIR}" train-christian-virtue-qwen2-5-1-5b-local-baseline
run_step "Generate and evaluate base-model test predictions" make -C "${ROOT_DIR}" eval-christian-virtue-qwen2-5-1-5b-local-base-test
run_step "Generate and evaluate adapter test predictions" make -C "${ROOT_DIR}" eval-christian-virtue-qwen2-5-1-5b-local-adapter-test
run_step "Compare base and adapter test runs" make -C "${ROOT_DIR}" compare-christian-virtue-qwen2-5-1-5b-local-test
run_step "Rebuild the curated local-baseline report" make -C "${ROOT_DIR}" report-christian-virtue-qwen2-5-1-5b-local-baseline
run_step "Run the publication verification gate" make -C "${ROOT_DIR}" verify-christian-virtue-qwen2-5-1-5b-local-publishable

echo
echo "Canonical local reproduction completed."
echo
echo "Key outputs:"
echo "- Report: ${REPORT_PATH}"
echo "- Local adapter package: ${PACKAGE_DIR}"
echo "- Latest train run: ${TRAIN_LATEST}"
echo "- Latest base eval run: ${BASE_LATEST}"
echo "- Latest adapter eval run: ${ADAPTER_LATEST}"
