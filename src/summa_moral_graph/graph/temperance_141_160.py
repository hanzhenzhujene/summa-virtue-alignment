from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, TypeVar, cast

import networkx as nx
from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.temperance_141_160_spec import (
    TEMPERANCE_141_160_MAX_QUESTION,
    TEMPERANCE_141_160_MIN_QUESTION,
    cluster_for_question,
    focus_tags_for_edge,
)
from ..models import (
    ArticleRecord,
    CorpusConceptRecord,
    PilotAnnotationRecord,
    PilotRelationType,
    QuestionRecord,
    SegmentRecord,
    Temperance141160Cluster,
    Temperance141160EdgeRecord,
    Temperance141160Focus,
)
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)
ReviewLayer = Literal["reviewed_doctrinal", "reviewed_structural_editorial"]
TemperanceEdgeKey = tuple[
    str,
    PilotRelationType,
    str,
    Temperance141160Cluster,
    tuple[Temperance141160Focus, ...],
]


def build_temperance_141_160_graph_artifacts() -> dict[str, int]:
    """Build node and edge exports for the temperance 141-160 tract."""

    doctrinal_annotations = _load_records(
        GOLD_DIR / "temperance_141_160_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "temperance_141_160_reviewed_structural_editorial_annotations.jsonl",
        PilotAnnotationRecord,
    )
    questions, articles, passages = load_tract_context()
    concepts = load_concepts_for_annotations(
        doctrinal_annotations + structural_editorial_annotations
    )

    doctrinal_edges = aggregate_edges(
        doctrinal_annotations,
        passages=passages,
        review_layer="reviewed_doctrinal",
    )
    structural_editorial_edges = aggregate_edges(
        structural_editorial_annotations,
        passages=passages,
        review_layer="reviewed_structural_editorial",
    )
    structural_edges = build_contains_edges(questions, articles, passages)
    node_rows = build_node_rows(concepts, questions, articles)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(
        PROCESSED_DIR / "temperance_141_160_reviewed_doctrinal_edges.jsonl",
        doctrinal_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "temperance_141_160_reviewed_structural_editorial_edges.jsonl",
        structural_editorial_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "temperance_141_160_structural_edges.jsonl",
        structural_edges,
    )
    write_csv_rows(
        PROCESSED_DIR / "temperance_141_160_nodes.csv",
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
        PROCESSED_DIR / "temperance_141_160_reviewed_doctrinal_edges.csv",
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
            "temperance_cluster",
            "temperance_focus",
        ],
    )

    doctrinal_graph = build_graph(node_rows, doctrinal_edges)
    combined_graph = build_graph(
        node_rows,
        [*doctrinal_edges, *structural_editorial_edges, *structural_edges],
    )
    nx.write_graphml(
        doctrinal_graph,
        PROCESSED_DIR / "temperance_141_160_reviewed_doctrinal.graphml",
    )
    nx.write_graphml(
        combined_graph,
        PROCESSED_DIR / "temperance_141_160_reviewed_with_structural.graphml",
    )

    synthesis = build_temperance_phase1_synthesis_artifacts()
    return {
        "nodes": len(node_rows),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
        "reviewed_structural_editorial_edges": len(structural_editorial_edges),
        "structural_edges": len(structural_edges),
        "temperance_phase1_synthesis_nodes": synthesis["nodes"],
        "temperance_phase1_synthesis_edges": synthesis["edges"],
    }


def build_temperance_phase1_synthesis_artifacts() -> dict[str, int]:
    """Build doctrinal and optional editorial synthesis exports for QQ. 141-160."""

    doctrinal_rows = list(
        load_jsonl(PROCESSED_DIR / "temperance_141_160_reviewed_doctrinal_edges.jsonl")
    )
    editorial_rows = list(
        load_jsonl(PROCESSED_DIR / "temperance_141_160_reviewed_structural_editorial_edges.jsonl")
    )
    node_rows = load_csv_rows(PROCESSED_DIR / "temperance_141_160_nodes.csv")

    doctrinal_graph = build_graph_from_rows(node_rows, doctrinal_rows)
    combined_graph = build_graph_from_rows(node_rows, [*doctrinal_rows, *editorial_rows])

    write_csv_rows(
        PROCESSED_DIR / "temperance_phase1_synthesis_nodes.csv",
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
        PROCESSED_DIR / "temperance_phase1_synthesis_edges.csv",
        doctrinal_rows,
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
            "temperance_cluster",
            "temperance_focus",
        ],
    )
    nx.write_graphml(
        doctrinal_graph,
        PROCESSED_DIR / "temperance_phase1_synthesis.graphml",
    )
    nx.write_graphml(
        combined_graph,
        PROCESSED_DIR / "temperance_phase1_synthesis_with_editorial.graphml",
    )
    return {"nodes": len(node_rows), "edges": len(doctrinal_rows)}


def load_tract_context() -> tuple[
    dict[str, QuestionRecord],
    dict[str, ArticleRecord],
    dict[str, SegmentRecord],
]:
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_141_160_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_141_160_MAX_QUESTION
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
    reviewed_path = GOLD_DIR / "temperance_141_160_reviewed_concepts.jsonl"
    if reviewed_path.exists():
        for payload in load_jsonl(reviewed_path):
            concept = CorpusConceptRecord.model_validate(payload)
            registry[concept.concept_id] = concept
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
    passages: dict[str, SegmentRecord],
    review_layer: ReviewLayer,
) -> list[Temperance141160EdgeRecord]:
    grouped: dict[TemperanceEdgeKey, list[PilotAnnotationRecord]] = defaultdict(list)
    for annotation in annotations:
        question_number = passages[annotation.source_passage_id].question_number
        cluster = cluster_for_question(question_number)
        focus = tuple(
            focus_tags_for_edge(
                question_number,
                annotation.subject_id,
                annotation.relation_type,
                annotation.object_id,
            )
        )
        grouped[
            (
                annotation.subject_id,
                annotation.relation_type,
                annotation.object_id,
                cluster,
                focus,
            )
        ].append(annotation)

    edges: list[Temperance141160EdgeRecord] = []
    for key, records in sorted(grouped.items(), key=lambda item: item[0]):
        subject_id, relation_type, object_id, cluster, focus = key
        first = records[0]
        edges.append(
            Temperance141160EdgeRecord(
                edge_id=(
                    f"edge.{cluster}.{subject_id}.{relation_type}.{object_id}"
                ).replace(" ", "_"),
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
                temperance_cluster=cluster,
                temperance_focus=list(focus),
            )
        )
    return edges


def build_contains_edges(
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
) -> list[Temperance141160EdgeRecord]:
    edges: list[Temperance141160EdgeRecord] = []
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        anchor_passage = next(
            passages[segment_id] for segment_id in article.segment_ids if segment_id in passages
        )
        question = questions[article.question_id]
        edges.append(
            Temperance141160EdgeRecord(
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
                support_types=[],
                evidence_snippets=[],
                review_layer="structural",
                temperance_cluster=cluster_for_question(question.question_number),
                temperance_focus=[],
            )
        )
    return edges


def build_node_rows(
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for concept_id, payload in concepts.items():
        notes_value = payload.get("notes")
        notes = notes_value if isinstance(notes_value, list) else []
        rows.append(
            {
                "node_id": concept_id,
                "label": payload["canonical_label"],
                "node_type": payload["node_type"],
                "registry_status": payload["registry_status"],
                "description": payload["description"],
                "notes": " | ".join(str(note) for note in notes),
            }
        )
    for question in questions.values():
        rows.append(
            {
                "node_id": question.question_id,
                "label": f"II-II q.{question.question_number}",
                "node_type": "question",
                "registry_status": "structural",
                "description": question.question_title,
                "notes": "",
            }
        )
    for article in articles.values():
        rows.append(
            {
                "node_id": article.article_id,
                "label": article.citation_label,
                "node_type": "article",
                "registry_status": "structural",
                "description": "Structural article node for the temperance 141-160 tract.",
                "notes": "",
            }
        )
    rows.sort(key=lambda row: str(row["node_id"]))
    return rows


def build_graph(
    node_rows: Sequence[Mapping[str, object]],
    edge_rows: Sequence[Temperance141160EdgeRecord],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for row in node_rows:
        node_id = str(row["node_id"])
        graph.add_node(
            node_id,
            **{key: graph_attr_value(value) for key, value in row.items()},
        )
    for edge in edge_rows:
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


def build_graph_from_rows(
    node_rows: Sequence[Mapping[str, object]],
    edge_rows: Sequence[Mapping[str, object]],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for row in node_rows:
        node_id = str(row["node_id"])
        graph.add_node(node_id, **{key: graph_attr_value(value) for key, value in row.items()})
    for row in edge_rows:
        graph.add_edge(
            str(row["subject_id"]),
            str(row["object_id"]),
            key=str(row["edge_id"]),
            **{key: graph_attr_value(value) for key, value in row.items()},
        )
    return graph


def load_csv_rows(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


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
            writer.writerow(row)


def graph_attr_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
