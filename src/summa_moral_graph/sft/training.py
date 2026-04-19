"""Runtime resolution and trainer wiring for Christian virtue LoRA and QLoRA experiments."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any

from ..utils.paths import REPO_ROOT
from .config import TrainingConfig
from .run_layout import (
    build_environment_snapshot,
    dataset_manifest_path,
    iso_timestamp,
    run_artifacts_for_dir,
    write_config_snapshot,
    write_json,
    write_jsonl,
)
from .runtime import ModelRuntime, detect_torch_availability, resolve_model_runtime

REQUIRED_TRAINING_PACKAGES = [
    "accelerate",
    "datasets",
    "peft",
    "torch",
    "transformers",
    "trl",
]

DEFAULT_LORA_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def describe_training_plan(config: TrainingConfig) -> dict[str, Any]:
    dataset_train_path = config.dataset_dir / f"{config.train_split}.jsonl"
    dataset_eval_path = config.dataset_dir / f"{config.eval_split}.jsonl"
    plan = {
        "run_name": config.run_name,
        "model_name_or_path": config.model_name_or_path,
        "train_path": str(dataset_train_path),
        "eval_path": str(dataset_eval_path),
        "output_dir": str(config.output_dir),
        "max_seq_length": config.max_seq_length,
        "max_train_examples": config.max_train_examples,
        "max_eval_examples": config.max_eval_examples,
        "requested_runtime_backend": config.runtime_backend,
        "requested_torch_dtype": config.torch_dtype,
        "lora_target_modules": config.lora_target_modules or list(DEFAULT_LORA_TARGET_MODULES),
        "gradient_checkpointing": config.gradient_checkpointing,
    }
    runtime = _detect_runtime(config)
    if runtime is not None:
        plan.update(
            {
                "effective_load_in_4bit": runtime.effective_load_in_4bit,
                "load_in_4bit": runtime.effective_load_in_4bit,
                "resolved_device": runtime.device_type,
                "runtime_warnings": list(runtime.warnings),
                "torch_dtype": runtime.torch_dtype_name,
            }
        )
    else:
        plan["load_in_4bit"] = config.load_in_4bit
    return plan


def resolve_training_runtime(
    config: TrainingConfig,
    *,
    cuda_available: bool,
    mps_available: bool,
    bf16_supported: bool,
) -> ModelRuntime:
    return resolve_model_runtime(
        runtime_backend=config.runtime_backend,
        torch_dtype=config.torch_dtype,
        load_in_4bit=config.load_in_4bit,
        cuda_available=cuda_available,
        mps_available=mps_available,
        bf16_supported=bf16_supported,
    )


def _detect_runtime(config: TrainingConfig) -> ModelRuntime | None:
    availability = detect_torch_availability()
    if availability is None:
        return None
    return resolve_training_runtime(
        config,
        cuda_available=availability.cuda_available,
        mps_available=availability.mps_available,
        bf16_supported=availability.bf16_supported,
    )


def ensure_training_dependencies(config: TrainingConfig) -> None:
    missing = [
        package
        for package in REQUIRED_TRAINING_PACKAGES
        if importlib.util.find_spec(package) is None
    ]
    runtime = _detect_runtime(config)
    if (
        runtime is not None
        and runtime.effective_load_in_4bit
        and importlib.util.find_spec("bitsandbytes") is None
    ):
        missing.append("bitsandbytes")
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(
            "Missing optional training dependencies: "
            f'{missing_str}. Install them with `pip install -e ".[dev,sft]"`.'
        )


def _load_jsonl_dataset(path: Path) -> list[dict[str, Any]]:
    import json

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _slice_rows(rows: list[dict[str, Any]], max_examples: int | None) -> list[dict[str, Any]]:
    if max_examples is None:
        return rows
    return rows[:max_examples]


def _write_training_report(metadata: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Christian Virtue Training Report",
        "",
        f"- Run name: {metadata['run_name']}",
        f"- Model: {metadata['model_name_or_path']}",
        f"- Train examples: {metadata['train_examples']}",
        f"- Eval examples: {metadata['eval_examples']}",
        f"- Adapter path: {metadata['adapter_path']}",
        f"- Config snapshot: {metadata['config_snapshot_path']}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in sorted(metadata["metrics"].items()):
        lines.append(f"- {key}: {value}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_qlora_training(config: TrainingConfig) -> dict[str, Any]:
    ensure_training_dependencies(config)

    import torch
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
    )
    from trl import SFTTrainer
    sft_config_class: Any | None
    try:
        from trl import SFTConfig as ImportedSFTConfig

        sft_config_class = ImportedSFTConfig
    except ImportError:
        sft_config_class = None

    train_path = config.dataset_dir / f"{config.train_split}.jsonl"
    eval_path = config.dataset_dir / f"{config.eval_split}.jsonl"
    if not train_path.exists():
        raise FileNotFoundError(f"Training split not found: {train_path}")
    if not eval_path.exists():
        raise FileNotFoundError(f"Eval split not found: {eval_path}")

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
        raise RuntimeError("Torch is required for training runtime detection.")
    environment = build_environment_snapshot(
        workspace_root=REPO_ROOT,
        resolved_device=runtime.device_type,
        torch_dtype=runtime.torch_dtype_name,
    )
    write_json(artifacts.environment_path, environment)

    train_rows = _slice_rows(_load_jsonl_dataset(train_path), config.max_train_examples)
    eval_rows = _slice_rows(_load_jsonl_dataset(eval_path), config.max_eval_examples)

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token

    def render_messages(row: dict[str, Any]) -> dict[str, Any]:
        messages = row["messages"]
        if hasattr(tokenizer, "apply_chat_template"):
            text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        else:
            text = "\n\n".join(f"{item['role']}: {item['content']}" for item in messages)
        return {"text": text}

    train_dataset = Dataset.from_list(train_rows).map(render_messages)
    eval_dataset = Dataset.from_list(eval_rows).map(render_messages)

    quantization_config = None
    if runtime.effective_load_in_4bit:
        from transformers import BitsAndBytesConfig

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
    if runtime.device_type != "cuda":
        model = model.to(runtime.device_type)
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()
    if runtime.effective_load_in_4bit:
        from peft import prepare_model_for_kbit_training

        model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=config.lora_target_modules or list(DEFAULT_LORA_TARGET_MODULES),
    )
    training_args_kwargs: dict[str, Any] = {
        "output_dir": str(config.output_dir),
        "run_name": config.run_name,
        "learning_rate": config.learning_rate,
        "num_train_epochs": config.num_train_epochs,
        "max_steps": config.max_steps,
        "per_device_train_batch_size": config.per_device_train_batch_size,
        "per_device_eval_batch_size": config.per_device_eval_batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "warmup_ratio": config.warmup_ratio,
        "weight_decay": config.weight_decay,
        "logging_steps": config.logging_steps,
        "eval_steps": config.eval_steps,
        "save_steps": config.save_steps,
        "save_total_limit": config.save_total_limit,
        "bf16": runtime.device_type == "cuda" and runtime.torch_dtype_name == "bfloat16",
        "fp16": runtime.device_type == "cuda" and runtime.torch_dtype_name == "float16",
        "report_to": config.report_to,
        "gradient_checkpointing": config.gradient_checkpointing,
        "seed": config.seed,
        "remove_unused_columns": False,
        "eval_strategy": "steps",
        "save_strategy": "steps",
    }
    trainer_class: Any = SFTTrainer
    trainer_init_parameters = inspect.signature(trainer_class.__init__).parameters
    if sft_config_class is not None and "processing_class" in trainer_init_parameters:
        trainer_args = sft_config_class(
            **training_args_kwargs,
            use_mps_device=runtime.device_type == "mps",
            dataset_text_field="text",
            max_length=config.max_seq_length,
            packing=False,
        )
        trainer = trainer_class(
            model=model,
            args=trainer_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            processing_class=tokenizer,
            peft_config=peft_config,
        )
    else:
        training_args = TrainingArguments(**training_args_kwargs)
        trainer = trainer_class(
            model=model,
            tokenizer=tokenizer,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            peft_config=peft_config,
            dataset_text_field="text",
            max_seq_length=config.max_seq_length,
            packing=False,
        )
    trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(config.output_dir)
    metrics = trainer.evaluate()
    write_json(artifacts.metrics_path, metrics)
    write_jsonl(artifacts.train_log_history_path, trainer.state.log_history)
    end_time = iso_timestamp()
    package_versions = environment["versions"]
    dataset_manifest = dataset_manifest_path(config.dataset_dir)
    metadata = {
        "accelerate_version": package_versions["accelerate"],
        "run_name": config.run_name,
        "model_name_or_path": config.model_name_or_path,
        "output_dir": str(config.output_dir),
        "adapter_path": str(config.output_dir),
        "config_snapshot_path": str(config_snapshot_path),
        "dataset_manifest_path": str(dataset_manifest) if dataset_manifest is not None else None,
        "end_time": end_time,
        "environment_path": str(artifacts.environment_path),
        "git_commit": environment["git_commit"],
        "metrics": metrics,
        "train_examples": len(train_dataset),
        "eval_examples": len(eval_dataset),
        "max_train_examples": config.max_train_examples,
        "max_eval_examples": config.max_eval_examples,
        "best_model_checkpoint": trainer.state.best_model_checkpoint,
        "global_step": trainer.state.global_step,
        "peft_version": package_versions["peft"],
        "python_version": environment["platform"]["python_version"],
        "resolved_device": runtime.device_type,
        "run_id": config.output_dir.name,
        "start_time": start_time,
        "torch_dtype": runtime.torch_dtype_name,
        "torch_version": package_versions["torch"],
        "train_log_history_path": str(artifacts.train_log_history_path),
        "transformers_version": package_versions["transformers"],
        "trl_version": package_versions["trl"],
    }
    write_json(artifacts.train_metadata_path, metadata)
    write_json(
        artifacts.run_manifest_path,
        {
            **metadata,
            "runtime_warnings": list(runtime.warnings),
        },
    )
    _write_training_report(metadata, artifacts.report_path)
    return metadata
