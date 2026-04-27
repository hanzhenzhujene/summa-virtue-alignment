from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, TypeVar, cast

import networkx as nx
from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.religion_tract_spec import (
    RELIGION_TRACT_MAX_QUESTION,
    RELIGION_TRACT_MIN_QUESTION,
)
from ..models import (
    ArticleRecord,
    CorpusConceptRecord,
    PilotAnnotationRecord,
    PilotRelationType,
    QuestionRecord,
    ReligionTractEdgeRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)
ReviewLayer = Literal["reviewed_doctrinal", "reviewed_structural_editorial"]


def build_religion_tract_graph_artifacts() -> dict[str, int]:
    """Build religion-tract node and edge exports."""

    doctrinal_annotations = dedupe_annotations(
        [
            *load_pilot_annotations(edge_layer="doctrinal"),
            *_load_records(
                GOLD_DIR / "religion_tract_reviewed_doctrinal_annotations.jsonl",
                PilotAnnotationRecord,
            ),
        ]
    )
    structural_editorial_annotations = dedupe_annotations(
        [
            *load_pilot_annotations(edge_layer="structural"),
            *_load_records(
                GOLD_DIR / "religion_tract_reviewed_structural_editorial_annotations.jsonl",
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
        PROCESSED_DIR / "religion_tract_reviewed_doctrinal_edges.jsonl",
        doctrinal_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "religion_tract_reviewed_structural_editorial_edges.jsonl",
        structural_editorial_edges,
    )
    write_jsonl(PROCESSED_DIR / "religion_tract_structural_edges.jsonl", structural_edges)
    write_csv_rows(
        PROCESSED_DIR / "religion_tract_nodes.csv",
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
        PROCESSED_DIR / "religion_tract_reviewed_doctrinal_edges.csv",
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
        PROCESSED_DIR / "religion_tract_reviewed_doctrinal.graphml",
    )
    nx.write_graphml(
        combined_graph,
        PROCESSED_DIR / "religion_tract_reviewed_with_structural.graphml",
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
        and RELIGION_TRACT_MIN_QUESTION
        <= int(annotation.source_passage_id.split(".q")[1][:3])
        <= RELIGION_TRACT_MAX_QUESTION
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
        if record.part_id == "ii-ii"
        and RELIGION_TRACT_MIN_QUESTION <= record.question_number <= RELIGION_TRACT_MAX_QUESTION
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
    reviewed_path = GOLD_DIR / "religion_tract_reviewed_concepts.jsonl"
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
    review_layer: ReviewLayer,
) -> list[ReligionTractEdgeRecord]:
    grouped: dict[tuple[str, PilotRelationType, str], list[PilotAnnotationRecord]] = defaultdict(
        list
    )
    for annotation in annotations:
        grouped[(annotation.subject_id, annotation.relation_type, annotation.object_id)].append(
            annotation
        )

    edges: list[ReligionTractEdgeRecord] = []
    for (subject_id, relation_type, object_id), records in sorted(grouped.items()):
        first = records[0]
        edges.append(
            ReligionTractEdgeRecord(
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
) -> list[ReligionTractEdgeRecord]:
    edges: list[ReligionTractEdgeRecord] = []
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        anchor_passage = next(
            passages[segment_id] for segment_id in article.segment_ids if segment_id in passages
        )
        question = questions[article.question_id]
        edges.append(
            ReligionTractEdgeRecord(
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
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for concept in concepts.values():
        rows.append(
            {
                "node_id": str(concept["concept_id"]),
                "label": str(concept["canonical_label"]),
                "node_type": str(concept["node_type"]),
                "registry_status": str(concept.get("registry_status", "reviewed_seed")),
                "description": str(concept["description"]),
                "notes": " | ".join(
                    str(note) for note in cast(list[object], concept.get("notes", []))
                ),
            }
        )
    for question in questions.values():
        rows.append(
            {
                "node_id": question.question_id,
                "label": f"II-II q.{question.question_number}",
                "node_type": "question",
                "registry_status": "structural",
                "description": "Structural question node for the religion tract.",
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
                "description": "Structural article node for the religion tract.",
                "notes": "",
            }
        )
    rows.sort(key=lambda row: str(row["node_id"]))
    return rows


def build_graph(
    node_rows: Sequence[Mapping[str, object]],
    edge_rows: Sequence[ReligionTractEdgeRecord],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for row in node_rows:
        graph.add_node(
            str(row["node_id"]),
            **{key: graph_attr_value(value) for key, value in row.items()},
        )
    for edge in edge_rows:
        payload = edge.model_dump(mode="json")
        graph.add_edge(
            edge.subject_id,
            edge.object_id,
            key=edge.edge_id,
            **{key: graph_attr_value(value) for key, value in payload.items()},
        )
    return graph


def write_csv_rows(
    path: Path,
    rows: Sequence[Mapping[str, object | None]],
    fieldnames: Sequence[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serialized = dict(row)
            for field in fieldnames:
                value = serialized.get(field)
                if isinstance(value, list):
                    serialized[field] = json_dumps(value)
            writer.writerow(serialized)


def json_dumps(value: object) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]


def graph_attr_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value
