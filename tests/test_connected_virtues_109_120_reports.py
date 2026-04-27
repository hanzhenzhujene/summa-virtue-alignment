from __future__ import annotations

import json
from pathlib import Path


def test_connected_virtues_109_120_reports_are_consistent(
    connected_virtues_109_120_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/connected_virtues_109_120_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    validation = json.loads(
        Path("data/processed/connected_virtues_109_120_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 466,
        "candidate_relation_count": 174,
        "external_goods_relation_count": 11,
        "legal_equity_relation_count": 4,
        "passage_count": 165,
        "question_count": 12,
        "registered_concepts_used": 23,
        "reviewed_annotation_count": 182,
        "reviewed_doctrinal_edge_count": 44,
        "reviewed_structural_editorial_count": 138,
        "self_presentation_relation_count": 21,
        "social_interaction_relation_count": 8,
    }
    assert coverage["under_annotated_questions"] == [109, 110, 117, 118]
    assert coverage["normalization_risk_questions"] == [
        109,
        110,
        111,
        114,
        115,
        116,
        117,
        118,
        119,
        120,
    ]
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_support_types_and_clusters_in_connected_virtues_annotations_are_valid(
    connected_virtues_109_120_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path(
            "data/gold/connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl"
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
    assert {row["connected_virtues_cluster"] for row in annotations} == {
        "self_presentation",
        "social_interaction",
        "external_goods",
        "legal_equity",
    }
