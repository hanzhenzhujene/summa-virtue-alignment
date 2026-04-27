"""Launch a local Gradio chat UI for the full-corpus Christian virtue adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

from summa_moral_graph.app.gradio_chat import (
    DEFAULT_GRADIO_CHAT_CONFIG_PATH,
    launch_gradio_chat_app,
)
from summa_moral_graph.sft import DEFAULT_CHAT_OUTPUT_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(DEFAULT_GRADIO_CHAT_CONFIG_PATH),
        help="Path to the inference config that defines the base model and default adapter.",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_CHAT_OUTPUT_ROOT),
        help="Root directory for timestamped chat session logs.",
    )
    parser.add_argument(
        "--server-name",
        default="127.0.0.1",
        help="Host interface for the local Gradio server.",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=7860,
        help="Local port for the Gradio chat server.",
    )
    parser.add_argument(
        "--no-inbrowser",
        action="store_true",
        help="Do not auto-open the Gradio app in a browser tab.",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Enable Gradio share mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    launch_gradio_chat_app(
        config_path=Path(args.config).resolve(),
        output_root=Path(args.output_root).resolve(),
        server_name=args.server_name,
        server_port=args.server_port,
        inbrowser=not args.no_inbrowser,
        share=args.share,
    )


if __name__ == "__main__":
    main()
