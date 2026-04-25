from __future__ import annotations

import json
from pathlib import Path

from scripts.run_aquinas_virtue_grounding_probe import (
    build_metrics,
    build_probe_inputs,
    label_present,
    relation_signal_present,
    score_prediction,
)


def test_build_probe_inputs_uses_user_prompt_without_target_answer(tmp_path: Path) -> None:
    dataset_path = tmp_path / "test.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "example_id": "example.1",
                "messages": [
                    {"role": "system", "content": "system"},
                    {"role": "user", "content": "How does Aquinas classify Chastity?"},
                    {"role": "assistant", "content": "target answer"},
                ],
                "metadata": {
                    "object_label": "Temperance",
                    "relation_type": "subjective_part_of",
                    "source_passage_ids": ["st.ii-ii.q143.a001.resp"],
                    "subject_label": "Chastity",
                    "support_types": ["explicit_textual"],
                    "task_type": "citation_grounded_moral_answer",
                    "tract": "temperance_141_160",
                },
                "split": "test",
                "task_type": "citation_grounded_moral_answer",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    rows = build_probe_inputs(dataset_path)

    assert len(rows) == 1
    assert rows[0]["messages"][1]["content"] == "How does Aquinas classify Chastity?"
    assert "target answer" not in json.dumps(rows[0]["messages"])
    assert rows[0]["expected_source_passage_ids"] == ["st.ii-ii.q143.a001.resp"]


def test_score_prediction_rewards_exact_segment_grounding() -> None:
    row = {
        "assistant_text": (
            "Chastity is a subjective part of Temperance in Aquinas's account of virtue.\n\n"
            "Citations:\n- st.ii-ii.q143.a001.resp"
        ),
        "example_id": "example.1",
        "expected_object_label": "Temperance",
        "expected_relation_type": "subjective_part_of",
        "expected_source_passage_ids": ["st.ii-ii.q143.a001.resp"],
        "expected_subject_label": "Chastity",
        "metadata": {"support_types": ["explicit_textual"]},
        "split": "test",
        "task_type": "citation_grounded_moral_answer",
        "tract": "temperance_141_160",
    }

    scored = score_prediction(row)

    assert scored["citation_exact"] is True
    assert scored["citation_partial"] is True
    assert scored["subject_label_present"] is True
    assert scored["object_label_present"] is True
    assert scored["relation_signal_present"] is True
    assert scored["aquinas_category_signal"] is True
    assert scored["generic_drift"] is False
    assert scored["grounding_score"] == 1.0


def test_score_prediction_penalizes_generic_drift_and_wrong_citation() -> None:
    row = {
        "assistant_text": (
            "Chastity is about self-care and personal growth.\n\n"
            "Citations:\n- st.ii-ii.q144.a001.resp"
        ),
        "example_id": "example.1",
        "expected_object_label": "Temperance",
        "expected_relation_type": "subjective_part_of",
        "expected_source_passage_ids": ["st.ii-ii.q143.a001.resp"],
        "expected_subject_label": "Chastity",
        "metadata": {"support_types": ["explicit_textual"]},
        "split": "test",
        "task_type": "citation_grounded_moral_answer",
        "tract": "temperance_141_160",
    }

    scored = score_prediction(row)

    assert scored["citation_exact"] is False
    assert scored["citation_partial"] is False
    assert scored["generic_drift"] is True
    assert scored["grounding_score"] < 0.5


def test_label_and_relation_helpers_accept_common_surface_forms() -> None:
    assert label_present("Adam's First Sin", "Aquinas treats Adams first sin as pride.")
    assert label_present("Commutative Justice", "Restitution belongs to commutative justice.")
    assert relation_signal_present("has_act", "Charity has fraternal correction as an act.")
    assert relation_signal_present("resides_in", "Justice resides in the will.")


def test_build_metrics_summarizes_grouped_rows() -> None:
    rows = [
        score_prediction(
            {
                "assistant_text": "Faith has Act of Faith as an act. st.ii-ii.q002.a002.resp",
                "example_id": "faith.1",
                "expected_object_label": "Act of Faith",
                "expected_relation_type": "has_act",
                "expected_source_passage_ids": ["st.ii-ii.q002.a002.resp"],
                "expected_subject_label": "Faith",
                "metadata": {"support_types": ["explicit_textual"]},
                "split": "test",
                "task_type": "reviewed_relation_explanation",
                "tract": "theological_virtues",
            }
        )
    ]

    metrics = build_metrics(rows)

    assert metrics["overall"]["count"] == 1
    assert metrics["overall"]["citation_exact_match"] == 1.0
    assert metrics["by_support_type"]["explicit_textual"]["grounding_score"] == 1.0
