"""Evaluate Christian virtue predictions against held-out benchmark answers and citations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import (
    default_evaluation_paths,
    evaluate_predictions,
    write_markdown_report,
    write_metrics_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default="data/processed/sft/exports/christian_virtue_v1",
        help="Directory containing all.jsonl and split exports.",
    )
    parser.add_argument(
        "--predictions",
        help=(
            "Optional JSONL file of predictions. If omitted, self-evaluate against "
            "the reference data."
        ),
    )
    parser.add_argument(
        "--report-path",
        help="Optional markdown report path.",
    )
    parser.add_argument(
        "--metrics-path",
        help="Optional JSON metrics output path.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        help="Optional split names to evaluate, for example: test ood_test.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir).resolve()
    predictions_path = Path(args.predictions).resolve() if args.predictions else None
    default_report_path, default_metrics_path = default_evaluation_paths(
        dataset_dir,
        predictions_path,
    )
    report_path = Path(args.report_path).resolve() if args.report_path else default_report_path
    metrics_path = Path(args.metrics_path).resolve() if args.metrics_path else default_metrics_path
    metrics = evaluate_predictions(
        dataset_dir=dataset_dir,
        predictions_path=predictions_path,
        reference_splits=args.splits,
    )
    write_markdown_report(metrics, report_path)
    write_metrics_json(metrics, metrics_path)
    print(
        json.dumps(
            {
                "dataset_dir": str(dataset_dir),
                "metrics_path": str(metrics_path),
                "report_path": str(report_path),
                "overall": metrics["overall"],
                "by_split": metrics["by_split"],
                "by_tract": metrics["by_tract"],
                "by_support_type": metrics["by_support_type"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
