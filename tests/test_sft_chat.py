from __future__ import annotations

from pathlib import Path

from summa_moral_graph.sft import (
    InferenceConfig,
    chat_session_paths,
    create_live_chat_session,
    describe_chat_plan,
    persist_live_chat_session,
    record_chat_exchange,
    record_chat_reset,
    render_chat_transcript_markdown,
)


def test_chat_session_paths_are_stable() -> None:
    run_dir = Path("/tmp/demo-chat-run")
    paths = chat_session_paths(run_dir)

    assert paths.run_dir == run_dir
    assert paths.transcript_jsonl_path == run_dir / "chat_transcript.jsonl"
    assert paths.transcript_markdown_path == run_dir / "chat_transcript.md"


def test_describe_chat_plan_reports_adapter_and_output_root(tmp_path) -> None:
    config = InferenceConfig(
        run_name="demo-chat",
        model_name_or_path="Qwen/Qwen2.5-1.5B-Instruct",
        dataset_dir=Path("data/processed/sft/exports/christian_virtue_v1"),
        split_names=["test"],
        output_dir=tmp_path / "unused-output",
        adapter_path=Path("runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest"),
        runtime_backend="mps",
        torch_dtype="float16",
        load_in_4bit=False,
    )

    plan = describe_chat_plan(
        config,
        output_root=tmp_path / "chat-root",
        system_prompt="Stay evidence-first.",
        one_shot="What is prudence?",
    )

    assert plan["model_name_or_path"] == "Qwen/Qwen2.5-1.5B-Instruct"
    assert "/runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/" in plan["adapter_path"]
    assert plan["chat_output_root"].endswith("/chat-root")
    assert plan["system_prompt"] == "Stay evidence-first."
    assert plan["one_shot"] == "What is prudence?"


def test_render_chat_transcript_markdown_is_readable() -> None:
    transcript = render_chat_transcript_markdown(
        [
            {"role": "system", "content": "Stay evidence-first."},
            {"role": "user", "content": "What is prudence?"},
            {"role": "assistant", "content": "Prudence perfects practical reason."},
            {"role": "command", "content": "/reset"},
        ]
    )

    assert transcript.startswith("# Christian Virtue Chat Transcript")
    assert "## System" in transcript
    assert "## User" in transcript
    assert "## Assistant" in transcript
    assert "## Session Event" in transcript
    assert "`/reset`" in transcript


def test_create_live_chat_session_writes_initial_artifacts(tmp_path) -> None:
    config = InferenceConfig(
        run_name="demo-chat",
        model_name_or_path="Qwen/Qwen2.5-1.5B-Instruct",
        dataset_dir=Path("data/processed/sft/exports/christian_virtue_v1"),
        split_names=["test"],
        output_dir=tmp_path / "unused-output",
        adapter_path=Path("runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest"),
        runtime_backend="mps",
        torch_dtype="float16",
        load_in_4bit=False,
    )

    session = create_live_chat_session(
        config,
        output_root=tmp_path / "chat-root",
        system_prompt="Stay evidence-first.",
        command_argv=["streamlit", "run", "streamlit_app.py"],
    )

    assert session.run_dir.parent == tmp_path / "chat-root"
    assert session.config_snapshot_path.exists()
    assert session.session_paths.transcript_jsonl_path.exists()
    assert session.session_paths.transcript_markdown_path.exists()
    assert (session.run_dir / "environment.json").exists()
    assert (session.run_dir / "run_manifest.json").exists()
    assert (session.run_dir / "command.log").exists()
    transcript_text = session.session_paths.transcript_markdown_path.read_text(encoding="utf-8")
    assert "Stay evidence-first." in transcript_text


def test_record_chat_exchange_and_reset_persist_history(tmp_path) -> None:
    config = InferenceConfig(
        run_name="demo-chat",
        model_name_or_path="Qwen/Qwen2.5-1.5B-Instruct",
        dataset_dir=Path("data/processed/sft/exports/christian_virtue_v1"),
        split_names=["test"],
        output_dir=tmp_path / "unused-output",
        adapter_path=Path("runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest"),
        runtime_backend="mps",
        torch_dtype="float16",
        load_in_4bit=False,
    )

    session = create_live_chat_session(
        config,
        output_root=tmp_path / "chat-root",
        system_prompt="Stay evidence-first.",
    )
    manifest = record_chat_exchange(
        session,
        config,
        runtime=None,
        user_text="What is prudence?",
        assistant_text="Prudence perfects practical reason.",
    )

    assert manifest["turn_count"] == 1
    assert session.history == [
        {"role": "user", "content": "What is prudence?"},
        {"role": "assistant", "content": "Prudence perfects practical reason."},
    ]
    transcript_text = session.session_paths.transcript_markdown_path.read_text(encoding="utf-8")
    assert "What is prudence?" in transcript_text
    assert "Prudence perfects practical reason." in transcript_text

    reset_manifest = record_chat_reset(session, config, runtime=None)
    assert reset_manifest["turn_count"] == 1
    assert session.history == []
    reset_transcript = session.session_paths.transcript_markdown_path.read_text(encoding="utf-8")
    assert "`/reset`" in reset_transcript

    final_manifest = persist_live_chat_session(session, config, runtime=None)
    assert final_manifest["run_id"] == session.run_dir.name
