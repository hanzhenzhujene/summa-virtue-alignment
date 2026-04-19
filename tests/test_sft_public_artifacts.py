from __future__ import annotations

import json
from pathlib import Path

from summa_moral_graph.sft.public_artifacts import (
    build_publication_doc_expectations,
    verify_publication_bundle,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_verify_publication_bundle_fixture(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    report_path = Path("docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md")
    package_manifest_path = (
        repo_root
        / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite_adapter"
        / "package_manifest.json"
    )
    package_manifest = {
        "adapter_eval_run_dir": (
            "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/20260418_203546"
        ),
        "adapter_metrics": {
            "citation_exact_match": 0.15,
            "citation_overlap": 0.15,
            "citation_partial_match": 0.15,
            "count": 233,
            "relation_type_accuracy": None,
        },
        "base_eval_run_dir": (
            "runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/20260418_143349"
        ),
        "base_metrics": {
            "citation_exact_match": 0.0,
            "citation_overlap": 0.0,
            "citation_partial_match": 0.0,
            "count": 233,
            "relation_type_accuracy": None,
        },
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "dataset_dir": "data/processed/sft/exports/christian_virtue_v1",
        "dataset_manifest_path": "data/processed/sft/exports/christian_virtue_v1/manifest.json",
        "git_commit": "abc123",
        "github_release_url": "https://github.com/example/repo/releases/tag/demo-tag",
        "hf_repo_id": "example/repo",
        "hf_repo_url": "https://huggingface.co/example/repo",
        "local_train_run_id": "20260418_193038",
        "published_report_path": str(report_path),
        "train_run_dir": "runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite/20260418_193038",
    }

    _write_json(package_manifest_path, package_manifest)
    _write_json(
        repo_root / package_manifest["dataset_manifest_path"],
        {"dataset_name": "christian_virtue_v1"},
    )

    train_run_dir = repo_root / package_manifest["train_run_dir"]
    base_run_dir = repo_root / package_manifest["base_eval_run_dir"]
    adapter_run_dir = repo_root / package_manifest["adapter_eval_run_dir"]

    _write_json(
        train_run_dir / "train_metadata.json",
        {
            "git_commit": "abc123",
            "model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
            "run_id": "20260418_193038",
        },
    )
    _write_json(base_run_dir / "metrics.json", {"overall": package_manifest["base_metrics"]})
    _write_json(adapter_run_dir / "metrics.json", {"overall": package_manifest["adapter_metrics"]})

    for relative_doc_path, expected_substrings in build_publication_doc_expectations(
        package_manifest
    ).items():
        document_path = repo_root / relative_doc_path
        document_path.parent.mkdir(parents=True, exist_ok=True)
        document_path.write_text("\n".join(expected_substrings), encoding="utf-8")

    summary = verify_publication_bundle(
        repo_root=repo_root,
        package_manifest_path=package_manifest_path,
    )

    assert summary["local_train_run_id"] == "20260418_193038"
    assert abs(summary["citation_exact_gain"] - 0.15) < 1e-9


def test_public_fine_tune_docs_and_exports_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    expected_paths = [
        repo_root / "docs/fine_tune_with_summa_moral_graph.md",
        repo_root / "docs/christian_virtue_sft.md",
        repo_root / "docs/christian_virtue_dataset_card.md",
        repo_root / "docs/reports/christian_virtue_experiments.md",
        repo_root / "docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/manifest.json",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/train.jsonl",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/benchmarks/test.jsonl",
        repo_root / "data/processed/sft/exports/christian_virtue_v1_ood/manifest.json",
        repo_root / "data/processed/sft/exports/christian_virtue_v1_ood/benchmarks/ood_test.jsonl",
        repo_root / "data/processed/sft/samples/christian_virtue_v1_sample.jsonl",
        repo_root / "data/processed/sft/samples/christian_virtue_goal_demo_panel.jsonl",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_readme_and_gitignore_expose_public_fine_tune_surface() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    gitignore_text = (repo_root / ".gitignore").read_text(encoding="utf-8")

    assert "Fine-Tune Your Model With Summa Moral Graph" in readme_text
    assert "docs/fine_tune_with_summa_moral_graph.md" in readme_text
    assert "pilot-lite" in readme_text
    assert "!data/processed/sft/exports/christian_virtue_v1/**" in gitignore_text
    assert "!data/processed/sft/exports/christian_virtue_v1_ood/**" in gitignore_text


def test_repo_publication_bundle_is_coherent() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    package_manifest_path = (
        repo_root
        / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite_adapter"
        / "package_manifest.json"
    )

    summary = verify_publication_bundle(
        repo_root=repo_root,
        package_manifest_path=package_manifest_path,
    )

    assert summary["adapter_citation_exact_match"] > summary["base_citation_exact_match"]
