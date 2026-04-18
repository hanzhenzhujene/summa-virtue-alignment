#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="${1:-pilot-lite}"
if [[ "${MODE}" != "pilot-lite" && "${MODE}" != "pilot" ]]; then
  echo "The full local loop supports 'pilot-lite' and 'pilot'." >&2
  exit 1
fi

bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_train.sh" "${MODE}"
bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh"
bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh"
bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_compare.sh"
