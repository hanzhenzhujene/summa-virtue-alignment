from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import build_dataset, load_dataset_build_config, serialize_built_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/sft/christian_virtue_v1.yaml",
        help="Path to the SFT dataset build config.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional override for the dataset export directory.",
    )
    parser.add_argument(
        "--sample-output-path",
        help="Optional override for the sample artifact path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_dataset_build_config(args.config)
    serialization = config.serialization
    if args.output_dir or args.sample_output_path:
        serialization = serialization.model_copy(
            update={
                "output_dir": Path(args.output_dir).resolve()
                if args.output_dir
                else serialization.output_dir,
                "sample_output_path": Path(args.sample_output_path).resolve()
                if args.sample_output_path
                else serialization.sample_output_path,
            }
        )
        config = config.model_copy(update={"serialization": serialization})

    dataset = build_dataset(config)
    summary = serialize_built_dataset(dataset)
    summary["manifest"] = dataset.manifest
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
