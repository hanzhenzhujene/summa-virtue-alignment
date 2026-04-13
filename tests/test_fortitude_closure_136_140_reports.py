from __future__ import annotations

import json
from pathlib import Path


def test_fortitude_closure_reports_are_consistent(
    fortitude_closure_136_140_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/fortitude_closure_136_140_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    validation = json.loads(
        Path("data/processed/fortitude_closure_136_140_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 532,
        "candidate_relation_count": 178,
        "fortitude_synthesis_edge_count": 64,
        "fortitude_synthesis_node_count": 89,
        "gift_linkage_relation_count": 6,
        "opposed_vice_relation_count": 4,
        "passage_count": 117,
        "patience_relation_count": 10,
        "perseverance_relation_count": 10,
        "precept_linkage_relation_count": 9,
        "question_count": 5,
        "registered_concepts_used": 23,
        "reviewed_annotation_count": 86,
        "reviewed_doctrinal_edge_count": 31,
        "reviewed_structural_editorial_count": 53,
    }
    assert coverage["under_annotated_questions"] == [137]
    assert coverage["normalization_risk_questions"] == [136, 137, 138, 139, 140]
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_fortitude_closure_question_rows_and_synthesis_notes_are_stable(
    fortitude_closure_136_140_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/fortitude_closure_136_140_coverage.json").read_text(
            encoding="utf-8"
        )
    )

    by_question = {row["question_number"]: row for row in coverage["questions"]}
    assert by_question[136]["parse_status"] == "partial"
    assert by_question[137]["parse_status"] == "ok"
    assert by_question[138]["parse_status"] == "partial"
    assert by_question[139]["parse_status"] == "ok"
    assert by_question[140]["parse_status"] == "partial"
    assert (
        coverage["fortitude_tract_summary"]["reviewed_doctrinal_edges_total"] == 64
    )
    assert (
        coverage["fortitude_tract_summary"]["reviewed_annotations_total"] == 236
    )
    assert any(
        "qq.123-128" in note
        for note in coverage["fortitude_tract_summary"]["notes"]
    )


def test_support_types_in_fortitude_closure_annotations_are_valid(
    fortitude_closure_136_140_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path(
            "data/gold/fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert annotations
    assert {row["support_type"] for row in annotations} == {
        "explicit_textual",
        "strong_textual_inference",
    }
    assert {
        row["source_passage_id"].split(".q")[1][:3]
        for row in annotations
    } == {"136", "137", "138", "139", "140"}
