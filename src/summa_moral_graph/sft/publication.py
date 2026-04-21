"""Adapter packaging helpers for the canonical Christian virtue publication bundle."""

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

PACKAGE_REPORT_ASSETS = {
    "docs/reports/assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg": (
        "assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg"
    ),
}

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


def _copy_repo_asset_if_present(
    source_relative_path: str, destination_dir: Path, destination_relative_path: str
) -> None:
    source_path = REPO_ROOT / source_relative_path
    if not source_path.exists():
        return
    destination_path = destination_dir / destination_relative_path
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)


def _repo_display_path(path: Path) -> str:
    candidate = path if path.is_absolute() else REPO_ROOT / path
    try:
        relative = candidate.relative_to(REPO_ROOT)
        return relative.as_posix() if str(relative) != "." else "."
    except ValueError:
        return str(path)


def _normalize_public_demo_string(value: str) -> str:
    return (
        value.replace(
            "christian-virtue-qwen2.5-1.5b-instruct-lora-mps-pilot-lite",
            "christian-virtue-qwen2.5-1.5b-instruct-lora-mps-local-baseline",
        )
        .replace(
            "runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite",
            "runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline",
        )
    )


def _sanitize_public_path_string(value: str) -> str:
    if value.startswith(("http://", "https://")):
        return value
    candidate = Path(value)
    if not candidate.is_absolute():
        return _normalize_public_demo_string(value)
    return _normalize_public_demo_string(_repo_display_path(candidate))


def _sanitize_public_json_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _sanitize_public_json_payload(item_value) for key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_public_json_payload(item) for item in value]
    if isinstance(value, str):
        return _sanitize_public_path_string(value)
    return value


def _copy_sanitized_json_if_present(source_dir: Path, destination_dir: Path, filename: str) -> None:
    source_path = source_dir / filename
    if not source_path.exists():
        return
    payload = _sanitize_public_json_payload(_read_json(source_path))
    write_json(destination_dir / filename, cast(dict[str, Any], payload))


def _copy_sanitized_text_if_present(source_dir: Path, destination_dir: Path, filename: str) -> None:
    source_path = source_dir / filename
    if not source_path.exists():
        return
    text = source_path.read_text(encoding="utf-8")
    (destination_dir / filename).write_text(
        _normalize_public_demo_string(text),
        encoding="utf-8",
    )


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


def _load_dataset_summary(dataset_manifest_path: Path) -> dict[str, Any] | None:
    if not dataset_manifest_path.exists():
        return None
    manifest = _read_json(dataset_manifest_path)
    split_sizes = cast(dict[str, Any], manifest.get("split_sizes", {}))
    total_examples = sum(int(value) for value in split_sizes.values() if value is not None)
    return {
        "dataset_name": manifest.get("dataset_name"),
        "source_annotations_used": manifest.get("source_annotations_used"),
        "grouping_key": manifest.get("grouping_key"),
        "split_sizes": split_sizes,
        "task_template_counts": manifest.get("task_template_counts", {}),
        "annotation_counts_by_support_type": manifest.get(
            "annotation_counts_by_support_type", {}
        ),
        "total_examples": total_examples,
    }


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
    dataset_manifest_path = (
        REPO_ROOT / "data/processed/sft/exports/christian_virtue_v1/manifest.json"
    )
    publication_git_commit = current_git_commit(REPO_ROOT) or str(train_metadata["git_commit"])
    return {
        "base_model": train_metadata["model_name_or_path"],
        "dataset_dir": "data/processed/sft/exports/christian_virtue_v1",
        "dataset_manifest_path": "data/processed/sft/exports/christian_virtue_v1/manifest.json",
        "dataset_summary": _load_dataset_summary(dataset_manifest_path),
        "git_commit": train_metadata["git_commit"],
        "publication_git_commit": publication_git_commit,
        "release_tag": release_tag,
        "github_repo_url": github_repo_url,
        "github_release_url": f"{github_repo_url}/releases/tag/{release_tag}",
        "hf_repo_id": hf_repo_id,
        "hf_repo_url": f"https://huggingface.co/{hf_repo_id}",
        "local_train_run_id": train_metadata["run_id"],
        "published_report_path": _repo_display_path(report_path),
        "published_report_assets": {
            destination_path: _repo_display_path(REPO_ROOT / source_path)
            for source_path, destination_path in PACKAGE_REPORT_ASSETS.items()
            if (REPO_ROOT / source_path).exists()
        },
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


def _release_slug_note(package_manifest: dict[str, Any]) -> str | None:
    release_tag = str(package_manifest.get("release_tag", "")).strip()
    run_id = str(package_manifest.get("local_train_run_id", "")).strip()
    if not release_tag or not run_id or run_id in release_tag:
        return None
    return (
        "The public GitHub release keeps the earlier distribution tag "
        f"`{release_tag}` for continuity, but the authoritative benchmark numbers in this "
        f"package and curated report come from the corrected run `{run_id}`."
    )


def build_model_card_text(
    *,
    package_manifest: dict[str, Any],
    report_path: Path,
    dataset_card_path: Path,
) -> str:
    summary = cast(dict[str, Any], package_manifest.get("summary", {}))
    dataset_summary = cast(dict[str, Any] | None, package_manifest.get("dataset_summary"))
    dataset_card_display = _repo_display_path(dataset_card_path)
    report_display = _repo_display_path(report_path)
    github_repo_url = str(package_manifest["github_repo_url"])
    publication_git_commit = str(
        package_manifest.get("publication_git_commit", package_manifest["git_commit"])
    )
    report_url = _github_blob_url(github_repo_url, publication_git_commit, report_display)
    dataset_card_url = _github_blob_url(
        github_repo_url, publication_git_commit, dataset_card_display
    )
    repo_url = str(package_manifest["github_repo_url"])
    release_url = str(package_manifest["github_release_url"])
    hf_url = str(package_manifest["hf_repo_url"])
    benchmark_figure = "./assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg"
    split_sizes = cast(dict[str, Any], (dataset_summary or {}).get("split_sizes", {}))
    task_template_counts = cast(
        dict[str, Any], (dataset_summary or {}).get("task_template_counts", {})
    )
    source_annotations_used = (dataset_summary or {}).get("source_annotations_used")
    total_examples = (dataset_summary or {}).get("total_examples")
    grouping_key = (dataset_summary or {}).get("grouping_key")
    source_annotations_text = (
        source_annotations_used if source_annotations_used is not None else "n/a"
    )
    total_examples_text = total_examples if total_examples is not None else "n/a"
    grouping_key_text = grouping_key if grouping_key is not None else "question_id"
    release_slug_note = _release_slug_note(package_manifest)
    strongest_task = cast(dict[str, Any] | None, summary.get("strongest_task"))
    strongest_tract = cast(dict[str, Any] | None, summary.get("strongest_tract"))

    lines = [
        "---",
        f"base_model: {package_manifest['base_model']}",
        "base_model_relation: adapter",
        "license: mit",
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
        "- evidence-grounded",
        "- citation-aware",
        "---",
        "",
        "# Summa Moral Graph Christian Virtue LoRA Adapter",
        "",
        "This is the canonical reproducible LoRA adapter for the `summa-moral-graph` Christian "
        "virtue SFT baseline. It fine-tunes `Qwen/Qwen2.5-1.5B-Instruct` toward "
        "Aquinas-grounded Christian virtue reasoning while preserving explicit passage-level "
        "traceability to reviewed evidence.",
        "",
        "## Abstract",
        "",
        "The purpose of this model is not to produce generic theological chat or to memorize "
        "citation strings. The goal is to show, in a compact and reproducible public baseline, "
        "that reviewed Summa Moral Graph supervision can measurably move a general model toward "
        "Aquinas's virtue categories, evidence-bounded answers, and citation-aware outputs.",
        "",
        "## Snapshot",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Base model | `{package_manifest['base_model']}` |",
        "| Training mode | LoRA on Apple Silicon `mps`, `float16`, no quantization |",
        f"| Reviewed source annotations | `{source_annotations_text}` |",
        f"| Total SFT examples | `{total_examples_text}` |",
        (
            f"| Train / val / test | `{split_sizes.get('train', 'n/a')} / "
            f"{split_sizes.get('val', 'n/a')} / {split_sizes.get('test', 'n/a')}` |"
        ),
        f"| Canonical run id | `{package_manifest['local_train_run_id']}` |",
        f"| Git commit | `{package_manifest['git_commit']}` |",
    ]
    if strongest_task is not None:
        lines.append(
            f"| Strongest task slice | `{strongest_task['label']}` "
            f"at `{_format_percent(float(strongest_task['candidate_exact']))}` |"
        )
    if strongest_tract is not None:
        lines.append(
            f"| Strongest tract slice | `{strongest_tract['label']}` "
            f"at `{_format_percent(float(strongest_tract['candidate_exact']))}` |"
        )
    lines.append("")
    if release_slug_note is not None:
        lines.extend(
            [
                "## Artifact Status",
                "",
                f"- {release_slug_note}",
                "- Treat the curated report and local package manifest as the canonical evaluation "
                "surface for the current repo numbers.",
                "- `subset_summary.json` records the exact balanced `(task_type, tract)` "
                "composition of the local training and eval subsets used for this run.",
                "",
            ]
        )
    lines.extend(
        [
            "## Why This Adapter Exists",
            "",
            "- Train an Aquinas-grounded Christian virtue assistant rather than a generic "
            "theology bot.",
            "- Keep the supervision evidence-first: reviewed doctrinal annotations only, "
            "joined back to stable passage ids.",
            "- Demonstrate a small public baseline that others can inspect, reproduce, "
            "and adapt to their own models before scaling up to larger runs.",
            "",
            "## Public Benchmark Highlights",
            "",
            "| Highlight | Base | Adapter | Delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    if strongest_task is not None:
        lines.append(
            f"| {strongest_task['label']} | "
            f"`{_format_percent(float(strongest_task['baseline_exact']))}` | "
            f"`{_format_percent(float(strongest_task['candidate_exact']))}` | "
            f"`{_format_percent(float(strongest_task['delta_exact']))}` |"
        )
    if strongest_tract is not None:
        lines.append(
            f"| {strongest_tract['label']} tract | "
            f"`{_format_percent(float(strongest_tract['baseline_exact']))}` | "
            f"`{_format_percent(float(strongest_tract['candidate_exact']))}` | "
            f"`{_format_percent(float(strongest_tract['delta_exact']))}` |"
        )
    lines.extend(["", "## Executive Readout", ""])
    if strongest_task is not None:
        lines.append(
            f"- The clearest public win is `{strongest_task['label']}`: "
            f"`{_format_percent(float(strongest_task['candidate_exact']))}` exact over "
            f"`{strongest_task['count']}` held-out prompts."
        )
    if strongest_tract is not None:
        lines.append(
            f"- Strongest tract slice: `{strongest_tract['label']}` at "
            f"`{_format_percent(float(strongest_tract['candidate_exact']))}` exact over "
            f"`{strongest_tract['count']}` prompts."
        )
    lines.extend(
        [
            "- This published run uses a deliberately small 1.5B local demo model, so "
            "the result should be read as proof that the pipeline works rather than as "
            "the ceiling for final quality.",
            "- This package intentionally foregrounds the strongest virtue-aligned slices; "
            "the full held-out matrix remains in the published report.",
            "- Full task/tract breakdowns and the qualitative goal-demo panel live in the "
            "published report.",
            "",
            f"![Held-out benchmark comparison]({benchmark_figure})",
            "",
            "*Figure. Held-out base-vs-adapter comparison from the canonical local "
            "`local-baseline` run. "
            "The key claim is straightforward: even a small reproducible demo baseline moves "
            "model behavior in the right direction, which makes this a credible public SFT "
            "template rather than only a code release.*",
            "",
            "## Dataset And Evidence Policy",
            "",
            "- Training export: `data/processed/sft/exports/christian_virtue_v1`",
            "- Dataset manifest: `data/processed/sft/exports/christian_virtue_v1/manifest.json`",
            f"- Dataset card: [GitHub link]({dataset_card_url})",
            f"- Full report: [GitHub link]({report_url})",
            f"- GitHub release: {release_url}",
            f"- Hugging Face adapter: {hf_url}",
            "- Supervision source: approved reviewed doctrinal annotations only",
            "- Excluded from default training truth: structural-editorial review, "
            "candidate material, and processed edge exports",
            f"- Leakage-safe grouping key: `{grouping_key_text}`",
            "",
            "Task families in this export:",
            "",
            (
                "- Passage-grounded doctrinal QA: "
                f"`{task_template_counts.get('passage_grounded_doctrinal_qa', 'n/a')}`"
            ),
            (
                "- Reviewed relation explanation: "
                f"`{task_template_counts.get('reviewed_relation_explanation', 'n/a')}`"
            ),
            (
                "- Citation-grounded moral answer: "
                f"`{task_template_counts.get('citation_grounded_moral_answer', 'n/a')}`"
            ),
            (
                "- Virtue concept explanation: "
                f"`{task_template_counts.get('virtue_concept_explanation', 'n/a')}`"
            ),
            "",
            "## How To Use This Adapter",
            "",
            "```python",
            "import torch",
            "from peft import PeftModel",
            "from transformers import AutoModelForCausalLM, AutoTokenizer",
            "",
            f"base_model_id = \"{package_manifest['base_model']}\"",
            f"adapter_id = \"{package_manifest['hf_repo_id']}\"",
            "",
            "tokenizer = AutoTokenizer.from_pretrained(base_model_id)",
            "base_model = AutoModelForCausalLM.from_pretrained(",
            "    base_model_id,",
            "    torch_dtype=torch.float16,",
            "    device_map=\"auto\",",
            ")",
            "model = PeftModel.from_pretrained(base_model, adapter_id)",
            "```",
            "",
            "Recommended use pattern:",
            "",
            "- Ask for Aquinas-grounded explanations of virtues, vices, acts, or relations.",
            "- Ask the model to stay within cited support and to preserve stable passage "
            "ids when possible.",
            "- Keep the tokenizer/chat template aligned with the listed base model so the "
            "canonical prompt format is preserved.",
            "- Use exactly the listed base model; this adapter is not meant to be merged "
            "into a different backbone without retesting.",
            "",
            "## Reproduce This Exact Artifact",
            "",
            f"- Hugging Face adapter: {hf_url}",
            f"- GitHub repo: {repo_url}",
            f"- Matching GitHub release: {release_url}",
            f"- Curated experiment report: [GitHub link]({report_url})",
            f"- Dataset card: [GitHub link]({dataset_card_url})",
            "",
            "The shortest canonical reproduction path is:",
            "",
            "```bash",
            "make setup-christian-virtue-local",
            "make reproduce-christian-virtue-qwen2-5-1-5b-local",
            "make verify-christian-virtue-qwen2-5-1-5b-local-publishable",
            "```",
            "",
            "The repo also keeps the stepwise train/eval/report commands and the full "
            "report if you need a more granular audit trail.",
            "",
            "## What This Demonstrates",
            "",
            "- The dataset can move even a small general instruction model toward "
            "better Aquinas-grounded virtue reasoning.",
            "- A fully local Apple-Silicon run can produce a meaningful, inspectable "
            "held-out improvement that proves the pipeline works.",
            "- The repo is usable as a public fine-tuning template for other "
            "researchers who want to swap in their own base model or scale up.",
            "",
            "## Next Step For Stronger Results",
            "",
            "- This published checkpoint is the easy-to-reproduce demo baseline, not the "
            "intended final ceiling for model quality.",
            "- The same dataset and workflow are designed to support larger models and "
            "longer GPU-backed experiments when stronger results become the priority.",
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
    summary = cast(dict[str, Any], package_manifest.get("summary", {}))
    report_display = _repo_display_path(report_path)
    dataset_card_display = _repo_display_path(dataset_card_path)
    github_repo_url = str(package_manifest["github_repo_url"])
    publication_git_commit = str(
        package_manifest.get("publication_git_commit", package_manifest["git_commit"])
    )
    report_url = _github_blob_url(github_repo_url, publication_git_commit, report_display)
    dataset_card_url = _github_blob_url(
        github_repo_url, publication_git_commit, dataset_card_display
    )
    release_slug_note = _release_slug_note(package_manifest)

    lines = [
        "# Christian Virtue Qwen2.5 1.5B Local Baseline",
        "",
        "This release mirrors the canonical local `local-baseline` adapter publication for the "
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
    ]
    if release_slug_note is not None:
        lines.extend(
            [
                "## Artifact Status",
                "",
                f"- {release_slug_note}",
                "- Treat the curated report and local package manifest as the canonical evaluation "
                "surface for the current repo numbers.",
                "- `subset_summary.json` records the exact balanced `(task_type, tract)` "
                "composition of the local training and eval subsets used for this run.",
                "",
            ]
        )
    lines.extend(
        [
            "## Executive Readout",
            "",
        ]
    )
    strongest_task = cast(dict[str, Any] | None, summary.get("strongest_task"))
    strongest_tract = cast(dict[str, Any] | None, summary.get("strongest_tract"))
    if strongest_task is not None:
        lines.append(
            f"- Clearest public win: `{strongest_task['label']}` at "
            f"`{_format_percent(float(strongest_task['candidate_exact']))}` exact over "
            f"`{strongest_task['count']}` prompts."
        )
    if strongest_tract is not None:
        lines.append(
            f"- Strongest tract slice: `{strongest_tract['label']}` at "
            f"`{_format_percent(float(strongest_tract['candidate_exact']))}` exact over "
            f"`{strongest_tract['count']}` prompts."
        )
    lines.extend(
        [
            "- This published run uses a deliberately small local demo model, so the "
            "result should be read as proof-of-pipeline rather than the final quality "
            "target.",
            "- This release foregrounds the strongest virtue-aligned slices; the full held-out "
            "matrix remains in the curated report.",
            "- Full task/tract breakdowns and the qualitative goal-demo panel live in the "
            "curated report.",
            "",
            "## Headline public highlights",
            "",
            (
                f"- Strongest task slice: `{strongest_task['label']}` at "
                f"`{_format_percent(float(strongest_task['candidate_exact']))}`"
                if strongest_task is not None
                else "- Strongest task slice: `n/a`"
            ),
            (
                f"- Strongest tract slice: `{strongest_tract['label']}` at "
                f"`{_format_percent(float(strongest_tract['candidate_exact']))}`"
                if strongest_tract is not None
                else "- Strongest tract slice: `n/a`"
            ),
            f"- Run id: `{package_manifest['local_train_run_id']}`",
            f"- Git commit: `{package_manifest['git_commit']}`",
            "",
            "## Canonical command path",
            "",
            "```bash",
            "make build-christian-virtue-sft",
            "make train-christian-virtue-qwen2-5-1-5b-local-smoke",
            "make train-christian-virtue-qwen2-5-1-5b-local-baseline",
            "make eval-christian-virtue-qwen2-5-1-5b-local-base-test",
            "make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test",
            "make compare-christian-virtue-qwen2-5-1-5b-local-test",
            "make report-christian-virtue-qwen2-5-1-5b-local-baseline",
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

    for source_path, destination_path in PACKAGE_REPORT_ASSETS.items():
        _copy_repo_asset_if_present(source_path, package_dir, destination_path)

    for filename in ["config_snapshot.yaml"]:
        _copy_sanitized_text_if_present(train_run_dir, package_dir, filename)
    for filename in [
        "environment.json",
        "run_manifest.json",
        "train_metadata.json",
        "subset_summary.json",
    ]:
        _copy_sanitized_json_if_present(train_run_dir, package_dir, filename)

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
