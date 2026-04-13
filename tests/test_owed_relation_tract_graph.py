from __future__ import annotations

import json
from pathlib import Path


def test_owed_relation_tract_reviewed_edges_are_backed_by_reviewed_annotations(
    owed_relation_tract_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in (
            json.loads(line)
            for path in (
                Path("data/gold/owed_relation_tract_reviewed_doctrinal_annotations.jsonl"),
            )
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    edges = [
        json.loads(line)
        for line in Path("data/processed/owed_relation_tract_reviewed_doctrinal_edges.jsonl")
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
        assert edge["due_mode"] in {
            "origin",
            "excellence",
            "authority",
            "benefaction",
            "rectificatory",
        }


def test_owed_relation_edge_aggregation_and_role_edges_are_consistent(
    owed_relation_tract_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/owed_relation_tract_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    obedience_edge = next(
        row
        for row in edges
        if row["edge_id"] == "edge.concept.obedience.responds_to_command.concept.command"
    )
    assert len(obedience_edge["support_annotation_ids"]) >= 2
    assert obedience_edge["due_mode"] == "authority"

    parent_edge = next(
        row
        for row in edges
        if row["edge_id"] == "edge.concept.piety.owed_to_role.concept.parent_role"
    )
    assert parent_edge["object_type"] == "role"
    assert parent_edge["due_mode"] == "origin"

    rectification_edge = next(
        row
        for row in edges
        if row["edge_id"] == "edge.concept.vengeance.rectifies_wrong.concept.prior_wrong"
    )
    assert rectification_edge["due_mode"] == "rectificatory"

    role_edges = [edge for edge in edges if edge["relation_type"] == "owed_to_role"]
    assert role_edges
    assert all(edge["object_type"] == "role" for edge in role_edges)


def test_candidate_data_stays_out_of_reviewed_owed_relation_exports(
    owed_relation_tract_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/owed_relation_tract_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    annotations = [
        json.loads(line)
        for line in Path("data/gold/owed_relation_tract_reviewed_doctrinal_annotations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert all(not edge["edge_id"].startswith("candidate.") for edge in edges)
    assert all(not row["annotation_id"].startswith("candidate.") for row in annotations)
