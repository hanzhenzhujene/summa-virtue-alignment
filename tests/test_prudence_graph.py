from __future__ import annotations

import json
from pathlib import Path


def test_prudence_part_taxonomy_edges_are_typed(prudence_artifacts) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/prudence_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    taxonomy_edges = [edge for edge in edges if edge["relation_type"].endswith("_part_of")]
    assert taxonomy_edges
    assert all(
        edge["part_taxonomy"] in {"integral", "subjective", "potential"} for edge in taxonomy_edges
    )


def test_reviewed_edge_aggregation_uses_reviewed_annotations_only(prudence_artifacts) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/prudence_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert edges
    assert all(edge["review_layer"] == "reviewed_doctrinal" for edge in edges)
    assert all("structural_editorial" not in edge["support_types"] for edge in edges)
    assert all(
        not any(
            annotation_id.startswith("cand-") for annotation_id in edge["support_annotation_ids"]
        )
        for edge in edges
    )


def test_candidate_data_excluded_from_reviewed_exports(prudence_artifacts) -> None:
    candidate_mentions = Path("data/candidate/prudence_candidate_mentions.jsonl").read_text(
        encoding="utf-8"
    )
    reviewed_edges = Path("data/processed/prudence_reviewed_doctrinal_edges.jsonl").read_text(
        encoding="utf-8"
    )
    assert "candidate." in candidate_mentions
    assert "candidate." not in reviewed_edges
