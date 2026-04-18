from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import (
    describe_inference_plan,
    load_inference_config,
    run_generation_inference,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/inference/qwen3_4b_base_test.yaml",
        help="Path to the inference config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print the resolved inference plan.",
    )
    parser.add_argument("--output-dir", help="Optional output directory override.")
    parser.add_argument("--adapter-path", help="Optional adapter path override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_inference_config(args.config)
    if args.output_dir:
        config = config.model_copy(update={"output_dir": Path(args.output_dir).resolve()})
    if args.adapter_path:
        config = config.model_copy(update={"adapter_path": Path(args.adapter_path).resolve()})
    if args.dry_run:
        print(json.dumps(describe_inference_plan(config), indent=2, sort_keys=True))
        return
    print(json.dumps(run_generation_inference(config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
