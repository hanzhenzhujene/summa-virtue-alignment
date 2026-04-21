from __future__ import annotations

import json
from pathlib import Path

from summa_moral_graph.sft.frontier import (
    analyze_citation_frontier,
    write_citation_frontier_artifacts,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _reference_row(
    *,
    example_id: str,
    tract: str,
    relation_type: str,
    question: str,
    passage_id: str,
    citation_label: str,
) -> dict[str, object]:
    return {
        "example_id": example_id,
        "task_type": "citation_grounded_moral_answer",
        "split": "test",
        "messages": [
            {"role": "system", "content": "You are a careful assistant."},
            {"role": "user", "content": question},
            {
                "role": "assistant",
                "content": (
                    "According to Aquinas, the answer is supported here.\n"
                    f"Citations:\n- {passage_id} ({citation_label})"
                ),
            },
        ],
        "metadata": {
            "tract": tract,
            "relation_type": relation_type,
            "source_passage_ids": [passage_id],
            "citation_labels": [citation_label],
        },
    }


def _prediction_row(
    example_id: str,
    text: str,
    *,
    tract: str,
    relation_type: str,
) -> dict[str, object]:
    return {
        "example_id": example_id,
        "task_type": "citation_grounded_moral_answer",
        "split": "test",
        "assistant_text": text,
        "metadata": {
            "tract": tract,
            "relation_type": relation_type,
        },
    }


def test_analyze_citation_frontier_summarizes_signal_categories(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    base_predictions_path = tmp_path / "runs" / "base.jsonl"
    adapter_predictions_path = tmp_path / "runs" / "adapter.jsonl"
    references = [
        _reference_row(
            example_id="ex-1",
            tract="theological_virtues",
            relation_type="has_act",
            question="According to Aquinas, what act belongs to Charity?",
            passage_id="st.ii-ii.q033.a001.resp",
            citation_label="II-II q.33 a.1 resp",
        ),
        _reference_row(
            example_id="ex-2",
            tract="prudence",
            relation_type="treated_in",
            question="Where does Aquinas treat Prudence in this corpus?",
            passage_id="st.ii-ii.q047.a001.resp",
            citation_label="II-II q.47 a.1 resp",
        ),
        _reference_row(
            example_id="ex-3",
            tract="justice_core",
            relation_type="requires_restitution",
            question="According to Aquinas, what does theft require?",
            passage_id="st.ii-ii.q062.a001.resp",
            citation_label="II-II q.62 a.1 resp",
        ),
    ]
    _write_jsonl(dataset_dir / "all.jsonl", references)
    _write_jsonl(
        base_predictions_path,
        [
            _prediction_row(
                "ex-1",
                "Charity belongs to fraternal correction.",
                tract="theological_virtues",
                relation_type="has_act",
            ),
            _prediction_row(
                "ex-2",
                "Prudence is discussed by Aquinas in the virtues.",
                tract="prudence",
                relation_type="treated_in",
            ),
            _prediction_row(
                "ex-3",
                "Theft requires restitution. Citations: - st.ii-ii.q061.a001.resp",
                tract="justice_core",
                relation_type="requires_restitution",
            ),
        ],
    )
    _write_jsonl(
        adapter_predictions_path,
        [
            _prediction_row(
                "ex-1",
                "According to Aquinas, Charity has fraternal correction as an act.\n"
                "Citations:\n- st.ii-ii.q033.a001.resp (II-II q.33 a.1 resp)",
                tract="theological_virtues",
                relation_type="has_act",
            ),
            _prediction_row(
                "ex-2",
                "Aquinas treats Prudence here: II-II q.47 a.1 resp.",
                tract="prudence",
                relation_type="treated_in",
            ),
            _prediction_row(
                "ex-3",
                "According to Aquinas, theft requires restitution.\n"
                "Citations:\n- st.ii-ii.q061.a001.resp",
                tract="justice_core",
                relation_type="requires_restitution",
            ),
        ],
    )

    analysis = analyze_citation_frontier(
        dataset_dir=dataset_dir,
        base_predictions_path=base_predictions_path,
        adapter_predictions_path=adapter_predictions_path,
    )

    adapter_overall = analysis["overall"]["adapter"]
    assert adapter_overall["count"] == 3
    assert abs(adapter_overall["exact_stable_id_match_rate"] - (1 / 3)) < 1e-9
    assert abs(adapter_overall["label_only_citation_rate"] - (1 / 3)) < 1e-9
    assert abs(adapter_overall["wrong_stable_id_rate"] - (1 / 3)) < 1e-9
    assert adapter_overall["no_citation_signal_rate"] == 0.0

    base_overall = analysis["overall"]["base"]
    assert abs(base_overall["wrong_stable_id_rate"] - (1 / 3)) < 1e-9
    assert abs(base_overall["no_citation_signal_rate"] - (2 / 3)) < 1e-9

    report_path = tmp_path / "docs" / "reports" / "frontier.md"
    metrics_path = tmp_path / "docs" / "reports" / "frontier.json"
    figure_path = tmp_path / "docs" / "reports" / "assets" / "frontier.svg"

    write_citation_frontier_artifacts(
        analysis=analysis,
        report_path=report_path,
        metrics_path=metrics_path,
        figure_path=figure_path,
    )

    report_text = report_path.read_text(encoding="utf-8")
    figure_text = figure_path.read_text(encoding="utf-8")
    assert "Christian Virtue Citation Frontier Audit" in report_text
    assert "Final Next-Step Thesis" in report_text
    assert "Recommended Citation-Frontier Recipe" in report_text
    assert "make train-christian-virtue-qwen2-5-1-5b-citation-frontier" in report_text
    assert "Key takeaway:" in report_text
    assert "assets/frontier.svg" in report_text
    assert metrics_path.exists()
    assert figure_path.exists()
    assert "Adapter citation signal rises" in figure_text
    assert "Share of held-out `citation_grounded_moral_answer` prompts" in figure_text
    assert "exact stable id" in figure_text
