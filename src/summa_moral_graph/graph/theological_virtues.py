from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, TypeVar, cast

import networkx as nx
from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..models import (
    ArticleRecord,
    PilotAnnotationRecord,
    PilotRelationType,
    QuestionRecord,
    SegmentRecord,
    TheologicalVirtuesEdgeRecord,
)
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)
ReviewLayer = Literal["reviewed_doctrinal", "reviewed_structural_editorial"]


def build_theological_virtues_graph_artifacts() -> dict[str, int]:
    """Build theological-virtues tract node and edge exports."""

    doctrinal_annotations = dedupe_annotations(
        [
            *load_pilot_annotations(edge_layer="doctrinal"),
            *_load_records(
                GOLD_DIR / "theological_virtues_reviewed_doctrinal_annotations.jsonl",
                PilotAnnotationRecord,
            ),
        ]
    )
    structural_editorial_annotations = dedupe_annotations(
        [
            *load_pilot_annotations(edge_layer="structural"),
            *_load_records(
                GOLD_DIR / "theological_virtues_reviewed_structural_editorial_annotations.jsonl",
                PilotAnnotationRecord,
            ),
        ]
    )
    questions, articles, passages = load_tract_context()
    concepts = load_concepts_for_annotations(
        doctrinal_annotations + structural_editorial_annotations
    )

    doctrinal_edges = aggregate_edges(
        doctrinal_annotations,
        review_layer="reviewed_doctrinal",
    )
    structural_editorial_edges = aggregate_edges(
        structural_editorial_annotations,
        review_layer="reviewed_structural_editorial",
    )
    structural_edges = build_contains_edges(questions, articles, passages)
    node_rows = build_node_rows(concepts, questions, articles)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        PROCESSED_DIR / "theological_virtues_reviewed_doctrinal_edges.jsonl",
        doctrinal_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "theological_virtues_reviewed_structural_editorial_edges.jsonl",
        structural_editorial_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "theological_virtues_structural_edges.jsonl",
        structural_edges,
    )
    write_csv_rows(
        PROCESSED_DIR / "theological_virtues_nodes.csv",
        node_rows,
        [
            "node_id",
            "label",
            "node_type",
            "registry_status",
            "description",
            "notes",
        ],
    )
    write_csv_rows(
        PROCESSED_DIR / "theological_virtues_reviewed_doctrinal_edges.csv",
        [cast(dict[str, object | None], edge.model_dump(mode="json")) for edge in doctrinal_edges],
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
        ],
    )

    doctrinal_graph = build_graph(node_rows, doctrinal_edges)
    combined_graph = build_graph(
        node_rows,
        [*doctrinal_edges, *structural_editorial_edges, *structural_edges],
    )
    nx.write_graphml(
        doctrinal_graph,
        PROCESSED_DIR / "theological_virtues_reviewed_doctrinal.graphml",
    )
    nx.write_graphml(
        combined_graph,
        PROCESSED_DIR / "theological_virtues_reviewed_with_structural.graphml",
    )
    return {
        "nodes": len(node_rows),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
        "reviewed_structural_editorial_edges": len(structural_editorial_edges),
        "structural_edges": len(structural_edges),
    }


def load_pilot_annotations(*, edge_layer: str) -> list[PilotAnnotationRecord]:
    path = (
        GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl"
        if edge_layer == "doctrinal"
        else GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl"
    )
    return [
        annotation
        for annotation in _load_records(path, PilotAnnotationRecord)
        if annotation.source_passage_id.startswith("st.ii-ii.q")
        and 1 <= int(annotation.source_passage_id.split(".q")[1][:3]) <= 46
    ]


def dedupe_annotations(
    annotations: list[PilotAnnotationRecord],
) -> list[PilotAnnotationRecord]:
    seen: dict[str, PilotAnnotationRecord] = {}
    for annotation in annotations:
        seen[annotation.annotation_id] = annotation
    return sorted(seen.values(), key=lambda record: record.annotation_id)


def load_tract_context() -> tuple[
    dict[str, QuestionRecord],
    dict[str, ArticleRecord],
    dict[str, SegmentRecord],
]:
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii" and 1 <= record.question_number <= 46
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


def load_concepts_for_annotations(
    annotations: list[PilotAnnotationRecord],
) -> dict[str, dict[str, object]]:
    registry = build_corpus_registry()
    concept_ids = {
        node_id
        for annotation in annotations
        for node_id in (annotation.subject_id, annotation.object_id)
        if node_id.startswith("concept.")
    }
    return {
        concept_id: registry[concept_id].model_dump(mode="json")
        for concept_id in sorted(concept_ids)
    }


def aggregate_edges(
    annotations: list[PilotAnnotationRecord],
    *,
    review_layer: ReviewLayer,
) -> list[TheologicalVirtuesEdgeRecord]:
    grouped: dict[tuple[str, PilotRelationType, str], list[PilotAnnotationRecord]] = defaultdict(
        list
    )
    for annotation in annotations:
        grouped[(annotation.subject_id, annotation.relation_type, annotation.object_id)].append(
            annotation
        )

    edges: list[TheologicalVirtuesEdgeRecord] = []
    for (subject_id, relation_type, object_id), records in sorted(grouped.items()):
        first = records[0]
        edges.append(
            TheologicalVirtuesEdgeRecord(
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
                review_layer=review_layer,
            )
        )
    return edges


def build_contains_edges(
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
) -> list[TheologicalVirtuesEdgeRecord]:
    edges: list[TheologicalVirtuesEdgeRecord] = []
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        anchor_passage = next(
            passages[segment_id] for segment_id in article.segment_ids if segment_id in passages
        )
        question = questions[article.question_id]
        edges.append(
            TheologicalVirtuesEdgeRecord(
                edge_id=f"structural.{question.question_id}.contains.{article.article_id}",
                subject_id=question.question_id,
                subject_label=f"II-II q.{question.question_number} — {question.question_title}",
                subject_type="question",
                relation_type="contains_article",
                object_id=article.article_id,
                object_label=f"{article.citation_label} — {article.article_title}",
                object_type="article",
                support_annotation_ids=[],
                source_passage_ids=[anchor_passage.segment_id],
                support_types=["structural_editorial"],
                evidence_snippets=[anchor_passage.text[:220]],
                review_layer="structural",
            )
        )
    return edges


def build_node_rows(
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for concept_id, concept in sorted(concepts.items()):
        rows.append(
            {
                "node_id": concept_id,
                "label": str(concept["canonical_label"]),
                "node_type": str(concept["node_type"]),
                "registry_status": str(concept["registry_status"]),
                "description": str(concept["description"]),
                "notes": " | ".join(string_list_value(concept.get("notes"))),
            }
        )
    for question in sorted(questions.values(), key=lambda record: record.question_id):
        rows.append(
            {
                "node_id": question.question_id,
                "label": f"II-II q.{question.question_number} — {question.question_title}",
                "node_type": "question",
                "registry_status": "structural",
                "description": "Structural question node for the theological virtues tract.",
                "notes": "",
            }
        )
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        rows.append(
            {
                "node_id": article.article_id,
                "label": f"{article.citation_label} — {article.article_title}",
                "node_type": "article",
                "registry_status": "structural",
                "description": "Structural article node for the theological virtues tract.",
                "notes": "",
            }
        )
    return rows


def build_graph(
    nodes: list[dict[str, str]],
    edges: list[TheologicalVirtuesEdgeRecord],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for node in nodes:
        graph.add_node(
            node["node_id"],
            **{key: graph_attr_value(value) for key, value in node.items()},
        )
    for edge in edges:
        graph.add_edge(
            edge.subject_id,
            edge.object_id,
            key=edge.edge_id,
            **{key: graph_attr_value(value) for key, value in edge.model_dump(mode="json").items()},
        )
    return graph


def graph_attr_value(value: object) -> str:
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def write_csv_rows(
    path: Path,
    rows: Sequence[Mapping[str, object | None]],
    fieldnames: Sequence[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = {field: csv_value(row.get(field)) for field in fieldnames}
            writer.writerow(serialized)


def csv_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return str(value)


def string_list_value(value: object | None) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
