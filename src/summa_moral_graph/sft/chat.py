"""Interactive chat helpers for talking to local Christian virtue adapters."""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.paths import REPO_ROOT
from .config import InferenceConfig
from .inference import (
    _align_generation_config,
    _clean_assistant_text,
    _detect_runtime,
    _render_prompt,
    ensure_inference_dependencies,
)
from .run_layout import (
    build_environment_snapshot,
    create_timestamped_run_dir,
    dataset_manifest_path,
    iso_timestamp,
    run_artifacts_for_dir,
    write_config_snapshot,
    write_json,
)

DEFAULT_CHAT_OUTPUT_ROOT = (
    REPO_ROOT / "runs" / "christian_virtue" / "qwen2_5_1_5b_instruct" / "full_corpus_chat"
)
DEFAULT_CHAT_SYSTEM_PROMPT = (
    "You are an Aquinas-grounded Christian virtue assistant trained on reviewed, passage-grounded "
    "Summa Moral Graph supervision. Answer directly, prefer concise evidence-first language, cite "
    "passage ids and citation labels when you can, and say when the reviewed evidence is unclear "
    "instead of inventing support."
)


@dataclass(frozen=True)
class ChatSessionPaths:
    run_dir: Path
    transcript_jsonl_path: Path
    transcript_markdown_path: Path


def chat_session_paths(run_dir: Path) -> ChatSessionPaths:
    return ChatSessionPaths(
        run_dir=run_dir,
        transcript_jsonl_path=run_dir / "chat_transcript.jsonl",
        transcript_markdown_path=run_dir / "chat_transcript.md",
    )


def describe_chat_plan(
    config: InferenceConfig,
    *,
    output_root: Path,
    system_prompt: str | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    runtime = _detect_runtime(config)
    return {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "chat_output_root": str(output_root),
        "dataset_dir": str(config.dataset_dir),
        "max_new_tokens": config.max_new_tokens,
        "model_name_or_path": config.model_name_or_path,
        "one_shot": one_shot,
        "resolved_device": runtime.device_type if runtime is not None else None,
        "run_name": config.run_name,
        "runtime_warnings": list(runtime.warnings) if runtime is not None else [],
        "system_prompt": system_prompt,
        "torch_dtype": runtime.torch_dtype_name if runtime is not None else None,
    }


def render_chat_transcript_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Christian Virtue Chat Transcript",
        "",
    ]
    for entry in entries:
        role = str(entry["role"])
        content = str(entry["content"]).strip()
        if role == "user":
            lines.extend(["## User", "", content, ""])
        elif role == "assistant":
            lines.extend(["## Assistant", "", content, ""])
        elif role == "command":
            lines.extend(["## Session Event", "", f"`{content}`", ""])
        else:
            lines.extend([f"## {role.title()}", "", content, ""])
    return "\n".join(lines).rstrip() + "\n"


def _write_transcript(paths: ChatSessionPaths, entries: list[dict[str, Any]]) -> None:
    with paths.transcript_jsonl_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    paths.transcript_markdown_path.write_text(
        render_chat_transcript_markdown(entries),
        encoding="utf-8",
    )


def _write_command_log(run_dir: Path, argv: list[str]) -> None:
    command_path = run_artifacts_for_dir(run_dir).command_log_path
    command_path.write_text(f"$ {shlex.join(argv)}\n", encoding="utf-8")


def _load_chat_model_bundle(config: InferenceConfig) -> tuple[Any, Any, Any]:
    ensure_inference_dependencies(config)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    runtime = _detect_runtime(config)
    if runtime is None:
        raise RuntimeError("Torch is required for chat runtime detection.")

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token

    torch_dtype = getattr(torch, runtime.torch_dtype_name)
    model: Any = AutoModelForCausalLM.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
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
    return model, tokenizer, runtime


def _generate_chat_response(
    *,
    model: Any,
    tokenizer: Any,
    config: InferenceConfig,
    messages: list[dict[str, str]],
) -> str:
    import torch

    prompt_text = _render_prompt(tokenizer, messages)
    device = next(model.parameters()).device
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
        generation_kwargs["do_sample"] = False
    with torch.no_grad():
        generated = model.generate(**tokenized, **generation_kwargs)
    input_length = int(tokenized["input_ids"].shape[-1])
    generated_ids = generated[0][input_length:]
    return _clean_assistant_text(tokenizer.decode(generated_ids, skip_special_tokens=True))


def run_interactive_chat(
    config: InferenceConfig,
    *,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    system_prompt: str | None = DEFAULT_CHAT_SYSTEM_PROMPT,
    one_shot: str | None = None,
    command_argv: list[str] | None = None,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    model, tokenizer, runtime = _load_chat_model_bundle(config)
    run_dir = create_timestamped_run_dir(output_root)
    artifacts = run_artifacts_for_dir(run_dir)
    session_paths = chat_session_paths(run_dir)
    if command_argv is not None:
        _write_command_log(run_dir, command_argv)

    config_snapshot_path = write_config_snapshot(
        run_dir,
        config_path=config.config_path,
        payload=config.model_dump(mode="json", exclude={"config_path"}),
    )
    environment = build_environment_snapshot(
        workspace_root=REPO_ROOT,
        resolved_device=runtime.device_type,
        torch_dtype=runtime.torch_dtype_name,
    )
    write_json(artifacts.environment_path, environment)

    start_time = iso_timestamp()
    history: list[dict[str, str]] = []
    transcript_entries: list[dict[str, Any]] = []
    if system_prompt:
        transcript_entries.append(
            {
                "content": system_prompt,
                "role": "system",
                "timestamp": start_time,
            }
        )
    _write_transcript(session_paths, transcript_entries)

    print(f"Chat session: {run_dir}")
    print(f"Model: {config.model_name_or_path}")
    if config.adapter_path is not None:
        print(f"Adapter: {config.adapter_path}")
    print("Commands: /reset, /exit")

    turn_count = 0
    pending_one_shot = one_shot

    while True:
        try:
            if pending_one_shot is not None:
                user_text = pending_one_shot.strip()
                pending_one_shot = None
                print(f"\nYou> {user_text}")
            else:
                user_text = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break

        if not user_text:
            continue
        if user_text in {"/exit", "/quit"}:
            break
        if user_text == "/reset":
            history = []
            transcript_entries.append(
                {
                    "content": "/reset",
                    "role": "command",
                    "timestamp": iso_timestamp(),
                }
            )
            _write_transcript(session_paths, transcript_entries)
            print("Conversation history cleared.")
            continue

        turn_count += 1
        transcript_entries.append(
            {
                "content": user_text,
                "role": "user",
                "timestamp": iso_timestamp(),
                "turn_index": turn_count,
            }
        )
        prompt_messages: list[dict[str, str]] = []
        if system_prompt:
            prompt_messages.append({"role": "system", "content": system_prompt})
        prompt_messages.extend(history)
        prompt_messages.append({"role": "user", "content": user_text})
        assistant_text = _generate_chat_response(
            model=model,
            tokenizer=tokenizer,
            config=config,
            messages=prompt_messages,
        )
        print(f"\nAssistant> {assistant_text}")
        transcript_entries.append(
            {
                "content": assistant_text,
                "role": "assistant",
                "timestamp": iso_timestamp(),
                "turn_index": turn_count,
            }
        )
        _write_transcript(session_paths, transcript_entries)
        history.extend(
            [
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": assistant_text},
            ]
        )
        if one_shot is not None:
            break

    end_time = iso_timestamp()
    package_versions = environment["versions"]
    dataset_manifest = dataset_manifest_path(config.dataset_dir)
    manifest = {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "command_log_path": str(artifacts.command_log_path),
        "config_snapshot_path": str(config_snapshot_path),
        "dataset_dir": str(config.dataset_dir),
        "dataset_manifest_path": str(dataset_manifest) if dataset_manifest is not None else None,
        "end_time": end_time,
        "environment_path": str(artifacts.environment_path),
        "git_commit": environment["git_commit"],
        "model_name_or_path": config.model_name_or_path,
        "one_shot": one_shot,
        "peft_version": package_versions["peft"],
        "python_version": environment["platform"]["python_version"],
        "resolved_device": runtime.device_type,
        "run_dir": str(run_dir),
        "run_id": run_dir.name,
        "run_manifest_path": str(artifacts.run_manifest_path),
        "run_name": config.run_name,
        "start_time": start_time,
        "system_prompt": system_prompt,
        "torch_dtype": runtime.torch_dtype_name,
        "torch_version": package_versions["torch"],
        "transcript_jsonl_path": str(session_paths.transcript_jsonl_path),
        "transcript_markdown_path": str(session_paths.transcript_markdown_path),
        "transformers_version": package_versions["transformers"],
        "trl_version": package_versions["trl"],
        "accelerate_version": package_versions["accelerate"],
        "turn_count": turn_count,
        "runtime_warnings": list(runtime.warnings),
    }
    write_json(artifacts.run_manifest_path, manifest)
    return manifest
