#!/usr/bin/env bash
# Run the core local experiment loop from train through base-vs-adapter comparison.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="${1:-local-baseline}"
case "${MODE}" in
  local-baseline|extended)
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_train.sh" "${MODE}"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_compare.sh"
    ;;
  citation-frontier)
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_train.sh" "${MODE}"
    if [[ ! -f "${SCRIPT_DIR}/../runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/metrics.json" ]]; then
      bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh"
    fi
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh" "${MODE}"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_compare.sh" "${MODE}"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh"
    ;;
  accuracy-first)
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_train.sh" "${MODE}"
    if [[ ! -f "${SCRIPT_DIR}/../runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/metrics.json" ]]; then
      bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh"
    fi
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh" "${MODE}"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_compare.sh" "${MODE}"
    ;;
  justice-guarded)
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_train.sh" "${MODE}"
    if [[ ! -f "${SCRIPT_DIR}/../runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/metrics.json" ]]; then
      bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh"
    fi
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh" "${MODE}"
    bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_compare.sh" "${MODE}"
    ;;
  *)
    echo "The full local loop supports 'local-baseline', 'citation-frontier', 'accuracy-first', 'justice-guarded', and 'extended'." >&2
    exit 1
    ;;
esac
