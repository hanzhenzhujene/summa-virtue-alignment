from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from ..annotations.justice_core_spec import (
    is_harmed_domain_relation,
    is_judicial_process_relation,
    is_justice_species_relation,
    is_restitution_related_relation,
)
from .corpus import CorpusAppBundle, candidate_relation_rows
from .theological_virtues import (
    edge_evidence_panel as base_edge_evidence_panel,
)
from .theological_virtues import (
    edge_in_question_range,
    trim_edge_to_question_range,
)


class JusticeCorePreset(TypedDict):
    label: str
    start_question: int
    end_question: int


JUSTICE_CORE_PRESETS: dict[str, JusticeCorePreset] = {
    "justice_overview": {
        "label": "Justice overview (QQ. 57-79)",
        "start_question": 57,
        "end_question": 79,
    },
    "justice_foundations": {
        "label": "Justice foundations (QQ. 57-63)",
        "start_question": 57,
        "end_question": 63,
    },
    "bodily_property_wrongs": {
        "label": "Bodily and property wrongs (QQ. 64-66)",
        "start_question": 64,
        "end_question": 66,
    },
    "judicial_process_wrongs": {
        "label": "Judicial-process wrongs (QQ. 67-71)",
        "start_question": 67,
        "end_question": 71,
    },
    "verbal_injuries": {
        "label": "Verbal injuries (QQ. 72-76)",
        "start_question": 72,
        "end_question": 76,
    },
    "exchange_wrongs": {
        "label": "Exchange wrongs (QQ. 77-78)",
        "start_question": 77,
        "end_question": 78,
    },
}


def load_justice_core_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (base / "data" / "processed" / "justice_core_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("justice core summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = JUSTICE_CORE_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def justice_focus_tags(edge: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    subject_id = str(edge["subject_id"])
    relation_type = str(edge["relation_type"])
    object_id = str(edge["object_id"])
    if is_justice_species_relation(subject_id, relation_type, object_id):
        tags.append("justice_species")
    if is_harmed_domain_relation(subject_id, relation_type, object_id):
        tags.append("harmed_domain")
    if is_restitution_related_relation(subject_id, relation_type, object_id):
        tags.append("restitution_related")
    if is_judicial_process_relation(subject_id, relation_type, object_id):
        tags.append("judicial_process")
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
        tags = justice_focus_tags(trimmed_edge)
        if focus_tags and not focus_tags.intersection(tags):
            continue
        trimmed_edge["justice_focus_tags"] = tags
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
    panel["justice_focus_tags"] = justice_focus_tags(row)
    return panel


def justice_core_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = JUSTICE_CORE_PRESETS["justice_overview"]["start_question"],
    end_question: int = JUSTICE_CORE_PRESETS["justice_overview"]["end_question"],
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
    top_passage_ids = []
    for edge in reviewed_edges:
        for passage_id in edge.get("source_passage_ids", []):
            if passage_id not in top_passage_ids:
                top_passage_ids.append(passage_id)
    for mention in candidate_mentions:
        passage_id = str(mention["passage_id"])
        if passage_id not in top_passage_ids:
            top_passage_ids.append(passage_id)
    related_questions = sorted(
        {
            bundle.passages[passage_id].question_number
            for passage_id in top_passage_ids
            if passage_id in bundle.passages
        }
    )
    return {
        "concept": bundle.registry[concept_id].model_dump(mode="json"),
        "reviewed_incident_edges": [
            {**edge, "justice_focus_tags": justice_focus_tags(edge)} for edge in reviewed_edges
        ],
        "editorial_correspondences": editorial_edges,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
        "top_supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in top_passage_ids[:12]
            if passage_id in bundle.passages
        ],
        "related_questions": related_questions,
        "coverage": {
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_edge_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
        },
        "unresolved_disambiguation_notes": bundle.registry[concept_id].disambiguation_notes,
    }
