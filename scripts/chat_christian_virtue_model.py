"""Open an interactive chat session with a local Christian virtue base model or adapter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from summa_moral_graph.sft import (
    DEFAULT_CHAT_OUTPUT_ROOT,
    DEFAULT_CHAT_SYSTEM_PROMPT,
    describe_chat_plan,
    load_inference_config,
    run_interactive_chat,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/inference/qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml",
        help="Path to the inference config that defines the base model and default adapter.",
    )
    parser.add_argument("--adapter-path", help="Optional adapter path override.")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_CHAT_OUTPUT_ROOT),
        help="Root directory for timestamped chat session logs.",
    )
    parser.add_argument(
        "--system-prompt",
        default=DEFAULT_CHAT_SYSTEM_PROMPT,
        help="Optional system prompt. Use --no-system-prompt to disable it entirely.",
    )
    parser.add_argument(
        "--no-system-prompt",
        action="store_true",
        help="Disable the default evidence-first system prompt.",
    )
    parser.add_argument(
        "--one-shot",
        help="Run a single prompt non-interactively and exit after one assistant reply.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        help="Optional max_new_tokens override for chat generation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved chat plan without loading the model.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_inference_config(args.config)
    if args.adapter_path:
        config = config.model_copy(update={"adapter_path": Path(args.adapter_path).resolve()})
    if args.max_new_tokens is not None:
        config = config.model_copy(update={"max_new_tokens": args.max_new_tokens})
    output_root = Path(args.output_root).resolve()
    system_prompt = None if args.no_system_prompt else args.system_prompt
    if args.dry_run:
        import json

        print(
            json.dumps(
                describe_chat_plan(
                    config,
                    output_root=output_root,
                    system_prompt=system_prompt,
                    one_shot=args.one_shot,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return
    manifest = run_interactive_chat(
        config,
        output_root=output_root,
        system_prompt=system_prompt,
        one_shot=args.one_shot,
        command_argv=["python", "scripts/chat_christian_virtue_model.py", *sys.argv[1:]],
    )
    print("\nSession saved:")
    print(f"- run dir: {manifest['run_dir']}")
    print(f"- transcript: {manifest['transcript_markdown_path']}")
    print(f"- manifest: {manifest['run_manifest_path']}")


if __name__ == "__main__":
    main()
