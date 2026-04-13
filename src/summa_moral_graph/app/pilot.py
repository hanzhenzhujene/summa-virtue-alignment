from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import networkx as nx
from pydantic import BaseModel

from ..annotations.pilot_spec import PILOT_SCOPE_SET
from ..models import (
    ArticleRecord,
    ConceptRegistryRecord,
    PilotAnnotationRecord,
    PilotEdgeRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..ontology import load_alias_overrides, load_pilot_registry, search_registry
from ..utils.jsonl import load_jsonl
from ..utils.paths import PROCESSED_DIR
from ..utils.text import normalize_text

ModelT = TypeVar("ModelT", bound=BaseModel)

NODE_COLORS = {
    "virtue": "#1d3557",
    "vice": "#b00020",
    "sin_type": "#7f1d1d",
    "habit": "#6b7280",
    "passion": "#c05621",
    "act_type": "#6d597a",
    "law": "#006d77",
    "law_type": "#2a9d8f",
    "grace": "#3a86ff",
    "grace_type": "#4895ef",
    "beatitude": "#6a994e",
    "gift_holy_spirit": "#5a189a",
    "charism": "#7b2cbf",
    "precept": "#ff8800",
    "faculty": "#4d908e",
    "object": "#adb5bd",
    "doctrine": "#495057",
    "end": "#e09f3e",
    "question": "#5c677d",
    "article": "#7f5539",
}

EDGE_COLORS = {
    "structural": "#b0b7c3",
    "doctrinal": "#264653",
}


@dataclass(frozen=True)
class PilotAppBundle:
    registry: dict[str, ConceptRegistryRecord]
    structural_annotations: list[PilotAnnotationRecord]
    doctrinal_annotations: list[PilotAnnotationRecord]
    structural_edges: list[PilotEdgeRecord]
    doctrinal_edges: list[PilotEdgeRecord]
    passages: dict[str, SegmentRecord]
    questions: dict[str, QuestionRecord]
    articles: dict[str, ArticleRecord]
    node_rows: list[dict[str, str]]
    validation: dict[str, Any]
    alias_overrides: dict[str, dict[str, object]]


def load_pilot_bundle(root: Path | None = None) -> PilotAppBundle:
    """Load pilot artifacts for the app and tests."""

    base = root or PROCESSED_DIR.parent.parent
    registry = load_pilot_registry(base / "data" / "gold" / "pilot_concept_registry.jsonl")
    structural_annotations = _load_records(
        base / "data" / "gold" / "pilot_reviewed_structural_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_annotations = _load_records(
        base / "data" / "gold" / "pilot_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_edges = _load_records(
        base / "data" / "processed" / "pilot_structural_edges.jsonl",
        PilotEdgeRecord,
    )
    doctrinal_edges = _load_records(
        base / "data" / "processed" / "pilot_doctrinal_edges.jsonl",
        PilotEdgeRecord,
    )
    passages = {
        record.segment_id: record
        for record in _load_records(
            base / "data" / "interim" / "summa_moral_segments.jsonl",
            SegmentRecord,
        )
        if (record.part_id, record.question_number) in PILOT_SCOPE_SET
    }
    article_ids = {record.article_id for record in passages.values()}
    articles = {
        record.article_id: record
        for record in _load_records(
            base / "data" / "interim" / "summa_moral_articles.jsonl",
            ArticleRecord,
        )
        if record.article_id in article_ids
    }
    question_ids = {record.question_id for record in articles.values()}
    questions = {
        record.question_id: record
        for record in _load_records(
            base / "data" / "interim" / "summa_moral_questions.jsonl",
            QuestionRecord,
        )
        if record.question_id in question_ids
    }
    with (base / "data" / "processed" / "pilot_nodes.csv").open("r", encoding="utf-8") as handle:
        node_rows = list(csv.DictReader(handle))
    validation = json.loads(
        (base / "data" / "processed" / "validation_report.json").read_text(encoding="utf-8")
    )
    alias_overrides = load_alias_overrides(base / "data" / "gold" / "pilot_alias_overrides.yml")
    return PilotAppBundle(
        registry=registry,
        structural_annotations=structural_annotations,
        doctrinal_annotations=doctrinal_annotations,
        structural_edges=structural_edges,
        doctrinal_edges=doctrinal_edges,
        passages=passages,
        questions=questions,
        articles=articles,
        node_rows=node_rows,
        validation=validation,
        alias_overrides=alias_overrides,
    )


def passage_search(
    bundle: PilotAppBundle,
    *,
    query: str = "",
    part_id: str | None = None,
    question_id: str | None = None,
    article_id: str | None = None,
    segment_type: str | None = None,
) -> list[SegmentRecord]:
    """Filter pilot passages for the passage explorer."""

    normalized_query = normalize_text(query).casefold()
    records = sorted(
        bundle.passages.values(),
        key=lambda record: (
            record.part_id,
            record.question_number,
            record.article_number,
            record.segment_id,
        ),
    )
    filtered: list[SegmentRecord] = []
    for record in records:
        if part_id and record.part_id != part_id:
            continue
        if question_id and record.question_id != question_id:
            continue
        if article_id and record.article_id != article_id:
            continue
        if segment_type and record.segment_type != segment_type:
            continue
        if normalized_query and normalized_query not in normalize_text(record.text).casefold():
            continue
        filtered.append(record)
    return filtered


def annotations_for_passage(
    bundle: PilotAppBundle,
    passage_id: str,
) -> list[PilotAnnotationRecord]:
    """Return all reviewed annotations linked to a passage."""

    annotations = [
        record
        for record in [*bundle.structural_annotations, *bundle.doctrinal_annotations]
        if record.source_passage_id == passage_id
    ]
    return sorted(annotations, key=lambda record: (record.edge_layer, record.annotation_id))


def highlight_passage_text(text: str, annotations: list[PilotAnnotationRecord]) -> str:
    """Highlight evidence snippets from linked annotations inside passage text."""

    highlighted = html.escape(text)
    for snippet in sorted(
        {annotation.evidence_text for annotation in annotations if annotation.evidence_text},
        key=len,
        reverse=True,
    )[:8]:
        escaped = html.escape(snippet)
        if escaped in highlighted:
            highlighted = highlighted.replace(escaped, f"<mark>{escaped}</mark>", 1)
    return highlighted


def passage_source_link(record: SegmentRecord) -> str:
    """Build a stable source link for a passage row."""

    return f"{record.source_url}#article{record.article_number}"


def concept_search(
    bundle: PilotAppBundle,
    query: str,
    *,
    node_types: set[str] | None = None,
) -> list[ConceptRegistryRecord]:
    """Search the registry by canonical label or alias."""

    matches = search_registry(query, bundle.registry)
    if not node_types:
        return matches
    return [record for record in matches if record.node_type in node_types]


def concept_evidence_bundle(
    bundle: PilotAppBundle,
    concept_id: str,
    *,
    include_structural: bool = False,
) -> dict[str, Any]:
    """Aggregate concept-level evidence, grouped edges, and supporting passages."""

    concept = bundle.registry[concept_id]
    edges = list(bundle.doctrinal_edges)
    if include_structural:
        edges.extend(bundle.structural_edges)
    incident_edges = [
        edge
        for edge in edges
        if edge.subject_id == concept_id or edge.object_id == concept_id
    ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    supporting_passages: list[dict[str, str]] = []
    seen_passages: set[str] = set()
    related_questions: set[str] = set()
    for edge in incident_edges:
        grouped[edge.relation_type].append(edge.model_dump(mode="json"))
        for passage_id in edge.source_passage_ids:
            if passage_id in bundle.passages and passage_id not in seen_passages:
                passage = bundle.passages[passage_id]
                supporting_passages.append(
                    {
                        "passage_id": passage.segment_id,
                        "citation_label": passage.citation_label,
                        "source_link": passage_source_link(passage),
                        "text": passage.text,
                    }
                )
                seen_passages.add(passage_id)
                related_questions.add(passage.question_id)
    supporting_passages.sort(key=lambda row: row["citation_label"])
    return {
        "concept": concept.model_dump(mode="json"),
        "grouped_edges": {key: value for key, value in sorted(grouped.items())},
        "supporting_passages": supporting_passages[:12],
        "related_questions": [
            bundle.questions[item].question_title
            for item in sorted(related_questions)
        ],
    }


def edge_evidence_bundle(
    bundle: PilotAppBundle,
    edge_id: str,
) -> dict[str, Any]:
    """Return a full evidence bundle for a single doctrinal or structural edge."""

    edge = next(
        record
        for record in [*bundle.doctrinal_edges, *bundle.structural_edges]
        if record.edge_id == edge_id
    )
    annotations = [
        record
        for record in [*bundle.structural_annotations, *bundle.doctrinal_annotations]
        if record.annotation_id in edge.support_annotation_ids
    ]
    passages = [
        bundle.passages[passage_id]
        for passage_id in edge.source_passage_ids
        if passage_id in bundle.passages
    ]
    return {
        "edge": edge.model_dump(mode="json"),
        "annotations": [record.model_dump(mode="json") for record in annotations],
        "passages": [
            {
                "passage_id": record.segment_id,
                "citation_label": record.citation_label,
                "source_link": passage_source_link(record),
                "text": record.text,
            }
            for record in passages
        ],
    }


def filter_edges(
    bundle: PilotAppBundle,
    *,
    relation_types: set[str] | None = None,
    node_types: set[str] | None = None,
    include_structural: bool = False,
    evidence_only_doctrinal: bool = True,
    center_concept: str | None = None,
    question_id: str | None = None,
) -> list[PilotEdgeRecord]:
    """Filter edges for the graph view and concept explorer."""

    edges = list(bundle.doctrinal_edges)
    if include_structural:
        edges.extend(bundle.structural_edges)

    filtered: list[PilotEdgeRecord] = []
    for edge in edges:
        if (
            evidence_only_doctrinal
            and edge.edge_layer == "doctrinal"
            and not edge.source_passage_ids
        ):
            continue
        if relation_types and edge.relation_type not in relation_types:
            continue
        if node_types and (
            edge.subject_type not in node_types
            or edge.object_type not in node_types
        ):
            continue
        if center_concept and center_concept not in {edge.subject_id, edge.object_id}:
            continue
        if question_id:
            touched_questions = {
                bundle.passages[passage_id].question_id
                for passage_id in edge.source_passage_ids
                if passage_id in bundle.passages
            }
            if question_id not in touched_questions and edge.subject_id != question_id:
                continue
        filtered.append(edge)
    return sorted(filtered, key=lambda record: (record.edge_layer, record.edge_id))


def build_graph_for_edges(
    bundle: PilotAppBundle,
    edges: list[PilotEdgeRecord],
) -> nx.MultiDiGraph:
    """Build an inspectable graph for the current filtered edge set."""

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
    """Render a pyvis graph with readable labels and edge coloring."""

    from pyvis.network import Network

    network = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#1f2933",
    )
    for node_id, attrs in graph.nodes(data=True):
        node_type = attrs.get("node_type", "")
        label = str(attrs.get("label", node_id))
        if node_type == "article":
            label = label.split(" — ", 1)[0]
        network.add_node(
            node_id,
            label=label,
            color=NODE_COLORS.get(str(node_type), "#6c757d"),
            title=str(attrs.get("notes", attrs.get("label", node_id))),
        )
    for source, target, edge_id, attrs in graph.edges(data=True, keys=True):
        network.add_edge(
            source,
            target,
            label=str(attrs.get("relation_type", "")),
            title=edge_id,
            color=EDGE_COLORS.get(str(attrs.get("edge_layer", "")), "#6c757d"),
            arrows="to",
        )
    network.force_atlas_2based(
        gravity=-38,
        central_gravity=0.02,
        spring_length=185,
        spring_strength=0.08,
    )
    return str(network.generate_html(notebook=False))


def stats_payload(bundle: PilotAppBundle) -> dict[str, Any]:
    """Compute counts and rankings for the stats page."""

    concept_type_counts = Counter(record.node_type for record in bundle.registry.values())
    relation_counts = Counter(record.relation_type for record in bundle.doctrinal_annotations)
    unique_passages = {
        record.source_passage_id
        for record in [*bundle.structural_annotations, *bundle.doctrinal_annotations]
    }
    evidence_counts: Counter[str] = Counter()
    for edge in bundle.doctrinal_edges:
        for concept_id in (edge.subject_id, edge.object_id):
            if concept_id.startswith("concept."):
                evidence_counts[concept_id] += len(set(edge.source_passage_ids))
    top_concepts = [
        {
            "concept_id": concept_id,
            "label": bundle.registry[concept_id].canonical_label,
            "evidence_count": count,
        }
        for concept_id, count in evidence_counts.most_common(10)
    ]
    return {
        "concept_type_counts": dict(sorted(concept_type_counts.items())),
        "annotation_relation_counts": dict(sorted(relation_counts.items())),
        "unique_passages_cited": len(unique_passages),
        "top_concepts_by_evidence": top_concepts,
        "structural_edge_count": len(bundle.structural_edges),
        "doctrinal_edge_count": len(bundle.doctrinal_edges),
        "concepts_with_notes": sum(1 for record in bundle.registry.values() if record.notes),
        "alias_collision_count": len(bundle.validation.get("alias_collisions", [])),
    }


def graph_legends() -> dict[str, dict[str, str]]:
    """Expose node and edge legends for the graph page."""

    return {"node_colors": NODE_COLORS, "edge_colors": EDGE_COLORS}


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
