"""Inference helpers for generating Christian virtue benchmark predictions from configs."""

from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Any

from ..utils.paths import REPO_ROOT
from .config import InferenceConfig
from .run_layout import (
    build_environment_snapshot,
    dataset_manifest_path,
    iso_timestamp,
    run_artifacts_for_dir,
    write_config_snapshot,
    write_json,
)
from .runtime import ModelRuntime, detect_torch_availability, resolve_model_runtime

REQUIRED_INFERENCE_PACKAGES = [
    "peft",
    "torch",
    "transformers",
]
THINK_BLOCK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)

InferenceRuntime = ModelRuntime


def _benchmark_path(dataset_dir: Path, split_name: str) -> Path:
    return dataset_dir / "benchmarks" / f"{split_name}.jsonl"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def load_benchmark_inputs(dataset_dir: Path, split_names: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name in split_names:
        path = _benchmark_path(dataset_dir, split_name)
        if not path.exists():
            raise FileNotFoundError(f"Benchmark split not found: {path}")
        rows.extend(_load_jsonl(path))
    return rows


def resolve_inference_runtime(
    config: InferenceConfig,
    *,
    cuda_available: bool,
    mps_available: bool,
    bf16_supported: bool,
) -> InferenceRuntime:
    return resolve_model_runtime(
        runtime_backend=config.runtime_backend,
        torch_dtype=config.torch_dtype,
        load_in_4bit=config.load_in_4bit,
        cuda_available=cuda_available,
        mps_available=mps_available,
        bf16_supported=bf16_supported,
    )


def _detect_runtime(config: InferenceConfig) -> InferenceRuntime | None:
    availability = detect_torch_availability()
    if availability is None:
        return None
    return resolve_inference_runtime(
        config,
        cuda_available=availability.cuda_available,
        mps_available=availability.mps_available,
        bf16_supported=availability.bf16_supported,
    )


def describe_inference_plan(config: InferenceConfig) -> dict[str, Any]:
    benchmark_paths = {
        split_name: str(_benchmark_path(config.dataset_dir, split_name))
        for split_name in config.split_names
    }
    plan = {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "benchmark_paths": benchmark_paths,
        "dataset_dir": str(config.dataset_dir),
        "max_new_tokens": config.max_new_tokens,
        "model_name_or_path": config.model_name_or_path,
        "output_dir": str(config.output_dir),
        "requested_runtime_backend": config.runtime_backend,
        "requested_torch_dtype": config.torch_dtype,
        "run_name": config.run_name,
        "split_names": list(config.split_names),
    }
    runtime = _detect_runtime(config)
    if runtime is not None:
        plan.update(
            {
                "effective_load_in_4bit": runtime.effective_load_in_4bit,
                "resolved_device": runtime.device_type,
                "runtime_warnings": list(runtime.warnings),
                "torch_dtype": runtime.torch_dtype_name,
            }
        )
    return plan


def ensure_inference_dependencies(config: InferenceConfig) -> None:
    missing = [
        package
        for package in REQUIRED_INFERENCE_PACKAGES
        if importlib.util.find_spec(package) is None
    ]
    runtime = _detect_runtime(config)
    if (
        config.load_in_4bit
        and runtime is not None
        and runtime.effective_load_in_4bit
        and importlib.util.find_spec("bitsandbytes") is None
    ):
        missing.append("bitsandbytes")
    if missing:
        missing_str = ", ".join(sorted(set(missing)))
        raise RuntimeError(
            "Missing optional inference dependencies: "
            f'{missing_str}. Install them with `pip install -e ".[dev,sft]"`.'
        )


def _render_prompt(tokenizer: Any, messages: list[dict[str, Any]]) -> str:
    if hasattr(tokenizer, "apply_chat_template"):
        return str(
            tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        )
    rendered = "\n\n".join(f"{item['role']}: {item['content']}" for item in messages)
    return f"{rendered}\n\nassistant:"


def _clean_assistant_text(text: str) -> str:
    cleaned = THINK_BLOCK_RE.sub("", text)
    return cleaned.strip()


def _align_generation_config(model: Any, config: InferenceConfig) -> None:
    generation_config = getattr(model, "generation_config", None)
    if generation_config is None:
        return
    generation_config.do_sample = config.do_sample
    if config.do_sample:
        generation_config.temperature = config.temperature
        generation_config.top_p = config.top_p
        return

    # Some base model generation configs ship sampling-only defaults that trigger noisy warnings
    # even when we are running deterministic evaluation. Clearing them keeps the public CLI path
    # quieter without changing the actual decode behavior.
    for field_name in ("temperature", "top_p", "top_k"):
        if hasattr(generation_config, field_name):
            setattr(generation_config, field_name, None)


def run_generation_inference(config: InferenceConfig) -> dict[str, Any]:
    ensure_inference_dependencies(config)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed

    benchmark_rows = load_benchmark_inputs(config.dataset_dir, config.split_names)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = run_artifacts_for_dir(config.output_dir)
    start_time = iso_timestamp()
    config_snapshot_path = write_config_snapshot(
        config.output_dir,
        config_path=config.config_path,
        payload=config.model_dump(mode="json", exclude={"config_path"}),
    )
    runtime = _detect_runtime(config)
    if runtime is None:
        raise RuntimeError("Torch is required for inference runtime detection.")
    environment = build_environment_snapshot(
        workspace_root=REPO_ROOT,
        resolved_device=runtime.device_type,
        torch_dtype=runtime.torch_dtype_name,
    )
    write_json(artifacts.environment_path, environment)
    predictions_path = artifacts.predictions_path
    partial_path = artifacts.partial_predictions_path
    existing_rows = _load_jsonl(partial_path) if partial_path.exists() else []
    completed_example_ids = {str(row["example_id"]) for row in existing_rows}
    remaining_rows = [
        row for row in benchmark_rows if str(row["example_id"]) not in completed_example_ids
    ]

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token

    quantization_config = None
    if runtime.effective_load_in_4bit:
        prefer_bf16 = runtime.torch_dtype_name == "bfloat16"
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=config.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
            bnb_4bit_compute_dtype=torch.bfloat16 if prefer_bf16 else torch.float16,
        )
    torch_dtype = getattr(torch, runtime.torch_dtype_name)

    model: Any = AutoModelForCausalLM.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
        quantization_config=quantization_config,
        device_map="auto" if runtime.device_type == "cuda" else None,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
    )
    if config.adapter_path is not None:
        if not config.adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {config.adapter_path}")
        model = PeftModel.from_pretrained(model, str(config.adapter_path))
    if runtime.device_type != "cuda":
        model = model.to(runtime.device_type)
    _align_generation_config(model, config)
    model.eval()
    set_seed(config.seed)

    device = next(model.parameters()).device
    prediction_rows: list[dict[str, Any]] = list(existing_rows)
    total_rows = len(benchmark_rows)
    if prediction_rows:
        print(
            json.dumps(
                {
                    "completed": len(prediction_rows),
                    "event": "resume_loaded",
                    "output_path": str(partial_path),
                    "remaining": len(remaining_rows),
                    "total": total_rows,
                },
                sort_keys=True,
            )
        )
    for index, row in enumerate(remaining_rows, start=len(prediction_rows) + 1):
        messages = row["messages"]
        prompt_text = _render_prompt(tokenizer, messages)
        tokenized = tokenizer(prompt_text, return_tensors="pt")
        tokenized = {key: value.to(device) for key, value in tokenized.items()}
        generation_kwargs = {
            "max_new_tokens": config.max_new_tokens,
            "pad_token_id": tokenizer.pad_token_id,
            "eos_token_id": tokenizer.eos_token_id,
            "repetition_penalty": config.repetition_penalty,
        }
        if config.do_sample:
            generation_kwargs.update(
                {
                    "do_sample": True,
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                }
            )
        else:
            generation_kwargs.update({"do_sample": False})
        with torch.no_grad():
            generated = model.generate(**tokenized, **generation_kwargs)
        input_length = int(tokenized["input_ids"].shape[-1])
        generated_ids = generated[0][input_length:]
        assistant_text = _clean_assistant_text(
            tokenizer.decode(generated_ids, skip_special_tokens=True)
        )
        prediction_rows.append(
            {
                "example_id": row["example_id"],
                "split": row["split"],
                "task_type": row["task_type"],
                "assistant_text": assistant_text,
                "metadata": row["metadata"],
                "model_name_or_path": config.model_name_or_path,
                "adapter_path": (
                    str(config.adapter_path) if config.adapter_path is not None else None
                ),
            }
        )
        with partial_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(prediction_rows[-1], ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        if index == total_rows or index % 10 == 0:
            print(
                json.dumps(
                    {
                        "completed": index,
                        "event": "generation_progress",
                        "output_path": str(partial_path),
                        "remaining": total_rows - index,
                        "total": total_rows,
                    },
                    sort_keys=True,
                )
            )

    _write_jsonl(predictions_path, prediction_rows)
    if partial_path.exists():
        partial_path.unlink()

    end_time = iso_timestamp()
    package_versions = environment["versions"]
    dataset_manifest = dataset_manifest_path(config.dataset_dir)
    manifest = {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "benchmark_count": len(benchmark_rows),
        "config_snapshot_path": str(config_snapshot_path),
        "dataset_dir": str(config.dataset_dir),
        "dataset_manifest_path": str(dataset_manifest) if dataset_manifest is not None else None,
        "end_time": end_time,
        "effective_load_in_4bit": runtime.effective_load_in_4bit,
        "environment_path": str(artifacts.environment_path),
        "git_commit": environment["git_commit"],
        "model_name_or_path": config.model_name_or_path,
        "peft_version": package_versions["peft"],
        "predictions_path": str(predictions_path),
        "python_version": environment["platform"]["python_version"],
        "resolved_device": runtime.device_type,
        "run_id": config.output_dir.name,
        "run_name": config.run_name,
        "split_names": list(config.split_names),
        "start_time": start_time,
        "torch_version": package_versions["torch"],
        "transformers_version": package_versions["transformers"],
        "runtime_warnings": list(runtime.warnings),
        "trl_version": package_versions["trl"],
        "accelerate_version": package_versions["accelerate"],
        "torch_dtype": runtime.torch_dtype_name,
    }
    write_json(artifacts.run_manifest_path, manifest)
    return manifest
