from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from ..annotations.fortitude_parts_129_135_spec import (
    DEFICIENCY_OPPOSITION_RELATIONS,
    EXCESS_OPPOSITION_RELATIONS,
    is_expenditure_related_edge,
    is_honor_related_edge,
)
from ..models import PilotRelationType
from .corpus import CorpusAppBundle, candidate_relation_rows
from .theological_virtues import (
    edge_evidence_panel as base_edge_evidence_panel,
)
from .theological_virtues import (
    edge_in_question_range,
    trim_edge_to_question_range,
)


class FortitudeParts129135Preset(TypedDict):
    label: str
    start_question: int
    end_question: int


FORTITUDE_PARTS_129_135_PRESETS: dict[str, FortitudeParts129135Preset] = {
    "full_fortitude_parts_129_135": {
        "label": "Full tract (QQ. 129-135)",
        "start_question": 129,
        "end_question": 135,
    },
    "magnanimity_cluster": {
        "label": "Magnanimity cluster (QQ. 129-133)",
        "start_question": 129,
        "end_question": 133,
    },
    "magnificence_cluster": {
        "label": "Magnificence cluster (QQ. 134-135)",
        "start_question": 134,
        "end_question": 135,
    },
    "excess_opposition_view": {
        "label": "Excess-opposition view",
        "start_question": 129,
        "end_question": 135,
    },
    "deficiency_opposition_view": {
        "label": "Deficiency-opposition view",
        "start_question": 129,
        "end_question": 135,
    },
}


def load_fortitude_parts_129_135_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (
            base / "data" / "processed" / "fortitude_parts_129_135_coverage.json"
        ).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError("fortitude parts 129-135 summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = FORTITUDE_PARTS_129_135_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def fortitude_parts_focus_tags(edge: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    subject_id = str(edge["subject_id"])
    relation_type = cast(PilotRelationType, edge["relation_type"])
    object_id = str(edge["object_id"])
    cluster = edge.get("fortitude_parts_cluster")
    if cluster == "honor_worthiness":
        tags.append("honor_related")
    if cluster == "expenditure_work":
        tags.append("expenditure_related")
    if relation_type in EXCESS_OPPOSITION_RELATIONS:
        tags.append("excess_opposition")
    if relation_type in DEFICIENCY_OPPOSITION_RELATIONS:
        tags.append("deficiency_opposition")
    if relation_type == "related_to_fortitude":
        tags.append("fortitude_related")
    if is_honor_related_edge(subject_id, relation_type, object_id):
        tags.append("honor_related")
    if is_expenditure_related_edge(subject_id, relation_type, object_id):
        tags.append("expenditure_related")
    return sorted(set(tags))


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
        tags = fortitude_parts_focus_tags(trimmed_edge)
        if focus_tags and not focus_tags.intersection(tags):
            continue
        trimmed_edge["fortitude_parts_focus_tags"] = tags
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
    effective_focus_tags = set(focus_tags or set())
    if preset_name == "excess_opposition_view":
        effective_focus_tags.add("excess_opposition")
    if preset_name == "deficiency_opposition_view":
        effective_focus_tags.add("deficiency_opposition")
    return filter_edges_by_question_range(
        bundle,
        start_question=start_question,
        end_question=end_question,
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types,
        node_types=node_types,
        center_concept=center_concept,
        focus_tags=effective_focus_tags or None,
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
    panel["fortitude_parts_cluster"] = row.get("fortitude_parts_cluster")
    panel["fortitude_parts_focus_tags"] = fortitude_parts_focus_tags(row)
    return panel


def fortitude_parts_129_135_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = FORTITUDE_PARTS_129_135_PRESETS[
        "full_fortitude_parts_129_135"
    ]["start_question"],
    end_question: int = FORTITUDE_PARTS_129_135_PRESETS[
        "full_fortitude_parts_129_135"
    ]["end_question"],
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
    supporting_passage_ids: list[str] = []
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
    reviewed_clusters = sorted(
        {
            str(edge["fortitude_parts_cluster"])
            for edge in reviewed_edges
            if edge.get("fortitude_parts_cluster")
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
        "supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in supporting_passage_ids[:12]
            if passage_id in bundle.passages
        ],
        "top_supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in supporting_passage_ids[:12]
            if passage_id in bundle.passages
        ],
        "related_questions": related_questions,
        "ambiguity_notes": bundle.registry[concept_id].disambiguation_notes,
        "coverage": {
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_edge_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
            "reviewed_clusters": reviewed_clusters,
        },
    }
