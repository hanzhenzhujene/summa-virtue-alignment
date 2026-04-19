#!/usr/bin/env bash
# Run the core local experiment loop from train through base-vs-adapter comparison.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="${1:-local-baseline}"
if [[ "${MODE}" != "local-baseline" && "${MODE}" != "extended" ]]; then
  echo "The full local loop supports 'local-baseline' and 'extended'." >&2
  exit 1
fi

bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_train.sh" "${MODE}"
bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh"
bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh"
bash "${SCRIPT_DIR}/run_christian_virtue_qwen2_5_1_5b_local_compare.sh"
