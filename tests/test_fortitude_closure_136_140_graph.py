from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import cast


def load_jsonl(path: str) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalize_labels(values: list[str]) -> set[str]:
    return {
        " ".join(value.casefold().replace("-", " ").replace("(", " ").replace(")", " ").split())
        for value in values
    }


def concept_labels(payload: dict[str, object]) -> set[str]:
    aliases = payload.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    values = [str(payload["canonical_label"]), *(str(value) for value in aliases)]
    return normalize_labels(values)


def test_fortitude_closure_reviewed_edges_are_backed_by_reviewed_annotations(
    fortitude_closure_136_140_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in load_jsonl(
            "data/gold/fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl"
        )
    }
    edges = load_jsonl("data/processed/fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl")

    assert edges
    for edge in edges:
        assert edge["review_layer"] == "reviewed_doctrinal"
        assert edge["support_annotation_ids"]
        assert set(cast(list[str], edge["support_annotation_ids"])).issubset(annotations)
        assert "structural_editorial" not in cast(list[str], edge["support_types"])
        assert edge["fortitude_closure_focus"]


def test_patience_perseverance_and_gift_distinctions_remain_separate(
    fortitude_closure_136_140_artifacts,
) -> None:
    concepts = {
        row["concept_id"]: row
        for row in load_jsonl("data/gold/fortitude_closure_136_140_reviewed_concepts.jsonl")
    }

    assert "concept.patience" in concepts
    assert "concept.perseverance_virtue" in concepts
    assert "concept.fortitude" in concepts
    assert "concept.fortitude_gift" in concepts
    assert concept_labels(concepts["concept.patience"]).isdisjoint(
        concept_labels(concepts["concept.perseverance_virtue"])
    )
    assert concept_labels(concepts["concept.fortitude"]).isdisjoint(
        concept_labels(concepts["concept.fortitude_gift"])
    )
    assert concept_labels(concepts["concept.longanimity_fortitude"]).isdisjoint(
        concept_labels(concepts["concept.constancy_fortitude"])
    )


def test_fortitude_closure_precept_and_gift_edges_use_intended_schema(
    fortitude_closure_136_140_artifacts,
) -> None:
    edges = load_jsonl("data/processed/fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl")

    precept_edges = [
        row for row in edges if "precept" in cast(list[str], row["fortitude_closure_focus"])
    ]
    gift_edges = [row for row in edges if "gift" in cast(list[str], row["fortitude_closure_focus"])]

    assert precept_edges
    assert gift_edges
    assert {
        row["relation_type"] for row in precept_edges
    } == {"commands_act_of", "directed_to", "forbids_opposed_vice_of", "precept_of"}
    assert all(
        row["subject_id"]
        in {"concept.precepts_of_fortitude", "concept.precepts_of_fortitude_parts"}
        for row in precept_edges
    )
    assert any(
        row["edge_id"] == "edge.concept.fortitude_gift.corresponding_gift_of.concept.fortitude"
        for row in gift_edges
    )


def test_candidate_data_stays_out_of_reviewed_fortitude_closure_exports(
    fortitude_closure_136_140_artifacts,
) -> None:
    edges = load_jsonl("data/processed/fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl")
    annotations = load_jsonl(
        "data/gold/fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl"
    )

    assert all(not str(edge["edge_id"]).startswith("candidate.") for edge in edges)
    assert all(not str(row["annotation_id"]).startswith("candidate.") for row in annotations)


def test_fortitude_synthesis_exports_are_consistent(
    fortitude_closure_136_140_artifacts,
) -> None:
    with Path("data/processed/fortitude_tract_synthesis_nodes.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        nodes = list(csv.DictReader(handle))
    with Path("data/processed/fortitude_tract_synthesis_edges.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        edges = list(csv.DictReader(handle))

    assert len(nodes) == 89
    assert len(edges) == 64
    edge_ids = {row["edge_id"] for row in edges}
    assert "edge.concept.magnanimity.concerns_honor.concept.honor_recognition" in edge_ids
    assert "edge.concept.fortitude_gift.corresponding_gift_of.concept.fortitude" in edge_ids
