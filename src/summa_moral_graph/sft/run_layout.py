from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True)
class RunArtifacts:
    run_dir: Path
    config_snapshot_path: Path
    metrics_path: Path
    report_path: Path
    predictions_path: Path
    partial_predictions_path: Path
    run_manifest_path: Path
    train_metadata_path: Path
    stdout_log_path: Path
    stderr_log_path: Path
    command_log_path: Path


def run_artifacts_for_dir(run_dir: Path) -> RunArtifacts:
    return RunArtifacts(
        run_dir=run_dir,
        config_snapshot_path=run_dir / "config_snapshot.yaml",
        metrics_path=run_dir / "metrics.json",
        report_path=run_dir / "report.md",
        predictions_path=run_dir / "predictions.jsonl",
        partial_predictions_path=run_dir / "predictions.partial.jsonl",
        run_manifest_path=run_dir / "run_manifest.json",
        train_metadata_path=run_dir / "train_metadata.json",
        stdout_log_path=run_dir / "stdout.log",
        stderr_log_path=run_dir / "stderr.log",
        command_log_path=run_dir / "command.log",
    )


def default_evaluation_paths(
    dataset_dir: Path, predictions_path: Path | None = None
) -> tuple[Path, Path]:
    if predictions_path is not None:
        run_dir = predictions_path.parent
        return run_dir / "report.md", run_dir / "metrics.json"
    return dataset_dir / "evaluation_report.md", dataset_dir / "evaluation_metrics.json"


def write_config_snapshot(
    output_dir: Path,
    *,
    config_path: Path | None,
    payload: dict[str, Any] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = run_artifacts_for_dir(output_dir).config_snapshot_path
    if config_path is not None and config_path.exists():
        snapshot_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
        return snapshot_path

    if payload is None:
        raise ValueError("payload is required when config_path is unavailable")

    snapshot_path.write_text(
        yaml.safe_dump(payload, sort_keys=True, allow_unicode=True),
        encoding="utf-8",
    )
    return snapshot_path


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def ensure_writable_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path, prefix=".write-check-", delete=True):
        pass
