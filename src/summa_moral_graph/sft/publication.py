from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

from ..utils.paths import REPO_ROOT
from .run_layout import current_git_commit, write_json
from .utils import tract_display_name

ADAPTER_PACKAGE_FILES = [
    "adapter_config.json",
    "adapter_model.safetensors",
    "added_tokens.json",
    "chat_template.jinja",
    "merges.txt",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.json",
]

TASK_DISPLAY_NAMES = {
    "citation_grounded_moral_answer": "Citation-grounded moral answer",
    "passage_grounded_doctrinal_qa": "Passage-grounded doctrinal QA",
    "reviewed_relation_explanation": "Reviewed relation explanation",
    "virtue_concept_explanation": "Virtue concept explanation",
}


def _read_json(path: Path) -> dict[str, Any]:
    import json

    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _copy_if_present(source_dir: Path, destination_dir: Path, filename: str) -> None:
    source_path = source_dir / filename
    if not source_path.exists():
        return
    shutil.copy2(source_path, destination_dir / filename)


def _repo_display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _metric_value(row: dict[str, Any], key: str) -> float:
    value = row.get(key, 0.0)
    if value is None:
        return 0.0
    return float(value)


def _bucket_display_name(bucket_name: str, key: str) -> str:
    if bucket_name == "by_task_type":
        return TASK_DISPLAY_NAMES.get(key, key.replace("_", " ").title())
    if bucket_name == "by_tract":
        return tract_display_name(key)
    return key.replace("_", " ").title()


def _metric_breakdown_rows(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    *,
    bucket_name: str,
) -> list[dict[str, Any]]:
    baseline_bucket = cast(dict[str, Any], baseline_metrics.get(bucket_name, {}))
    candidate_bucket = cast(dict[str, Any], candidate_metrics.get(bucket_name, {}))
    rows: list[dict[str, Any]] = []
    for key, candidate_row_any in candidate_bucket.items():
        candidate_row = cast(dict[str, Any], candidate_row_any)
        baseline_row = cast(dict[str, Any], baseline_bucket.get(key, {}))
        count_value = candidate_row.get("count", 0)
        rows.append(
            {
                "key": str(key),
                "label": _bucket_display_name(bucket_name, str(key)),
                "count": int(count_value) if count_value is not None else 0,
                "baseline_exact": _metric_value(baseline_row, "citation_exact_match"),
                "candidate_exact": _metric_value(candidate_row, "citation_exact_match"),
            }
        )
    rows.sort(
        key=lambda row: (
            float(row["candidate_exact"]),
            float(row["candidate_exact"]) - float(row["baseline_exact"]),
            int(row["count"]),
            str(row["label"]),
        ),
        reverse=True,
    )
    return rows


def _lowest_metric_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return min(
        rows,
        key=lambda row: (
            float(row["candidate_exact"]),
            float(row["candidate_exact"]) - float(row["baseline_exact"]),
            int(row["count"]),
            str(row["label"]),
        ),
    )


def _serialize_summary_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    baseline_exact = float(row["baseline_exact"])
    candidate_exact = float(row["candidate_exact"])
    return {
        "key": str(row["key"]),
        "label": str(row["label"]),
        "count": int(row["count"]),
        "baseline_exact": baseline_exact,
        "candidate_exact": candidate_exact,
        "delta_exact": candidate_exact - baseline_exact,
    }


def _build_metric_summary(
    *,
    base_metrics: dict[str, Any],
    adapter_metrics: dict[str, Any],
) -> dict[str, Any]:
    task_rows = _metric_breakdown_rows(base_metrics, adapter_metrics, bucket_name="by_task_type")
    tract_rows = _metric_breakdown_rows(base_metrics, adapter_metrics, bucket_name="by_tract")
    zero_gain_tracts = [
        {
            "key": str(row["key"]),
            "label": str(row["label"]),
            "count": int(row["count"]),
        }
        for row in tract_rows
        if float(row["candidate_exact"]) == 0.0 and int(row["count"]) > 0
    ]
    return {
        "strongest_task": _serialize_summary_row(task_rows[0] if task_rows else None),
        "strongest_tract": _serialize_summary_row(tract_rows[0] if tract_rows else None),
        "weakest_task": _serialize_summary_row(_lowest_metric_row(task_rows)),
        "zero_gain_tracts": zero_gain_tracts,
    }


def _github_blob_url(github_repo_url: str, git_commit: str, repo_path: str) -> str:
    return f"{github_repo_url}/blob/{git_commit}/{repo_path}"


def release_target_from_train_run(train_run_dir: Path) -> str:
    train_metadata = _read_json(train_run_dir / "train_metadata.json")
    git_commit = train_metadata.get("git_commit")
    if not isinstance(git_commit, str) or not git_commit:
        raise RuntimeError(f"Missing git_commit in {train_run_dir / 'train_metadata.json'}")
    return git_commit


def build_adapter_package_manifest(
    *,
    train_run_dir: Path,
    base_eval_run_dir: Path,
    adapter_eval_run_dir: Path,
    report_path: Path,
    hf_repo_id: str,
    release_tag: str,
    github_repo_url: str,
) -> dict[str, Any]:
    train_metadata = _read_json(train_run_dir / "train_metadata.json")
    base_metrics = _read_json(base_eval_run_dir / "metrics.json")
    adapter_metrics = _read_json(adapter_eval_run_dir / "metrics.json")
    return {
        "base_model": train_metadata["model_name_or_path"],
        "dataset_dir": "data/processed/sft/exports/christian_virtue_v1",
        "dataset_manifest_path": "data/processed/sft/exports/christian_virtue_v1/manifest.json",
        "git_commit": train_metadata["git_commit"],
        "github_repo_url": github_repo_url,
        "github_release_url": f"{github_repo_url}/releases/tag/{release_tag}",
        "hf_repo_id": hf_repo_id,
        "hf_repo_url": f"https://huggingface.co/{hf_repo_id}",
        "local_train_run_id": train_metadata["run_id"],
        "published_report_path": _repo_display_path(report_path),
        "train_run_dir": _repo_display_path(train_run_dir),
        "base_eval_run_dir": _repo_display_path(base_eval_run_dir),
        "adapter_eval_run_dir": _repo_display_path(adapter_eval_run_dir),
        "base_metrics": base_metrics["overall"],
        "adapter_metrics": adapter_metrics["overall"],
        "summary": _build_metric_summary(
            base_metrics=base_metrics,
            adapter_metrics=adapter_metrics,
        ),
    }


def build_model_card_text(
    *,
    package_manifest: dict[str, Any],
    report_path: Path,
    dataset_card_path: Path,
) -> str:
    base_metrics = package_manifest["base_metrics"]
    adapter_metrics = package_manifest["adapter_metrics"]
    summary = cast(dict[str, Any], package_manifest.get("summary", {}))
    dataset_card_display = _repo_display_path(dataset_card_path)
    report_display = _repo_display_path(report_path)
    github_repo_url = str(package_manifest["github_repo_url"])
    git_commit = str(package_manifest["git_commit"])
    report_url = _github_blob_url(github_repo_url, git_commit, report_display)
    dataset_card_url = _github_blob_url(github_repo_url, git_commit, dataset_card_display)

    lines = [
        "---",
        f"base_model: {package_manifest['base_model']}",
        "library_name: peft",
        "pipeline_tag: text-generation",
        "language:",
        "- en",
        "tags:",
        "- lora",
        "- text-generation",
        "- christian-virtue",
        "- aquinas",
        "- summa-moral-graph",
        "---",
        "",
        "# Summa Moral Graph Christian Virtue LoRA Adapter",
        "",
        "This adapter is the canonical local `pilot-lite` demonstration checkpoint for the "
        "Christian virtue SFT pipeline in `summa-moral-graph`.",
        "",
        "## Purpose",
        "",
        "This model is meant to move a general instruction model toward Aquinas-grounded "
        "Christian virtue reasoning. Citation traceability is included as a guardrail, not as "
        "the whole purpose of the fine-tune.",
        "",
        "## Base Model",
        "",
        f"- `{package_manifest['base_model']}`",
        "- LoRA adapter trained on Apple Silicon `mps`",
        "- `float16`, no 4-bit quantization",
        "",
        "## Dataset",
        "",
        "- Training export: `data/processed/sft/exports/christian_virtue_v1`",
        "- Dataset manifest: `data/processed/sft/exports/christian_virtue_v1/manifest.json`",
        f"- Dataset card: [GitHub link]({dataset_card_url})",
        "",
        "## Canonical Run",
        "",
        f"- Train run id: `{package_manifest['local_train_run_id']}`",
        f"- Git commit: `{package_manifest['git_commit']}`",
        f"- Hugging Face model page: {package_manifest['hf_repo_url']}",
        f"- Matching GitHub release: {package_manifest['github_release_url']}",
        f"- Published report: [GitHub link]({report_url})",
        "",
        "## Executive Readout",
        "",
        f"- Held-out test citation exact moved from "
        f"`{_format_percent(float(base_metrics['citation_exact_match']))}` to "
        f"`{_format_percent(float(adapter_metrics['citation_exact_match']))}`.",
    ]

    strongest_task = cast(dict[str, Any] | None, summary.get("strongest_task"))
    strongest_tract = cast(dict[str, Any] | None, summary.get("strongest_tract"))
    weakest_task = cast(dict[str, Any] | None, summary.get("weakest_task"))
    zero_gain_tracts = cast(list[dict[str, Any]], summary.get("zero_gain_tracts", []))
    if strongest_task is not None:
        lines.append(
            f"- Strongest task slice: `{strongest_task['label']}` at "
            f"`{_format_percent(float(strongest_task['candidate_exact']))}` exact over "
            f"`{strongest_task['count']}` prompts."
        )
    if strongest_tract is not None:
        lines.append(
            f"- Strongest tract slice: `{strongest_tract['label']}` at "
            f"`{_format_percent(float(strongest_tract['candidate_exact']))}` exact over "
            f"`{strongest_tract['count']}` prompts."
        )
    if weakest_task is not None:
        lines.append(
            f"- Hardest task type: `{weakest_task['label']}` at "
            f"`{_format_percent(float(weakest_task['candidate_exact']))}` exact over "
            f"`{weakest_task['count']}` prompts."
        )
    if zero_gain_tracts:
        lines.append(
            "- Zero-gain tracts in this run: "
            + ", ".join(f"`{row['label']}`" for row in zero_gain_tracts)
            + "."
        )
    lines.extend(
        [
            "- Full task/tract breakdowns and the qualitative goal-demo panel live in the "
            "published report.",
            "",
            "## Headline Held-Out Test Result",
            "",
            f"- Base citation exact match: `{base_metrics['citation_exact_match']:.3f}`",
            f"- Adapter citation exact match: `{adapter_metrics['citation_exact_match']:.3f}`",
            "",
            "## Intended Use",
            "",
            "- Aquinas-grounded Christian virtue QA and doctrinal explanation",
            "- Demonstrating how to fine-tune on the Summa Moral Graph dataset",
            "- Reproducible adapter publication tied to a documented run",
            "",
            "## Reproduce The Canonical Local Baseline",
            "",
            "```bash",
            "make build-christian-virtue-sft",
            "make train-christian-virtue-qwen2-5-1-5b-local-smoke",
            "make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite",
            "make eval-christian-virtue-qwen2-5-1-5b-local-base-test",
            "make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test",
            "make compare-christian-virtue-qwen2-5-1-5b-local-test",
            "make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite",
            "make verify-christian-virtue-qwen2-5-1-5b-local-publishable",
            "```",
            "",
            "## Limits",
            "",
            "- This is a local pilot baseline, not the final best-quality checkpoint",
            "- The hardest citation-grounded moral-answer cases remain unsolved",
            "- The adapter should be used with the listed base model only",
            "",
        ]
    )
    return "\n".join(lines)


def build_release_notes_text(
    *,
    package_manifest: dict[str, Any],
    report_path: Path,
    dataset_card_path: Path,
) -> str:
    base_metrics = package_manifest["base_metrics"]
    adapter_metrics = package_manifest["adapter_metrics"]
    summary = cast(dict[str, Any], package_manifest.get("summary", {}))
    report_display = _repo_display_path(report_path)
    dataset_card_display = _repo_display_path(dataset_card_path)
    github_repo_url = str(package_manifest["github_repo_url"])
    git_commit = str(package_manifest["git_commit"])
    report_url = _github_blob_url(github_repo_url, git_commit, report_display)
    dataset_card_url = _github_blob_url(github_repo_url, git_commit, dataset_card_display)

    lines = [
        "# Christian Virtue Qwen2.5 1.5B Local Pilot-Lite",
        "",
        "This release mirrors the canonical local `pilot-lite` adapter publication for the "
        "`summa-moral-graph` Christian virtue SFT pipeline.",
        "",
        "## Included here",
        "",
        f"- Hugging Face adapter: {package_manifest['hf_repo_url']}",
        f"- Curated experiment report: {report_url}",
        f"- Dataset card: {dataset_card_url}",
        "- Training export: `data/processed/sft/exports/christian_virtue_v1`",
        "",
        "## Purpose",
        "",
        "Train an Aquinas-grounded Christian virtue assistant that answers within reviewed "
        "evidence, uses Aquinas's moral categories, and preserves source traceability.",
        "",
        "## Executive Readout",
        "",
        f"- Held-out test citation exact moved from "
        f"`{_format_percent(float(base_metrics['citation_exact_match']))}` to "
        f"`{_format_percent(float(adapter_metrics['citation_exact_match']))}`.",
    ]
    strongest_task = cast(dict[str, Any] | None, summary.get("strongest_task"))
    strongest_tract = cast(dict[str, Any] | None, summary.get("strongest_tract"))
    weakest_task = cast(dict[str, Any] | None, summary.get("weakest_task"))
    zero_gain_tracts = cast(list[dict[str, Any]], summary.get("zero_gain_tracts", []))
    if strongest_task is not None:
        lines.append(
            f"- Strongest task slice: `{strongest_task['label']}` at "
            f"`{_format_percent(float(strongest_task['candidate_exact']))}` exact over "
            f"`{strongest_task['count']}` prompts."
        )
    if strongest_tract is not None:
        lines.append(
            f"- Strongest tract slice: `{strongest_tract['label']}` at "
            f"`{_format_percent(float(strongest_tract['candidate_exact']))}` exact over "
            f"`{strongest_tract['count']}` prompts."
        )
    if weakest_task is not None:
        lines.append(
            f"- Hardest task type: `{weakest_task['label']}` at "
            f"`{_format_percent(float(weakest_task['candidate_exact']))}` exact over "
            f"`{weakest_task['count']}` prompts."
        )
    if zero_gain_tracts:
        lines.append(
            "- Zero-gain tracts in this run: "
            + ", ".join(f"`{row['label']}`" for row in zero_gain_tracts)
            + "."
        )
    lines.extend(
        [
            "- Full task/tract breakdowns and the qualitative goal-demo panel live in the "
            "curated report.",
            "",
            "## Headline result",
            "",
            f"- Base citation exact match: `{base_metrics['citation_exact_match']:.3f}`",
            f"- Adapter citation exact match: `{adapter_metrics['citation_exact_match']:.3f}`",
            f"- Run id: `{package_manifest['local_train_run_id']}`",
            f"- Git commit: `{package_manifest['git_commit']}`",
            "",
            "## Canonical command path",
            "",
            "```bash",
            "make build-christian-virtue-sft",
            "make train-christian-virtue-qwen2-5-1-5b-local-smoke",
            "make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite",
            "make eval-christian-virtue-qwen2-5-1-5b-local-base-test",
            "make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test",
            "make compare-christian-virtue-qwen2-5-1-5b-local-test",
            "make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite",
            "make verify-christian-virtue-qwen2-5-1-5b-local-publishable",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_adapter_package(
    *,
    train_run_dir: Path,
    base_eval_run_dir: Path,
    adapter_eval_run_dir: Path,
    package_dir: Path,
    hf_repo_id: str,
    release_tag: str,
    github_repo_url: str,
    report_path: Path,
    dataset_card_path: Path,
) -> Path:
    if not (train_run_dir / "adapter_model.safetensors").exists():
        raise FileNotFoundError(f"Adapter weights not found in {train_run_dir}")

    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)

    for filename in ADAPTER_PACKAGE_FILES:
        _copy_if_present(train_run_dir, package_dir, filename)

    for filename in [
        "config_snapshot.yaml",
        "environment.json",
        "run_manifest.json",
        "train_metadata.json",
    ]:
        _copy_if_present(train_run_dir, package_dir, filename)

    manifest = build_adapter_package_manifest(
        train_run_dir=train_run_dir,
        base_eval_run_dir=base_eval_run_dir,
        adapter_eval_run_dir=adapter_eval_run_dir,
        report_path=report_path,
        hf_repo_id=hf_repo_id,
        release_tag=release_tag,
        github_repo_url=github_repo_url,
    )
    write_json(package_dir / "package_manifest.json", manifest)
    (package_dir / "README.md").write_text(
        build_model_card_text(
            package_manifest=manifest,
            report_path=report_path,
            dataset_card_path=dataset_card_path,
        ),
        encoding="utf-8",
    )
    (package_dir / "release_notes.md").write_text(
        build_release_notes_text(
            package_manifest=manifest,
            report_path=report_path,
            dataset_card_path=dataset_card_path,
        ),
        encoding="utf-8",
    )
    return package_dir


def publish_adapter_package_to_hf(
    *,
    package_dir: Path,
    repo_id: str,
    commit_message: str,
    private: bool = False,
) -> str:
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo_id=repo_id, repo_type="model", private=private, exist_ok=True)
    api.upload_folder(
        folder_path=str(package_dir),
        repo_id=repo_id,
        repo_type="model",
        commit_message=commit_message,
    )
    return f"https://huggingface.co/{repo_id}"


def create_or_update_github_release(
    *,
    tag: str,
    title: str,
    notes_path: Path,
    repo: str | None = None,
    target: str | None = None,
) -> str:
    common_args = ["gh"]
    if repo is not None:
        common_args.extend(["--repo", repo])

    view_command = [*common_args, "release", "view", tag]
    exists = (
        subprocess.run(
            view_command,
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        == 0
    )

    if exists:
        edit_command = [
            *common_args,
            "release",
            "edit",
            tag,
            "--title",
            title,
            "--notes-file",
            str(notes_path),
        ]
        subprocess.run(edit_command, check=True)
    else:
        create_command = [
            *common_args,
            "release",
            "create",
            tag,
            "--title",
            title,
            "--notes-file",
            str(notes_path),
        ]
        if target is not None:
            create_command.extend(["--target", target])
        subprocess.run(create_command, check=True)

    view_url_command = [*common_args, "release", "view", tag, "--json", "url", "--jq", ".url"]
    completed = subprocess.run(view_url_command, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def default_release_target(cwd: Path) -> str:
    commit = current_git_commit(cwd)
    if commit is None:
        raise RuntimeError(f"Could not determine git commit for {cwd}")
    return commit
