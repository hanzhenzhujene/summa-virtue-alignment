"""Package and optionally publish the canonical Christian virtue adapter and release metadata."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from summa_moral_graph.sft import (
    create_or_update_github_release,
    publish_adapter_package_to_hf,
    release_target_from_train_run,
    write_adapter_package,
)
from summa_moral_graph.utils.paths import REPO_ROOT

DEFAULT_HF_REPO_ID = "JennyZhu0822/summa-virtue-qwen2.5-1.5b"


def _parse_github_remote_url(remote_url: str) -> tuple[str, str] | None:
    ssh_match = re.match(r"git@github\.com:(?P<repo>[^/]+/[^/]+?)(?:\.git)?$", remote_url)
    if ssh_match is not None:
        repo = ssh_match.group("repo")
        return repo, f"https://github.com/{repo}"
    https_match = re.match(
        r"https://github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        remote_url,
    )
    if https_match is not None:
        repo = https_match.group("repo")
        return repo, f"https://github.com/{repo}"
    return None


def _infer_github_repo() -> tuple[str, str]:
    remote_completed = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if remote_completed.returncode == 0:
        parsed = _parse_github_remote_url(remote_completed.stdout.strip())
        if parsed is not None:
            return parsed

    completed = subprocess.run(
        [
            "gh",
            "repo",
            "view",
            "--json",
            "nameWithOwner,url",
            "--jq",
            '.nameWithOwner + "|" + .url',
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    repo_name, repo_url = completed.stdout.strip().split("|", maxsplit=1)
    return repo_name, repo_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--train-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite/latest",
        type=Path,
    )
    parser.add_argument(
        "--base-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--adapter-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--report-path",
        default=REPO_ROOT / "docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md",
        type=Path,
    )
    parser.add_argument(
        "--dataset-card-path",
        default=REPO_ROOT / "docs/christian_virtue_dataset_card.md",
        type=Path,
    )
    parser.add_argument(
        "--package-dir",
        default=REPO_ROOT / "artifacts/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite_adapter",
        type=Path,
    )
    parser.add_argument("--hf-repo-id", default=DEFAULT_HF_REPO_ID)
    parser.add_argument("--github-repo")
    parser.add_argument("--github-repo-url")
    parser.add_argument("--release-tag")
    parser.add_argument("--release-title")
    parser.add_argument("--release-target")
    parser.add_argument("--skip-hf", action="store_true")
    parser.add_argument("--skip-github-release", action="store_true")
    parser.add_argument("--private", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    github_repo, github_repo_url = _infer_github_repo()
    if args.github_repo:
        github_repo = args.github_repo
    if args.github_repo_url:
        github_repo_url = args.github_repo_url

    train_metadata = json.loads(
        (args.train_run_dir / "train_metadata.json").read_text(encoding="utf-8")
    )
    run_id = str(train_metadata["run_id"])
    release_tag = args.release_tag or f"christian-virtue-qwen2.5-1.5b-pilot-lite-{run_id}"
    release_title = args.release_title or f"Christian Virtue Qwen2.5 1.5B Pilot-Lite ({run_id})"
    release_target = args.release_target or release_target_from_train_run(args.train_run_dir)

    package_dir = write_adapter_package(
        train_run_dir=args.train_run_dir,
        base_eval_run_dir=args.base_run_dir,
        adapter_eval_run_dir=args.adapter_run_dir,
        package_dir=args.package_dir,
        hf_repo_id=args.hf_repo_id,
        release_tag=release_tag,
        github_repo_url=github_repo_url,
        report_path=args.report_path,
        dataset_card_path=args.dataset_card_path,
    )

    hf_url = f"https://huggingface.co/{args.hf_repo_id}"
    if not args.skip_hf:
        hf_url = publish_adapter_package_to_hf(
            package_dir=package_dir,
            repo_id=args.hf_repo_id,
            commit_message=f"Publish Christian virtue pilot-lite adapter ({run_id})",
            private=args.private,
        )

    release_url = f"{github_repo_url}/releases/tag/{release_tag}"
    if not args.skip_github_release:
        release_url = create_or_update_github_release(
            tag=release_tag,
            title=release_title,
            notes_path=package_dir / "release_notes.md",
            repo=github_repo,
            target=release_target,
        )

    print(
        json.dumps(
            {
                "package_dir": str(package_dir),
                "hf_repo_id": args.hf_repo_id,
                "hf_url": hf_url,
                "github_repo": github_repo,
                "release_tag": release_tag,
                "release_target": release_target,
                "release_url": release_url,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
