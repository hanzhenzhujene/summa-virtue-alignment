from __future__ import annotations

from pathlib import Path

from summa_moral_graph.app.gradio_chat import (
    DEFAULT_GRADIO_CHAT_GITHUB_URL,
    DEFAULT_GRADIO_CHAT_HF_URL,
    DEFAULT_GRADIO_CHAT_SPACE_URL,
    DEFAULT_GRADIO_CHAT_VIEWER_URL,
    gradio_chatbot_messages,
    gradio_header_html,
    gradio_session_status_markdown,
)
from summa_moral_graph.sft import InferenceConfig, LiveChatSession, chat_session_paths


def _demo_config() -> InferenceConfig:
    return InferenceConfig(
        run_name="demo-chat",
        model_name_or_path="Qwen/Qwen2.5-1.5B-Instruct",
        dataset_dir=Path("data/processed/sft/exports/christian_virtue_v1"),
        split_names=["test"],
        output_dir=Path("runs/demo-unused"),
        adapter_path=Path("runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest"),
        runtime_backend="mps",
        torch_dtype="float16",
        load_in_4bit=False,
    )


def test_gradio_session_status_markdown_without_session_is_readable() -> None:
    markdown = gradio_session_status_markdown(_demo_config(), None)

    assert "### Current Setup" in markdown
    assert "Qwen/Qwen2.5-1.5B-Instruct" in markdown
    assert "full_corpus_chat" in markdown
    assert "Active run" in markdown


def test_gradio_session_status_markdown_with_session_uses_relative_paths() -> None:
    run_dir = Path(
        "/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/"
        "runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_chat/20260423_170000"
    )
    session = LiveChatSession(
        run_dir=run_dir,
        config_snapshot_path=run_dir / "config_snapshot.yaml",
        environment={},
        session_paths=chat_session_paths(run_dir),
        start_time="2026-04-23T17:00:00-04:00",
        system_prompt="Stay evidence-first.",
        history=[],
        transcript_entries=[],
        turn_count=2,
    )

    markdown = gradio_session_status_markdown(_demo_config(), session)

    assert "20260423_170000" in markdown
    assert (
        "runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_chat/20260423_170000"
        in markdown
    )
    assert "Turns logged" in markdown


def test_gradio_chatbot_messages_skip_system_and_command_entries() -> None:
    run_dir = Path("/tmp/demo-gradio-chat")
    session = LiveChatSession(
        run_dir=run_dir,
        config_snapshot_path=run_dir / "config_snapshot.yaml",
        environment={},
        session_paths=chat_session_paths(run_dir),
        start_time="2026-04-23T17:00:00-04:00",
        system_prompt="Stay evidence-first.",
        history=[],
        transcript_entries=[
            {"role": "system", "content": "Stay evidence-first."},
            {"role": "user", "content": "What is prudence?"},
            {"role": "assistant", "content": "Prudence perfects practical reason."},
            {"role": "command", "content": "/reset"},
        ],
        turn_count=1,
    )

    messages = gradio_chatbot_messages(session)

    assert messages == [
        {"role": "user", "content": "What is prudence?"},
        {"role": "assistant", "content": "Prudence perfects practical reason."},
    ]


def test_gradio_header_html_surfaces_links_and_small_model_note() -> None:
    html = gradio_header_html()

    assert "Christian Virtue Chat" in html
    assert "Qwen/Qwen2.5-1.5B-Instruct" in html
    assert DEFAULT_GRADIO_CHAT_GITHUB_URL in html
    assert DEFAULT_GRADIO_CHAT_HF_URL in html
    assert DEFAULT_GRADIO_CHAT_SPACE_URL in html
    assert DEFAULT_GRADIO_CHAT_VIEWER_URL in html
