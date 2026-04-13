from __future__ import annotations

import json
from pathlib import Path


def test_theological_virtues_reviewed_edges_stay_doctrinal_only(
    theological_virtues_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/theological_virtues_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert edges
    assert all(edge["review_layer"] == "reviewed_doctrinal" for edge in edges)
    assert all("structural_editorial" not in edge["support_types"] for edge in edges)


def test_theological_virtues_edge_aggregation_keeps_multiple_supports(
    theological_virtues_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/theological_virtues_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    edge = next(
        row
        for row in edges
        if row["edge_id"] == "edge.concept.charity.regulated_by.concept.precepts_of_charity"
    )
    assert len(edge["support_annotation_ids"]) == 2
    assert len(edge["source_passage_ids"]) == 2


def test_candidate_data_excluded_from_theological_reviewed_exports(
    theological_virtues_artifacts,
) -> None:
    reviewed_edges = Path(
        "data/processed/theological_virtues_reviewed_doctrinal_edges.jsonl"
    ).read_text(encoding="utf-8")
    assert "candidate." not in reviewed_edges
