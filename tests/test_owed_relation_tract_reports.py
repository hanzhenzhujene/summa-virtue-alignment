from __future__ import annotations

import json
from pathlib import Path


def test_owed_relation_tract_reports_are_consistent(owed_relation_tract_artifacts) -> None:
    coverage = json.loads(
        Path("data/processed/owed_relation_tract_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        Path("data/processed/owed_relation_tract_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "authority_related_due_relation_count": 8,
        "benefaction_related_due_relation_count": 9,
        "candidate_mention_count": 732,
        "candidate_relation_count": 226,
        "excellence_related_due_relation_count": 10,
        "origin_related_due_relation_count": 6,
        "passage_count": 282,
        "question_count": 8,
        "rectificatory_relation_count": 5,
        "registered_concepts_used": 27,
        "reviewed_annotation_count": 169,
        "reviewed_doctrinal_edge_count": 38,
        "reviewed_structural_editorial_count": 110,
    }
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_support_types_and_due_modes_in_owed_relation_annotations_are_valid(
    owed_relation_tract_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path("data/gold/owed_relation_tract_reviewed_doctrinal_annotations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    allowed_support = {
        "explicit_textual",
        "strong_textual_inference",
        "structural_editorial",
    }
    allowed_due_modes = {
        "origin",
        "excellence",
        "authority",
        "benefaction",
        "rectificatory",
    }
    assert annotations
    assert {row["support_type"] for row in annotations}.issubset(allowed_support)
    assert {row["due_mode"] for row in annotations} == allowed_due_modes
