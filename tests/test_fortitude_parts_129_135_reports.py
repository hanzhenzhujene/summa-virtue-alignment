from __future__ import annotations

import json
from pathlib import Path


def test_fortitude_parts_reports_are_consistent(
    fortitude_parts_129_135_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/fortitude_parts_129_135_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    validation = json.loads(
        Path("data/processed/fortitude_parts_129_135_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 346,
        "candidate_relation_count": 114,
        "deficiency_opposition_relation_count": 2,
        "excess_opposition_relation_count": 4,
        "expenditure_related_relation_count": 13,
        "honor_related_relation_count": 20,
        "passage_count": 106,
        "question_count": 7,
        "registered_concepts_used": 20,
        "reviewed_annotation_count": 150,
        "reviewed_doctrinal_edge_count": 33,
        "reviewed_structural_editorial_count": 97,
    }
    assert coverage["under_annotated_questions"] == [129, 130]
    assert coverage["normalization_risk_questions"] == [129, 130, 131, 132, 133, 134, 135]
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_support_types_and_clusters_in_fortitude_parts_annotations_are_valid(
    fortitude_parts_129_135_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path(
            "data/gold/fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl"
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
    } == {"129", "130", "131", "132", "133", "134", "135"}
