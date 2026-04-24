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
from summa_moral_graph.sft.chat import (
    _deterministic_comparison_answer,
    _deterministic_definition_answer,
    _deterministic_guidance_answer,
    _deterministic_practical_answer,
    _deterministic_relation_answer,
    _deterministic_why_answer,
    _strip_template_boilerplate,
    generate_deterministic_chat_reply,
    retrieve_chat_evidence,
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


def test_strip_template_boilerplate_removes_benchmark_phrases() -> None:
    raw = (
        "According to the reviewed passage, Prudence resides in practical reason. "
        "The passage states this directly. Article 2 explicitly says that prudence resides only "
        "in the practical reason.\n\nCitations:\n- st.ii-ii.q047.a002.resp "
        "(II-II q.47 a.2 resp)"
    )

    cleaned = _strip_template_boilerplate(raw)

    assert "According to the reviewed passage" not in cleaned
    assert "The passage states this directly" not in cleaned
    assert "Article 2 explicitly says" not in cleaned
    assert "Prudence resides in practical reason." in cleaned
    assert "Citations:" in cleaned


def test_retrieve_chat_evidence_finds_prudence_sources() -> None:
    bundle = retrieve_chat_evidence("What is prudence according to Aquinas?")

    passage_ids = {entry.record.segment_id for entry in bundle.passages}
    annotation_passage_ids = {entry.source_passage_id for entry in bundle.annotations}

    assert bundle.passages
    assert any(
        passage_id.startswith("st.ii-ii.q047")
        for passage_id in passage_ids | annotation_passage_ids
    )


def test_deterministic_definition_answer_prefers_direct_thomistic_prose() -> None:
    bundle = retrieve_chat_evidence("What is prudence according to Aquinas?")

    answer = _deterministic_definition_answer("What is prudence according to Aquinas?", bundle)

    assert answer is not None
    assert "right reason applied to action" in answer.lower()
    assert "According to the reviewed passage" not in answer
    assert "st.ii-ii.q047.a008.resp" in answer


def test_deterministic_comparison_answer_explains_difference_naturally() -> None:
    bundle = retrieve_chat_evidence("How does justice differ from mercy?")

    answer = _deterministic_comparison_answer("How does justice differ from mercy?", bundle)

    assert answer is not None
    assert "whereas mercy responds to another's distress" in answer.lower()
    assert "does not violate justice" in answer.lower()
    assert "st.ii-ii.q058.a001.resp" in answer
    assert "st.ii-ii.q030.a001.resp" in answer


def test_deterministic_why_answer_handles_prudence_question() -> None:
    bundle = retrieve_chat_evidence("Why is prudence necessary for the moral life?")

    answer = _deterministic_why_answer(
        "Why is prudence necessary for the moral life?",
        bundle,
    )

    assert answer is not None
    assert "prudence is necessary for the moral life" in answer.lower()
    assert "right reason applied to action" in answer.lower()
    assert "st.ii-ii.q047.a008.resp" in answer


def test_deterministic_guidance_answer_handles_justice_and_mercy() -> None:
    bundle = retrieve_chat_evidence(
        "How should a Christian think about mercy and justice together?"
    )

    answer = _deterministic_guidance_answer(
        "How should a Christian think about mercy and justice together?",
        bundle,
    )

    assert answer is not None
    assert "should not treat justice and mercy as rivals" in answer.lower()
    assert "justice is safeguarded" in answer.lower()
    assert "st.ii-ii.q030.a003.resp" in answer


def test_deterministic_guidance_answer_handles_temperance_practice() -> None:
    bundle = retrieve_chat_evidence("How can I practice temperance according to Aquinas?")

    answer = _deterministic_guidance_answer(
        "How can I practice temperance according to Aquinas?",
        bundle,
    )

    assert answer is not None
    assert "let reason set the measure of pleasure" in answer.lower()
    assert "st.ii-ii.q141.a006.resp" in answer


def test_deterministic_relation_answer_handles_classification_question() -> None:
    bundle = retrieve_chat_evidence("How does Aquinas classify abstinence within temperance?")

    answer = _deterministic_relation_answer(
        "How does Aquinas classify abstinence within temperance?",
        bundle,
    )

    assert answer is not None
    assert "abstinence is a subjective part of temperance" in answer.lower()
    assert "st.ii-ii.q143.a001.resp" in answer


def test_deterministic_relation_answer_handles_opposition_question() -> None:
    bundle = retrieve_chat_evidence("What virtue opposes sloth?")

    answer = _deterministic_relation_answer("What virtue opposes sloth?", bundle)

    assert answer is not None
    assert "charity is opposed to sloth" in answer.lower()
    assert "st.ii-ii.q035.a003.resp" in answer


def test_deterministic_relation_answer_handles_annexed_relation() -> None:
    bundle = retrieve_chat_evidence("How is truth related to justice?")

    answer = _deterministic_relation_answer("How is truth related to justice?", bundle)

    assert answer is not None
    assert "truth is annexed to justice" in answer.lower()
    assert "st.ii-ii.q109.a003.resp" in answer


def test_deterministic_relation_answer_handles_justice_resides_in_question() -> None:
    bundle = retrieve_chat_evidence("Where does justice reside?")

    answer = _deterministic_relation_answer("Where does justice reside?", bundle)

    assert answer is not None
    assert "justice resides in will" in answer.lower()
    assert "st.ii-ii.q058.a004.resp" in answer


def test_deterministic_practical_answer_handles_anger() -> None:
    bundle = retrieve_chat_evidence(
        "I struggle with anger. How should I respond according to Aquinas?"
    )

    answer = _deterministic_practical_answer(
        "I struggle with anger. How should I respond according to Aquinas?",
        bundle,
    )

    assert answer is not None
    assert "bring it under right reason" in answer.lower()
    assert "meekness checks the first onrush of anger" in answer.lower()
    assert "st.ii-ii.q157.a001.resp" in answer


def test_deterministic_practical_answer_handles_envy() -> None:
    bundle = retrieve_chat_evidence("I am jealous of other people's success. What should I do?")

    answer = _deterministic_practical_answer(
        "I am jealous of other people's success. What should I do?",
        bundle,
    )

    assert answer is not None
    assert "that is envy" in answer.lower()
    assert "charity rejoices in a neighbor's good" in answer.lower()
    assert "st.ii-ii.q036.a001.resp" in answer


def test_deterministic_practical_answer_handles_fear_and_courage() -> None:
    bundle = retrieve_chat_evidence(
        "How should I think about fear and courage in a hard situation?"
    )

    answer = _deterministic_practical_answer(
        "How should I think about fear and courage in a hard situation?",
        bundle,
    )

    assert answer is not None
    assert "courage means feeling no fear" in answer.lower()
    assert "abandoning reason because of difficulty or danger" in answer.lower()
    assert "st.ii-ii.q123.a001.resp" in answer


def test_generate_deterministic_chat_reply_handles_practical_prompt() -> None:
    answer = generate_deterministic_chat_reply(
        "I struggle with anger. How should I respond according to Aquinas?"
    )

    assert answer is not None
    assert "bring it under right reason" in answer.lower()
    assert "st.ii-ii.q158.a001.resp" in answer
