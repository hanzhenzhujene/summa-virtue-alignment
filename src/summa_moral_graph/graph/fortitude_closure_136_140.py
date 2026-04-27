from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, TypeVar, cast

import networkx as nx
from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.fortitude_closure_136_140_spec import (
    FORTITUDE_CLOSURE_136_140_MAX_QUESTION,
    FORTITUDE_CLOSURE_136_140_MIN_QUESTION,
    focus_tags_for_edge,
)
from ..models import (
    ArticleRecord,
    CorpusConceptRecord,
    FortitudeClosure136140EdgeRecord,
    FortitudeClosure136140Focus,
    PilotAnnotationRecord,
    PilotRelationType,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)
ReviewLayer = Literal["reviewed_doctrinal", "reviewed_structural_editorial"]
QUESTION_FOCUS: dict[int, FortitudeClosure136140Focus] = {
    136: "patience",
    137: "perseverance",
    138: "opposed_vice",
    139: "gift",
    140: "precept",
}


def build_fortitude_closure_136_140_graph_artifacts() -> dict[str, int]:
    """Build node and edge exports for the fortitude closure tract and synthesis."""

    doctrinal_annotations = _load_records(
        GOLD_DIR / "fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "fortitude_closure_136_140_reviewed_structural_editorial_annotations.jsonl",
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
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl",
        doctrinal_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_structural_editorial_edges.jsonl",
        structural_editorial_edges,
    )
    write_jsonl(
        PROCESSED_DIR / "fortitude_closure_136_140_structural_edges.jsonl",
        structural_edges,
    )
    write_csv_rows(
        PROCESSED_DIR / "fortitude_closure_136_140_nodes.csv",
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
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_doctrinal_edges.csv",
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
            "fortitude_closure_focus",
        ],
    )

    doctrinal_graph = build_graph(node_rows, doctrinal_edges)
    combined_graph = build_graph(
        node_rows,
        [*doctrinal_edges, *structural_editorial_edges, *structural_edges],
    )
    nx.write_graphml(
        doctrinal_graph,
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_doctrinal.graphml",
    )
    nx.write_graphml(
        combined_graph,
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_with_structural.graphml",
    )

    synthesis = build_fortitude_tract_synthesis_artifacts()
    return {
        "nodes": len(node_rows),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
        "reviewed_structural_editorial_edges": len(structural_editorial_edges),
        "structural_edges": len(structural_edges),
        "fortitude_synthesis_nodes": synthesis["nodes"],
        "fortitude_synthesis_edges": synthesis["edges"],
    }


def build_fortitude_tract_synthesis_artifacts() -> dict[str, int]:
    """Build doctrinal and optional editorial synthesis exports for fortitude material."""

    doctrinal_rows = list(
        load_jsonl(PROCESSED_DIR / "fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl")
    )
    doctrinal_rows.extend(
        load_jsonl(PROCESSED_DIR / "fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl")
    )
    editorial_rows = list(
        load_jsonl(
            PROCESSED_DIR / "fortitude_parts_129_135_reviewed_structural_editorial_edges.jsonl"
        )
    )
    editorial_rows.extend(
        load_jsonl(
            PROCESSED_DIR / "fortitude_closure_136_140_reviewed_structural_editorial_edges.jsonl"
        )
    )

    node_rows = merge_node_rows(
        [
            load_csv_rows(PROCESSED_DIR / "fortitude_parts_129_135_nodes.csv"),
            load_csv_rows(PROCESSED_DIR / "fortitude_closure_136_140_nodes.csv"),
        ]
    )
    doctrinal_graph = build_graph_from_rows(node_rows, doctrinal_rows)
    combined_graph = build_graph_from_rows(node_rows, [*doctrinal_rows, *editorial_rows])

    write_csv_rows(
        PROCESSED_DIR / "fortitude_tract_synthesis_nodes.csv",
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
        PROCESSED_DIR / "fortitude_tract_synthesis_edges.csv",
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
            "fortitude_parts_cluster",
            "fortitude_closure_focus",
        ],
    )
    nx.write_graphml(
        doctrinal_graph,
        PROCESSED_DIR / "fortitude_tract_synthesis.graphml",
    )
    nx.write_graphml(
        combined_graph,
        PROCESSED_DIR / "fortitude_tract_synthesis_with_editorial.graphml",
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
        and FORTITUDE_CLOSURE_136_140_MIN_QUESTION
        <= record.question_number
        <= FORTITUDE_CLOSURE_136_140_MAX_QUESTION
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
    for filename in (
        "fortitude_parts_129_135_reviewed_concepts.jsonl",
        "fortitude_closure_136_140_reviewed_concepts.jsonl",
    ):
        reviewed_path = GOLD_DIR / filename
        if not reviewed_path.exists():
            continue
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
) -> list[FortitudeClosure136140EdgeRecord]:
    grouped: dict[tuple[str, PilotRelationType, str], list[PilotAnnotationRecord]] = defaultdict(
        list
    )
    for annotation in annotations:
        grouped[
            (
                annotation.subject_id,
                annotation.relation_type,
                annotation.object_id,
            )
        ].append(annotation)

    edges: list[FortitudeClosure136140EdgeRecord] = []
    for (subject_id, relation_type, object_id), records in sorted(grouped.items()):
        first = records[0]
        focus_tags = {
            tag
            for record in records
            for tag in focus_tags_for_edge(
                record.subject_id,
                record.relation_type,
                record.object_id,
            )
        }
        if not focus_tags:
            focus_tags.update(
                QUESTION_FOCUS[passages[record.source_passage_id].question_number]
                for record in records
                if passages[record.source_passage_id].question_number in QUESTION_FOCUS
            )
        edges.append(
            FortitudeClosure136140EdgeRecord(
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
                fortitude_closure_focus=sorted(focus_tags),
            )
        )
    return edges


def build_contains_edges(
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
) -> list[FortitudeClosure136140EdgeRecord]:
    edges: list[FortitudeClosure136140EdgeRecord] = []
    for article in sorted(articles.values(), key=lambda record: record.article_id):
        anchor_passage = next(
            passages[segment_id] for segment_id in article.segment_ids if segment_id in passages
        )
        question = questions[article.question_id]
        edges.append(
            FortitudeClosure136140EdgeRecord(
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
                fortitude_closure_focus=focus_tags_for_edge(
                    question.question_id,
                    "contains_article",
                    article.article_id,
                ),
            )
        )
    return edges


def build_node_rows(
    concepts: Mapping[str, Mapping[str, object]],
    questions: Mapping[str, QuestionRecord],
    articles: Mapping[str, ArticleRecord],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for concept_id, payload in sorted(concepts.items()):
        rows.append(
            {
                "node_id": concept_id,
                "label": payload["canonical_label"],
                "node_type": payload["node_type"],
                "registry_status": payload.get("registry_status", "reviewed_seed"),
                "description": payload["description"],
                "notes": " | ".join(cast(list[str], payload.get("notes", []))),
            }
        )
    for question in sorted(questions.values(), key=lambda record: record.question_id):
        rows.append(
            {
                "node_id": question.question_id,
                "label": f"II-II q.{question.question_number} — {question.question_title}",
                "node_type": "question",
                "registry_status": "structural",
                "description": "Structural question node for the fortitude closure tract.",
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
                "description": "Structural article node for the fortitude closure tract.",
                "notes": "",
            }
        )
    return rows


def merge_node_rows(row_groups: Sequence[list[dict[str, object]]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for rows in row_groups:
        for row in rows:
            merged[str(row["node_id"])] = row
    return [merged[key] for key in sorted(merged)]


def build_graph(
    node_rows: Sequence[Mapping[str, object]],
    edges: Sequence[FortitudeClosure136140EdgeRecord],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for row in node_rows:
        graph.add_node(
            str(row["node_id"]),
            **{key: graph_attr_value(value) for key, value in row.items()},
        )
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


def build_graph_from_rows(
    node_rows: Sequence[Mapping[str, object]],
    edges: Sequence[Mapping[str, object]],
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for row in node_rows:
        graph.add_node(
            str(row["node_id"]),
            **{key: graph_attr_value(value) for key, value in row.items()},
        )
    for edge in edges:
        graph.add_edge(
            str(edge["subject_id"]),
            str(edge["object_id"]),
            key=str(edge["edge_id"]),
            **{key: graph_attr_value(value) for key, value in dict(edge).items()},
        )
    return graph


def write_csv_rows(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    fieldnames: Sequence[str],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def load_csv_rows(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [cast(dict[str, object], row) for row in csv.DictReader(handle)]


def graph_attr_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(str(item) for item in value)
    return value


def _load_records(path: Path, model: type[ModelT]) -> list[ModelT]:
    return [model.model_validate(payload) for payload in load_jsonl(path)]
