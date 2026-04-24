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


@dataclass(frozen=True)
class ChatModelBundle:
    model: Any
    tokenizer: Any
    runtime: Any


@dataclass
class LiveChatSession:
    run_dir: Path
    config_snapshot_path: Path
    environment: dict[str, Any]
    session_paths: ChatSessionPaths
    start_time: str
    system_prompt: str | None
    history: list[dict[str, str]]
    transcript_entries: list[dict[str, Any]]
    turn_count: int = 0


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


def load_chat_model_bundle(config: InferenceConfig) -> ChatModelBundle:
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
    return ChatModelBundle(model=model, tokenizer=tokenizer, runtime=runtime)


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


def generate_chat_reply(
    bundle: ChatModelBundle,
    config: InferenceConfig,
    *,
    messages: list[dict[str, str]],
) -> str:
    return _generate_chat_response(
        model=bundle.model,
        tokenizer=bundle.tokenizer,
        config=config,
        messages=messages,
    )


def _chat_manifest(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    artifacts = run_artifacts_for_dir(session.run_dir)
    package_versions = session.environment["versions"]
    dataset_manifest = dataset_manifest_path(config.dataset_dir)
    return {
        "accelerate_version": package_versions["accelerate"],
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "command_log_path": str(artifacts.command_log_path),
        "config_snapshot_path": str(session.config_snapshot_path),
        "dataset_dir": str(config.dataset_dir),
        "dataset_manifest_path": str(dataset_manifest) if dataset_manifest is not None else None,
        "end_time": iso_timestamp(),
        "environment_path": str(artifacts.environment_path),
        "git_commit": session.environment["git_commit"],
        "model_name_or_path": config.model_name_or_path,
        "one_shot": one_shot,
        "peft_version": package_versions["peft"],
        "python_version": session.environment["platform"]["python_version"],
        "resolved_device": runtime.device_type if runtime is not None else None,
        "run_dir": str(session.run_dir),
        "run_id": session.run_dir.name,
        "run_manifest_path": str(artifacts.run_manifest_path),
        "run_name": config.run_name,
        "runtime_warnings": list(runtime.warnings) if runtime is not None else [],
        "start_time": session.start_time,
        "system_prompt": session.system_prompt,
        "torch_dtype": runtime.torch_dtype_name if runtime is not None else None,
        "torch_version": package_versions["torch"],
        "transcript_jsonl_path": str(session.session_paths.transcript_jsonl_path),
        "transcript_markdown_path": str(session.session_paths.transcript_markdown_path),
        "transformers_version": package_versions["transformers"],
        "trl_version": package_versions["trl"],
        "turn_count": session.turn_count,
    }


def persist_live_chat_session(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    _write_transcript(session.session_paths, session.transcript_entries)
    manifest = _chat_manifest(session, config, runtime=runtime, one_shot=one_shot)
    write_json(run_artifacts_for_dir(session.run_dir).run_manifest_path, manifest)
    return manifest


def create_live_chat_session(
    config: InferenceConfig,
    *,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    system_prompt: str | None = DEFAULT_CHAT_SYSTEM_PROMPT,
    command_argv: list[str] | None = None,
    runtime: Any | None = None,
) -> LiveChatSession:
    output_root.mkdir(parents=True, exist_ok=True)
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
        resolved_device=runtime.device_type if runtime is not None else None,
        torch_dtype=runtime.torch_dtype_name if runtime is not None else None,
    )
    write_json(artifacts.environment_path, environment)

    start_time = iso_timestamp()
    transcript_entries: list[dict[str, Any]] = []
    if system_prompt:
        transcript_entries.append(
            {
                "content": system_prompt,
                "role": "system",
                "timestamp": start_time,
            }
        )

    session = LiveChatSession(
        run_dir=run_dir,
        config_snapshot_path=config_snapshot_path,
        environment=environment,
        session_paths=session_paths,
        start_time=start_time,
        system_prompt=system_prompt,
        history=[],
        transcript_entries=transcript_entries,
    )
    persist_live_chat_session(session, config, runtime=runtime)
    return session


def record_chat_reset(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    session.history.clear()
    session.transcript_entries.append(
        {
            "content": "/reset",
            "role": "command",
            "timestamp": iso_timestamp(),
        }
    )
    return persist_live_chat_session(session, config, runtime=runtime, one_shot=one_shot)


def record_chat_exchange(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    user_text: str,
    assistant_text: str,
    one_shot: str | None = None,
) -> dict[str, Any]:
    session.turn_count += 1
    session.transcript_entries.extend(
        [
            {
                "content": user_text,
                "role": "user",
                "timestamp": iso_timestamp(),
                "turn_index": session.turn_count,
            },
            {
                "content": assistant_text,
                "role": "assistant",
                "timestamp": iso_timestamp(),
                "turn_index": session.turn_count,
            },
        ]
    )
    session.history.extend(
        [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ]
    )
    return persist_live_chat_session(session, config, runtime=runtime, one_shot=one_shot)


def run_interactive_chat(
    config: InferenceConfig,
    *,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    system_prompt: str | None = DEFAULT_CHAT_SYSTEM_PROMPT,
    one_shot: str | None = None,
    command_argv: list[str] | None = None,
) -> dict[str, Any]:
    bundle = load_chat_model_bundle(config)
    session = create_live_chat_session(
        config,
        output_root=output_root,
        system_prompt=system_prompt,
        command_argv=command_argv,
        runtime=bundle.runtime,
    )

    print(f"Chat session: {session.run_dir}")
    print(f"Model: {config.model_name_or_path}")
    if config.adapter_path is not None:
        print(f"Adapter: {config.adapter_path}")
    print("Commands: /reset, /exit")

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
            record_chat_reset(session, config, runtime=bundle.runtime, one_shot=one_shot)
            print("Conversation history cleared.")
            continue

        prompt_messages: list[dict[str, str]] = []
        if system_prompt:
            prompt_messages.append({"role": "system", "content": system_prompt})
        prompt_messages.extend(session.history)
        prompt_messages.append({"role": "user", "content": user_text})
        assistant_text = generate_chat_reply(
            bundle,
            config=config,
            messages=prompt_messages,
        )
        print(f"\nAssistant> {assistant_text}")
        record_chat_exchange(
            session,
            config,
            runtime=bundle.runtime,
            user_text=user_text,
            assistant_text=assistant_text,
            one_shot=one_shot,
        )
        if one_shot is not None:
            break

    return persist_live_chat_session(session, config, runtime=bundle.runtime, one_shot=one_shot)
