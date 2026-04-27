from __future__ import annotations

import json
from pathlib import Path


def test_temperance_closure_reports_are_consistent(
    temperance_closure_161_170_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/temperance_closure_161_170_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        Path("data/processed/temperance_closure_161_170_validation_report.json").read_text(
            encoding="utf-8"
        )
    )

    assert coverage["summary"]["question_count"] == 10
    assert coverage["summary"]["passage_count"] == 161
    assert coverage["summary"]["temperance_full_synthesis_node_count"] >= 1
    assert coverage["summary"]["temperance_full_synthesis_edge_count"] >= 1
    assert coverage["summary"]["humility_pride_relation_count"] >= 1
    assert coverage["summary"]["adams_first_sin_case_relation_count"] >= 1
    assert coverage["summary"]["studiousness_curiosity_relation_count"] >= 1
    assert coverage["summary"]["external_modesty_relation_count"] >= 1
    assert coverage["summary"]["precept_linkage_relation_count"] >= 1
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_temperance_closure_question_rows_keep_cluster_and_usage_details(
    temperance_closure_161_170_artifacts,
) -> None:
    coverage = json.loads(
        Path("data/processed/temperance_closure_161_170_coverage.json").read_text(encoding="utf-8")
    )
    by_question = {row["question_number"]: row for row in coverage["questions"]}

    assert by_question[161]["subcluster"] == "humility_pride"
    assert by_question[163]["subcluster"] == "adams_first_sin"
    assert by_question[166]["subcluster"] == "study_curiosity"
    assert by_question[168]["subcluster"] == "external_modesty"
    assert by_question[170]["subcluster"] == "precept"
    assert by_question[163]["schema_extension_usage"]["case_of"] >= 1
    assert by_question[166]["schema_extension_usage"]["concerns_ordered_inquiry"] >= 1
    assert by_question[168]["schema_extension_usage"]["concerns_external_behavior"] >= 1
    assert by_question[169]["schema_extension_usage"]["concerns_outward_attire"] >= 1
    assert by_question[170]["schema_extension_usage"]["precept_of"] >= 1


def test_support_types_in_temperance_closure_annotations_are_valid(
    temperance_closure_161_170_artifacts,
) -> None:
    annotations = [
        json.loads(line)
        for line in Path(
            "data/gold/temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert annotations
    assert {row["support_type"] for row in annotations}.issubset(
        {"explicit_textual", "strong_textual_inference"}
    )
    assert {int(row["source_passage_id"].split(".q")[1][:3]) for row in annotations} == set(
        range(161, 171)
    )
