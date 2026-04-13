from __future__ import annotations

import json
from pathlib import Path


def test_justice_core_reports_are_consistent(justice_core_artifacts) -> None:
    coverage = json.loads(
        Path("data/processed/justice_core_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        Path("data/processed/justice_core_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 1813,
        "candidate_relation_count": 656,
        "harmed_domain_relation_count": 21,
        "judicial_process_relation_count": 31,
        "justice_species_relation_count": 11,
        "passage_count": 927,
        "question_count": 23,
        "registered_concepts_used": 66,
        "restitution_related_relation_count": 7,
        "reviewed_annotation_count": 299,
        "reviewed_doctrinal_edge_count": 98,
        "reviewed_structural_editorial_count": 186,
    }
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_support_types_in_justice_annotations_are_valid(justice_core_artifacts) -> None:
    annotations = [
        json.loads(line)
        for line in Path("data/gold/justice_core_reviewed_doctrinal_annotations.jsonl")
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
