"""Run a fast frontier audit for the current Christian virtue local baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft.frontier import (
    analyze_citation_frontier,
    write_citation_frontier_artifacts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit the current citation-grounded moral-answer frontier using existing "
            "base and adapter predictions."
        )
    )
    parser.add_argument(
        "--dataset-dir",
        default="data/processed/sft/exports/christian_virtue_v1",
        help="Dataset export directory with all.jsonl.",
    )
    parser.add_argument(
        "--base-predictions",
        default="runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/predictions.jsonl",
        help="Base-model predictions JSONL path.",
    )
    parser.add_argument(
        "--adapter-predictions",
        default=(
            "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest/predictions.jsonl"
        ),
        help="Adapter predictions JSONL path.",
    )
    parser.add_argument(
        "--split",
        default="test",
        help="Held-out split to audit.",
    )
    parser.add_argument(
        "--task-type",
        default="citation_grounded_moral_answer",
        help="Task family to audit.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/christian_virtue_citation_frontier_audit.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--metrics-path",
        default="docs/reports/christian_virtue_citation_frontier_audit.json",
        help="JSON metrics output path.",
    )
    parser.add_argument(
        "--figure-path",
        default="docs/reports/assets/christian_virtue_citation_frontier_modes.svg",
        help="SVG figure output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    analysis = analyze_citation_frontier(
        dataset_dir=Path(args.dataset_dir).resolve(),
        base_predictions_path=Path(args.base_predictions).resolve(),
        adapter_predictions_path=Path(args.adapter_predictions).resolve(),
        split_name=args.split,
        task_type=args.task_type,
    )
    artifacts = write_citation_frontier_artifacts(
        analysis=analysis,
        report_path=Path(args.report_path).resolve(),
        metrics_path=Path(args.metrics_path).resolve(),
        figure_path=Path(args.figure_path).resolve(),
    )
    print(
        json.dumps(
            {
                **artifacts,
                "task_type": args.task_type,
                "split": args.split,
                "count": analysis["overall"]["adapter"]["count"],
                "adapter_exact_stable_id_rate": analysis["overall"]["adapter"][
                    "exact_stable_id_match_rate"
                ],
                "adapter_any_citation_signal_rate": analysis["overall"]["adapter"][
                    "any_citation_signal_rate"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
