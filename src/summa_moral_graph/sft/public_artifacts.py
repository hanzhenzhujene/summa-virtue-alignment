from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from ..utils.paths import REPO_ROOT
from .doc_links import extract_markdown_targets, validate_internal_markdown_links

DEFAULT_PUBLICATION_PACKAGE_MANIFEST = (
    REPO_ROOT
    / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite_adapter/package_manifest.json"
)


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _format_metric(value: Any) -> str:
    return f"{float(value):.3f}"


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

    return {
        Path("README.md"): [
            "Fine-Tune Your Model With Summa Moral Graph",
            hf_url,
            release_url,
            str(report_path),
            release_tag,
            base_metric,
            adapter_metric,
        ],
        Path("docs/fine_tune_with_summa_moral_graph.md"): [
            hf_url,
            release_url,
            report_name,
            run_id,
            base_metric,
            adapter_metric,
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
            adapter_metric,
        ],
        report_path: [
            hf_url,
            release_url,
            run_id,
            git_commit,
            base_metric,
            adapter_metric,
        ],
    }


def verify_publication_bundle(
    *,
    repo_root: Path = REPO_ROOT,
    package_manifest_path: Path = DEFAULT_PUBLICATION_PACKAGE_MANIFEST,
) -> dict[str, Any]:
    package_manifest = _read_json(package_manifest_path)

    expected_paths = {
        "train_run_dir": repo_root / str(package_manifest["train_run_dir"]),
        "base_eval_run_dir": repo_root / str(package_manifest["base_eval_run_dir"]),
        "adapter_eval_run_dir": repo_root / str(package_manifest["adapter_eval_run_dir"]),
        "published_report_path": repo_root / str(package_manifest["published_report_path"]),
        "dataset_manifest_path": repo_root / str(package_manifest["dataset_manifest_path"]),
        "package_manifest_path": package_manifest_path,
    }

    for label, path in expected_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing {label}: {path}")

    train_run_dir = expected_paths["train_run_dir"]
    base_eval_run_dir = expected_paths["base_eval_run_dir"]
    adapter_eval_run_dir = expected_paths["adapter_eval_run_dir"]

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
        raise RuntimeError("Base metrics in package manifest do not match base evaluation metrics.")
    if package_manifest["adapter_metrics"] != adapter_metrics:
        raise RuntimeError(
            "Adapter metrics in package manifest do not match adapter evaluation metrics."
        )

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

    return {
        "package_manifest_path": str(package_manifest_path.relative_to(repo_root)),
        "train_run_dir": str(train_run_dir.relative_to(repo_root)),
        "base_eval_run_dir": str(base_eval_run_dir.relative_to(repo_root)),
        "adapter_eval_run_dir": str(adapter_eval_run_dir.relative_to(repo_root)),
        "published_report_path": str(
            expected_paths["published_report_path"].relative_to(repo_root)
        ),
        "dataset_manifest_path": str(
            expected_paths["dataset_manifest_path"].relative_to(repo_root)
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
    }
