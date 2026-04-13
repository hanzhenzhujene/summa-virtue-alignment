from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from ..annotations.temperance_141_160_spec import focus_tags_for_edge
from ..models import PilotRelationType
from .corpus import CorpusAppBundle, candidate_relation_rows
from .theological_virtues import edge_evidence_panel as base_edge_evidence_panel
from .theological_virtues import edge_in_question_range, trim_edge_to_question_range


class Temperance141160Preset(TypedDict):
    label: str
    start_question: int
    end_question: int


TEMPERANCE_141_160_PRESETS: dict[str, Temperance141160Preset] = {
    "temperance_overview_141_160": {
        "label": "Temperance overview (QQ. 141-160)",
        "start_question": 141,
        "end_question": 160,
    },
    "temperance_proper_141_143": {
        "label": "Temperance proper (QQ. 141-143)",
        "start_question": 141,
        "end_question": 143,
    },
    "integral_parts_144_145": {
        "label": "Integral parts (QQ. 144-145)",
        "start_question": 144,
        "end_question": 145,
    },
    "food_drink_146_150": {
        "label": "Food and drink (QQ. 146-150)",
        "start_question": 146,
        "end_question": 150,
    },
    "chastity_lust_151_154": {
        "label": "Chastity and lust (QQ. 151-154)",
        "start_question": 151,
        "end_question": 154,
    },
    "potential_parts_155_160": {
        "label": "Potential parts (QQ. 155-160)",
        "start_question": 155,
        "end_question": 160,
    },
    "temperance_doctrinal_only_synthesis": {
        "label": "Doctrinal-only synthesis",
        "start_question": 141,
        "end_question": 160,
    },
    "temperance_doctrinal_editorial_synthesis": {
        "label": "Doctrinal + editorial synthesis",
        "start_question": 141,
        "end_question": 160,
    },
}


def load_temperance_141_160_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (
            base / "data" / "processed" / "temperance_141_160_coverage.json"
        ).read_text(encoding="utf-8")
    )
    if not isinstance(payload, dict):
        raise ValueError("temperance 141-160 summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = TEMPERANCE_141_160_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


def temperance_focus_tags(edge: dict[str, Any]) -> list[str]:
    existing = edge.get("temperance_focus") or edge.get("temperance_focus_tags")
    if isinstance(existing, list) and existing:
        return sorted(str(value) for value in existing)
    question_numbers: list[int] = []
    for passage_id in edge.get("source_passage_ids", []):
        parts = str(passage_id).split(".")
        if len(parts) >= 3 and parts[2].startswith("q"):
            question_numbers.append(int(parts[2][1:]))
    question_number = question_numbers[0] if question_numbers else 141
    return [
        str(tag)
        for tag in focus_tags_for_edge(
            question_number,
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
        tags = temperance_focus_tags(trimmed_edge)
        if focus_tags and not focus_tags.intersection(tags):
            continue
        trimmed_edge["temperance_focus_tags"] = tags
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
    if preset_name == "temperance_proper_141_143":
        effective_focus_tags.add("temperance_proper")
    if preset_name == "integral_parts_144_145":
        effective_focus_tags.add("general_integral")
    if preset_name == "food_drink_146_150":
        effective_focus_tags.add("food_drink")
    if preset_name == "chastity_lust_151_154":
        effective_focus_tags.add("sexual")
    if preset_name == "potential_parts_155_160":
        effective_focus_tags.add("potential_parts")
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
    panel["temperance_focus_tags"] = temperance_focus_tags(row)
    panel["temperance_cluster"] = row.get("temperance_cluster")
    panel["temperance_distinctions"] = {
        "part_taxonomy": sorted(
            {
                tag
                for tag in panel["temperance_focus_tags"]
                if tag in {"integral_part", "subjective_part", "potential_part"}
            }
        ),
        "matter_domains": sorted(
            {
                tag
                for tag in panel["temperance_focus_tags"]
                if tag
                in {
                    "food",
                    "drink",
                    "sex",
                    "continence_incontinence",
                    "meekness_anger",
                    "clemency_cruelty",
                    "modesty_general",
                }
            }
        ),
    }
    return panel


def temperance_141_160_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = TEMPERANCE_141_160_PRESETS["temperance_overview_141_160"][
        "start_question"
    ],
    end_question: int = TEMPERANCE_141_160_PRESETS["temperance_overview_141_160"][
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
        for tag in temperance_focus_tags(edge):
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
        "coverage": {
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_edge_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
            "focus_counts": dict(sorted(focus_counts.items())),
        },
    }
