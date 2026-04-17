from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import load_metrics_file, write_comparison_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-metrics",
        required=True,
        help="Path to the baseline metrics.json.",
    )
    parser.add_argument(
        "--candidate-metrics",
        required=True,
        help="Path to the candidate metrics.json.",
    )
    parser.add_argument("--output", required=True, help="Markdown comparison report path.")
    parser.add_argument("--baseline-label", default="base", help="Label for the baseline run.")
    parser.add_argument("--candidate-label", default="adapter", help="Label for the candidate run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline_metrics_path = Path(args.baseline_metrics).resolve()
    candidate_metrics_path = Path(args.candidate_metrics).resolve()
    output_path = Path(args.output).resolve()

    baseline_metrics = load_metrics_file(baseline_metrics_path)
    candidate_metrics = load_metrics_file(candidate_metrics_path)
    write_comparison_report(
        baseline_metrics,
        candidate_metrics,
        output_path,
        baseline_label=args.baseline_label,
        candidate_label=args.candidate_label,
    )
    print(
        json.dumps(
            {
                "baseline_metrics": str(baseline_metrics_path),
                "candidate_metrics": str(candidate_metrics_path),
                "output_path": str(output_path),
                "baseline_label": args.baseline_label,
                "candidate_label": args.candidate_label,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
