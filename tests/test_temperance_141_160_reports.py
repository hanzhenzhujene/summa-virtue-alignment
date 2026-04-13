from __future__ import annotations

import json
from pathlib import Path


def test_temperance_reports_are_consistent(
    temperance_141_160_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/temperance_141_160_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        Path("data/processed/temperance_141_160_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"] == {
        "candidate_mention_count": 2085,
        "candidate_relation_count": 674,
        "clemency_cruelty_relation_count": 5,
        "continence_incontinence_relation_count": 6,
        "drink_related_relation_count": 8,
        "food_related_relation_count": 10,
        "integral_part_relation_count": 2,
        "meekness_anger_relation_count": 8,
        "modesty_general_relation_count": 3,
        "passage_count": 815,
        "potential_part_relation_count": 7,
        "question_count": 20,
        "registered_concepts_used": 48,
        "reviewed_annotation_count": 234,
        "reviewed_doctrinal_edge_count": 67,
        "reviewed_structural_editorial_count": 166,
        "sex_related_relation_count": 17,
        "subjective_part_relation_count": 7,
        "temperance_phase1_synthesis_edge_count": 67,
        "temperance_phase1_synthesis_node_count": 163,
    }
    assert coverage["under_annotated_questions"] == [144, 145, 147, 152, 155, 158]
    assert coverage["questions_with_part_taxonomy_risk"] == []
    assert coverage["questions_with_matter_domain_risk"] == []
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_temperance_question_rows_keep_cluster_and_usage_details(
    temperance_141_160_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/temperance_141_160_coverage.json").read_text(encoding="utf-8")
    )
    by_question = {row["question_number"]: row for row in coverage["questions"]}

    assert by_question[141]["parse_status"] == "ok"
    assert by_question[143]["parse_status"] == "partial"
    assert by_question[148]["parse_status"] == "partial"
    assert by_question[149]["parse_status"] == "partial"
    assert by_question[143]["part_taxonomy_usage"] == {
        "integral": 2,
        "potential": 3,
        "subjective": 4,
    }
    assert by_question[157]["part_taxonomy_usage"] == {"potential": 2}
    assert by_question[160]["matter_domain_usage"] == {"modesty_general": 2}


def test_support_types_in_temperance_annotations_are_valid(
    temperance_141_160_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path("data/gold/temperance_141_160_reviewed_doctrinal_annotations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert annotations
    assert {row["support_type"] for row in annotations} == {"explicit_textual"}
    assert {
        int(row["source_passage_id"].split(".q")[1][:3]) for row in annotations
    } == set(range(141, 161))
