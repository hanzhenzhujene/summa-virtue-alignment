from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..models import (
    ArticleRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    PilotAnnotationRecord,
    QuestionRecord,
    SegmentRecord,
    TheologicalVirtuesCoverageQuestionRecord,
    TheologicalVirtuesEdgeRecord,
    TheologicalVirtuesValidationReport,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_theological_virtues_reports() -> dict[str, int | str]:
    """Build theological virtues coverage and validation outputs."""

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

    doctrinal_annotations = load_combined_annotations(edge_layer="doctrinal")
    structural_editorial_annotations = load_combined_annotations(edge_layer="structural")
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "theological_virtues_reviewed_doctrinal_edges.jsonl",
        TheologicalVirtuesEdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "theological_virtues_reviewed_structural_editorial_edges.jsonl",
        TheologicalVirtuesEdgeRecord,
    )
    candidate_mentions = [
        record
        for record in _load_records(
            CANDIDATE_DIR / "corpus_candidate_mentions.jsonl",
            CorpusCandidateMentionRecord,
        )
        if record.passage_id in passages
    ]
    candidate_relations = [
        record
        for record in _load_records(
            CANDIDATE_DIR / "corpus_candidate_relation_proposals.jsonl",
            CorpusCandidateRelationProposalRecord,
        )
        if record.source_passage_id in passages
    ]
    concepts = load_tract_concepts(doctrinal_annotations + structural_editorial_annotations)

    coverage = build_theological_virtues_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_theological_virtues_artifacts(
        concepts=concepts,
        questions=questions,
        articles=articles,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        structural_editorial_edges=structural_editorial_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
        coverage=coverage,
    )

    coverage_payload = {
        "summary": {
            "question_count": len(coverage),
            "passage_count": len(passages),
            "reviewed_annotation_count": len(doctrinal_annotations)
            + len(structural_editorial_annotations),
            "reviewed_doctrinal_edge_count": len(doctrinal_edges),
            "reviewed_structural_editorial_count": len(structural_editorial_annotations),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
            "registered_concepts_used": len(concepts),
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "theological_virtues_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "theological_virtues_validation_report.json").write_text(
        json.dumps(
            validation.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    write_coverage_markdown(
        coverage_payload,
        REPO_ROOT / "docs" / "theological_virtues_coverage.md",
    )
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "theological_virtues_validation.md",
    )
    return {
        "status": validation.status,
        "questions": len(coverage),
        "passages": len(passages),
        "reviewed_annotations": len(doctrinal_annotations) + len(structural_editorial_annotations),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
        "reviewed_structural_editorial": len(structural_editorial_annotations),
        "candidate_mentions": len(candidate_mentions),
        "candidate_relation_proposals": len(candidate_relations),
    }


def load_combined_annotations(*, edge_layer: str) -> list[PilotAnnotationRecord]:
    pilot_path = (
        GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl"
        if edge_layer == "doctrinal"
        else GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl"
    )
    tract_path = (
        GOLD_DIR / "theological_virtues_reviewed_doctrinal_annotations.jsonl"
        if edge_layer == "doctrinal"
        else GOLD_DIR / "theological_virtues_reviewed_structural_editorial_annotations.jsonl"
    )
    combined = [
        *[
            annotation
            for annotation in _load_records(pilot_path, PilotAnnotationRecord)
            if annotation.source_passage_id.startswith("st.ii-ii.q")
            and 1 <= int(annotation.source_passage_id.split(".q")[1][:3]) <= 46
        ],
        *_load_records(tract_path, PilotAnnotationRecord),
    ]
    deduped: dict[str, PilotAnnotationRecord] = {}
    for annotation in combined:
        deduped[annotation.annotation_id] = annotation
    return sorted(deduped.values(), key=lambda record: record.annotation_id)


def load_tract_concepts(
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


def build_theological_virtues_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[TheologicalVirtuesEdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[TheologicalVirtuesCoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii" and 1 <= int(row["question_number"]) <= 46
    }
    passage_counts = Counter(passage.question_id for passage in passages.values())
    reviewed_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    doctrinal_edge_counts: Counter[str] = Counter()
    candidate_mention_counts: Counter[str] = Counter()
    candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    question_by_passage = {
        passage_id: passage.question_id for passage_id, passage in passages.items()
    }

    for annotation in doctrinal_annotations:
        question_id = question_by_passage[annotation.source_passage_id]
        reviewed_counts[question_id] += 1
        if annotation.subject_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.subject_label)
        if annotation.object_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.object_label)

    for annotation in structural_editorial_annotations:
        question_id = question_by_passage[annotation.source_passage_id]
        reviewed_counts[question_id] += 1
        structural_counts[question_id] += 1
        if annotation.object_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.object_label)

    edge_seen_by_question: dict[str, set[str]] = defaultdict(set)
    for edge in doctrinal_edges:
        for passage_id in edge.source_passage_ids:
            question_id = question_by_passage[passage_id]
            edge_seen_by_question[question_id].add(edge.edge_id)
    for question_id, edge_ids in edge_seen_by_question.items():
        doctrinal_edge_counts[question_id] = len(edge_ids)

    for mention in candidate_mentions:
        question_id = question_by_passage[mention.passage_id]
        candidate_mention_counts[question_id] += 1
        if mention.ambiguity_flag:
            ambiguity_counts[question_id] += 1

    for relation in candidate_relations:
        question_id = question_by_passage[relation.source_passage_id]
        candidate_relation_counts[question_id] += 1
        if relation.ambiguity_flag:
            ambiguity_counts[question_id] += 1

    records: list[TheologicalVirtuesCoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda record: record.question_number):
        records.append(
            TheologicalVirtuesCoverageQuestionRecord(
                question_id=question.question_id,
                question_number=question.question_number,
                question_title=question.question_title,
                parse_status=question_status.get(question.question_id, "ok"),
                passage_count=passage_counts[question.question_id],
                reviewed_annotation_count=reviewed_counts[question.question_id],
                reviewed_doctrinal_edge_count=doctrinal_edge_counts[question.question_id],
                reviewed_structural_editorial_count=structural_counts[question.question_id],
                candidate_mention_count=candidate_mention_counts[question.question_id],
                candidate_relation_count=candidate_relation_counts[question.question_id],
                major_concepts=sorted(concepts_by_question[question.question_id])[:20],
                unresolved_ambiguity_count=ambiguity_counts[question.question_id],
            )
        )
    return records


def identify_under_annotated_questions(
    coverage: list[TheologicalVirtuesCoverageQuestionRecord],
) -> list[int]:
    ratios = {
        record.question_number: (
            record.reviewed_annotation_count / record.passage_count if record.passage_count else 0.0
        )
        for record in coverage
    }
    threshold = sorted(ratios.values())[max(0, len(ratios) // 3 - 1)]
    return [
        question_number for question_number, ratio in sorted(ratios.items()) if ratio <= threshold
    ]


def validate_theological_virtues_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[TheologicalVirtuesEdgeRecord],
    structural_editorial_edges: list[TheologicalVirtuesEdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[TheologicalVirtuesCoverageQuestionRecord],
) -> TheologicalVirtuesValidationReport:
    warnings: list[str] = []
    duplicate_flags: list[str] = []
    valid_node_ids = set(concepts) | set(questions) | set(articles)

    seen_review_keys: set[tuple[str, str, str, str, str]] = set()
    for annotation in doctrinal_annotations + structural_editorial_annotations:
        if annotation.subject_id not in valid_node_ids:
            warnings.append(f"Unknown annotation subject: {annotation.annotation_id}")
        if annotation.object_id not in valid_node_ids:
            warnings.append(f"Unknown annotation object: {annotation.annotation_id}")
        if annotation.source_passage_id not in passages:
            warnings.append(f"Unknown annotation passage: {annotation.annotation_id}")
            continue
        if annotation.evidence_text not in passages[annotation.source_passage_id].text:
            warnings.append(f"Evidence text mismatch: {annotation.annotation_id}")
        if not annotation.evidence_text.strip():
            warnings.append(f"Empty evidence text: {annotation.annotation_id}")
        review_key = (
            annotation.source_passage_id,
            annotation.subject_id,
            annotation.relation_type,
            annotation.object_id,
            annotation.support_type,
        )
        if review_key in seen_review_keys:
            duplicate_flags.append(
                f"Duplicate reviewed annotation tuple: {annotation.annotation_id}"
            )
        seen_review_keys.add(review_key)

    annotation_ids = {annotation.annotation_id for annotation in doctrinal_annotations}
    for edge in doctrinal_edges:
        if edge.review_layer != "reviewed_doctrinal":
            warnings.append(f"Wrong doctrinal review layer: {edge.edge_id}")
        if "structural_editorial" in edge.support_types:
            warnings.append(f"Editorial support leaked into doctrinal edge: {edge.edge_id}")
        if any(
            annotation_id not in annotation_ids for annotation_id in edge.support_annotation_ids
        ):
            warnings.append(f"Doctrinal edge missing reviewed annotation backing: {edge.edge_id}")

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Wrong structural-editorial review layer: {edge.edge_id}")

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention missing passage: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation missing passage: {relation.proposal_id}")

    if len({record.question_id for record in coverage}) != len(questions):
        warnings.append("Coverage question count does not match tract question count.")

    return TheologicalVirtuesValidationReport(
        status="warning" if warnings or duplicate_flags else "ok",
        question_count=len(coverage),
        reviewed_annotation_count=(
            len(doctrinal_annotations) + len(structural_editorial_annotations)
        ),
        reviewed_doctrinal_edge_count=len(doctrinal_edges),
        reviewed_structural_editorial_count=len(structural_editorial_annotations),
        candidate_mention_count=len(candidate_mentions),
        candidate_relation_count=len(candidate_relations),
        duplicate_annotation_flags=duplicate_flags,
        unresolved_warnings=warnings,
    )


def write_coverage_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Theological Virtues Coverage",
        "",
        "## Summary",
        f"- Questions covered: `{payload['summary']['question_count']}`",
        f"- Passages: `{payload['summary']['passage_count']}`",
        f"- Registered concepts used: `{payload['summary']['registered_concepts_used']}`",
        f"- Reviewed annotations: `{payload['summary']['reviewed_annotation_count']}`",
        f"- Reviewed doctrinal edges: `{payload['summary']['reviewed_doctrinal_edge_count']}`",
        (
            "- Reviewed structural-editorial correspondences: "
            f"`{payload['summary']['reviewed_structural_editorial_count']}`"
        ),
        f"- Candidate mentions: `{payload['summary']['candidate_mention_count']}`",
        f"- Candidate relation proposals: `{payload['summary']['candidate_relation_count']}`",
        "",
        "## Under-Annotated Questions",
    ]
    for question_number in payload["under_annotated_questions"]:
        lines.append(f"- `II-II q.{question_number}`")
    lines.extend(["", "## Question Detail"])
    for row in payload["questions"]:
        lines.append(
            f"- `II-II q.{row['question_number']}` `{row['parse_status']}` "
            f"| passages={row['passage_count']} "
            f"| reviewed={row['reviewed_annotation_count']} "
            f"| doctrinal_edges={row['reviewed_doctrinal_edge_count']} "
            f"| candidate_mentions={row['candidate_mention_count']} "
            f"| candidate_relations={row['candidate_relation_count']} "
            f"| ambiguities={row['unresolved_ambiguity_count']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: TheologicalVirtuesValidationReport,
    path: Path,
) -> None:
    lines = [
        "# Theological Virtues Validation",
        "",
        f"- Status: `{report.status}`",
        f"- Questions: `{report.question_count}`",
        f"- Reviewed annotations: `{report.reviewed_annotation_count}`",
        f"- Reviewed doctrinal edges: `{report.reviewed_doctrinal_edge_count}`",
        (
            "- Reviewed structural-editorial correspondences: "
            f"`{report.reviewed_structural_editorial_count}`"
        ),
        f"- Candidate mentions: `{report.candidate_mention_count}`",
        f"- Candidate relation proposals: `{report.candidate_relation_count}`",
    ]
    if report.duplicate_annotation_flags:
        lines.extend(["", "## Duplicate Flags"])
        lines.extend(f"- `{item}`" for item in report.duplicate_annotation_flags)
    if report.unresolved_warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- `{item}`" for item in report.unresolved_warnings)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
