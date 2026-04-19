#!/usr/bin/env bash
# Run the full canonical local Qwen2.5-1.5B publication loop from dataset build through verify.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

run_step() {
  local label="$1"
  shift
  echo
  echo "==> ${label}"
  "$@"
}

run_step "Build Christian virtue dataset" make -C "${ROOT_DIR}" build-christian-virtue-sft
run_step "Run local smoke train" make -C "${ROOT_DIR}" train-christian-virtue-qwen2-5-1-5b-local-smoke
run_step "Run canonical pilot-lite train" make -C "${ROOT_DIR}" train-christian-virtue-qwen2-5-1-5b-local-pilot-lite
run_step "Generate and evaluate base-model test predictions" make -C "${ROOT_DIR}" eval-christian-virtue-qwen2-5-1-5b-local-base-test
run_step "Generate and evaluate adapter test predictions" make -C "${ROOT_DIR}" eval-christian-virtue-qwen2-5-1-5b-local-adapter-test
run_step "Compare base and adapter test runs" make -C "${ROOT_DIR}" compare-christian-virtue-qwen2-5-1-5b-local-test
run_step "Rebuild the curated pilot-lite report" make -C "${ROOT_DIR}" report-christian-virtue-qwen2-5-1-5b-local-pilot-lite
run_step "Run the publication verification gate" make -C "${ROOT_DIR}" verify-christian-virtue-qwen2-5-1-5b-local-publishable

echo
echo "Canonical local reproduction completed."
