from __future__ import annotations

import json
from pathlib import Path


def test_justice_core_reviewed_edges_are_backed_by_reviewed_annotations(
    justice_core_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in (
            json.loads(line)
            for path in (
                Path("data/gold/pilot_reviewed_doctrinal_annotations.jsonl"),
                Path("data/gold/justice_core_reviewed_doctrinal_annotations.jsonl"),
            )
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if row["source_passage_id"].startswith("st.ii-ii.q")
        and 57 <= int(row["source_passage_id"].split(".q")[1][:3]) <= 79
    }
    edges = [
        json.loads(line)
        for line in Path("data/processed/justice_core_reviewed_doctrinal_edges.jsonl")
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


def test_justice_core_domain_process_edges_are_internally_consistent(
    justice_core_artifacts,
) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/justice_core_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    harmed = [edge for edge in edges if edge["relation_type"] == "harms_domain"]
    process = [edge for edge in edges if edge["relation_type"] == "corrupts_process"]
    roles = [edge for edge in edges if edge["relation_type"] == "abuses_role"]
    restitution = [edge for edge in edges if edge["relation_type"] == "requires_restitution"]

    assert harmed and process and roles and restitution
    assert all(edge["object_type"] == "domain" for edge in harmed)
    assert all(edge["object_type"] == "process" for edge in process)
    assert all(edge["object_type"] == "role" for edge in roles)
    assert all(edge["object_id"] == "concept.restitution" for edge in restitution)


def test_candidate_data_stays_out_of_reviewed_justice_exports(justice_core_artifacts) -> None:
    edges = [
        json.loads(line)
        for line in Path("data/processed/justice_core_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    annotations = [
        json.loads(line)
        for line in Path("data/gold/justice_core_reviewed_doctrinal_annotations.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]

    assert all(not edge["edge_id"].startswith("candidate.") for edge in edges)
    assert all(not row["annotation_id"].startswith("candidate.") for row in annotations)
