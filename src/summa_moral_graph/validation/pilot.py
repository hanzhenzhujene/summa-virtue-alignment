from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..annotations.pilot_spec import PILOT_SCOPE_SET
from ..models import (
    ArticleRecord,
    ConceptRegistryRecord,
    PilotAnnotationRecord,
    PilotEdgeRecord,
    PilotValidationReport,
    QuestionRecord,
    SegmentRecord,
)
from ..ontology import find_alias_collisions, load_alias_overrides
from ..utils.jsonl import load_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_pilot_validation_artifacts() -> dict[str, int | str]:
    """Validate pilot annotations and graph exports, then write report artifacts."""

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
    structural_edges = _load_records(
        PROCESSED_DIR / "pilot_structural_edges.jsonl",
        PilotEdgeRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "pilot_doctrinal_edges.jsonl",
        PilotEdgeRecord,
    )
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

    report = validate_pilot_artifacts(
        registry=registry,
        structural_annotations=structural_annotations,
        doctrinal_annotations=doctrinal_annotations,
        structural_edges=structural_edges,
        doctrinal_edges=doctrinal_edges,
        passages=passages,
        articles=articles,
        questions=questions,
    )
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "validation_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    write_validation_summary(report, REPO_ROOT / "docs" / "validation_summary.md")
    return {
        "status": report.status,
        "passages": report.passage_count,
        "concepts": report.concept_count,
        "annotations": report.annotation_count,
        "doctrinal_edges": report.doctrinal_edge_count,
        "structural_edges": report.structural_edge_count,
    }


def validate_pilot_artifacts(
    *,
    registry: dict[str, ConceptRegistryRecord],
    structural_annotations: list[PilotAnnotationRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_edges: list[PilotEdgeRecord],
    doctrinal_edges: list[PilotEdgeRecord],
    passages: dict[str, SegmentRecord],
    articles: dict[str, ArticleRecord],
    questions: dict[str, QuestionRecord],
) -> PilotValidationReport:
    """Run pilot QA checks over registry, annotations, and graph exports."""

    duplicate_annotations: list[str] = []
    missing_evidence: list[str] = []
    warnings: list[str] = []

    valid_node_ids = set(registry) | set(articles) | set(questions)
    seen: set[tuple[str, str, str, str, str]] = set()
    for annotation in [*structural_annotations, *doctrinal_annotations]:
        if annotation.source_passage_id not in passages:
            warnings.append(f"Unknown passage id: {annotation.annotation_id}")
            continue
        if annotation.subject_id not in valid_node_ids:
            warnings.append(f"Unknown subject id: {annotation.annotation_id}")
        if annotation.object_id not in valid_node_ids:
            warnings.append(f"Unknown object id: {annotation.annotation_id}")
        if annotation.evidence_text not in passages[annotation.source_passage_id].text:
            missing_evidence.append(annotation.annotation_id)
        key = (
            annotation.source_passage_id,
            annotation.subject_id,
            annotation.relation_type,
            annotation.object_id,
            annotation.edge_layer,
        )
        if key in seen:
            duplicate_annotations.append(annotation.annotation_id)
        seen.add(key)

    for edge in doctrinal_edges:
        if not edge.support_annotation_ids:
            warnings.append(f"Doctrinal edge missing annotation support: {edge.edge_id}")
        if edge.edge_layer != "doctrinal":
            warnings.append(f"Doctrinal export contains non-doctrinal edge: {edge.edge_id}")

    for edge in structural_edges:
        if edge.edge_layer != "structural":
            warnings.append(f"Structural export contains non-structural edge: {edge.edge_id}")

    node_rows = load_node_rows(PROCESSED_DIR / "pilot_nodes.csv")
    for row in node_rows:
        node_id = row["node_id"]
        origin = row["origin"]
        if origin == "registry" and node_id not in registry:
            warnings.append(f"Node row missing from registry: {node_id}")
        if origin == "structural" and node_id not in valid_node_ids:
            warnings.append(f"Structural node row missing from source data: {node_id}")

    alias_collisions = find_alias_collisions(registry, load_alias_overrides())
    return PilotValidationReport(
        status="warning"
        if duplicate_annotations or missing_evidence or alias_collisions or warnings
        else "ok",
        passage_count=len(passages),
        concept_count=len(registry),
        annotation_count=len(structural_annotations) + len(doctrinal_annotations),
        doctrinal_edge_count=len(doctrinal_edges),
        structural_edge_count=len(structural_edges),
        duplicate_annotations=duplicate_annotations,
        missing_evidence=missing_evidence,
        alias_collisions=alias_collisions,
        unresolved_warnings=warnings,
    )


def write_validation_summary(report: PilotValidationReport, path: Path) -> None:
    """Write a concise markdown summary beside the machine-readable report."""

    lines = [
        "# Validation Summary",
        "",
        f"- status: `{report.status}`",
        f"- passages: `{report.passage_count}`",
        f"- concepts: `{report.concept_count}`",
        f"- annotations: `{report.annotation_count}`",
        f"- doctrinal edges: `{report.doctrinal_edge_count}`",
        f"- structural edges: `{report.structural_edge_count}`",
        "",
        "## Flags",
        f"- duplicate annotations: `{len(report.duplicate_annotations)}`",
        f"- missing evidence snippets: `{len(report.missing_evidence)}`",
        f"- suspicious alias collisions: `{len(report.alias_collisions)}`",
        f"- unresolved warnings: `{len(report.unresolved_warnings)}`",
    ]
    if report.duplicate_annotations:
        lines.extend(
            [
                "",
                "### Duplicate Annotations",
                *[f"- `{item}`" for item in report.duplicate_annotations],
            ]
        )
    if report.missing_evidence:
        lines.extend(
            [
                "",
                "### Missing Evidence",
                *[f"- `{item}`" for item in report.missing_evidence],
            ]
        )
    if report.alias_collisions:
        lines.extend(
            [
                "",
                "### Alias Collisions",
                *[f"- `{item}`" for item in report.alias_collisions],
            ]
        )
    if report.unresolved_warnings:
        lines.extend(["", "### Warnings", *[f"- `{item}`" for item in report.unresolved_warnings]])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_node_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
