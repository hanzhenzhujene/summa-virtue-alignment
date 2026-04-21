from __future__ import annotations

import json
from pathlib import Path

from summa_moral_graph.sft.doc_links import (
    extract_markdown_targets,
    resolve_internal_markdown_target,
    validate_internal_markdown_links,
)
from summa_moral_graph.sft.public_artifacts import (
    build_publication_doc_expectations,
    find_machine_path_leaks,
    verify_publication_bundle,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_verify_publication_bundle_fixture(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    report_path = Path("docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md")
    package_manifest_path = (
        repo_root
        / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter"
        / "package_manifest.json"
    )
    package_manifest: dict[str, object] = {
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
        "github_repo_url": "https://github.com/example/repo",
        "github_release_url": "https://github.com/example/repo/releases/tag/demo-tag",
        "hf_repo_id": "example/repo",
        "hf_repo_url": "https://huggingface.co/example/repo",
        "local_train_run_id": "20260418_193038",
        "published_report_path": str(report_path),
        "summary": {
            "strongest_task": {
                "key": "reviewed_relation_explanation",
                "label": "Reviewed relation explanation",
                "count": 67,
                "baseline_exact": 0.0,
                "candidate_exact": 0.194,
                "delta_exact": 0.194,
            },
            "strongest_tract": {
                "key": "justice_core",
                "label": "Justice core",
                "count": 42,
                "baseline_exact": 0.0,
                "candidate_exact": 0.238,
                "delta_exact": 0.238,
            },
            "weakest_task": {
                "key": "citation_grounded_moral_answer",
                "label": "Citation-grounded moral answer",
                "count": 67,
                "baseline_exact": 0.0,
                "candidate_exact": 0.0,
                "delta_exact": 0.0,
            },
            "zero_gain_tracts": [
                {
                    "key": "connected_virtues_109_120",
                    "label": "Connected virtues (II-II qq.109-120)",
                    "count": 7,
                }
            ],
        },
        "train_run_dir": (
            "runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline/20260418_193038"
        ),
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

    package_dir = package_manifest_path.parent
    (package_dir / "README.md").write_text(
        "\n".join(
            [
                "## Executive Readout",
                str(package_manifest["github_release_url"]),
                str(package_manifest["hf_repo_url"]),
                "This published run uses a deliberately small 1.5B local demo model.",
                "Strongest task slice: `Reviewed relation explanation`",
                "Strongest tract slice: `Justice core`",
                "Full task/tract breakdowns and the qualitative goal-demo panel live in the "
                "published report.",
            ]
        ),
        encoding="utf-8",
    )
    (package_dir / "release_notes.md").write_text(
        "\n".join(
            [
                "## Executive Readout",
                str(package_manifest["hf_repo_url"]),
                "This published run uses a deliberately small local demo model.",
                "Strongest task slice: `Reviewed relation explanation`",
                "Strongest tract slice: `Justice core`",
                "Full task/tract breakdowns and the qualitative goal-demo panel live in the "
                "curated report.",
            ]
        ),
        encoding="utf-8",
    )

    summary = verify_publication_bundle(
        repo_root=repo_root,
        package_manifest_path=package_manifest_path,
    )

    assert summary["local_train_run_id"] == "20260418_193038"
    assert abs(summary["citation_exact_gain"] - 0.15) < 1e-9
    assert "README.md" in summary["checked_package_surfaces"]
    assert "release_notes.md" in summary["checked_package_surfaces"]
    assert "README.md" in summary["checked_path_leak_surfaces"]


def test_verify_publication_bundle_supports_repo_only_mode(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    report_path = Path("docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md")
    package_manifest_path = (
        repo_root
        / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter"
        / "package_manifest.json"
    )
    package_manifest: dict[str, object] = {
        "adapter_eval_run_dir": (
            "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest"
        ),
        "adapter_metrics": {
            "citation_exact_match": 0.3562231759656652,
            "citation_overlap": 0.3562231759656652,
            "citation_partial_match": 0.3562231759656652,
            "count": 233,
            "relation_type_accuracy": None,
        },
        "base_eval_run_dir": "runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest",
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
        "github_repo_url": "https://github.com/example/repo",
        "github_release_url": "https://github.com/example/repo/releases/tag/demo-tag",
        "hf_repo_id": "example/repo",
        "hf_repo_url": "https://huggingface.co/example/repo",
        "local_train_run_id": "20260420_160727",
        "published_report_path": str(report_path),
        "summary": {
            "strongest_task": {
                "key": "virtue_concept_explanation",
                "label": "Virtue concept explanation",
                "count": 32,
                "baseline_exact": 0.0,
                "candidate_exact": 0.65625,
                "delta_exact": 0.65625,
            },
            "strongest_tract": {
                "key": "justice_core",
                "label": "Justice core",
                "count": 42,
                "baseline_exact": 0.0,
                "candidate_exact": 0.4523809523809524,
                "delta_exact": 0.4523809523809524,
            },
            "weakest_task": {
                "key": "citation_grounded_moral_answer",
                "label": "Citation-grounded moral answer",
                "count": 67,
                "baseline_exact": 0.0,
                "candidate_exact": 0.0,
                "delta_exact": 0.0,
            },
            "zero_gain_tracts": [],
        },
        "train_run_dir": "runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline/latest",
    }

    _write_json(package_manifest_path, package_manifest)
    _write_json(
        repo_root / package_manifest["dataset_manifest_path"],
        {"dataset_name": "christian_virtue_v1"},
    )

    for relative_doc_path, expected_substrings in build_publication_doc_expectations(
        package_manifest
    ).items():
        document_path = repo_root / relative_doc_path
        document_path.parent.mkdir(parents=True, exist_ok=True)
        document_path.write_text("\n".join(expected_substrings), encoding="utf-8")

    package_dir = package_manifest_path.parent
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "README.md").write_text(
        "\n".join(
            [
                "## Executive Readout",
                str(package_manifest["github_release_url"]),
                str(package_manifest["hf_repo_url"]),
                "This published run uses a deliberately small 1.5B local demo model.",
                "Strongest task slice: `Virtue concept explanation`",
                "Strongest tract slice: `Justice core`",
                "Full task/tract breakdowns and the qualitative goal-demo panel live in the "
                "published report.",
            ]
        ),
        encoding="utf-8",
    )
    (package_dir / "release_notes.md").write_text(
        "\n".join(
            [
                "## Executive Readout",
                str(package_manifest["hf_repo_url"]),
                "This published run uses a deliberately small local demo model.",
                "Strongest task slice: `Virtue concept explanation`",
                "Strongest tract slice: `Justice core`",
                "Full task/tract breakdowns and the qualitative goal-demo panel live in the "
                "curated report.",
            ]
        ),
        encoding="utf-8",
    )

    summary = verify_publication_bundle(
        repo_root=repo_root,
        package_manifest_path=package_manifest_path,
    )

    assert summary["run_artifact_verification_mode"] == "package_manifest_only"
    assert summary["missing_run_artifact_paths"] == [
        "train_run_dir",
        "base_eval_run_dir",
        "adapter_eval_run_dir",
    ]
    assert abs(summary["citation_exact_gain"] - 0.3562231759656652) < 1e-9


def test_markdown_link_resolution_handles_internal_and_external_targets(tmp_path) -> None:
    repo_root = tmp_path / "repo"
    document_path = repo_root / "docs" / "guide.md"
    linked_doc = repo_root / "docs" / "other.md"
    linked_image = repo_root / "docs" / "assets" / "chart.svg"

    linked_doc.parent.mkdir(parents=True, exist_ok=True)
    linked_image.parent.mkdir(parents=True, exist_ok=True)
    linked_doc.write_text("# Other\n", encoding="utf-8")
    linked_image.write_text("<svg />\n", encoding="utf-8")
    document_path.write_text(
        "\n".join(
            [
                "[Doc](./other.md)",
                "![Chart](./assets/chart.svg)",
                "[External](https://example.com)",
                "[Section](#local-anchor)",
            ]
        ),
        encoding="utf-8",
    )

    targets = extract_markdown_targets(document_path.read_text(encoding="utf-8"))
    assert "./other.md" in targets
    assert "./assets/chart.svg" in targets
    assert "https://example.com" in targets
    assert "#local-anchor" in targets

    assert resolve_internal_markdown_target(document_path, "./other.md") == linked_doc.resolve()
    assert (
        resolve_internal_markdown_target(document_path, "./assets/chart.svg")
        == linked_image.resolve()
    )
    assert resolve_internal_markdown_target(document_path, "https://example.com") is None
    assert resolve_internal_markdown_target(document_path, "#local-anchor") is None


def test_public_fine_tune_docs_and_exports_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    expected_paths = [
        repo_root / "docs/fine_tune_with_summa_moral_graph.md",
        repo_root / "docs/christian_virtue_sft.md",
        repo_root / "docs/christian_virtue_dataset_card.md",
        repo_root / "docs/repository_map.md",
        repo_root / "docs/reports/assets/README.md",
        repo_root / "data/processed/sft/README.md",
        repo_root / "docs/reports/christian_virtue_experiments.md",
        repo_root / "docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md",
        repo_root / "docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md",
        repo_root / "docs/reports/christian_virtue_citation_frontier_audit.md",
        repo_root / "docs/reports/christian_virtue_citation_frontier_audit.json",
        repo_root / "docs/reports/assets/christian_virtue_citation_frontier_modes.svg",
        repo_root
        / "docs/reports/assets/christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/manifest.json",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/train.jsonl",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/benchmarks/test.jsonl",
        repo_root / "data/processed/sft/exports/christian_virtue_v1_ood/manifest.json",
        repo_root / "data/processed/sft/exports/christian_virtue_v1_ood/benchmarks/ood_test.jsonl",
        repo_root / "data/processed/sft/samples/christian_virtue_v1_sample.jsonl",
        repo_root / "data/processed/sft/samples/christian_virtue_goal_demo_panel.jsonl",
        repo_root / "requirements/local-mps-py312.lock.txt",
        repo_root / "scripts/setup_christian_virtue_local.sh",
        repo_root / "scripts/reproduce_christian_virtue_qwen2_5_1_5b_local.sh",
        repo_root / "scripts/audit_christian_virtue_frontier.py",
        repo_root / "scripts/build_christian_virtue_citation_frontier_report.py",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_readme_and_gitignore_expose_public_fine_tune_surface() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    dataset_card_text = (repo_root / "docs/christian_virtue_dataset_card.md").read_text(
        encoding="utf-8"
    )
    repo_map_text = (repo_root / "docs/repository_map.md").read_text(encoding="utf-8")
    report_index_text = (repo_root / "docs/reports/christian_virtue_experiments.md").read_text(
        encoding="utf-8"
    )
    assets_readme_text = (repo_root / "docs/reports/assets/README.md").read_text(encoding="utf-8")
    fine_tune_text = (repo_root / "docs/fine_tune_with_summa_moral_graph.md").read_text(
        encoding="utf-8"
    )
    sft_readme_text = (repo_root / "data/processed/sft/README.md").read_text(encoding="utf-8")
    gitignore_text = (repo_root / ".gitignore").read_text(encoding="utf-8")
    makefile_text = (repo_root / "Makefile").read_text(encoding="utf-8")

    assert "Fine-Tune Your Model With Summa Moral Graph" in readme_text
    assert "6032" in readme_text
    assert "doctrinally usable `resp`/`ad` segments" in readme_text
    assert "docs/fine_tune_with_summa_moral_graph.md" in readme_text
    assert "local-baseline" in readme_text
    assert "make setup-christian-virtue-local" in readme_text
    assert "make reproduce-christian-virtue-qwen2-5-1-5b-local" in readme_text
    assert "make audit-christian-virtue-qwen2-5-1-5b-local-frontier" in readme_text
    assert "make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop" in readme_text
    assert "requirements/local-mps-py312.lock.txt" in readme_text
    assert (
        "artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md"
        in readme_text
    )
    assert "docs/reports/christian_virtue_citation_frontier_audit.md" in readme_text
    assert "docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md" in readme_text
    assert "docs/fine_tune_with_summa_moral_graph.md" in dataset_card_text
    assert "christian_virtue_qwen2_5_1_5b_local_baseline_report.md" in dataset_card_text
    assert "make setup-christian-virtue-local" in fine_tune_text
    assert "make reproduce-christian-virtue-qwen2-5-1-5b-local" in fine_tune_text
    assert "make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop" in fine_tune_text
    assert "christian_virtue_qwen2_5_1_5b_citation_frontier_report.md" in fine_tune_text
    assert "task_tract_quota_round_robin" in fine_tune_text
    assert "citation_grounded_moral_answer=64" in fine_tune_text
    assert "make reproduce-christian-virtue-qwen2-5-1-5b-local" in report_index_text
    assert "make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop" in report_index_text
    assert "christian_virtue_citation_frontier_audit.md" in report_index_text
    assert "christian_virtue_qwen2_5_1_5b_citation_frontier_report.md" in report_index_text
    assert "scripts/setup_christian_virtue_local.sh" in repo_map_text
    assert "scripts/audit_christian_virtue_frontier.py" in repo_map_text
    assert "scripts/build_christian_virtue_citation_frontier_report.py" in repo_map_text
    assert "scripts/run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh" in repo_map_text
    assert "configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml" in repo_map_text
    assert "make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop" in repo_map_text
    assert "requirements/local-mps-py312.lock.txt" in repo_map_text
    assert "christian_virtue_qwen2_5_1_5b_local_recipe_timing_comparison.svg" in assets_readme_text
    assert (
        "christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg"
        in assets_readme_text
    )
    assert "docs/christian_virtue_dataset_card.md" in sft_readme_text
    assert "setup-christian-virtue-local:" in makefile_text
    assert "reproduce-christian-virtue-qwen2-5-1-5b-local:" in makefile_text
    assert "!data/processed/sft/exports/christian_virtue_v1/**" in gitignore_text
    assert "!data/processed/sft/exports/christian_virtue_v1_ood/**" in gitignore_text
    assert (
        "!artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md"
        in gitignore_text
    )
    assert (
        "!artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/package_manifest.json"
        in gitignore_text
    )
    assert (
        "!artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/release_notes.md"
        in gitignore_text
    )
    assert (
        "!artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg"
        in gitignore_text
    )

    for relative_path in [
        Path("README.md"),
        Path("docs/fine_tune_with_summa_moral_graph.md"),
        Path("docs/christian_virtue_dataset_card.md"),
        Path("docs/repository_map.md"),
        Path("docs/reports/assets/README.md"),
        Path("docs/christian_virtue_sft.md"),
        Path("docs/reports/christian_virtue_experiments.md"),
    ]:
        missing_targets = validate_internal_markdown_links(repo_root / relative_path)
        assert not missing_targets, (relative_path, missing_targets)


def test_python_script_entrypoints_start_with_docstrings() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    for script_path in sorted((repo_root / "scripts").glob("*.py")):
        lines = script_path.read_text(encoding="utf-8").splitlines()
        first_nonempty = next((line for line in lines if line.strip()), "")
        assert first_nonempty.startswith(('"""', "'''")), script_path


def test_report_assets_are_documented_and_linked() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assets_dir = repo_root / "docs/reports/assets"
    assets_readme_text = (assets_dir / "README.md").read_text(encoding="utf-8")
    report_texts = [
        path.read_text(encoding="utf-8")
        for path in sorted((repo_root / "docs/reports").glob("*.md"))
    ]

    for asset_path in sorted(assets_dir.glob("*.svg")):
        asset_name = asset_path.name
        assert asset_name in assets_readme_text, asset_name
        assert any(asset_name in report_text for report_text in report_texts), asset_name


def test_public_repo_surfaces_do_not_embed_machine_absolute_paths() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    assert not find_machine_path_leaks(repo_root)


def test_repo_publication_bundle_is_coherent() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    package_manifest_path = (
        repo_root
        / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter"
        / "package_manifest.json"
    )

    summary = verify_publication_bundle(
        repo_root=repo_root,
        package_manifest_path=package_manifest_path,
    )

    assert summary["adapter_citation_exact_match"] > summary["base_citation_exact_match"]
    assert "docs/christian_virtue_dataset_card.md" in summary["checked_docs"]
    assert "docs/public_claim_map.md" in summary["checked_docs"]
    assert "data/processed/sft/README.md" in summary["checked_docs"]
    assert "docs/reports/christian_virtue_citation_frontier_audit.md" in summary["checked_docs"]
    assert (
        "docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md"
        in summary["checked_docs"]
    )
    assert "README.md" in summary["checked_doc_link_counts"]
    assert "docs/public_claim_map.md" in summary["checked_doc_link_counts"]
    assert (
        "docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md"
        in summary["checked_doc_link_counts"]
    )
    assert "README.md" in summary["checked_package_surfaces"]
    assert "release_notes.md" in summary["checked_package_surfaces"]
