"""Verification helpers for keeping public docs and packaged adapter surfaces in sync."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from ..utils.paths import REPO_ROOT
from .doc_links import extract_markdown_targets, validate_internal_markdown_links

DEFAULT_PUBLICATION_PACKAGE_MANIFEST = (
    REPO_ROOT
    / (
        "artifacts/christian_virtue/qwen2_5_1_5b_instruct/"
        "local_baseline_adapter/package_manifest.json"
    )
)
DATASET_CARD_PATH = Path("docs/christian_virtue_dataset_card.md")
PUBLIC_CLAIM_MAP_PATH = Path("docs/public_claim_map.md")
REPOSITORY_MAP_PATH = Path("docs/repository_map.md")
REPORT_ASSETS_README_PATH = Path("docs/reports/assets/README.md")
SFT_README_PATH = Path("data/processed/sft/README.md")
FRONTIER_AUDIT_PATH = Path("docs/reports/christian_virtue_citation_frontier_audit.md")
FRONTIER_FOLLOWUP_REPORT_PATH = (
    Path("docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md")
)
JUSTICE_GUARDED_REPORT_PATH = (
    Path("docs/reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md")
)
ACCURACY_FIRST_REPORT_PATH = (
    Path("docs/reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md")
)
MACHINE_PATH_PATTERNS = (
    re.compile(r"/Users/[^\s)\]\"']+"),
    re.compile(r"/home/[^\s)\]\"']+"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\s)\]\"']+"),
)


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _format_metric(value: Any) -> str:
    return f"{float(value):.3f}"


def _format_percent(value: Any) -> str:
    return f"{float(value) * 100:.1f}%"


def iter_public_surface_paths(repo_root: Path) -> list[Path]:
    """List public repo surfaces that should never leak local absolute filesystem paths."""

    paths: list[Path] = []

    readme_path = repo_root / "README.md"
    if readme_path.exists():
        paths.append(readme_path)

    docs_root = repo_root / "docs"
    if docs_root.exists():
        paths.extend(sorted(docs_root.rglob("*.md")))

    processed_root = repo_root / "data" / "processed"
    if processed_root.exists():
        paths.extend(sorted(processed_root.rglob("*.json")))

    artifacts_root = repo_root / "artifacts"
    if artifacts_root.exists():
        paths.extend(sorted(artifacts_root.rglob("*.md")))
        paths.extend(sorted(artifacts_root.rglob("*.json")))

    return paths


def find_machine_path_leaks(repo_root: Path) -> dict[str, list[str]]:
    """Return any machine-specific absolute paths embedded in public repo surfaces."""

    leaks: dict[str, list[str]] = {}
    for path in iter_public_surface_paths(repo_root):
        text = path.read_text(encoding="utf-8")
        matches: set[str] = set()
        for pattern in MACHINE_PATH_PATTERNS:
            matches.update(pattern.findall(text))
        if matches:
            leaks[str(path.relative_to(repo_root))] = sorted(matches)
    return dict(sorted(leaks.items()))


def build_publication_doc_expectations(
    package_manifest: dict[str, Any],
) -> dict[Path, list[str]]:
    report_path = Path(str(package_manifest["published_report_path"]))
    report_name = report_path.name
    hf_url = str(package_manifest["hf_repo_url"])
    release_url = str(package_manifest["github_release_url"])
    run_id = str(package_manifest["local_train_run_id"])
    git_commit = str(package_manifest["git_commit"])
    release_tag = release_url.rstrip("/").rsplit("/", maxsplit=1)[-1]
    base_metric = _format_metric(package_manifest["base_metrics"]["citation_exact_match"])
    adapter_metric = _format_metric(package_manifest["adapter_metrics"]["citation_exact_match"])
    summary = cast(dict[str, Any], package_manifest.get("summary", {}))
    strongest_task = cast(dict[str, Any] | None, summary.get("strongest_task"))
    strongest_tract = cast(dict[str, Any] | None, summary.get("strongest_tract"))
    strongest_task_label = (
        str(strongest_task["label"]) if strongest_task is not None else "Strongest task slice"
    )
    strongest_task_metric = (
        _format_percent(float(strongest_task["candidate_exact"]))
        if strongest_task is not None
        else adapter_metric
    )
    strongest_tract_label = (
        str(strongest_tract["label"]) if strongest_tract is not None else "Strongest tract slice"
    )

    return {
        Path("README.md"): [
            "Fine-Tune Your Model With Summa Moral Graph",
            hf_url,
            release_url,
            str(report_path),
            release_tag,
            strongest_task_label,
            strongest_task_metric,
            strongest_tract_label,
        ],
        Path("docs/fine_tune_with_summa_moral_graph.md"): [
            hf_url,
            release_url,
            report_name,
            run_id,
            base_metric,
            adapter_metric,
        ],
        PUBLIC_CLAIM_MAP_PATH: [
            "# Public Claim Map",
            "36.5%",
            "38.6%",
            "41.2%",
            "3.0%",
            "make public-release-check",
            "make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop",
            "not a general theology chatbot",
            "not a replacement public baseline",
        ],
        Path("docs/christian_virtue_sft.md"): [
            hf_url,
            release_url,
            run_id,
            adapter_metric,
        ],
        Path("docs/reports/christian_virtue_experiments.md"): [
            hf_url,
            release_url,
            run_id,
            strongest_task_label,
            strongest_task_metric,
            strongest_tract_label,
        ],
        REPOSITORY_MAP_PATH: [
            "requirements/local-mps-py312.lock.txt",
            "scripts/setup_christian_virtue_local.sh",
            "make reproduce-christian-virtue-qwen2-5-1-5b-local",
        ],
        REPORT_ASSETS_README_PATH: [
            "christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg",
            "christian_virtue_qwen2_5_1_5b_local_recipe_timing_comparison.svg",
            "christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg",
            "christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg",
            "Flagship report",
        ],
        FRONTIER_AUDIT_PATH: [
            "# Christian Virtue Citation Frontier Audit",
            "citation_grounded_moral_answer",
            "configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml",
            "make audit-christian-virtue-qwen2-5-1-5b-citation-frontier",
            "47.8%",
        ],
        FRONTIER_FOLLOWUP_REPORT_PATH: [
            "# Christian Virtue Citation-Frontier Follow-Up",
            "Citation-grounded moral answer",
            "36.5%",
            "38.6%",
            "3.0%",
            "justice_core",
            "strong_textual_inference",
            "christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md",
            "christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg",
        ],
        JUSTICE_GUARDED_REPORT_PATH: [
            "# Justice-Guarded Citation-Repair Report",
            "39.1%",
            "42.9%",
            "justice_core",
            "strong_textual_inference",
            "christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md",
        ],
        ACCURACY_FIRST_REPORT_PATH: [
            "# Accuracy-First Hybrid Report",
            "41.2%",
            "50.7%",
            "64.2%",
            "citation_grounded_moral_answer",
            "justice_core",
            "strong_textual_inference",
            "strongest same-budget overall result",
        ],
        DATASET_CARD_PATH: [
            "Aquinas-grounded Christian virtue reasoning",
            "docs/fine_tune_with_summa_moral_graph.md",
            report_name,
            hf_url,
            release_url,
            "data/processed/sft/exports/christian_virtue_v1",
        ],
        SFT_README_PATH: [
            "exports/christian_virtue_v1/",
            "docs/christian_virtue_dataset_card.md",
            "docs/fine_tune_with_summa_moral_graph.md",
            report_name,
        ],
        report_path: [
            hf_url,
            release_url,
            run_id,
            git_commit,
            base_metric,
            adapter_metric,
            "## Executive Readout",
            "Goal-demo exact citations",
        ],
    }


def build_publication_package_surface_expectations(
    package_manifest: dict[str, Any],
) -> dict[str, list[str]]:
    summary = cast(dict[str, Any], package_manifest.get("summary", {}))
    strongest_task = cast(dict[str, Any] | None, summary.get("strongest_task"))
    strongest_tract = cast(dict[str, Any] | None, summary.get("strongest_tract"))

    expected: dict[str, list[str]] = {
        "README.md": [
            "## Executive Readout",
            str(package_manifest["github_release_url"]),
            str(package_manifest["hf_repo_url"]),
            "deliberately small 1.5B local demo model",
            "Full task/tract breakdowns and the qualitative goal-demo panel live in the "
            "published report.",
        ],
        "release_notes.md": [
            "## Executive Readout",
            str(package_manifest["hf_repo_url"]),
            "deliberately small local demo model",
            "Full task/tract breakdowns and the qualitative goal-demo panel live in the "
            "curated report.",
        ],
    }
    if strongest_task is not None:
        expected["README.md"].append(f"`{strongest_task['label']}`")
        expected["release_notes.md"].append(f"`{strongest_task['label']}`")
    if strongest_tract is not None:
        expected["README.md"].append(f"`{strongest_tract['label']}`")
        expected["release_notes.md"].append(f"`{strongest_tract['label']}`")
    return expected


def verify_publication_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    package_manifest_path: Path = DEFAULT_PUBLICATION_PACKAGE_MANIFEST,
) -> dict[str, Any]:
    package_manifest = _read_json(package_manifest_path)

    required_repo_paths = {
        "published_report_path": repo_root / str(package_manifest["published_report_path"]),
        "dataset_manifest_path": repo_root / str(package_manifest["dataset_manifest_path"]),
        "package_manifest_path": package_manifest_path,
    }

    for label, path in required_repo_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing {label}: {path}")

    train_run_dir = repo_root / str(package_manifest["train_run_dir"])
    base_eval_run_dir = repo_root / str(package_manifest["base_eval_run_dir"])
    adapter_eval_run_dir = repo_root / str(package_manifest["adapter_eval_run_dir"])
    run_artifact_paths = {
        "train_run_dir": train_run_dir,
        "base_eval_run_dir": base_eval_run_dir,
        "adapter_eval_run_dir": adapter_eval_run_dir,
    }
    missing_run_artifact_paths = [
        label for label, path in run_artifact_paths.items() if not path.exists()
    ]

    if not isinstance(package_manifest.get("base_metrics"), dict):
        raise RuntimeError("Package manifest is missing structured base_metrics.")
    if not isinstance(package_manifest.get("adapter_metrics"), dict):
        raise RuntimeError("Package manifest is missing structured adapter_metrics.")

    if not missing_run_artifact_paths:
        train_metadata = _read_json(train_run_dir / "train_metadata.json")
        base_metrics = _read_json(base_eval_run_dir / "metrics.json")["overall"]
        adapter_metrics = _read_json(adapter_eval_run_dir / "metrics.json")["overall"]

        if str(train_metadata["run_id"]) != str(package_manifest["local_train_run_id"]):
            raise RuntimeError(
                "Train run id mismatch between package manifest and train metadata: "
                f"{package_manifest['local_train_run_id']} vs {train_metadata['run_id']}"
            )
        if str(train_metadata["git_commit"]) != str(package_manifest["git_commit"]):
            raise RuntimeError(
                "Git commit mismatch between package manifest and train metadata: "
                f"{package_manifest['git_commit']} vs {train_metadata['git_commit']}"
            )
        if package_manifest["base_metrics"] != base_metrics:
            raise RuntimeError(
                "Base metrics in package manifest do not match base evaluation metrics."
            )
        if package_manifest["adapter_metrics"] != adapter_metrics:
            raise RuntimeError(
                "Adapter metrics in package manifest do not match adapter evaluation metrics."
            )
        run_artifact_verification_mode = "full"
    else:
        if not str(package_manifest.get("local_train_run_id", "")).strip():
            raise RuntimeError("Package manifest is missing local_train_run_id.")
        if not str(package_manifest.get("git_commit", "")).strip():
            raise RuntimeError("Package manifest is missing git_commit.")
        base_metrics = cast(dict[str, Any], package_manifest["base_metrics"])
        adapter_metrics = cast(dict[str, Any], package_manifest["adapter_metrics"])
        run_artifact_verification_mode = "package_manifest_only"

    base_exact = float(base_metrics["citation_exact_match"])
    adapter_exact = float(adapter_metrics["citation_exact_match"])
    if adapter_exact <= base_exact:
        raise RuntimeError(
            "Canonical published adapter no longer improves citation exact match over base: "
            f"{adapter_exact:.3f} <= {base_exact:.3f}"
        )

    checked_docs: list[str] = []
    checked_doc_link_counts: dict[str, int] = {}
    for relative_doc_path, expected_substrings in build_publication_doc_expectations(
        package_manifest
    ).items():
        document_path = repo_root / relative_doc_path
        if not document_path.exists():
            raise FileNotFoundError(f"Missing public document surface: {document_path}")
        document_text = document_path.read_text(encoding="utf-8")
        for substring in expected_substrings:
            if substring not in document_text:
                raise RuntimeError(
                    f"Expected substring {substring!r} in public surface {document_path}"
                )
        missing_targets = validate_internal_markdown_links(document_path)
        if missing_targets:
            missing_display = ", ".join(sorted(missing_targets))
            raise RuntimeError(
                f"Broken internal markdown links in public surface {document_path}: "
                f"{missing_display}"
            )
        checked_docs.append(str(relative_doc_path))
        checked_doc_link_counts[str(relative_doc_path)] = len(
            extract_markdown_targets(document_text)
        )

    package_dir = package_manifest_path.parent
    checked_package_surfaces: list[str] = []
    for relative_name, expected_substrings in build_publication_package_surface_expectations(
        package_manifest
    ).items():
        surface_path = package_dir / relative_name
        if not surface_path.exists():
            raise FileNotFoundError(f"Missing package publication surface: {surface_path}")
        surface_text = surface_path.read_text(encoding="utf-8")
        for substring in expected_substrings:
            if substring not in surface_text:
                raise RuntimeError(
                    f"Expected substring {substring!r} in package surface {surface_path}"
                )
        checked_package_surfaces.append(relative_name)

    machine_path_leaks = find_machine_path_leaks(repo_root)
    if machine_path_leaks:
        formatted_leaks = "; ".join(
            f"{path}: {', '.join(matches)}" for path, matches in machine_path_leaks.items()
        )
        raise RuntimeError(
            "Machine-specific absolute paths leaked into public repo surfaces: "
            f"{formatted_leaks}"
        )

    return {
        "package_manifest_path": str(package_manifest_path.relative_to(repo_root)),
        "train_run_dir": str(train_run_dir.relative_to(repo_root)),
        "base_eval_run_dir": str(base_eval_run_dir.relative_to(repo_root)),
        "adapter_eval_run_dir": str(adapter_eval_run_dir.relative_to(repo_root)),
        "published_report_path": str(
            required_repo_paths["published_report_path"].relative_to(repo_root)
        ),
        "dataset_manifest_path": str(
            required_repo_paths["dataset_manifest_path"].relative_to(repo_root)
        ),
        "local_train_run_id": str(package_manifest["local_train_run_id"]),
        "git_commit": str(package_manifest["git_commit"]),
        "hf_repo_url": str(package_manifest["hf_repo_url"]),
        "github_release_url": str(package_manifest["github_release_url"]),
        "base_citation_exact_match": base_exact,
        "adapter_citation_exact_match": adapter_exact,
        "citation_exact_gain": adapter_exact - base_exact,
        "checked_docs": checked_docs,
        "checked_doc_link_counts": checked_doc_link_counts,
        "checked_path_leak_surfaces": [
            str(path.relative_to(repo_root)) for path in iter_public_surface_paths(repo_root)
        ],
        "checked_package_surfaces": checked_package_surfaces,
        "run_artifact_verification_mode": run_artifact_verification_mode,
        "missing_run_artifact_paths": missing_run_artifact_paths,
    }
