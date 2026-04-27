from __future__ import annotations

import json
from pathlib import Path


def test_religion_tract_reviewed_edges_are_backed_by_reviewed_annotations(
    religion_tract_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in (
            json.loads(line)
            for path in (
                Path("data/gold/pilot_reviewed_doctrinal_annotations.jsonl"),
                Path("data/gold/religion_tract_reviewed_doctrinal_annotations.jsonl"),
            )
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row["source_passage_id"].startswith("st.ii-ii.q")
        and 80 <= int(row["source_passage_id"].split(".q")[1][:3]) <= 100
    }
    edges = [
        json.loads(line)
        for line in Path("data/processed/religion_tract_reviewed_doctrinal_edges.jsonl")
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


def test_religion_tract_edge_aggregation_and_sacred_object_relations_are_consistent(
    religion_tract_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/religion_tract_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    religion_edge = next(
        row
        for row in edges
        if row["edge_id"] == "edge.concept.religion.directed_to.concept.divine_worship"
    )
    assert len(religion_edge["support_annotation_ids"]) >= 3
    assert len(religion_edge["source_passage_ids"]) >= 3

    sacred_edges = [
        edge
        for edge in edges
        if edge["relation_type"]
        in {
            "concerns_sacred_object",
            "misuses_sacred_object",
            "corrupts_spiritual_exchange",
        }
    ]
    assert sacred_edges
    assert all(edge["object_type"] in {"object", "domain"} for edge in sacred_edges)

    act_edges = [edge for edge in edges if edge["relation_type"] == "has_act"]
    assert act_edges
    assert all(edge["subject_type"] == "virtue" for edge in act_edges)
    assert all(edge["object_type"] == "act_type" for edge in act_edges)


def test_candidate_data_stays_out_of_reviewed_religion_exports(
    religion_tract_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/religion_tract_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    annotations = [
        json.loads(line)
        for line in Path("data/gold/religion_tract_reviewed_doctrinal_annotations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert all(not edge["edge_id"].startswith("candidate.") for edge in edges)
    assert all(not row["annotation_id"].startswith("candidate.") for row in annotations)
