from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from .config import TrainingConfig

REQUIRED_TRAINING_PACKAGES = [
    "accelerate",
    "bitsandbytes",
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
    return {
        "run_name": config.run_name,
        "model_name_or_path": config.model_name_or_path,
        "train_path": str(dataset_train_path),
        "eval_path": str(dataset_eval_path),
        "output_dir": str(config.output_dir),
        "max_seq_length": config.max_seq_length,
        "load_in_4bit": config.load_in_4bit,
        "lora_target_modules": config.lora_target_modules or list(DEFAULT_LORA_TARGET_MODULES),
        "gradient_checkpointing": config.gradient_checkpointing,
    }


def ensure_training_dependencies() -> None:
    missing = [
        package
        for package in REQUIRED_TRAINING_PACKAGES
        if importlib.util.find_spec(package) is None
    ]
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


def run_qlora_training(config: TrainingConfig) -> dict[str, Any]:
    ensure_training_dependencies()

    import torch
    from datasets import Dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import SFTTrainer

    train_path = config.dataset_dir / f"{config.train_split}.jsonl"
    eval_path = config.dataset_dir / f"{config.eval_split}.jsonl"
    if not train_path.exists():
        raise FileNotFoundError(f"Training split not found: {train_path}")
    if not eval_path.exists():
        raise FileNotFoundError(f"Eval split not found: {eval_path}")

    train_rows = _load_jsonl_dataset(train_path)
    eval_rows = _load_jsonl_dataset(eval_path)

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

    prefer_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=config.load_in_4bit,
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
    if config.gradient_checkpointing:
        model.gradient_checkpointing_enable()
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
    training_args = TrainingArguments(
        output_dir=str(config.output_dir),
        run_name=config.run_name,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        max_steps=config.max_steps,
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        logging_steps=config.logging_steps,
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        bf16=prefer_bf16,
        fp16=torch.cuda.is_available() and not prefer_bf16,
        report_to=config.report_to,
        gradient_checkpointing=config.gradient_checkpointing,
        seed=config.seed,
        remove_unused_columns=False,
        eval_strategy="steps",
        save_strategy="steps",
    )
    trainer = SFTTrainer(
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
    return {
        "run_name": config.run_name,
        "output_dir": str(config.output_dir),
        "metrics": metrics,
        "train_examples": len(train_dataset),
        "eval_examples": len(eval_dataset),
    }
