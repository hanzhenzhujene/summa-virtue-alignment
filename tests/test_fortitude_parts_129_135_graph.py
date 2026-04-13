from __future__ import annotations

import json
from pathlib import Path


def test_fortitude_parts_reviewed_edges_are_backed_by_reviewed_annotations(
    fortitude_parts_129_135_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in (
            json.loads(line)
            for path in (
                Path("data/gold/fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl"),
            )
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    edges = [
        json.loads(line)
        for line in Path(
            "data/processed/fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert edges
    for edge in edges:
        assert edge["review_layer"] == "reviewed_doctrinal"
        assert edge["support_annotation_ids"]
        assert set(edge["support_annotation_ids"]).issubset(annotations)
        assert "structural_editorial" not in edge["support_types"]
        assert edge["fortitude_parts_cluster"] in {"honor_worthiness", "expenditure_work"}


def test_fortitude_parts_distinctions_and_opposition_modes_are_preserved(
    fortitude_parts_129_135_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path(
            "data/processed/fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    magnanimity_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.magnanimity.concerns_honor.concept.honor_recognition"
    )
    assert magnanimity_edge["fortitude_parts_cluster"] == "honor_worthiness"
    assert len(magnanimity_edge["support_annotation_ids"]) == 4

    magnificence_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.magnificence.concerns_great_expenditure.concept.great_expenditure"
    )
    assert magnificence_edge["fortitude_parts_cluster"] == "expenditure_work"
    assert magnificence_edge["object_type"] == "domain"

    excess_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.presumption_magnanimity.excess_opposed_to.concept.magnanimity"
    )
    assert excess_edge["relation_type"] == "excess_opposed_to"

    deficiency_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.pusillanimity.deficiency_opposed_to.concept.magnanimity"
    )
    assert deficiency_edge["relation_type"] == "deficiency_opposed_to"

    contrary_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.waste_magnificence.contrary_to.concept.meanness_magnificence"
    )
    assert contrary_edge["fortitude_parts_cluster"] == "expenditure_work"


def test_candidate_data_stays_out_of_reviewed_fortitude_parts_exports(
    fortitude_parts_129_135_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path(
            "data/processed/fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    annotations = [
        json.loads(line)
        for line in Path(
            "data/gold/fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert all(not edge["edge_id"].startswith("candidate.") for edge in edges)
    assert all(not row["annotation_id"].startswith("candidate.") for row in annotations)
