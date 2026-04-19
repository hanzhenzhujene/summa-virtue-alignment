"""Timestamped run-directory and environment-manifest helpers for SFT experiments."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True)
class RunArtifacts:
    run_dir: Path
    config_snapshot_path: Path
    environment_path: Path
    metrics_path: Path
    report_path: Path
    predictions_path: Path
    partial_predictions_path: Path
    run_manifest_path: Path
    train_metadata_path: Path
    train_log_history_path: Path
    stdout_log_path: Path
    stderr_log_path: Path
    command_log_path: Path


def run_artifacts_for_dir(run_dir: Path) -> RunArtifacts:
    return RunArtifacts(
        run_dir=run_dir,
        config_snapshot_path=run_dir / "config_snapshot.yaml",
        environment_path=run_dir / "environment.json",
        metrics_path=run_dir / "metrics.json",
        report_path=run_dir / "report.md",
        predictions_path=run_dir / "predictions.jsonl",
        partial_predictions_path=run_dir / "predictions.partial.jsonl",
        run_manifest_path=run_dir / "run_manifest.json",
        train_metadata_path=run_dir / "train_metadata.json",
        train_log_history_path=run_dir / "train_log_history.jsonl",
        stdout_log_path=run_dir / "stdout.log",
        stderr_log_path=run_dir / "stderr.log",
        command_log_path=run_dir / "command.log",
    )


def generate_run_id(now: datetime | None = None) -> str:
    current = now or datetime.now().astimezone()
    return current.strftime("%Y%m%d_%H%M%S")


def create_timestamped_run_dir(root_dir: Path, *, now: datetime | None = None) -> Path:
    root_dir.mkdir(parents=True, exist_ok=True)
    base_run_id = generate_run_id(now)
    candidate = root_dir / base_run_id
    suffix = 1
    while candidate.exists():
        candidate = root_dir / f"{base_run_id}_{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str))
            handle.write("\n")
    return path


def iso_timestamp(now: datetime | None = None) -> str:
    current = now or datetime.now().astimezone()
    return current.isoformat(timespec="seconds")


def current_git_commit(cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            check=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def installed_package_versions(packages: Iterable[str]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def dataset_manifest_path(dataset_dir: Path) -> Path | None:
    manifest_path = dataset_dir / "manifest.json"
    if manifest_path.exists():
        return manifest_path
    return None


def build_environment_snapshot(
    *,
    workspace_root: Path,
    resolved_device: str | None = None,
    torch_dtype: str | None = None,
) -> dict[str, Any]:
    package_versions = installed_package_versions(
        ["torch", "transformers", "peft", "trl", "accelerate"]
    )
    return {
        "cwd": str(Path.cwd()),
        "git_commit": current_git_commit(workspace_root),
        "platform": {
            "machine": platform.machine(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "system": platform.system(),
        },
        "resolved_device": resolved_device,
        "torch_dtype": torch_dtype,
        "versions": package_versions,
    }


def ensure_writable_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path, prefix=".write-check-", delete=True):
        pass
