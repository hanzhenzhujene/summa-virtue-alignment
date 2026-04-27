from __future__ import annotations

import json
from pathlib import Path


def test_theological_virtues_reports_are_consistent(theological_virtues_artifacts) -> None:
    coverage = json.loads(
        Path("data/processed/theological_virtues_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        Path("data/processed/theological_virtues_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 5832,
        "candidate_relation_count": 2161,
        "passage_count": 999,
        "question_count": 46,
        "registered_concepts_used": 58,
        "reviewed_annotation_count": 185,
        "reviewed_doctrinal_edge_count": 54,
        "reviewed_structural_editorial_count": 126,
    }
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_support_types_in_theological_annotations_are_valid(theological_virtues_artifacts) -> None:
    annotations = [
        json.loads(line)
        for line in Path("data/gold/theological_virtues_reviewed_doctrinal_annotations.jsonl")
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
