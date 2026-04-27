from __future__ import annotations

import json
from pathlib import Path


def test_pilot_graph_exports_distinguish_structural_and_doctrinal_edges(pilot_artifacts) -> None:
    doctrinal = [
        json.loads(line)
        for line in Path("data/processed/pilot_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    structural = [
        json.loads(line)
        for line in Path("data/processed/pilot_structural_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert doctrinal
    assert structural
    assert all(edge["edge_layer"] == "doctrinal" for edge in doctrinal)
    assert all(edge["edge_layer"] == "structural" for edge in structural)
    assert any(edge["relation_type"] == "contains_article" for edge in structural)
    assert any(edge["relation_type"] == "treated_in" for edge in structural)
    assert all(edge["support_annotation_ids"] for edge in doctrinal)
