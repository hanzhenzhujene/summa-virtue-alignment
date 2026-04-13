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


def test_temperance_closure_reviewed_edges_are_backed_by_reviewed_annotations(
    temperance_closure_161_170_artifacts,
) -> None:
    annotations = {
        row["annotation_id"]
        for row in load_jsonl(
            "data/gold/temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl"
        )
    }
    edges = load_jsonl("data/processed/temperance_closure_161_170_reviewed_doctrinal_edges.jsonl")

    assert edges
    for edge in edges:
        assert edge["review_layer"] == "reviewed_doctrinal"
        assert edge["support_annotation_ids"]
        assert set(cast(list[str], edge["support_annotation_ids"])).issubset(annotations)
        assert "structural_editorial" not in cast(list[str], edge["support_types"])
        assert edge["temperance_closure_focus"]


def test_temperance_closure_identity_separations_remain_stable(
    temperance_closure_161_170_artifacts,
) -> None:
    closure_concepts = {
        row["concept_id"]: row
        for row in load_jsonl("data/gold/temperance_closure_161_170_reviewed_concepts.jsonl")
    }
    phase1_concepts = {
        row["concept_id"]: row
        for row in load_jsonl("data/gold/temperance_141_160_reviewed_concepts.jsonl")
    }

    assert concept_labels(closure_concepts["concept.humility"]).isdisjoint(
        concept_labels(closure_concepts["concept.pride"])
    )
    assert concept_labels(closure_concepts["concept.pride"]).isdisjoint(
        concept_labels(closure_concepts["concept.adams_first_sin"])
    )
    assert concept_labels(closure_concepts["concept.studiousness"]).isdisjoint(
        concept_labels(closure_concepts["concept.curiosity"])
    )
    assert concept_labels(phase1_concepts["concept.modesty_general"]).isdisjoint(
        concept_labels(closure_concepts["concept.external_behavior_modesty"])
    )
    assert concept_labels(phase1_concepts["concept.modesty_general"]).isdisjoint(
        concept_labels(closure_concepts["concept.outward_attire_modesty"])
    )


def test_temperance_closure_case_inquiry_external_and_precept_edges_use_intended_schema(
    temperance_closure_161_170_artifacts,
) -> None:
    edges = load_jsonl("data/processed/temperance_closure_161_170_reviewed_doctrinal_edges.jsonl")

    assert any(
        row["edge_id"] == "edge.concept.adams_first_sin.case_of.concept.pride" for row in edges
    )
    assert any(
        row["relation_type"] == "results_in_punishment"
        and row["subject_id"] == "concept.adams_first_sin"
        for row in edges
    )
    assert any(
        row["relation_type"] == "tempted_by"
        and row["object_id"] == "concept.first_parents_temptation"
        for row in edges
    )
    assert any(
        row["relation_type"] == "concerns_ordered_inquiry"
        and row["object_id"] in {"concept.ordered_inquiry", "concept.disordered_inquiry"}
        for row in edges
    )
    assert any(
        row["relation_type"] == "concerns_external_behavior"
        and row["object_id"] in {"concept.outward_behavior", "concept.playful_actions"}
        for row in edges
    )
    assert any(
        row["relation_type"] == "concerns_outward_attire"
        and row["object_id"] == "concept.outward_apparel"
        for row in edges
    )
    assert all(
        str(row["subject_id"]).startswith("concept.precepts_of_temperance")
        for row in edges
        if row["relation_type"] in {"precept_of", "commands_act_of", "forbids_opposed_vice_of"}
    )


def test_candidate_data_stays_out_of_reviewed_temperance_closure_exports(
    temperance_closure_161_170_artifacts,
) -> None:
    edges = load_jsonl("data/processed/temperance_closure_161_170_reviewed_doctrinal_edges.jsonl")
    annotations = load_jsonl(
        "data/gold/temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl"
    )

    assert all(not str(edge["edge_id"]).startswith("candidate.") for edge in edges)
    assert all(not str(row["annotation_id"]).startswith("candidate.") for row in annotations)


def test_temperance_full_synthesis_exports_are_consistent(
    temperance_closure_161_170_artifacts,
) -> None:
    with Path("data/processed/temperance_full_synthesis_nodes.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        nodes = list(csv.DictReader(handle))
    with Path("data/processed/temperance_full_synthesis_edges.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        edges = list(csv.DictReader(handle))

    assert len(nodes) > 163
    assert len(edges) > 67
    edge_ids = {row["edge_id"] for row in edges}
    assert (
        "edge.temperance_proper.concept.temperance.species_of.concept.cardinal_virtue" in edge_ids
    )
    assert "edge.concept.adams_first_sin.case_of.concept.pride" in edge_ids
