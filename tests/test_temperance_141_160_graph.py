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


def test_temperance_reviewed_edges_are_backed_by_reviewed_annotations(
    temperance_141_160_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in load_jsonl("data/gold/temperance_141_160_reviewed_doctrinal_annotations.jsonl")
    }
    edges = load_jsonl("data/processed/temperance_141_160_reviewed_doctrinal_edges.jsonl")

    assert edges
    for edge in edges:
        assert edge["review_layer"] == "reviewed_doctrinal"
        assert edge["support_annotation_ids"]
        assert set(cast(list[str], edge["support_annotation_ids"])).issubset(annotations)
        assert "structural_editorial" not in cast(list[str], edge["support_types"])
        assert edge["temperance_focus"]


def test_temperance_identity_separations_remain_stable(
    temperance_141_160_artifacts,
) -> None:
    concepts = {
        row["concept_id"]: row
        for row in load_jsonl("data/gold/temperance_141_160_reviewed_concepts.jsonl")
    }

    assert concept_labels(concepts["concept.abstinence"]).isdisjoint(
        concept_labels(concepts["concept.fasting"])
    )
    assert concept_labels(concepts["concept.chastity"]).isdisjoint(
        concept_labels(concepts["concept.virginity"])
    )
    assert concept_labels(concepts["concept.continence"]).isdisjoint(
        concept_labels(concepts["concept.temperance"])
    )
    assert concept_labels(concepts["concept.meekness"]).isdisjoint(
        concept_labels(concepts["concept.clemency"])
    )
    assert concepts["concept.anger"]["node_type"] == "passion"
    assert concepts["concept.anger_vice"]["node_type"] == "vice"


def test_temperance_part_taxonomy_and_domain_edges_use_intended_schema(
    temperance_141_160_artifacts,
) -> None:
    edges = load_jsonl("data/processed/temperance_141_160_reviewed_doctrinal_edges.jsonl")

    part_edges = [
        row
        for row in edges
        if row["relation_type"] in {"integral_part_of", "subjective_part_of", "potential_part_of"}
    ]
    assert part_edges
    assert all(row["object_id"] == "concept.temperance" for row in part_edges)
    assert any("integral_part" in cast(list[str], row["temperance_focus"]) for row in part_edges)
    assert any("subjective_part" in cast(list[str], row["temperance_focus"]) for row in part_edges)
    assert any("potential_part" in cast(list[str], row["temperance_focus"]) for row in part_edges)

    edge_ids = {row["edge_id"] for row in edges}
    assert (
        "edge.food_drink.concept.fasting.act_of.concept.abstinence" in edge_ids
    )
    assert (
        "edge.potential_parts.concept.meekness.concerns_anger.concept.anger" in edge_ids
    )
    assert (
        "edge.potential_parts.concept.modesty_general.concerns_outward_moderation.concept.outward_moderation"
        in edge_ids
    )


def test_candidate_data_stays_out_of_reviewed_temperance_exports(
    temperance_141_160_artifacts,
) -> None:
    edges = load_jsonl("data/processed/temperance_141_160_reviewed_doctrinal_edges.jsonl")
    annotations = load_jsonl(
        "data/gold/temperance_141_160_reviewed_doctrinal_annotations.jsonl"
    )

    assert all(not str(edge["edge_id"]).startswith("candidate.") for edge in edges)
    assert all(not str(row["annotation_id"]).startswith("candidate.") for row in annotations)


def test_temperance_phase1_synthesis_exports_are_consistent(
    temperance_141_160_artifacts,
) -> None:
    with Path("data/processed/temperance_phase1_synthesis_nodes.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        nodes = list(csv.DictReader(handle))
    with Path("data/processed/temperance_phase1_synthesis_edges.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        edges = list(csv.DictReader(handle))

    assert len(nodes) == 163
    assert len(edges) == 67
    edge_ids = {row["edge_id"] for row in edges}
    assert (
        "edge.temperance_proper.concept.temperance.species_of.concept.cardinal_virtue"
        in edge_ids
    )
    assert (
        "edge.potential_parts.concept.cruelty.contrary_to.concept.clemency" in edge_ids
    )
