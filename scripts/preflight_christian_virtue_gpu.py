from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from summa_moral_graph.sft import (
    missing_required_paths,
    module_import_status,
    python_version_ok,
    python_version_string,
    workspace_free_gb,
    writable_directory_status,
)
from summa_moral_graph.utils.paths import REPO_ROOT

REQUIRED_CONFIGS = [
    REPO_ROOT / "configs/sft/christian_virtue_v1.yaml",
    REPO_ROOT / "configs/sft/christian_virtue_v1_ood.yaml",
    REPO_ROOT / "configs/train/qwen3_0_6b_qlora.yaml",
    REPO_ROOT / "configs/train/qwen3_0_6b_qlora_smoke.yaml",
    REPO_ROOT / "configs/inference/qwen3_0_6b_base_test.yaml",
    REPO_ROOT / "configs/inference/qwen3_0_6b_base_ood.yaml",
    REPO_ROOT / "configs/inference/qwen3_0_6b_adapter_test.yaml",
    REPO_ROOT / "configs/inference/qwen3_0_6b_adapter_ood.yaml",
]

REQUIRED_MODULES = [
    "accelerate",
    "bitsandbytes",
    "datasets",
    "peft",
    "torch",
    "transformers",
    "trl",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default="runs/christian_virtue/qwen3_0_6b",
        help="Directory that should be writable for the small-model run loop.",
    )
    parser.add_argument(
        "--min-free-gb",
        type=float,
        default=10.0,
        help="Fail if the workspace has less free disk than this threshold.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = (
        (REPO_ROOT / args.output_dir).resolve()
        if not Path(args.output_dir).is_absolute()
        else Path(args.output_dir).resolve()
    )

    errors: list[str] = []
    warnings: list[str] = []
    if platform.system() != "Linux":
        warnings.append(
            "This remote small-model path is tuned for Linux CUDA machines; non-Linux "
            "validation is still useful but not the target training environment."
        )
    python_ok = python_version_ok(tuple(sys.version_info))
    if not python_ok:
        errors.append("Python 3.11+ is required for the Christian virtue small-model loop.")

    module_status = module_import_status(REQUIRED_MODULES)
    missing_modules = sorted(name for name, ok in module_status.items() if not ok)
    if missing_modules:
        errors.append(
            "Missing or broken training dependencies: " + ", ".join(missing_modules)
        )

    torch_info: dict[str, object] = {"imported": False}
    if module_status.get("torch", False):
        import torch

        torch_info = {
            "imported": True,
            "version": getattr(torch, "__version__", "unknown"),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
            "bf16_supported": (
                torch.cuda.is_available() and torch.cuda.is_bf16_supported()
            ),
        }
        if torch.cuda.is_available():
            torch_info["device_name"] = torch.cuda.get_device_name(0)
        else:
            errors.append("torch.cuda.is_available() is false; this loop expects a CUDA GPU.")

    free_gb = workspace_free_gb(REPO_ROOT)
    if free_gb < args.min_free_gb:
        errors.append(
            f"Workspace only has {free_gb} GB free; need at least {args.min_free_gb} GB."
        )

    missing_paths = missing_required_paths(REQUIRED_CONFIGS)
    if missing_paths:
        errors.append("Missing required configs: " + ", ".join(missing_paths))

    writable_ok, writable_error = writable_directory_status(output_dir)
    if not writable_ok:
        errors.append(f"Output directory is not writable: {writable_error}")

    payload = {
        "ok": not errors,
        "platform": platform.platform(),
        "python_version": python_version_string(),
        "required_modules": module_status,
        "torch": torch_info,
        "workspace_free_gb": free_gb,
        "required_configs_checked": [str(path) for path in REQUIRED_CONFIGS],
        "output_dir": str(output_dir),
        "writable_output_dir": writable_ok,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
