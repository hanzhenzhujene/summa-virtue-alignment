from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from ..annotations.fortitude_closure_136_140_spec import focus_tags_for_edge
from ..models import PilotRelationType
from .corpus import CorpusAppBundle, candidate_relation_rows
from .theological_virtues import (
    edge_evidence_panel as base_edge_evidence_panel,
)
from .theological_virtues import (
    edge_in_question_range,
    trim_edge_to_question_range,
)


class FortitudeClosure136140Preset(TypedDict):
    label: str
    start_question: int
    end_question: int


FORTITUDE_CLOSURE_136_140_PRESETS: dict[str, FortitudeClosure136140Preset] = {
    "patience_q136": {
        "label": "Patience (Q136)",
        "start_question": 136,
        "end_question": 136,
    },
    "perseverance_q137": {
        "label": "Perseverance (Q137)",
        "start_question": 137,
        "end_question": 137,
    },
    "opposed_vices_q138": {
        "label": "Opposed vices (Q138)",
        "start_question": 138,
        "end_question": 138,
    },
    "gift_of_fortitude_q139": {
        "label": "Gift of fortitude (Q139)",
        "start_question": 139,
        "end_question": 139,
    },
    "precepts_of_fortitude_q140": {
        "label": "Precepts of fortitude (Q140)",
        "start_question": 140,
        "end_question": 140,
    },
    "fortitude_tract_full_synthesis": {
        "label": "Fortitude tract full synthesis (QQ. 123-140)",
        "start_question": 123,
        "end_question": 140,
    },
    "fortitude_tract_doctrinal_only_synthesis": {
        "label": "Fortitude tract doctrinal-only synthesis",
        "start_question": 123,
        "end_question": 140,
    },
    "fortitude_tract_doctrinal_editorial_synthesis": {
        "label": "Fortitude tract doctrinal + editorial synthesis",
        "start_question": 123,
        "end_question": 140,
    },
}


def load_fortitude_closure_136_140_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (
            base / "data" / "processed" / "fortitude_closure_136_140_coverage.json"
        ).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError("fortitude closure 136-140 summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = FORTITUDE_CLOSURE_136_140_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def fortitude_closure_focus_tags(edge: dict[str, Any]) -> list[str]:
    existing = edge.get("fortitude_closure_focus") or edge.get("fortitude_closure_focus_tags")
    if isinstance(existing, list) and existing:
        return sorted(str(value) for value in existing)
    return [
        str(tag)
        for tag in focus_tags_for_edge(
            str(edge["subject_id"]),
            cast(PilotRelationType, edge["relation_type"]),
            str(edge["object_id"]),
        )
    ]


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
        tags = fortitude_closure_focus_tags(trimmed_edge)
        if start_question == 123 and end_question == 140:
            tags = sorted(set(tags + ["synthesis"]))
        if focus_tags and not focus_tags.intersection(tags):
            continue
        trimmed_edge["fortitude_closure_focus_tags"] = tags
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
    effective_include_editorial = include_editorial
    effective_include_candidate = include_candidate
    if preset_name == "patience_q136":
        effective_focus_tags.add("patience")
    if preset_name == "perseverance_q137":
        effective_focus_tags.add("perseverance")
    if preset_name == "opposed_vices_q138":
        effective_focus_tags.add("opposed_vice")
    if preset_name == "gift_of_fortitude_q139":
        effective_focus_tags.add("gift")
    if preset_name == "precepts_of_fortitude_q140":
        effective_focus_tags.add("precept")
    if preset_name == "fortitude_tract_doctrinal_editorial_synthesis":
        effective_include_editorial = True
    if preset_name == "fortitude_tract_doctrinal_only_synthesis":
        effective_include_editorial = False
        effective_include_candidate = False
    return filter_edges_by_question_range(
        bundle,
        start_question=start_question,
        end_question=end_question,
        include_editorial=effective_include_editorial,
        include_candidate=effective_include_candidate,
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
    panel["fortitude_closure_focus_tags"] = fortitude_closure_focus_tags(row)
    panel["fortitude_distinctions"] = {
        "patience_vs_perseverance": any(
            tag in {"patience", "perseverance"}
            for tag in panel["fortitude_closure_focus_tags"]
        ),
        "gift_vs_virtue_fortitude": "gift" in panel["fortitude_closure_focus_tags"],
        "precept_linkage": "precept" in panel["fortitude_closure_focus_tags"],
    }
    return panel


def fortitude_closure_136_140_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = FORTITUDE_CLOSURE_136_140_PRESETS["fortitude_tract_full_synthesis"][
        "start_question"
    ],
    end_question: int = FORTITUDE_CLOSURE_136_140_PRESETS["fortitude_tract_full_synthesis"][
        "end_question"
    ],
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
        if passage_id in bundle.passages and passage_id not in supporting_passage_ids:
            supporting_passage_ids.append(passage_id)
    supporting_passages = [
        {
            "passage_id": passage_id,
            "citation_label": bundle.passages[passage_id].citation_label,
            "text": bundle.passages[passage_id].text,
        }
        for passage_id in supporting_passage_ids[:10]
        if passage_id in bundle.passages
    ]
    related_questions = sorted(
        {
            bundle.passages[passage_id].question_id
            for passage_id in supporting_passage_ids
            if passage_id in bundle.passages
        }
    )
    focus_counts: dict[str, int] = {}
    for edge in reviewed_edges:
        for tag in fortitude_closure_focus_tags(edge):
            focus_counts[tag] = focus_counts.get(tag, 0) + 1
    concept = bundle.registry[concept_id]
    return {
        "concept": concept.model_dump(mode="json"),
        "reviewed_incident_edges": reviewed_edges,
        "reviewed_doctrinal_edges": reviewed_edges,
        "editorial_correspondences": editorial_edges,
        "reviewed_structural_edges": editorial_edges,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
        "top_supporting_passages": supporting_passages,
        "related_questions": related_questions,
        "coverage": {
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_edge_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
            "focus_counts": dict(sorted(focus_counts.items())),
        },
        "unresolved_disambiguation_notes": concept.disambiguation_notes,
    }
