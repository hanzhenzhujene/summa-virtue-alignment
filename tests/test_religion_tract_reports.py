from __future__ import annotations

import json
from pathlib import Path


def test_religion_tract_reports_are_consistent(religion_tract_artifacts) -> None:
    coverage = json.loads(
        Path("data/processed/religion_tract_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        Path("data/processed/religion_tract_validation_report.json").read_text(encoding="utf-8")
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 2077,
        "candidate_relation_count": 659,
        "deficiency_opposition_relation_count": 5,
        "excess_opposition_relation_count": 5,
        "passage_count": 939,
        "positive_act_relation_count": 25,
        "question_count": 21,
        "registered_concepts_used": 42,
        "reviewed_annotation_count": 231,
        "reviewed_doctrinal_edge_count": 63,
        "reviewed_structural_editorial_count": 157,
        "sacred_object_relation_count": 28,
    }
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_support_types_in_religion_tract_annotations_are_valid(
    religion_tract_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path("data/gold/religion_tract_reviewed_doctrinal_annotations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    allowed = {
        "explicit_textual",
        "strong_textual_inference",
        "structural_editorial",
    }
    assert annotations
    assert {row["support_type"] for row in annotations}.issubset(allowed)
