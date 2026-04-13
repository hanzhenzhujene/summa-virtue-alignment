from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from ..annotations.temperance_closure_161_170_spec import (
    focus_tags_for_edge as closure_focus_tags_for_edge,
)
from ..models import PilotRelationType
from .corpus import CorpusAppBundle, candidate_relation_rows
from .temperance_141_160 import temperance_focus_tags as phase1_temperance_focus_tags
from .theological_virtues import edge_evidence_panel as base_edge_evidence_panel
from .theological_virtues import edge_in_question_range, trim_edge_to_question_range


class TemperanceClosure161170Preset(TypedDict):
    label: str
    start_question: int
    end_question: int


TEMPERANCE_CLOSURE_161_170_PRESETS: dict[str, TemperanceClosure161170Preset] = {
    "humility_pride_161_162": {
        "label": "Humility and pride (QQ. 161-162)",
        "start_question": 161,
        "end_question": 162,
    },
    "adams_first_sin_163_165": {
        "label": "Adam's first sin (QQ. 163-165)",
        "start_question": 163,
        "end_question": 165,
    },
    "studiousness_curiosity_166_167": {
        "label": "Studiousness and curiosity (QQ. 166-167)",
        "start_question": 166,
        "end_question": 167,
    },
    "external_modesty_168_169": {
        "label": "External modesty (QQ. 168-169)",
        "start_question": 168,
        "end_question": 169,
    },
    "precepts_of_temperance_q170": {
        "label": "Precepts of temperance (Q170)",
        "start_question": 170,
        "end_question": 170,
    },
    "temperance_full_synthesis": {
        "label": "Temperance full synthesis (QQ. 141-170)",
        "start_question": 141,
        "end_question": 170,
    },
    "temperance_doctrinal_only_synthesis": {
        "label": "Temperance doctrinal-only synthesis",
        "start_question": 141,
        "end_question": 170,
    },
    "temperance_doctrinal_editorial_synthesis": {
        "label": "Temperance doctrinal + editorial synthesis",
        "start_question": 141,
        "end_question": 170,
    },
}


def load_temperance_closure_161_170_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (base / "data" / "processed" / "temperance_closure_161_170_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("temperance closure 161-170 summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = TEMPERANCE_CLOSURE_161_170_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def _question_numbers_for_edge(edge: dict[str, Any]) -> list[int]:
    question_numbers: list[int] = []
    for passage_id in edge.get("source_passage_ids", []):
        parts = str(passage_id).split(".")
        if len(parts) >= 3 and parts[2].startswith("q"):
            question_numbers.append(int(parts[2][1:]))
    return question_numbers


def temperance_closure_focus_tags(edge: dict[str, Any]) -> list[str]:
    tags: set[str] = set()

    phase1_existing = edge.get("temperance_focus") or edge.get("temperance_focus_tags")
    if isinstance(phase1_existing, list) and phase1_existing:
        tags.update(str(value) for value in phase1_existing)

    closure_existing = edge.get("temperance_closure_focus") or edge.get(
        "temperance_closure_focus_tags"
    )
    if isinstance(closure_existing, list) and closure_existing:
        tags.update(str(value) for value in closure_existing)

    question_numbers = _question_numbers_for_edge(edge)
    if not tags and any(141 <= question_number <= 160 for question_number in question_numbers):
        tags.update(phase1_temperance_focus_tags(edge))
    if any(161 <= question_number <= 170 for question_number in question_numbers):
        closure_numbers = [
            question_number for question_number in question_numbers if 161 <= question_number <= 170
        ]
        if closure_numbers:
            tags.update(
                str(tag)
                for tag in closure_focus_tags_for_edge(
                    min(closure_numbers),
                    str(edge["subject_id"]),
                    cast(PilotRelationType, edge["relation_type"]),
                    str(edge["object_id"]),
                )
            )
    return sorted(tags)


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
        tags = temperance_closure_focus_tags(trimmed_edge)
        if start_question == 141 and end_question == 170:
            tags = sorted(set(tags + ["synthesis"]))
        if focus_tags and not focus_tags.intersection(tags):
            continue
        trimmed_edge["temperance_closure_focus_tags"] = tags
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
    if preset_name == "humility_pride_161_162":
        effective_focus_tags.add("humility_pride")
    if preset_name == "adams_first_sin_163_165":
        effective_focus_tags.add("adam_case")
    if preset_name == "studiousness_curiosity_166_167":
        effective_focus_tags.add("study_curiosity")
    if preset_name == "external_modesty_168_169":
        effective_focus_tags.add("external_modesty")
    if preset_name == "precepts_of_temperance_q170":
        effective_focus_tags.add("precept_linkage")
    if preset_name == "temperance_doctrinal_editorial_synthesis":
        effective_include_editorial = True
    if preset_name == "temperance_doctrinal_only_synthesis":
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
    focus_tags = temperance_closure_focus_tags(row)
    panel["temperance_closure_focus_tags"] = focus_tags
    panel["temperance_scope_cluster"] = row.get("temperance_closure_cluster") or row.get(
        "temperance_cluster"
    )
    panel["temperance_distinctions"] = {
        "humility_vs_pride": "humility_pride" in focus_tags,
        "pride_vs_adams_first_sin": "adam_case" in focus_tags,
        "studiousness_vs_curiosity": "study_curiosity" in focus_tags,
        "modesty_general_vs_external_species": bool(
            {
                "modesty_general",
                "external_modesty",
                "external_behavior",
                "external_attire",
            }.intersection(focus_tags)
        ),
        "precept_linkage": "precept_linkage" in focus_tags,
    }
    return panel


def temperance_closure_161_170_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = TEMPERANCE_CLOSURE_161_170_PRESETS["temperance_full_synthesis"][
        "start_question"
    ],
    end_question: int = TEMPERANCE_CLOSURE_161_170_PRESETS["temperance_full_synthesis"][
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
    for edge in [*reviewed_edges, *editorial_edges]:
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
    focus_counts: dict[str, int] = {}
    for edge in reviewed_edges:
        for tag in temperance_closure_focus_tags(edge):
            focus_counts[tag] = focus_counts.get(tag, 0) + 1
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
        "unresolved_disambiguation_notes": bundle.registry[concept_id].disambiguation_notes,
        "coverage": {
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_edge_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
            "focus_counts": dict(sorted(focus_counts.items())),
        },
    }
