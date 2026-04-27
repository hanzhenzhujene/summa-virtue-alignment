"""Build and publish the online Christian virtue chat demo to a Hugging Face Space."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

from summa_moral_graph.sft import load_dataset_build_config, load_inference_config
from summa_moral_graph.sft.chat import DEFAULT_CHAT_SUPPLEMENTAL_ANNOTATION_PATHS
from summa_moral_graph.utils.paths import REPO_ROOT

DEFAULT_SPACE_REPO_ID = "JennyZhu0822/summa-virtue-chat"
DEFAULT_SPACE_TITLE = "Summa Virtue Chat"
DEFAULT_SPACE_CONFIG_PATH = (
    REPO_ROOT / "configs" / "inference" / "qwen2_5_1_5b_instruct_full_corpus_online_chat.yaml"
)
DEFAULT_DATASET_CONFIG_PATH = REPO_ROOT / "configs" / "sft" / "christian_virtue_v1.yaml"
DEFAULT_SPACE_SDK_VERSION = "5.50.0"
ADAPTER_BUNDLE_FILES = (
    "README.md",
    "adapter_config.json",
    "adapter_model.safetensors",
    "config_snapshot.yaml",
    "environment.json",
    "metrics.json",
    "report.md",
    "run_manifest.json",
    "subset_summary.json",
    "train_metadata.json",
)
DEFAULT_SPACE_REQUIREMENTS = """\
beautifulsoup4>=4.12,<5
httpx>=0.27,<1
jsonschema>=4.23,<5
networkx>=3.3,<4
pandas>=2.2,<3
pydantic>=2.7,<3
PyYAML>=6,<7
pyvis>=0.3,<1
accelerate>=1.1,<2
datasets>=3.0,<5
peft>=0.13,<1
torch>=2.4,<3
transformers>=4.55,<5
trl>=0.12,<1
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_SPACE_REPO_ID,
        help="Hugging Face Space repo id, for example JennyZhu0822/summa-virtue-chat.",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_SPACE_TITLE,
        help="Display title written into the Space README.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_SPACE_CONFIG_PATH),
        help="Inference config used by the online Gradio chat demo.",
    )
    parser.add_argument(
        "--bundle-dir",
        default="",
        help="Optional output directory for the generated Space bundle.",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Create or keep the Space private instead of public.",
    )
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Build the Space bundle locally without uploading it.",
    )
    return parser.parse_args()


def _space_page_url(repo_id: str) -> str:
    return f"https://huggingface.co/spaces/{repo_id}"


def _space_host_url(repo_id: str) -> str:
    owner, name = repo_id.split("/", 1)
    return f"https://{owner.lower()}-{name.lower().replace('_', '-')}.hf.space"


def _copy_repo_path(path: Path, *, bundle_root: Path) -> None:
    resolved = path.resolve()
    relative = resolved.relative_to(REPO_ROOT)
    destination = bundle_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if resolved.is_dir():
        shutil.copytree(resolved, destination, dirs_exist_ok=True)
        return
    shutil.copy2(resolved, destination)


def _copy_adapter_bundle(adapter_dir: Path, *, bundle_root: Path) -> None:
    resolved = adapter_dir.resolve()
    relative = resolved.relative_to(REPO_ROOT)
    destination = bundle_root / relative
    destination.mkdir(parents=True, exist_ok=True)
    for name in ADAPTER_BUNDLE_FILES:
        source = resolved / name
        if not source.exists():
            continue
        shutil.copy2(source, destination / name)


def _bundle_source_paths(config_path: Path) -> list[Path]:
    inference_config = load_inference_config(config_path)
    dataset_config = load_dataset_build_config(DEFAULT_DATASET_CONFIG_PATH)
    if inference_config.adapter_path is None:
        raise ValueError("Online chat deployment requires an adapter_path in the inference config.")
    paths: list[Path] = [
        REPO_ROOT / "src" / "summa_moral_graph",
        DEFAULT_DATASET_CONFIG_PATH,
        config_path,
        inference_config.dataset_dir,
        dataset_config.corpus.segments_path,
        dataset_config.corpus.questions_path,
        dataset_config.corpus.articles_path,
    ]
    paths.extend(source.annotations_path for source in dataset_config.sources)
    paths.extend(DEFAULT_CHAT_SUPPLEMENTAL_ANNOTATION_PATHS)
    return paths


def _space_readme_text(*, repo_id: str, title: str) -> str:
    return f"""---
title: {title}
emoji: 📚
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: {DEFAULT_SPACE_SDK_VERSION}
app_file: app.py
pinned: false
---

# {title}

Small-model Aquinas-grounded chat demo built on `Qwen/Qwen2.5-1.5B-Instruct` plus the
full-corpus Christian virtue LoRA adapter.

- GitHub repo: [hanzhenzhujene/summa-virtue-alignment](https://github.com/hanzhenzhujene/summa-virtue-alignment)
- Published adapter: [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Space page: [{repo_id}]({_space_page_url(repo_id)})
- Evidence viewer: [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

This Space is the recommended online chat surface for the Christian virtue assistant. Streamlit
remains the evidence browser and graph viewer.
"""


def _space_app_text(config_path: Path) -> str:
    config_relative = config_path.resolve().relative_to(REPO_ROOT)
    return "\n".join(
        [
            '"""Serve the Christian virtue Gradio chat app inside a Hugging Face Space."""',
            "",
            "from __future__ import annotations",
            "",
            "import sys",
            "from pathlib import Path",
            "",
            "ROOT = Path(__file__).resolve().parent",
            'sys.path.insert(0, str(ROOT / "src"))',
            "",
            "from summa_moral_graph.app.gradio_chat import build_gradio_chat_app",
            "",
            "",
            "demo = build_gradio_chat_app(",
            f'    config_path=ROOT / "{config_relative.as_posix()}",',
            '    output_root=(',
            '        ROOT / "runs" / "christian_virtue" / "qwen2_5_1_5b_instruct"',
            '        / "full_corpus_chat"',
            "    ),",
            ")",
            "",
            "",
            'if __name__ == "__main__":',
            '    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)',
            "",
        ]
    )


def build_space_bundle(
    *,
    bundle_root: Path,
    config_path: Path,
    repo_id: str,
    title: str,
) -> Path:
    bundle_root.mkdir(parents=True, exist_ok=True)
    inference_config = load_inference_config(config_path)
    for source_path in _bundle_source_paths(config_path):
        _copy_repo_path(source_path, bundle_root=bundle_root)
    if inference_config.adapter_path is None:
        raise ValueError("Online chat deployment requires an adapter_path in the inference config.")
    _copy_adapter_bundle(inference_config.adapter_path, bundle_root=bundle_root)
    (bundle_root / "app.py").write_text(_space_app_text(config_path), encoding="utf-8")
    (bundle_root / "README.md").write_text(
        _space_readme_text(repo_id=repo_id, title=title),
        encoding="utf-8",
    )
    (bundle_root / "requirements.txt").write_text(DEFAULT_SPACE_REQUIREMENTS, encoding="utf-8")
    return bundle_root


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Inference config not found: {config_path}")

    api = HfApi()
    if args.bundle_dir:
        bundle_root = build_space_bundle(
            bundle_root=Path(args.bundle_dir).resolve(),
            config_path=config_path,
            repo_id=args.repo_id,
            title=args.title,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="summa-virtue-space-") as temp_dir:
            bundle_root = build_space_bundle(
                bundle_root=Path(temp_dir),
                config_path=config_path,
                repo_id=args.repo_id,
                title=args.title,
            )
            if args.skip_upload:
                print(f"Built Space bundle at: {bundle_root}")
                return
            api.create_repo(
                repo_id=args.repo_id,
                repo_type="space",
                space_sdk="gradio",
                private=args.private,
                exist_ok=True,
            )
            api.upload_folder(
                repo_id=args.repo_id,
                repo_type="space",
                folder_path=str(bundle_root),
                commit_message="Update Christian virtue online chat demo",
            )
            runtime = api.get_space_runtime(args.repo_id)
            print(f"Space page: {_space_page_url(args.repo_id)}")
            print(f"Space host: {_space_host_url(args.repo_id)}")
            print(f"Runtime stage: {runtime.stage}")
            print(f"Runtime hardware: {runtime.hardware}")
            return

    if args.skip_upload:
        print(f"Built Space bundle at: {bundle_root}")
        return

    api.create_repo(
        repo_id=args.repo_id,
        repo_type="space",
        space_sdk="gradio",
        private=args.private,
        exist_ok=True,
    )
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="space",
        folder_path=str(bundle_root),
        commit_message="Update Christian virtue online chat demo",
    )
    runtime = api.get_space_runtime(args.repo_id)
    print(f"Space page: {_space_page_url(args.repo_id)}")
    print(f"Space host: {_space_host_url(args.repo_id)}")
    print(f"Runtime stage: {runtime.stage}")
    print(f"Runtime hardware: {runtime.hardware}")


if __name__ == "__main__":
    main()
