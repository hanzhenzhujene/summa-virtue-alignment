from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import TypeVar

from pydantic import BaseModel

from ..models import (
    ArticleRecord,
    CandidateMentionRecord,
    CandidateRelationProposalRecord,
    PrudenceAnnotationRecord,
    PrudenceConceptRecord,
    PrudenceCoverageQuestionRecord,
    PrudenceEdgeRecord,
    PrudenceValidationReport,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_prudence_reports() -> dict[str, int | str]:
    """Build prudence coverage and validation reports."""

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
    editorial_annotations = _load_records(
        GOLD_DIR / "prudence_reviewed_structural_editorial_annotations.jsonl",
        PrudenceAnnotationRecord,
    )
    candidate_mentions = _load_records(
        CANDIDATE_DIR / "prudence_candidate_mentions.jsonl",
        CandidateMentionRecord,
    )
    candidate_relations = _load_records(
        CANDIDATE_DIR / "prudence_candidate_relation_proposals.jsonl",
        CandidateRelationProposalRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "prudence_reviewed_doctrinal_edges.jsonl",
        PrudenceEdgeRecord,
    )
    editorial_edges = _load_records(
        PROCESSED_DIR / "prudence_reviewed_structural_editorial_edges.jsonl",
        PrudenceEdgeRecord,
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

    coverage = build_prudence_coverage(
        questions,
        passages,
        concepts,
        doctrinal_annotations,
        doctrinal_edges,
        candidate_mentions,
        candidate_relations,
    )
    validation = validate_prudence_artifacts(
        concepts,
        questions,
        articles,
        passages,
        doctrinal_annotations,
        editorial_annotations,
        doctrinal_edges,
        editorial_edges,
        candidate_mentions,
        candidate_relations,
    )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    coverage_payload = {
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
    }
    (PROCESSED_DIR / "prudence_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "prudence_validation_report.json").write_text(
        json.dumps(
            validation.model_dump(mode="json"), indent=2, ensure_ascii=False, sort_keys=True
        ),
        encoding="utf-8",
    )
    return {
        "status": validation.status,
        "coverage_questions": len(coverage),
        "reviewed_doctrinal_annotations": len(doctrinal_annotations),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
    }


def build_prudence_coverage(
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    concepts: dict[str, PrudenceConceptRecord],
    doctrinal_annotations: list[PrudenceAnnotationRecord],
    doctrinal_edges: list[PrudenceEdgeRecord],
    candidate_mentions: list[CandidateMentionRecord],
    candidate_relations: list[CandidateRelationProposalRecord],
) -> list[PrudenceCoverageQuestionRecord]:
    """Build question-level coverage records for the prudence tract."""

    passage_counts = Counter(passage.question_id for passage in passages.values())
    annotations_by_question: Counter[str] = Counter()
    doctrinal_edges_by_question: Counter[str] = Counter()
    candidate_mentions_by_question: Counter[str] = Counter()
    candidate_relations_by_question: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    ambiguity_counts: Counter[str] = Counter()
    part_usage: dict[str, Counter[str]] = defaultdict(Counter)
    question_by_passage = {
        passage_id: segment_record.question_id for passage_id, segment_record in passages.items()
    }

    for annotation in doctrinal_annotations:
        question_id = question_by_passage[annotation.source_passage_id]
        annotations_by_question[question_id] += 1
        if annotation.subject_id in concepts:
            concepts_by_question[question_id].add(concepts[annotation.subject_id].label)
        if annotation.object_id in concepts:
            concepts_by_question[question_id].add(concepts[annotation.object_id].label)
        if annotation.relation_type.endswith("_part_of"):
            subtype = annotation.relation_type.split("_", 1)[0]
            part_usage[question_id][subtype] += 1

    edge_seen_by_question: dict[str, set[str]] = defaultdict(set)
    for edge in doctrinal_edges:
        for passage_id in edge.source_passage_ids:
            question_id = question_by_passage[passage_id]
            edge_seen_by_question[question_id].add(edge.edge_id)
    for question_id, edge_ids in edge_seen_by_question.items():
        doctrinal_edges_by_question[question_id] = len(edge_ids)

    for mention in candidate_mentions:
        question_id = question_by_passage[mention.source_passage_id]
        candidate_mentions_by_question[question_id] += 1
        ambiguity_counts[question_id] += 1

    for proposal in candidate_relations:
        question_id = question_by_passage[proposal.source_passage_id]
        candidate_relations_by_question[question_id] += 1
        ambiguity_counts[question_id] += 1

    coverage: list[PrudenceCoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda record: record.question_number):
        coverage.append(
            PrudenceCoverageQuestionRecord(
                question_id=question.question_id,
                question_number=question.question_number,
                parse_status="ok",
                passage_count=passage_counts[question.question_id],
                reviewed_annotation_count=annotations_by_question[question.question_id],
                reviewed_doctrinal_edge_count=doctrinal_edges_by_question[question.question_id],
                candidate_mention_count=candidate_mentions_by_question[question.question_id],
                candidate_relation_count=candidate_relations_by_question[question.question_id],
                major_concepts=sorted(concepts_by_question[question.question_id])[:20],
                unresolved_ambiguity_count=ambiguity_counts[question.question_id],
                part_taxonomy_usage=dict(part_usage[question.question_id]),
            )
        )
    return coverage


def identify_under_annotated_questions(
    coverage: list[PrudenceCoverageQuestionRecord],
) -> list[int]:
    """Identify comparatively under-annotated prudence questions."""

    if not coverage:
        return []
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


def validate_prudence_artifacts(
    concepts: dict[str, PrudenceConceptRecord],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PrudenceAnnotationRecord],
    editorial_annotations: list[PrudenceAnnotationRecord],
    doctrinal_edges: list[PrudenceEdgeRecord],
    editorial_edges: list[PrudenceEdgeRecord],
    candidate_mentions: list[CandidateMentionRecord],
    candidate_relations: list[CandidateRelationProposalRecord],
) -> PrudenceValidationReport:
    """Validate prudence-specific reviewed, editorial, and candidate layers."""

    warnings: list[str] = []
    duplicate_flags: list[str] = []

    valid_node_ids = set(concepts) | set(questions) | set(articles)
    for annotation in doctrinal_annotations + editorial_annotations:
        if annotation.subject_id not in valid_node_ids:
            warnings.append(f"Unknown annotation subject_id: {annotation.annotation_id}")
        if annotation.object_id not in valid_node_ids:
            warnings.append(f"Unknown annotation object_id: {annotation.annotation_id}")
        if annotation.source_passage_id not in passages:
            warnings.append(f"Unknown source_passage_id: {annotation.annotation_id}")
            continue
        if annotation.evidence_text not in passages[annotation.source_passage_id].text:
            warnings.append(
                f"Evidence text does not match source passage: {annotation.annotation_id}"
            )
        if annotation.review_status != "approved":
            warnings.append(f"Reviewed annotation is not approved: {annotation.annotation_id}")
        if (
            annotation.support_type == "structural_editorial"
            and annotation in doctrinal_annotations
        ):
            warnings.append(
                "Doctrinal annotation uses structural_editorial support: "
                f"{annotation.annotation_id}"
            )

    seen_tuples: set[tuple[str, str, str, str]] = set()
    for annotation in doctrinal_annotations + editorial_annotations:
        key = (
            annotation.source_passage_id,
            annotation.subject_id,
            annotation.relation_type,
            annotation.object_id,
        )
        if key in seen_tuples:
            duplicate_flags.append(
                f"Duplicate reviewed annotation tuple: {annotation.annotation_id}"
            )
        seen_tuples.add(key)

    for edge in doctrinal_edges:
        if not edge.support_annotation_ids:
            warnings.append(f"Reviewed doctrinal edge missing support annotations: {edge.edge_id}")
        if "structural_editorial" in edge.support_types:
            warnings.append(f"Editorial support leaked into doctrinal edge: {edge.edge_id}")
        if any(annotation_id.startswith("cand-") for annotation_id in edge.support_annotation_ids):
            warnings.append(f"Candidate data leaked into doctrinal edge: {edge.edge_id}")
        if edge.part_taxonomy is None and edge.relation_type.endswith("_part_of"):
            warnings.append(f"Part taxonomy edge missing subtype: {edge.edge_id}")

    for edge in editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Editorial edge has wrong review layer: {edge.edge_id}")

    for annotation in doctrinal_annotations:
        if annotation.relation_type.endswith("_part_of"):
            concept = concepts.get(annotation.subject_id)
            if concept is None or concept.part_taxonomy is None:
                warnings.append(
                    f"Part relation subject lacks part_taxonomy: {annotation.annotation_id}"
                )
            else:
                relation_taxonomy = annotation.relation_type.split("_", 1)[0]
                if concept.part_taxonomy != relation_taxonomy:
                    warnings.append(
                        f"Part taxonomy mismatch for {annotation.annotation_id}: "
                        f"{concept.part_taxonomy} vs {relation_taxonomy}"
                    )
            if annotation.object_id != "concept.prudence":
                warnings.append(
                    f"Part relation does not target prudence: {annotation.annotation_id}"
                )

    for mention in candidate_mentions:
        if mention.source_passage_id not in passages:
            warnings.append(f"Candidate mention references missing passage: {mention.mention_id}")
    for proposal in candidate_relations:
        if proposal.source_passage_id not in passages:
            warnings.append(
                f"Candidate relation references missing passage: {proposal.proposal_id}"
            )

    return PrudenceValidationReport(
        status="warning" if warnings or duplicate_flags else "ok",
        reviewed_annotation_count=len(doctrinal_annotations),
        reviewed_doctrinal_edge_count=len(doctrinal_edges),
        reviewed_structural_editorial_count=len(editorial_annotations),
        candidate_mention_count=len(candidate_mentions),
        candidate_relation_count=len(candidate_relations),
        duplicate_annotation_flags=duplicate_flags,
        unresolved_warnings=warnings,
    )


def _load_records(path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
