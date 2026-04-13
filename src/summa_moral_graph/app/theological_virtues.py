from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict, cast

from .corpus import CorpusAppBundle, candidate_relation_rows


class TheologicalVirtuesPreset(TypedDict):
    label: str
    start_question: int
    end_question: int


THEOLOGICAL_VIRTUES_PRESETS: dict[str, TheologicalVirtuesPreset] = {
    "faith": {
        "label": "Faith tract (QQ. 1-16)",
        "start_question": 1,
        "end_question": 16,
    },
    "hope": {
        "label": "Hope tract (QQ. 17-22)",
        "start_question": 17,
        "end_question": 22,
    },
    "charity": {
        "label": "Charity tract (QQ. 23-46)",
        "start_question": 23,
        "end_question": 46,
    },
    "all_theological_virtues": {
        "label": "All theological virtues (QQ. 1-46)",
        "start_question": 1,
        "end_question": 46,
    },
}


def load_theological_virtues_summary(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    payload = json.loads(
        (base / "data" / "processed" / "theological_virtues_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    if not isinstance(payload, dict):
        raise ValueError("theological virtues summary must deserialize to a dictionary")
    return cast(dict[str, Any], payload)


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = THEOLOGICAL_VIRTUES_PRESETS[preset_name]
    return int(preset["start_question"]), int(preset["end_question"])


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
        if relation_types and str(edge["relation_type"]) not in relation_types:
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
    )


def edge_in_question_range(
    bundle: CorpusAppBundle,
    edge: dict[str, Any],
    start_question: int,
    end_question: int,
) -> bool:
    source_passage_ids = [str(passage_id) for passage_id in edge.get("source_passage_ids", [])]
    if source_passage_ids:
        for passage_id in source_passage_ids:
            passage = bundle.passages.get(passage_id)
            if (
                passage is not None
                and passage.part_id == "ii-ii"
                and start_question <= passage.question_number <= end_question
            ):
                return True
        return False
    for node_id in (str(edge["subject_id"]), str(edge["object_id"])):
        question_number = node_question_number(node_id)
        if question_number is not None and start_question <= question_number <= end_question:
            return True
    return False


def trim_edge_to_question_range(
    bundle: CorpusAppBundle,
    edge: dict[str, Any],
    *,
    start_question: int,
    end_question: int,
) -> dict[str, Any] | None:
    source_passage_ids = [str(passage_id) for passage_id in edge.get("source_passage_ids", [])]
    if not source_passage_ids:
        return edge

    kept_passage_ids = [
        passage_id
        for passage_id in source_passage_ids
        if passage_id in bundle.passages
        and bundle.passages[passage_id].part_id == "ii-ii"
        and start_question <= bundle.passages[passage_id].question_number <= end_question
    ]
    if not kept_passage_ids:
        return None

    trimmed = dict(edge)
    trimmed["source_passage_ids"] = kept_passage_ids
    if edge.get("layer") == "candidate":
        trimmed["evidence_snippets"] = [
            snippet
            for passage_id, snippet in zip(
                source_passage_ids,
                edge.get("evidence_snippets", []),
                strict=False,
            )
            if passage_id in kept_passage_ids
        ]
        return trimmed

    annotations_by_id = {
        str(annotation["annotation_id"]): annotation for annotation in bundle.reviewed_annotations
    }
    kept_annotations = [
        annotations_by_id[annotation_id]
        for annotation_id in edge.get("support_annotation_ids", [])
        if annotation_id in annotations_by_id
        and str(annotations_by_id[annotation_id]["source_passage_id"]) in kept_passage_ids
    ]
    if kept_annotations:
        trimmed["support_annotation_ids"] = [
            str(annotation["annotation_id"]) for annotation in kept_annotations
        ]
        trimmed["support_types"] = sorted(
            {str(annotation["support_type"]) for annotation in kept_annotations}
        )
        trimmed["evidence_snippets"] = [
            str(annotation["evidence_text"]) for annotation in kept_annotations
        ]
    return trimmed


def node_question_number(node_id: str) -> int | None:
    if node_id.startswith("st.ii-ii.q") and len(node_id) >= 12:
        try:
            return int(node_id.split(".q")[1][:3])
        except ValueError:
            return None
    return None


def edge_evidence_panel(
    bundle: CorpusAppBundle,
    edge_id: str,
    *,
    edge_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if edge_row is None:
        candidate_edges = candidate_relation_rows(bundle, question_id=None, center_concept=None)
        edge = next(
            edge
            for edge in [
                *bundle.reviewed_doctrinal_edges,
                *bundle.reviewed_structural_edges,
                *candidate_edges,
            ]
            if str(edge["edge_id"]) == edge_id
        )
    else:
        edge = edge_row
    supporting_annotations = [
        row
        for row in bundle.reviewed_annotations
        if row["annotation_id"] in edge.get("support_annotation_ids", [])
    ]
    supporting_passages = [
        {
            "passage_id": passage_id,
            "citation_label": bundle.passages[passage_id].citation_label,
            "text": bundle.passages[passage_id].text,
        }
        for passage_id in edge.get("source_passage_ids", [])
        if passage_id in bundle.passages
    ]
    return {
        "source_concept": edge["subject_label"],
        "relation_type": edge["relation_type"],
        "target_concept": edge["object_label"],
        "support_type": edge.get("support_types", []),
        "supporting_annotation_ids": edge.get("support_annotation_ids", []),
        "supporting_passage_ids": edge.get("source_passage_ids", []),
        "evidence_snippets": edge.get("evidence_snippets", []),
        "annotations": supporting_annotations,
        "passages": supporting_passages,
        "layer": edge["layer"],
    }


def theological_virtues_concept_page_data(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int = 1,
    end_question: int = 46,
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
    reviewed_annotations = [
        row
        for row in bundle.reviewed_annotations
        if row["source_passage_id"] in bundle.passages
        and bundle.passages[row["source_passage_id"]].part_id == "ii-ii"
        and start_question
        <= bundle.passages[row["source_passage_id"]].question_number
        <= end_question
        and concept_id in {row["subject_id"], row["object_id"]}
    ]
    supporting_passage_ids = []
    for row in reviewed_annotations:
        passage_id = str(row["source_passage_id"])
        if passage_id not in supporting_passage_ids:
            supporting_passage_ids.append(passage_id)
    for row in candidate_mentions:
        passage_id = str(row["passage_id"])
        if passage_id not in supporting_passage_ids:
            supporting_passage_ids.append(passage_id)
    related_questions = sorted(
        {
            bundle.passages[passage_id].question_number
            for passage_id in supporting_passage_ids
            if passage_id in bundle.passages
        }
    )
    concept = bundle.registry[concept_id]
    return {
        "concept": concept.model_dump(mode="json"),
        "reviewed_incident_edges": reviewed_edges,
        "editorial_correspondences": editorial_edges,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
        "top_supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in supporting_passage_ids[:10]
        ],
        "related_questions": related_questions,
        "unresolved_disambiguation_notes": concept.disambiguation_notes,
    }
