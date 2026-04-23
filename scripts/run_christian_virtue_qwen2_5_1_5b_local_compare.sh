#!/usr/bin/env bash
# Compare the latest local base and adapter evaluation runs and write a markdown summary.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

MODE="${1:-local-baseline}"
BASE_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/base_test"
ADAPTER_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test"
FULL_CORPUS_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_adapter_test"
CITATION_FRONTIER_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_adapter_test"
ACCURACY_FIRST_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid_adapter_test"
JUSTICE_GUARDED_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/justice_guarded_citation_repair_adapter_test"

case "${MODE}" in
  local-baseline)
    BASE_METRICS="${BASE_ROOT}/latest/metrics.json"
    CANDIDATE_METRICS="${ADAPTER_ROOT}/latest/metrics.json"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/compare_test"
    BASELINE_LABEL="qwen2.5-1.5b-base-test"
    CANDIDATE_LABEL="qwen2.5-1.5b-local-baseline-adapter-test"
    BASELINE_HINT="Run the base evaluation first."
    CANDIDATE_HINT="Run the adapter evaluation first."
    ;;
  full-corpus)
    BASE_METRICS="${ADAPTER_ROOT}/latest/metrics.json"
    CANDIDATE_METRICS="${FULL_CORPUS_ROOT}/latest/metrics.json"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_compare_test"
    BASELINE_LABEL="qwen2.5-1.5b-local-baseline-adapter-test"
    CANDIDATE_LABEL="qwen2.5-1.5b-full-corpus-adapter-test"
    BASELINE_HINT="Run the canonical local-baseline adapter evaluation first."
    CANDIDATE_HINT="Run the full-corpus adapter evaluation first."
    ;;
  citation-frontier)
    BASE_METRICS="${ADAPTER_ROOT}/latest/metrics.json"
    CANDIDATE_METRICS="${CITATION_FRONTIER_ROOT}/latest/metrics.json"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_compare_test"
    BASELINE_LABEL="qwen2.5-1.5b-local-baseline-adapter-test"
    CANDIDATE_LABEL="qwen2.5-1.5b-citation-frontier-adapter-test"
    BASELINE_HINT="Run the canonical local-baseline adapter evaluation first."
    CANDIDATE_HINT="Run the citation-frontier adapter evaluation first."
    ;;
  accuracy-first)
    BASE_METRICS="${ADAPTER_ROOT}/latest/metrics.json"
    CANDIDATE_METRICS="${ACCURACY_FIRST_ROOT}/latest/metrics.json"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid_compare_test"
    BASELINE_LABEL="qwen2.5-1.5b-local-baseline-adapter-test"
    CANDIDATE_LABEL="qwen2.5-1.5b-accuracy-first-hybrid-adapter-test"
    BASELINE_HINT="Run the canonical local-baseline adapter evaluation first."
    CANDIDATE_HINT="Run the accuracy-first adapter evaluation first."
    ;;
  justice-guarded)
    BASE_METRICS="${ADAPTER_ROOT}/latest/metrics.json"
    CANDIDATE_METRICS="${JUSTICE_GUARDED_ROOT}/latest/metrics.json"
    RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/justice_guarded_citation_repair_compare_test"
    BASELINE_LABEL="qwen2.5-1.5b-local-baseline-adapter-test"
    CANDIDATE_LABEL="qwen2.5-1.5b-justice-guarded-citation-repair-adapter-test"
    BASELINE_HINT="Run the canonical local-baseline adapter evaluation first."
    CANDIDATE_HINT="Run the justice-guarded adapter evaluation first."
    ;;
  *)
    echo "Unknown mode: ${MODE}. Expected 'local-baseline', 'full-corpus', 'citation-frontier', 'accuracy-first', or 'justice-guarded'." >&2
    exit 1
    ;;
esac

if [[ ! -f "${BASE_METRICS}" ]]; then
  echo "Baseline metrics not found: ${BASE_METRICS}" >&2
  echo "${BASELINE_HINT}" >&2
  exit 1
fi

if [[ ! -f "${CANDIDATE_METRICS}" ]]; then
  echo "Candidate metrics not found: ${CANDIDATE_METRICS}" >&2
  echo "${CANDIDATE_HINT}" >&2
  exit 1
fi

RUN_DIR="$(create_timestamped_run_dir "${RUN_ROOT}")"

init_run_dir "${RUN_DIR}"

run_logged \
  "${RUN_DIR}" \
  "${PYTHON_BIN}" \
  "${ROOT_DIR}/scripts/compare_christian_virtue_runs.py" \
  --baseline-metrics \
  "${BASE_METRICS}" \
  --candidate-metrics \
  "${CANDIDATE_METRICS}" \
  --baseline-label \
  "${BASELINE_LABEL}" \
  --candidate-label \
  "${CANDIDATE_LABEL}" \
  --output \
  "${RUN_DIR}/report.md"

link_latest_run "${RUN_ROOT}" "${RUN_DIR}"
