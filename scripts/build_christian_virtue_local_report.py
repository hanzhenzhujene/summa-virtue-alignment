from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft import (
    write_publishable_local_report,
    write_task_comparison_svg,
    write_training_curves_svg,
)
from summa_moral_graph.utils.paths import REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default=REPO_ROOT / "data/processed/sft/exports/christian_virtue_v1",
        type=Path,
    )
    parser.add_argument(
        "--train-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite/latest",
        type=Path,
    )
    parser.add_argument(
        "--base-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--adapter-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--goal-demo-panel",
        default=REPO_ROOT / "data/processed/sft/samples/christian_virtue_goal_demo_panel.jsonl",
        type=Path,
    )
    parser.add_argument(
        "--output",
        default=REPO_ROOT / "docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md",
        type=Path,
    )
    parser.add_argument(
        "--assets-dir",
        default=REPO_ROOT / "docs/reports/assets",
        type=Path,
    )
    parser.add_argument("--published-model-url")
    parser.add_argument("--release-url")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    training_curves_path = (
        args.assets_dir / "christian_virtue_qwen2_5_1_5b_pilot_lite_training_curves.svg"
    )
    comparison_path = args.assets_dir / "christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg"

    write_training_curves_svg(args.train_run_dir / "train_log_history.jsonl", training_curves_path)
    base_metrics_path = args.base_run_dir / "metrics.json"
    adapter_metrics_path = args.adapter_run_dir / "metrics.json"
    write_task_comparison_svg(
        json.loads(base_metrics_path.read_text(encoding="utf-8")),
        json.loads(adapter_metrics_path.read_text(encoding="utf-8")),
        comparison_path,
    )
    report_path = write_publishable_local_report(
        dataset_dir=args.dataset_dir,
        train_run_dir=args.train_run_dir,
        base_run_dir=args.base_run_dir,
        adapter_run_dir=args.adapter_run_dir,
        panel_path=args.goal_demo_panel,
        output_path=args.output,
        training_curves_asset_path=Path(f"./assets/{training_curves_path.name}"),
        comparison_asset_path=Path(f"./assets/{comparison_path.name}"),
        published_model_url=args.published_model_url,
        release_url=args.release_url,
    )
    print(
        json.dumps(
            {
                "output_path": str(report_path),
                "training_curves_path": str(training_curves_path),
                "comparison_path": str(comparison_path),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
