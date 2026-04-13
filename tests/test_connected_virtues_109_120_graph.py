from __future__ import annotations

import json
from pathlib import Path


def test_connected_virtues_reviewed_edges_are_backed_by_reviewed_annotations(
    connected_virtues_109_120_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in (
            json.loads(line)
            for path in (
                Path("data/gold/connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl"),
            )
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    edges = [
        json.loads(line)
        for line in Path(
            "data/processed/connected_virtues_109_120_reviewed_doctrinal_edges.jsonl"
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
        assert edge["connected_virtues_cluster"] in {
            "self_presentation",
            "social_interaction",
            "external_goods",
            "legal_equity",
        }


def test_connected_virtues_edge_aggregation_and_cluster_relations_are_consistent(
    connected_virtues_109_120_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path(
            "data/processed/connected_virtues_109_120_reviewed_doctrinal_edges.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    truth_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == (
            "edge.concept.truth_self_presentation."
            "concerns_self_presentation.concept.self_presentation"
        )
    )
    assert truth_edge["connected_virtues_cluster"] == "self_presentation"
    assert truth_edge["object_type"] == "domain"

    affability_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == (
            "edge.concept.friendliness_affability."
            "concerns_social_interaction.concept.social_interaction"
        )
    )
    assert affability_edge["connected_virtues_cluster"] == "social_interaction"
    assert affability_edge["object_type"] == "domain"

    liberality_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.liberality.concerns_external_goods.concept.external_goods"
    )
    assert liberality_edge["connected_virtues_cluster"] == "external_goods"
    assert liberality_edge["object_type"] == "domain"

    epikeia_edge = next(
        row
        for row in edges
        if row["edge_id"]
        == "edge.concept.epikeia.corrects_legal_letter.concept.legal_letter"
    )
    assert epikeia_edge["connected_virtues_cluster"] == "legal_equity"
    assert epikeia_edge["relation_type"] == "corrects_legal_letter"
    assert epikeia_edge["object_type"] == "law"


def test_candidate_data_stays_out_of_reviewed_connected_virtues_exports(
    connected_virtues_109_120_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path(
            "data/processed/connected_virtues_109_120_reviewed_doctrinal_edges.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    annotations = [
        json.loads(line)
        for line in Path(
            "data/gold/connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl"
        )
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert all(not edge["edge_id"].startswith("candidate.") for edge in edges)
    assert all(not row["annotation_id"].startswith("candidate.") for row in annotations)
