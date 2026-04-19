from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, cast

from ..utils.paths import REPO_ROOT
from .run_layout import current_git_commit, write_json

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
    }


def build_model_card_text(
    *,
    package_manifest: dict[str, Any],
    report_path: Path,
    dataset_card_path: Path,
) -> str:
    base_metrics = package_manifest["base_metrics"]
    adapter_metrics = package_manifest["adapter_metrics"]
    dataset_card_display = _repo_display_path(dataset_card_path)
    report_display = _repo_display_path(report_path)
    return (
        "---\n"
        f"base_model: {package_manifest['base_model']}\n"
        "library_name: peft\n"
        "pipeline_tag: text-generation\n"
        "language:\n"
        "- en\n"
        "tags:\n"
        "- lora\n"
        "- text-generation\n"
        "- christian-virtue\n"
        "- aquinas\n"
        "- summa-moral-graph\n"
        "---\n\n"
        "# Summa Moral Graph Christian Virtue LoRA Adapter\n\n"
        "This adapter is the canonical local `pilot-lite` demonstration checkpoint for the "
        "Christian virtue SFT pipeline in `summa-moral-graph`.\n\n"
        "## Purpose\n\n"
        "This model is meant to move a general instruction model toward Aquinas-grounded "
        "Christian virtue reasoning. Citation traceability is included as a guardrail, not as "
        "the whole purpose of the fine-tune.\n\n"
        "## Base Model\n\n"
        f"- `{package_manifest['base_model']}`\n"
        "- LoRA adapter trained on Apple Silicon `mps`\n"
        "- `float16`, no 4-bit quantization\n\n"
        "## Dataset\n\n"
        "- Training export: `data/processed/sft/exports/christian_virtue_v1`\n"
        "- Dataset manifest: `data/processed/sft/exports/christian_virtue_v1/manifest.json`\n"
        f"- Dataset card: `{dataset_card_display}`\n\n"
        "## Canonical Run\n\n"
        f"- Train run id: `{package_manifest['local_train_run_id']}`\n"
        f"- Git commit: `{package_manifest['git_commit']}`\n"
        f"- Published report: `{report_display}`\n\n"
        "## Headline Held-Out Test Result\n\n"
        f"- Base citation exact match: `{base_metrics['citation_exact_match']:.3f}`\n"
        f"- Adapter citation exact match: `{adapter_metrics['citation_exact_match']:.3f}`\n\n"
        "## Intended Use\n\n"
        "- Aquinas-grounded Christian virtue QA and doctrinal explanation\n"
        "- Demonstrating how to fine-tune on the Summa Moral Graph dataset\n"
        "- Reproducible adapter publication tied to a documented run\n\n"
        "## Reproduce The Canonical Local Baseline\n\n"
        "```bash\n"
        "make build-christian-virtue-sft\n"
        "make train-christian-virtue-qwen2-5-1-5b-local-smoke\n"
        "make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite\n"
        "make eval-christian-virtue-qwen2-5-1-5b-local-base-test\n"
        "make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test\n"
        "make compare-christian-virtue-qwen2-5-1-5b-local-test\n"
        "make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite\n"
        "make verify-christian-virtue-qwen2-5-1-5b-local-publishable\n"
        "```\n\n"
        "## Limits\n\n"
        "- This is a local pilot baseline, not the final best-quality checkpoint\n"
        "- The hardest citation-grounded moral-answer cases remain unsolved\n"
        "- The adapter should be used with the listed base model only\n"
    )


def build_release_notes_text(
    *,
    package_manifest: dict[str, Any],
    report_path: Path,
    dataset_card_path: Path,
) -> str:
    base_metrics = package_manifest["base_metrics"]
    adapter_metrics = package_manifest["adapter_metrics"]
    report_display = _repo_display_path(report_path)
    dataset_card_display = _repo_display_path(dataset_card_path)
    return (
        "# Christian Virtue Qwen2.5 1.5B Local Pilot-Lite\n\n"
        "This release mirrors the canonical local `pilot-lite` adapter publication for the "
        "`summa-moral-graph` Christian virtue SFT pipeline.\n\n"
        "## Included here\n\n"
        f"- Hugging Face adapter: {package_manifest['hf_repo_url']}\n"
        f"- Curated experiment report: {report_display}\n"
        f"- Dataset card: {dataset_card_display}\n"
        "- Training export: `data/processed/sft/exports/christian_virtue_v1`\n\n"
        "## Purpose\n\n"
        "Train an Aquinas-grounded Christian virtue assistant that answers within reviewed "
        "evidence, uses Aquinas's moral categories, and preserves source traceability.\n\n"
        "## Headline result\n\n"
        f"- Base citation exact match: `{base_metrics['citation_exact_match']:.3f}`\n"
        f"- Adapter citation exact match: `{adapter_metrics['citation_exact_match']:.3f}`\n"
        f"- Run id: `{package_manifest['local_train_run_id']}`\n"
        f"- Git commit: `{package_manifest['git_commit']}`\n\n"
        "## Canonical command path\n\n"
        "```bash\n"
        "make build-christian-virtue-sft\n"
        "make train-christian-virtue-qwen2-5-1-5b-local-smoke\n"
        "make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite\n"
        "make eval-christian-virtue-qwen2-5-1-5b-local-base-test\n"
        "make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test\n"
        "make compare-christian-virtue-qwen2-5-1-5b-local-test\n"
        "make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite\n"
        "make verify-christian-virtue-qwen2-5-1-5b-local-publishable\n"
        "```\n"
    )


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
