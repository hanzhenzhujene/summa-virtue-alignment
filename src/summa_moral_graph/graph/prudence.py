from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar, cast

import networkx as nx
from pydantic import BaseModel

from ..models import (
    ArticleRecord,
    PrudenceAnnotationRecord,
    PrudenceConceptRecord,
    PrudenceEdgeRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..models.prudence import PrudenceRelationType
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_prudence_graph_artifacts() -> dict[str, int]:
    """Build prudence-specific node, edge, and graph exports."""

    concepts = {
        concept_record.concept_id: concept_record
        for concept_record in _load_records(
            GOLD_DIR / "prudence_reviewed_concepts.jsonl",
            PrudenceConceptRecord,
        )
    }
    doctrinal_annotations = _load_records(
        GOLD_DIR / "prudence_reviewed_doctrinal_annotations.jsonl",
        PrudenceAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "prudence_reviewed_structural_editorial_annotations.jsonl",
        PrudenceAnnotationRecord,
    )
    questions = {
        question_record.question_id: question_record
        for question_record in _load_records(
            INTERIM_DIR / "summa_moral_questions.jsonl",
            QuestionRecord,
        )
        if question_record.part_id == "ii-ii" and 47 <= question_record.question_number <= 56
    }
    articles = {
        article_record.article_id: article_record
        for article_record in _load_records(
            INTERIM_DIR / "summa_moral_articles.jsonl",
            ArticleRecord,
        )
        if article_record.question_id in questions
    }
    passages = {
        segment_record.segment_id: segment_record
        for segment_record in _load_records(
            INTERIM_DIR / "summa_moral_segments.jsonl",
            SegmentRecord,
        )
        if segment_record.article_id in articles
    }

    doctrinal_edges = aggregate_edges(doctrinal_annotations, concepts)
    editorial_edges = aggregate_edges(structural_editorial_annotations, concepts)
    structural_edges = build_structural_edges(questions, articles, passages)

    nodes = build_node_rows(concepts, questions, articles)
    write_jsonl(PROCESSED_DIR / "prudence_reviewed_doctrinal_edges.jsonl", doctrinal_edges)
    write_jsonl(
        PROCESSED_DIR / "prudence_reviewed_structural_editorial_edges.jsonl",
        editorial_edges,
    )
    write_jsonl(PROCESSED_DIR / "prudence_structural_edges.jsonl", structural_edges)
    write_csv_rows(
        PROCESSED_DIR / "prudence_nodes.csv",
        nodes,
        [
            "node_id",
            "label",
            "node_type",
            "review_status",
            "part_taxonomy",
            "description",
            "disambiguation_note",
        ],
    )
    write_csv_rows(
        PROCESSED_DIR / "prudence_reviewed_doctrinal_edges.csv",
        [
            cast(dict[str, object | None], edge_record.model_dump(mode="json"))
            for edge_record in doctrinal_edges
        ],
        [
            "edge_id",
            "subject_id",
            "subject_label",
            "subject_type",
            "relation_type",
            "object_id",
            "object_label",
            "object_type",
            "support_annotation_ids",
            "source_passage_ids",
            "support_types",
            "evidence_snippets",
            "review_layer",
            "part_taxonomy",
        ],
    )

    doctrinal_graph = build_graph(nodes, doctrinal_edges)
    combined_graph = build_graph(nodes, doctrinal_edges + structural_edges)
    nx.write_graphml(doctrinal_graph, PROCESSED_DIR / "prudence_reviewed_doctrinal.graphml")
    nx.write_graphml(combined_graph, PROCESSED_DIR / "prudence_reviewed_with_structural.graphml")
    return {
        "nodes": len(nodes),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
        "reviewed_structural_editorial_edges": len(editorial_edges),
        "structural_edges": len(structural_edges),
    }


def aggregate_edges(
    annotations: list[PrudenceAnnotationRecord],
    concepts: dict[str, PrudenceConceptRecord],
) -> list[PrudenceEdgeRecord]:
    """Aggregate reviewed annotations into inspectable edge records."""

    grouped: dict[tuple[str, PrudenceRelationType, str], list[PrudenceAnnotationRecord]] = (
        defaultdict(list)
    )
    for annotation in annotations:
        grouped[(annotation.subject_id, annotation.relation_type, annotation.object_id)].append(
            annotation
        )

    edges: list[PrudenceEdgeRecord] = []
    for (subject_id, relation_type, object_id), records in sorted(grouped.items()):
        first = records[0]
        subject_concept = concepts.get(subject_id)
        subject_part = subject_concept.part_taxonomy if subject_concept else None
        edges.append(
            PrudenceEdgeRecord(
                edge_id=f"edge.{subject_id}.{relation_type}.{object_id}".replace(" ", "_"),
                subject_id=subject_id,
                subject_label=first.subject_label,
                subject_type=first.subject_type,
                relation_type=relation_type,
                object_id=object_id,
                object_label=first.object_label,
                object_type=first.object_type,
                support_annotation_ids=[record.annotation_id for record in records],
                source_passage_ids=[record.source_passage_id for record in records],
                support_types=sorted({record.support_type for record in records}),
                evidence_snippets=[record.evidence_text for record in records],
                review_layer=(
                    "reviewed_structural_editorial"
                    if all(record.support_type == "structural_editorial" for record in records)
                    else "reviewed_doctrinal"
                ),
                part_taxonomy=subject_part if relation_type.endswith("_part_of") else None,
            )
        )
    return edges


def build_structural_edges(
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
) -> list[PrudenceEdgeRecord]:
    """Build separate structural article-question edges."""

    edges: list[PrudenceEdgeRecord] = []
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        anchor_passage = next(
            passages[segment_id] for segment_id in article.segment_ids if segment_id in passages
        )
        question = questions[article.question_id]
        edges.append(
            PrudenceEdgeRecord(
                edge_id=f"structural.{article.article_id}.part_of.{question.question_id}",
                subject_id=article.article_id,
                subject_label=f"{article.citation_label} — {article.article_title}",
                subject_type="article",
                relation_type="part_of",
                object_id=question.question_id,
                object_label=f"II-II q.{question.question_number} — {question.question_title}",
                object_type="question",
                support_annotation_ids=[],
                source_passage_ids=[anchor_passage.segment_id],
                support_types=["structural_editorial"],
                evidence_snippets=[anchor_passage.text[:220]],
                review_layer="structural",
                part_taxonomy=None,
            )
        )
    return edges


def build_node_rows(
    concepts: dict[str, PrudenceConceptRecord],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
) -> list[dict[str, str | None]]:
    """Build node rows for concept and structural nodes."""

    rows: list[dict[str, str | None]] = []
    for concept_record in sorted(concepts.values(), key=lambda item: item.concept_id):
        rows.append(
            {
                "node_id": concept_record.concept_id,
                "label": concept_record.label,
                "node_type": concept_record.node_type,
                "review_status": concept_record.review_status,
                "part_taxonomy": concept_record.part_taxonomy,
                "description": concept_record.description,
                "disambiguation_note": concept_record.disambiguation_note,
            }
        )
    for question_record in sorted(questions.values(), key=lambda item: item.question_id):
        rows.append(
            {
                "node_id": question_record.question_id,
                "label": (
                    f"II-II q.{question_record.question_number} — {question_record.question_title}"
                ),
                "node_type": "question",
                "review_status": "structural",
                "part_taxonomy": None,
                "description": "Structural question node for the prudence tract.",
                "disambiguation_note": None,
            }
        )
    for article_record in sorted(articles.values(), key=lambda item: item.article_id):
        rows.append(
            {
                "node_id": article_record.article_id,
                "label": (f"{article_record.citation_label} — {article_record.article_title}"),
                "node_type": "article",
                "review_status": "structural",
                "part_taxonomy": None,
                "description": "Structural article node for the prudence tract.",
                "disambiguation_note": None,
            }
        )
    return rows


def build_graph(
    nodes: list[dict[str, str | None]],
    edges: list[PrudenceEdgeRecord],
) -> nx.MultiDiGraph:
    """Build a NetworkX graph from node and edge rows."""

    graph = nx.MultiDiGraph()
    for row in nodes:
        node_id = cast(str, row["node_id"])
        graph.add_node(node_id, **{key: graph_attr_value(value) for key, value in row.items()})
    for edge in edges:
        graph.add_edge(
            edge.subject_id,
            edge.object_id,
            key=edge.edge_id,
            **{key: graph_attr_value(value) for key, value in edge.model_dump(mode="json").items()},
        )
    return graph


def write_csv_rows(
    path: Path,
    rows: Sequence[Mapping[str, object | None]],
    fieldnames: Sequence[str],
) -> None:
    """Write rows to CSV with a stable column order."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]


def graph_attr_value(value: object) -> object:
    """Convert values into GraphML-safe scalar attributes."""

    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value
