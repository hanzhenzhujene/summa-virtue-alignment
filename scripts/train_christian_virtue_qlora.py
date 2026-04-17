from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import describe_training_plan, load_training_config, run_qlora_training


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/train/qwen3_4b_qlora.yaml",
        help="Path to the training config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the resolved training plan.",
    )
    parser.add_argument("--output-dir", help="Optional output directory override.")
    parser.add_argument("--run-name", help="Optional run name override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_training_config(args.config)
    updates = {}
    if args.output_dir:
        updates["output_dir"] = Path(args.output_dir).resolve()
    if args.run_name:
        updates["run_name"] = args.run_name
    if updates:
        config = config.model_copy(update=updates)
    if args.dry_run:
        print(json.dumps(describe_training_plan(config), indent=2, sort_keys=True))
        return
    print(json.dumps(run_qlora_training(config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
