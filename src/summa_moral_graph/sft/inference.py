from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from .config import InferenceConfig

REQUIRED_INFERENCE_PACKAGES = [
    "peft",
    "torch",
    "transformers",
]


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


def load_benchmark_inputs(dataset_dir: Path, split_names: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name in split_names:
        path = _benchmark_path(dataset_dir, split_name)
        if not path.exists():
            raise FileNotFoundError(f"Benchmark split not found: {path}")
        rows.extend(_load_jsonl(path))
    return rows


def describe_inference_plan(config: InferenceConfig) -> dict[str, Any]:
    benchmark_paths = {
        split_name: str(_benchmark_path(config.dataset_dir, split_name))
        for split_name in config.split_names
    }
    return {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "benchmark_paths": benchmark_paths,
        "dataset_dir": str(config.dataset_dir),
        "max_new_tokens": config.max_new_tokens,
        "model_name_or_path": config.model_name_or_path,
        "output_dir": str(config.output_dir),
        "run_name": config.run_name,
        "split_names": list(config.split_names),
    }


def ensure_inference_dependencies(config: InferenceConfig) -> None:
    missing = [
        package
        for package in REQUIRED_INFERENCE_PACKAGES
        if importlib.util.find_spec(package) is None
    ]
    if config.load_in_4bit and importlib.util.find_spec("bitsandbytes") is None:
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
            )
        )
    rendered = "\n\n".join(f"{item['role']}: {item['content']}" for item in messages)
    return f"{rendered}\n\nassistant:"


def run_generation_inference(config: InferenceConfig) -> dict[str, Any]:
    ensure_inference_dependencies(config)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed

    benchmark_rows = load_benchmark_inputs(config.dataset_dir, config.split_names)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token

    quantization_config = None
    if config.load_in_4bit:
        prefer_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type=config.bnb_4bit_quant_type,
            bnb_4bit_use_double_quant=config.bnb_4bit_use_double_quant,
            bnb_4bit_compute_dtype=torch.bfloat16 if prefer_bf16 else torch.float16,
        )

    model = AutoModelForCausalLM.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
        quantization_config=quantization_config,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    if config.adapter_path is not None:
        if not config.adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {config.adapter_path}")
        model = PeftModel.from_pretrained(model, str(config.adapter_path))
    model.eval()
    set_seed(config.seed)

    device = next(model.parameters()).device
    prediction_rows: list[dict[str, Any]] = []
    for row in benchmark_rows:
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
        assistant_text = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
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

    predictions_path = config.output_dir / "predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for row in prediction_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    manifest = {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "benchmark_count": len(benchmark_rows),
        "dataset_dir": str(config.dataset_dir),
        "model_name_or_path": config.model_name_or_path,
        "predictions_path": str(predictions_path),
        "run_name": config.run_name,
        "split_names": list(config.split_names),
    }
    manifest_path = config.output_dir / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest
