"""Run a lightweight qualitative smoke test over Christian virtue chat behavior."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import (
    DEFAULT_CHAT_SMOKE_OUTPUT_ROOT,
    load_inference_config,
    run_chat_smoke_suite,
)
from summa_moral_graph.utils.paths import REPO_ROOT

DEFAULT_CONFIG_PATH = (
    REPO_ROOT / "configs" / "inference" / "qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Inference config used to log model, adapter, and dataset metadata.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_CHAT_SMOKE_OUTPUT_ROOT,
        help="Root directory for timestamped chat smoke runs.",
    )
    parser.add_argument(
        "--with-model",
        action="store_true",
        help=(
            "Load the local model bundle and run the full chat path instead of "
            "deterministic-only."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved smoke-test plan without writing a run directory.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_inference_config(args.config)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "adapter_path": str(config.adapter_path) if config.adapter_path else None,
                    "config_path": str(args.config),
                    "dataset_dir": str(config.dataset_dir),
                    "include_model": bool(args.with_model),
                    "model_name_or_path": config.model_name_or_path,
                    "output_root": str(args.output_root),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return

    result = run_chat_smoke_suite(
        config=config,
        output_root=args.output_root,
        include_model=bool(args.with_model),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
