#!/usr/bin/env bash
# Launch the long-running full-corpus local loop in the background and record a PID + launch log.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/christian_virtue_small_common.sh
source "${SCRIPT_DIR}/christian_virtue_small_common.sh"
resolve_python_bin

RUN_ROOT="${ROOT_DIR}/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus"
mkdir -p "${RUN_ROOT}"

LAUNCH_ID="$("${PYTHON_BIN}" - <<'PY'
from summa_moral_graph.sft.run_layout import generate_run_id

print(generate_run_id())
PY
)"

LAUNCH_LOG="${RUN_ROOT}/launch_full_corpus_loop_${LAUNCH_ID}.log"
PID_FILE="${RUN_ROOT}/launch_full_corpus_loop_${LAUNCH_ID}.pid"
LATEST_LOG_LINK="${RUN_ROOT}/launch_latest.log"
LATEST_PID_FILE="${RUN_ROOT}/launch_latest.pid"

COMMAND=(bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_loop.sh" full-corpus)

{
  printf 'Launch id: %s\n' "${LAUNCH_ID}"
  printf 'Workspace root: %s\n' "${ROOT_DIR}"
  printf '$ '
  printf '%q ' "${COMMAND[@]}"
  printf '\n'
} > "${LAUNCH_LOG}"

nohup "${COMMAND[@]}" >> "${LAUNCH_LOG}" 2>&1 < /dev/null &
PID=$!
disown "${PID}" 2>/dev/null || true

printf '%s\n' "${PID}" > "${PID_FILE}"
printf '%s\n' "${PID}" > "${LATEST_PID_FILE}"
ln -sfn "$(basename "${LAUNCH_LOG}")" "${LATEST_LOG_LINK}"

echo "Launched full-corpus loop in background."
echo "PID: ${PID}"
echo "PID file: ${PID_FILE}"
echo "Launch log: ${LAUNCH_LOG}"
echo "Latest launch log: ${LATEST_LOG_LINK}"
echo "Monitor with: tail -f ${LAUNCH_LOG}"
echo "When training starts, the active run directory will appear under: ${RUN_ROOT}/latest"
