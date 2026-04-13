from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import networkx as nx
from pydantic import BaseModel

from ..models import (
    CandidateMentionRecord,
    CandidateRelationProposalRecord,
    PrudenceAnnotationRecord,
    PrudenceConceptRecord,
    PrudenceEdgeRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)


PRUDENCE_PRESETS = {
    "overview": {
        "label": "Prudence overview (QQ. 47–56)",
        "questions": list(range(47, 57)),
    },
    "core": {
        "label": "Prudence core",
        "questions": [47, 48],
    },
    "parts": {
        "label": "Prudence parts",
        "questions": [48, 49, 50, 51],
    },
    "gift_defects_counterfeit": {
        "label": "Gift / defects / counterfeit forms",
        "questions": [52, 53, 54, 55],
    },
}


@dataclass(frozen=True)
class PrudenceAppBundle:
    concepts: dict[str, PrudenceConceptRecord]
    doctrinal_annotations: list[PrudenceAnnotationRecord]
    editorial_annotations: list[PrudenceAnnotationRecord]
    candidate_mentions: list[CandidateMentionRecord]
    candidate_relations: list[CandidateRelationProposalRecord]
    passages: dict[str, SegmentRecord]
    doctrinal_edges: list[PrudenceEdgeRecord]
    editorial_edges: list[PrudenceEdgeRecord]
    node_rows: list[dict[str, str]]
    coverage: dict[str, object]
    validation: dict[str, object]


def load_prudence_bundle(root: Path | None = None) -> PrudenceAppBundle:
    """Load prudence tract artifacts for app use."""

    base = root or PROCESSED_DIR.parent.parent
    concepts = {
        concept_record.concept_id: concept_record
        for concept_record in _load_records(
            base / "data" / "gold" / "prudence_reviewed_concepts.jsonl",
            PrudenceConceptRecord,
        )
    }
    doctrinal_annotations = _load_records(
        base / "data" / "gold" / "prudence_reviewed_doctrinal_annotations.jsonl",
        PrudenceAnnotationRecord,
    )
    editorial_annotations = _load_records(
        base / "data" / "gold" / "prudence_reviewed_structural_editorial_annotations.jsonl",
        PrudenceAnnotationRecord,
    )
    candidate_mentions = _load_records(
        base / "data" / "candidate" / "prudence_candidate_mentions.jsonl",
        CandidateMentionRecord,
    )
    candidate_relations = _load_records(
        base / "data" / "candidate" / "prudence_candidate_relation_proposals.jsonl",
        CandidateRelationProposalRecord,
    )
    passages = {
        segment_record.segment_id: segment_record
        for segment_record in _load_records(
            base / "data" / "interim" / "summa_moral_segments.jsonl",
            SegmentRecord,
        )
        if segment_record.part_id == "ii-ii" and 47 <= segment_record.question_number <= 56
    }
    doctrinal_edges = _load_records(
        base / "data" / "processed" / "prudence_reviewed_doctrinal_edges.jsonl",
        PrudenceEdgeRecord,
    )
    editorial_edges = _load_records(
        base / "data" / "processed" / "prudence_reviewed_structural_editorial_edges.jsonl",
        PrudenceEdgeRecord,
    )
    with (base / "data" / "processed" / "prudence_nodes.csv").open("r", encoding="utf-8") as handle:
        node_rows = list(csv.DictReader(handle))
    coverage = json.loads(
        (base / "data" / "processed" / "prudence_coverage.json").read_text(encoding="utf-8")
    )
    validation = json.loads(
        (base / "data" / "processed" / "prudence_validation_report.json").read_text(
            encoding="utf-8"
        )
    )
    return PrudenceAppBundle(
        concepts=concepts,
        doctrinal_annotations=doctrinal_annotations,
        editorial_annotations=editorial_annotations,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
        passages=passages,
        doctrinal_edges=doctrinal_edges,
        editorial_edges=editorial_edges,
        node_rows=node_rows,
        coverage=coverage,
        validation=validation,
    )


def filter_edges_by_preset(
    bundle: PrudenceAppBundle,
    preset_name: str,
    *,
    include_editorial: bool = False,
) -> list[PrudenceEdgeRecord]:
    """Return edges filtered to an explicit prudence preset."""

    preset = PRUDENCE_PRESETS[preset_name]
    question_set = set(preset["questions"])
    edges = list(bundle.doctrinal_edges)
    if include_editorial:
        edges.extend(bundle.editorial_edges)
    return [edge for edge in edges if edge_question_numbers(edge, bundle.passages) & question_set]


def filter_edges_by_part_taxonomy(
    edges: list[PrudenceEdgeRecord],
    allowed_subtypes: set[str],
) -> list[PrudenceEdgeRecord]:
    """Filter prudence part relations by integral, subjective, or potential subtype."""

    if not allowed_subtypes:
        return edges
    filtered: list[PrudenceEdgeRecord] = []
    for edge in edges:
        if edge.part_taxonomy is None:
            filtered.append(edge)
            continue
        if edge.part_taxonomy in allowed_subtypes:
            filtered.append(edge)
    return filtered


def edge_evidence_panel(
    bundle: PrudenceAppBundle,
    edge_id: str,
) -> dict[str, object]:
    """Build an evidence-first panel payload for a prudence edge."""

    edge = next(
        record
        for record in [*bundle.doctrinal_edges, *bundle.editorial_edges]
        if record.edge_id == edge_id
    )
    annotations = [
        record
        for record in [*bundle.doctrinal_annotations, *bundle.editorial_annotations]
        if record.annotation_id in edge.support_annotation_ids
    ]
    passages = [
        bundle.passages[passage_id]
        for passage_id in edge.source_passage_ids
        if passage_id in bundle.passages
    ]
    return {
        "source_concept": edge.subject_label,
        "relation_type": edge.relation_type,
        "target_concept": edge.object_label,
        "support_type": edge.support_types,
        "supporting_annotation_ids": edge.support_annotation_ids,
        "supporting_passage_ids": edge.source_passage_ids,
        "evidence_snippets": edge.evidence_snippets,
        "part_subtype": edge.part_taxonomy,
        "annotations": [record.model_dump(mode="json") for record in annotations],
        "passages": [
            {
                "passage_id": record.segment_id,
                "citation_label": record.citation_label,
                "text": record.text,
            }
            for record in passages
        ],
    }


def concept_page_data(
    bundle: PrudenceAppBundle,
    concept_id: str,
) -> dict[str, object]:
    """Build coverage-aware concept page data for a single prudence concept."""

    concept = bundle.concepts[concept_id]
    reviewed_edges = [
        edge
        for edge in bundle.doctrinal_edges
        if edge.subject_id == concept_id or edge.object_id == concept_id
    ]
    editorial_edges = [
        edge
        for edge in bundle.editorial_edges
        if edge.subject_id == concept_id or edge.object_id == concept_id
    ]
    candidate_mentions = [
        mention
        for mention in bundle.candidate_mentions
        if mention.candidate_concept_id.endswith(concept_id.split(".")[-1])
        or concept.label.lower() in mention.note.lower()
    ]
    supporting_passages = []
    seen_passages: set[str] = set()
    related_questions: set[int] = set()
    for edge in reviewed_edges:
        for passage_id in edge.source_passage_ids:
            if passage_id in bundle.passages and passage_id not in seen_passages:
                passage = bundle.passages[passage_id]
                supporting_passages.append(
                    {
                        "passage_id": passage.segment_id,
                        "citation_label": passage.citation_label,
                        "text": passage.text,
                    }
                )
                seen_passages.add(passage_id)
                related_questions.add(passage.question_number)
    return {
        "concept": concept.model_dump(mode="json"),
        "reviewed_incident_edges": [edge.model_dump(mode="json") for edge in reviewed_edges],
        "editorial_correspondences": [edge.model_dump(mode="json") for edge in editorial_edges],
        "candidate_mentions": [record.model_dump(mode="json") for record in candidate_mentions],
        "top_supporting_passages": supporting_passages[:8],
        "related_questions": sorted(related_questions),
        "unresolved_disambiguation_notes": [
            note for note in [concept.disambiguation_note, concept.unresolved_note] if note
        ],
    }


def build_graph_for_edges(
    bundle: PrudenceAppBundle,
    edges: list[PrudenceEdgeRecord],
) -> nx.MultiDiGraph:
    """Build a focused NetworkX graph for filtered prudence edges."""

    node_lookup = {row["node_id"]: row for row in bundle.node_rows}
    node_ids = {edge.subject_id for edge in edges} | {edge.object_id for edge in edges}
    graph = nx.MultiDiGraph()
    for node_id in node_ids:
        graph.add_node(node_id, **node_lookup[node_id])
    for edge in edges:
        graph.add_edge(
            edge.subject_id,
            edge.object_id,
            key=edge.edge_id,
            **edge.model_dump(mode="json"),
        )
    return graph


def graph_html(graph: nx.MultiDiGraph, *, height: int = 760) -> str:
    """Render a prudence graph as embeddable HTML."""

    from pyvis.network import Network

    network = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#1f2933",
    )
    for node_id, attrs in graph.nodes(data=True):
        color = {
            "virtue": "#1d3557",
            "prudence_part": "#457b9d",
            "gift_holy_spirit": "#6d597a",
            "vice": "#9d0208",
            "defect": "#bc4749",
            "faculty": "#2a9d8f",
            "act": "#8d99ae",
            "end": "#e09f3e",
            "beatitude": "#6a994e",
            "taxonomy": "#8338ec",
            "article": "#7f5539",
            "question": "#5c677d",
        }.get(attrs.get("node_type", ""), "#6c757d")
        network.add_node(
            node_id,
            label=attrs.get("label", node_id),
            color=color,
            title=str(attrs.get("description", attrs.get("label", node_id))),
        )
    for source, target, edge_id, attrs in graph.edges(data=True, keys=True):
        network.add_edge(
            source,
            target,
            label=attrs.get("relation_type", ""),
            title=edge_id,
            arrows="to",
        )
    network.force_atlas_2based(
        gravity=-35,
        central_gravity=0.015,
        spring_length=180,
        spring_strength=0.08,
    )
    return str(network.generate_html(notebook=False))


def edge_question_numbers(edge: PrudenceEdgeRecord, passages: dict[str, SegmentRecord]) -> set[int]:
    """Resolve the question numbers touched by an edge's supporting passages."""

    return {
        passages[passage_id].question_number
        for passage_id in edge.source_passage_ids
        if passage_id in passages
    }


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
