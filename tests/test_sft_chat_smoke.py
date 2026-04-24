from __future__ import annotations

from pathlib import Path

from summa_moral_graph.sft import (
    DEFAULT_CHAT_EXAMPLE_PROMPTS,
    ChatSmokeCase,
    evaluate_chat_smoke_case,
    load_inference_config,
    run_chat_smoke_suite,
)
from summa_moral_graph.sft.chat_smoke import DEFAULT_CHAT_SMOKE_CASES


def test_chat_smoke_examples_cover_richer_prompt_families() -> None:
    prompts = set(DEFAULT_CHAT_EXAMPLE_PROMPTS)

    assert "What is prudence according to Aquinas?" in prompts
    assert "How does justice differ from mercy?" in prompts
    assert "Where does justice reside?" in prompts
    assert "I struggle with anger. How should I respond according to Aquinas?" in prompts


def test_evaluate_chat_smoke_case_detects_missing_bits() -> None:
    case = ChatSmokeCase(
        case_id="demo",
        category="definition",
        prompt="What is prudence according to Aquinas?",
        required_substrings=("right reason",),
        required_citations=("st.ii-ii.q047.a008.resp",),
    )

    result = evaluate_chat_smoke_case(
        case,
        "According to the reviewed passage, prudence is reason.",
        used_model=False,
    )

    assert not result.passed
    assert "right reason" in result.missing_required_substrings
    assert "st.ii-ii.q047.a008.resp" in result.missing_required_citations
    assert "according to the reviewed passage" in result.forbidden_hits


def test_run_chat_smoke_suite_writes_latest_run(tmp_path: Path) -> None:
    config = load_inference_config(
        "configs/inference/qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml"
    )

    result = run_chat_smoke_suite(
        config=config,
        output_root=tmp_path / "chat-smoke",
        include_model=False,
        cases=DEFAULT_CHAT_SMOKE_CASES[:3],
    )

    latest_path = Path(result["latest_path"])
    report_path = Path(result["report_path"])
    metrics_path = Path(result["run_dir"]) / "metrics.json"

    assert latest_path.is_symlink()
    assert report_path.exists()
    assert metrics_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "Christian Virtue Chat Smoke Report" in report_text
    assert "deterministic-only" in report_text
    assert "prudence_definition" in report_text
