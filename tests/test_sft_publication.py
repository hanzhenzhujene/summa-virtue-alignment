from __future__ import annotations

import json
from pathlib import Path

from summa_moral_graph.sft.publication import release_target_from_train_run, write_adapter_package


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_write_adapter_package_copies_files_and_writes_metadata(tmp_path) -> None:
    train_run_dir = tmp_path / "runs" / "pilot_lite" / "20260418_101010"
    base_run_dir = tmp_path / "runs" / "base_test" / "20260418_111111"
    adapter_run_dir = tmp_path / "runs" / "adapter_test" / "20260418_121212"
    package_dir = tmp_path / "artifacts" / "package"
    report_path = Path("docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md")
    dataset_card_path = Path("docs/christian_virtue_dataset_card.md")

    train_run_dir.mkdir(parents=True, exist_ok=True)
    (train_run_dir / "adapter_model.safetensors").write_text("weights", encoding="utf-8")
    (train_run_dir / "adapter_config.json").write_text("{}", encoding="utf-8")
    _write_json(
        train_run_dir / "train_metadata.json",
        {
            "git_commit": "abc123",
            "model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
            "run_id": "20260418_101010",
        },
    )
    _write_json(train_run_dir / "run_manifest.json", {"run_id": "20260418_101010"})
    _write_json(train_run_dir / "environment.json", {"python": "3.12.2"})
    (train_run_dir / "config_snapshot.yaml").write_text("run_name: fixture\n", encoding="utf-8")
    _write_json(
        base_run_dir / "metrics.json",
        {
            "overall": {"citation_exact_match": 0.0},
            "by_task_type": {
                "reviewed_relation_explanation": {"citation_exact_match": 0.0, "count": 2},
                "citation_grounded_moral_answer": {"citation_exact_match": 0.0, "count": 3},
            },
            "by_tract": {
                "theological_virtues": {"citation_exact_match": 0.0, "count": 2},
                "connected_virtues_109_120": {"citation_exact_match": 0.0, "count": 1},
            },
        },
    )
    _write_json(
        adapter_run_dir / "metrics.json",
        {
            "overall": {"citation_exact_match": 0.2},
            "by_task_type": {
                "reviewed_relation_explanation": {"citation_exact_match": 0.5, "count": 2},
                "citation_grounded_moral_answer": {"citation_exact_match": 0.0, "count": 3},
            },
            "by_tract": {
                "theological_virtues": {"citation_exact_match": 0.5, "count": 2},
                "connected_virtues_109_120": {"citation_exact_match": 0.0, "count": 1},
            },
        },
    )

    written_dir = write_adapter_package(
        train_run_dir=train_run_dir,
        base_eval_run_dir=base_run_dir,
        adapter_eval_run_dir=adapter_run_dir,
        package_dir=package_dir,
        hf_repo_id="JennyZhu0822/demo",
        release_tag="demo-tag",
        github_repo_url="https://github.com/hanzhenzhujene/summa-moral-graph-fork",
        report_path=report_path,
        dataset_card_path=dataset_card_path,
    )

    assert written_dir == package_dir
    assert (package_dir / "adapter_model.safetensors").exists()
    assert (package_dir / "adapter_config.json").exists()
    assert (package_dir / "README.md").exists()
    assert (package_dir / "release_notes.md").exists()
    manifest = json.loads((package_dir / "package_manifest.json").read_text(encoding="utf-8"))
    assert manifest["hf_repo_id"] == "JennyZhu0822/demo"
    assert manifest["github_repo_url"] == "https://github.com/hanzhenzhujene/summa-moral-graph-fork"
    assert manifest["local_train_run_id"] == "20260418_101010"
    assert manifest["summary"]["strongest_task"]["label"] == "Reviewed relation explanation"
    assert manifest["summary"]["strongest_tract"]["label"] == "Theological virtues"
    assert manifest["summary"]["weakest_task"]["label"] == "Citation-grounded moral answer"
    assert (
        manifest["published_report_path"]
        == "docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md"
    )
    readme = (package_dir / "README.md").read_text(encoding="utf-8")
    release_notes = (package_dir / "release_notes.md").read_text(encoding="utf-8")
    assert readme.startswith("---\n")
    assert "pipeline_tag: text-generation" in readme
    assert "docs/christian_virtue_dataset_card.md" in readme
    assert "## Executive Readout" in readme
    assert "Strongest task slice" in readme
    assert "Hardest task type" in readme
    assert "github.com/hanzhenzhujene/summa-moral-graph-fork/releases/tag/demo-tag" in readme
    assert "make verify-christian-virtue-qwen2-5-1-5b-local-publishable" in readme
    assert "## Executive Readout" in release_notes
    assert "Strongest tract slice" in release_notes
    assert "Zero-gain tracts" in release_notes
    assert "make verify-christian-virtue-qwen2-5-1-5b-local-publishable" in release_notes
    assert str(tmp_path) not in readme


def test_release_target_from_train_run_uses_train_metadata_git_commit(tmp_path) -> None:
    train_run_dir = tmp_path / "runs" / "pilot_lite" / "20260418_101010"
    _write_json(
        train_run_dir / "train_metadata.json",
        {
            "git_commit": "abc123deadbeef",
            "model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
            "run_id": "20260418_101010",
        },
    )

    assert release_target_from_train_run(train_run_dir) == "abc123deadbeef"
