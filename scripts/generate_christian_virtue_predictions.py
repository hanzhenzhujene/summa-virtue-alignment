from __future__ import annotations

import argparse
import json

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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_inference_config(args.config)
    if args.dry_run:
        print(json.dumps(describe_inference_plan(config), indent=2, sort_keys=True))
        return
    print(json.dumps(run_generation_inference(config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
