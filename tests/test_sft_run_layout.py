from __future__ import annotations

from summa_moral_graph.sft.run_layout import default_evaluation_paths, run_artifacts_for_dir


def test_run_artifacts_for_dir_uses_standard_names(tmp_path) -> None:
    run_dir = tmp_path / "runs" / "fixture"

    artifacts = run_artifacts_for_dir(run_dir)

    assert artifacts.config_snapshot_path == run_dir / "config_snapshot.yaml"
    assert artifacts.metrics_path == run_dir / "metrics.json"
    assert artifacts.report_path == run_dir / "report.md"
    assert artifacts.predictions_path == run_dir / "predictions.jsonl"
    assert artifacts.partial_predictions_path == run_dir / "predictions.partial.jsonl"
    assert artifacts.run_manifest_path == run_dir / "run_manifest.json"
    assert artifacts.train_metadata_path == run_dir / "train_metadata.json"
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
