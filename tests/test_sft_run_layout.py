from __future__ import annotations

from datetime import datetime

from summa_moral_graph.sft.run_layout import (
    create_timestamped_run_dir,
    default_evaluation_paths,
    run_artifacts_for_dir,
)


def test_run_artifacts_for_dir_uses_standard_names(tmp_path) -> None:
    run_dir = tmp_path / "runs" / "fixture"

    artifacts = run_artifacts_for_dir(run_dir)

    assert artifacts.config_snapshot_path == run_dir / "config_snapshot.yaml"
    assert artifacts.environment_path == run_dir / "environment.json"
    assert artifacts.metrics_path == run_dir / "metrics.json"
    assert artifacts.report_path == run_dir / "report.md"
    assert artifacts.predictions_path == run_dir / "predictions.jsonl"
    assert artifacts.partial_predictions_path == run_dir / "predictions.partial.jsonl"
    assert artifacts.run_manifest_path == run_dir / "run_manifest.json"
    assert artifacts.train_metadata_path == run_dir / "train_metadata.json"
    assert artifacts.train_log_history_path == run_dir / "train_log_history.jsonl"
    assert artifacts.subset_summary_path == run_dir / "subset_summary.json"
    assert artifacts.stdout_log_path == run_dir / "stdout.log"
    assert artifacts.stderr_log_path == run_dir / "stderr.log"
    assert artifacts.command_log_path == run_dir / "command.log"


def test_default_evaluation_paths_follow_prediction_run_dir(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    predictions_path = tmp_path / "runs" / "base_test" / "predictions.jsonl"

    report_path, metrics_path = default_evaluation_paths(dataset_dir, predictions_path)

    assert report_path == predictions_path.parent / "report.md"
    assert metrics_path == predictions_path.parent / "metrics.json"


def test_default_evaluation_paths_fall_back_to_dataset_dir(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"

    report_path, metrics_path = default_evaluation_paths(dataset_dir)

    assert report_path == dataset_dir / "evaluation_report.md"
    assert metrics_path == dataset_dir / "evaluation_metrics.json"


def test_create_timestamped_run_dir_uses_timestamp_and_suffix(tmp_path) -> None:
    root_dir = tmp_path / "runs" / "local_baseline"

    first = create_timestamped_run_dir(root_dir, now=datetime(2026, 4, 17, 9, 30, 15))
    second = create_timestamped_run_dir(root_dir, now=datetime(2026, 4, 17, 9, 30, 15))

    assert first.name == "20260417_093015"
    assert second.name == "20260417_093015_01"
