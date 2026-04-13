from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from .corpus import CorpusAppBundle, candidate_relation_rows
from .theological_virtues import (
    edge_evidence_panel as base_edge_evidence_panel,
)
from .theological_virtues import (
    edge_in_question_range,
    trim_edge_to_question_range,
)


class OwedRelationTractPreset(TypedDict):
    label: str
    start_question: int
    end_question: int


OWED_RELATION_TRACT_PRESETS: dict[str, OwedRelationTractPreset] = {
    "full_owed_relation_tract": {
        "label": "Full owed-relation tract (QQ. 101-108)",
        "start_question": 101,
        "end_question": 108,
    },
    "origin_piety": {
        "label": "Origin / piety (Q101)",
        "start_question": 101,
        "end_question": 101,
    },
    "excellence_observance_honor": {
        "label": "Excellence / observance / honor (QQ. 102-103)",
        "start_question": 102,
        "end_question": 103,
    },
    "authority_obedience": {
        "label": "Authority / obedience (QQ. 104-105)",
        "start_question": 104,
        "end_question": 105,
    },
    "benefit_gratitude": {
        "label": "Benefit / gratitude (QQ. 106-107)",
        "start_question": 106,
        "end_question": 107,
    },
    "wrong_rectification_vengeance": {
        "label": "Wrong / rectification / vengeance (Q108)",
        "start_question": 108,
        "end_question": 108,
    },
}


def load_owed_relation_tract_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (base / "data" / "processed" / "owed_relation_tract_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("owed-relation tract summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = OWED_RELATION_TRACT_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def owed_relation_focus_tags(edge: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    due_mode = edge.get("due_mode")
    if due_mode == "origin":
        tags.append("origin_due")
    if due_mode == "excellence":
        tags.append("excellence_due")
    if due_mode == "authority":
        tags.append("authority_due")
    if due_mode == "benefaction":
        tags.append("benefaction_due")
    if due_mode == "rectificatory":
        tags.append("rectificatory_due")
    if str(edge.get("object_type")) == "role":
        tags.append("role_level")
    return tags


def filter_edges_by_question_range(
    bundle: CorpusAppBundle,
    *,
    start_question: int,
    end_question: int,
    include_editorial: bool = False,
    include_candidate: bool = False,
    relation_types: set[str] | None = None,
    node_types: set[str] | None = None,
    center_concept: str | None = None,
    focus_tags: set[str] | None = None,
) -> list[dict[str, Any]]:
    edges = [
        edge
        for edge in bundle.reviewed_doctrinal_edges
        if edge_in_question_range(bundle, edge, start_question, end_question)
    ]
    if include_editorial:
        edges.extend(
            edge
            for edge in bundle.reviewed_structural_edges
            if edge_in_question_range(bundle, edge, start_question, end_question)
        )
    if include_candidate:
        edges.extend(
            edge
            for edge in candidate_relation_rows(
                bundle,
                question_id=None,
                center_concept=center_concept,
            )
            if edge_in_question_range(bundle, edge, start_question, end_question)
        )
    filtered: list[dict[str, Any]] = []
    for edge in edges:
        trimmed_edge = trim_edge_to_question_range(
            bundle,
            edge,
            start_question=start_question,
            end_question=end_question,
        )
        if trimmed_edge is None:
            continue
        if relation_types and str(trimmed_edge["relation_type"]) not in relation_types:
            continue
        if node_types and (
            str(trimmed_edge["subject_type"]) not in node_types
            or str(trimmed_edge["object_type"]) not in node_types
        ):
            continue
        if center_concept and center_concept not in {
            str(trimmed_edge["subject_id"]),
            str(trimmed_edge["object_id"]),
        }:
            continue
        tags = owed_relation_focus_tags(trimmed_edge)
        if focus_tags and not focus_tags.intersection(tags):
            continue
        trimmed_edge["owed_relation_focus_tags"] = tags
        filtered.append(trimmed_edge)
    filtered.sort(key=lambda item: (str(item["layer"]), str(item["edge_id"])))
    return filtered


def filter_edges_by_preset(
    bundle: CorpusAppBundle,
    preset_name: str,
    *,
    include_editorial: bool = False,
    include_candidate: bool = False,
    relation_types: set[str] | None = None,
    node_types: set[str] | None = None,
    center_concept: str | None = None,
    focus_tags: set[str] | None = None,
) -> list[dict[str, Any]]:
    start_question, end_question = preset_range(preset_name)
    return filter_edges_by_question_range(
        bundle,
        start_question=start_question,
        end_question=end_question,
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types,
        node_types=node_types,
        center_concept=center_concept,
        focus_tags=focus_tags,
    )


def edge_evidence_panel(
    bundle: CorpusAppBundle,
    edge_id: str,
    *,
    edge_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    panel = base_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    row = edge_row
    if row is None:
        row = next(
            edge
            for edge in [*bundle.reviewed_doctrinal_edges, *bundle.reviewed_structural_edges]
            if str(edge["edge_id"]) == edge_id
        )
    panel["due_mode"] = row.get("due_mode")
    panel["owed_relation_focus_tags"] = owed_relation_focus_tags(row)
    return panel


def owed_relation_tract_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = OWED_RELATION_TRACT_PRESETS["full_owed_relation_tract"]["start_question"],
    end_question: int = OWED_RELATION_TRACT_PRESETS["full_owed_relation_tract"]["end_question"],
) -> dict[str, Any]:
    reviewed_edges = [
        edge
        for edge in bundle.reviewed_doctrinal_edges
        if concept_id in {str(edge["subject_id"]), str(edge["object_id"])}
        and edge_in_question_range(bundle, edge, start_question, end_question)
    ]
    editorial_edges = [
        edge
        for edge in bundle.reviewed_structural_edges
        if concept_id in {str(edge["subject_id"]), str(edge["object_id"])}
        and edge_in_question_range(bundle, edge, start_question, end_question)
    ]
    candidate_mentions = [
        mention.model_dump(mode="json")
        for mention in bundle.candidate_mentions
        if mention.passage_id in bundle.passages
        and bundle.passages[mention.passage_id].part_id == "ii-ii"
        and start_question <= bundle.passages[mention.passage_id].question_number <= end_question
        and (
            mention.proposed_concept_id == concept_id or concept_id in mention.proposed_concept_ids
        )
    ]
    candidate_relations = [
        relation.model_dump(mode="json")
        for relation in bundle.candidate_relations
        if relation.source_passage_id in bundle.passages
        and bundle.passages[relation.source_passage_id].part_id == "ii-ii"
        and start_question
        <= bundle.passages[relation.source_passage_id].question_number
        <= end_question
        and concept_id in {relation.subject_id, relation.object_id}
    ]
    supporting_passage_ids = []
    for edge in reviewed_edges:
        for passage_id in edge.get("source_passage_ids", []):
            if passage_id not in supporting_passage_ids:
                supporting_passage_ids.append(passage_id)
    for mention in candidate_mentions:
        passage_id = str(mention["passage_id"])
        if passage_id not in supporting_passage_ids:
            supporting_passage_ids.append(passage_id)
    related_questions = sorted(
        {
            bundle.passages[passage_id].question_number
            for passage_id in supporting_passage_ids
            if passage_id in bundle.passages
        }
    )
    return {
        "concept": bundle.registry[concept_id].model_dump(mode="json"),
        "reviewed_incident_edges": reviewed_edges,
        "reviewed_doctrinal_edges": reviewed_edges,
        "editorial_correspondences": editorial_edges,
        "reviewed_structural_edges": editorial_edges,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
        "top_supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in supporting_passage_ids[:10]
            if passage_id in bundle.passages
        ],
        "related_questions": related_questions,
        "coverage": {
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
        },
        "ambiguity_notes": bundle.registry[concept_id].disambiguation_notes,
    }
