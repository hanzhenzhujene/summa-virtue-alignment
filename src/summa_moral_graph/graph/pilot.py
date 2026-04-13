from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar, cast

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
from ..models.pilot import PilotRelationType
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_pilot_graph_artifacts() -> dict[str, int]:
    """Build pilot node and edge exports plus GraphML artifacts."""

    registry = {
        record.concept_id: record
        for record in _load_records(
            GOLD_DIR / "pilot_concept_registry.jsonl",
            ConceptRegistryRecord,
        )
    }
    structural_annotations = _load_records(
        GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_annotations = _load_records(
        GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    questions, articles, passages = load_pilot_context()

    structural_edges = aggregate_edges(structural_annotations)
    doctrinal_edges = aggregate_edges(doctrinal_annotations)
    structural_edges.extend(build_contains_edges(questions, articles, passages))
    structural_edges.sort(key=lambda record: record.edge_id)

    node_rows = build_node_rows(registry, questions, articles)
    write_jsonl(PROCESSED_DIR / "pilot_structural_edges.jsonl", structural_edges)
    write_jsonl(PROCESSED_DIR / "pilot_doctrinal_edges.jsonl", doctrinal_edges)
    write_csv_rows(
        PROCESSED_DIR / "pilot_nodes.csv",
        node_rows,
        ["node_id", "label", "node_type", "origin", "source_scope", "notes"],
    )
    write_csv_rows(
        PROCESSED_DIR / "pilot_doctrinal_edges.csv",
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
            "edge_layer",
            "support_annotation_ids",
            "source_passage_ids",
            "support_types",
            "evidence_snippets",
            "due_mode",
            "connected_virtues_cluster",
        ],
    )

    doctrinal_graph = build_graph(node_rows, doctrinal_edges)
    combined_graph = build_graph(node_rows, [*doctrinal_edges, *structural_edges])
    nx.write_graphml(doctrinal_graph, PROCESSED_DIR / "pilot_doctrinal.graphml")
    nx.write_graphml(combined_graph, PROCESSED_DIR / "pilot_combined.graphml")
    return {
        "concepts": len(registry),
        "doctrinal_edges": len(doctrinal_edges),
        "structural_edges": len(structural_edges),
        "nodes": len(node_rows),
    }


def load_pilot_context() -> tuple[
    dict[str, QuestionRecord],
    dict[str, ArticleRecord],
    dict[str, SegmentRecord],
]:
    """Load pilot question/article/segment records from interim exports."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if (record.part_id, record.question_number) in PILOT_SCOPE_SET
    }
    articles = {
        record.article_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_articles.jsonl", ArticleRecord)
        if record.question_id in questions
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
        if record.article_id in articles
    }
    return questions, articles, passages


def aggregate_edges(
    annotations: list[PilotAnnotationRecord],
) -> list[PilotEdgeRecord]:
    """Aggregate annotations into inspectable pilot edge bundles."""

    grouped: dict[
        tuple[str, str, PilotRelationType, str], list[PilotAnnotationRecord]
    ] = defaultdict(list)
    for annotation in annotations:
        grouped[
            (
                annotation.edge_layer,
                annotation.subject_id,
                annotation.relation_type,
                annotation.object_id,
            )
        ].append(annotation)

    edges: list[PilotEdgeRecord] = []
    for (_, subject_id, relation_type, object_id), records in sorted(grouped.items()):
        first = records[0]
        edges.append(
            PilotEdgeRecord(
                edge_id=f"edge.{subject_id}.{relation_type}.{object_id}".replace(" ", "_"),
                subject_id=subject_id,
                subject_label=first.subject_label,
                subject_type=first.subject_type,
                relation_type=relation_type,
                object_id=object_id,
                object_label=first.object_label,
                object_type=first.object_type,
                edge_layer=first.edge_layer,
                support_annotation_ids=[record.annotation_id for record in records],
                source_passage_ids=[record.source_passage_id for record in records],
                support_types=sorted({record.support_type for record in records}),
                evidence_snippets=[record.evidence_text for record in records],
            )
        )
    return edges


def build_contains_edges(
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
) -> list[PilotEdgeRecord]:
    """Build structural question->article containment edges."""

    edges: list[PilotEdgeRecord] = []
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        anchor = next(
            passages[segment_id]
            for segment_id in article.segment_ids
            if segment_id in passages
        )
        question = questions[article.question_id]
        edges.append(
            PilotEdgeRecord(
                edge_id=f"structural.{question.question_id}.contains.{article.article_id}",
                subject_id=question.question_id,
                subject_label=(
                    f"{anchor.part_id.upper()} q.{question.question_number} — "
                    f"{question.question_title}"
                ),
                subject_type="question",
                relation_type="contains_article",
                object_id=article.article_id,
                object_label=f"{article.citation_label} — {article.article_title}",
                object_type="article",
                edge_layer="structural",
                support_annotation_ids=[],
                source_passage_ids=[anchor.segment_id],
                support_types=["structural_editorial"],
                evidence_snippets=[anchor.text[:220]],
            )
        )
    return edges


def build_node_rows(
    registry: dict[str, ConceptRegistryRecord],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
) -> list[dict[str, str]]:
    """Build node table rows for concepts plus structural question/article nodes."""

    rows: list[dict[str, str]] = []
    for concept_record in sorted(registry.values(), key=lambda item: item.concept_id):
        rows.append(
            {
                "node_id": concept_record.concept_id,
                "label": concept_record.canonical_label,
                "node_type": concept_record.node_type,
                "origin": "registry",
                "source_scope": " | ".join(concept_record.source_scope),
                "notes": " | ".join(concept_record.notes),
            }
        )
    for question_record in sorted(questions.values(), key=lambda item: item.question_id):
        rows.append(
            {
                "node_id": question_record.question_id,
                "label": (
                    f"{question_record.part_id.upper()} "
                    f"q.{question_record.question_number} — "
                    f"{question_record.question_title}"
                ),
                "node_type": "question",
                "origin": "structural",
                "source_scope": question_record.question_id,
                "notes": "",
            }
        )
    for article_record in sorted(articles.values(), key=lambda item: item.article_id):
        rows.append(
            {
                "node_id": article_record.article_id,
                "label": (
                    f"{article_record.citation_label} — "
                    f"{article_record.article_title}"
                ),
                "node_type": "article",
                "origin": "structural",
                "source_scope": article_record.question_id,
                "notes": "",
            }
        )
    return rows


def build_graph(
    nodes: list[dict[str, str]],
    edges: list[PilotEdgeRecord],
) -> nx.MultiDiGraph:
    """Build a graph suitable for GraphML export and app inspection."""

    graph = nx.MultiDiGraph()
    for row in nodes:
        node_id = row["node_id"]
        graph.add_node(node_id, **{key: graph_attr_value(value) for key, value in row.items()})
    for edge in edges:
        graph.add_edge(
            edge.subject_id,
            edge.object_id,
            key=edge.edge_id,
            **{
                key: graph_attr_value(value)
                for key, value in edge.model_dump(mode="json").items()
            },
        )
    return graph


def write_csv_rows(
    path: Path,
    rows: Sequence[Mapping[str, object | None]],
    fieldnames: Sequence[str],
) -> None:
    """Write CSV rows in a stable column order."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def graph_attr_value(value: object) -> object:
    """Convert values to GraphML-safe scalar attributes."""

    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
