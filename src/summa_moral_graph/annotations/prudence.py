from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ..models import (
    ArticleRecord,
    CandidateMentionRecord,
    CandidateRelationProposalRecord,
    PrudenceAnnotationRecord,
    PrudenceConceptRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..models.prudence import ConceptNodeType, PrudenceRelationType
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR
from .prudence_spec import (
    ARTICLE_TREATED_IN_MAP,
    CANDIDATE_MENTIONS,
    CANDIDATE_RELATION_PROPOSALS,
    CONCEPT_SEARCH_TERMS,
    RELATION_SEEDS,
    REVIEWED_CONCEPTS,
    STRUCTURAL_EDITORIAL_SEEDS,
    RelationSeed,
)

PRUDENCE_MIN_QUESTION = 47
PRUDENCE_MAX_QUESTION = 56


@dataclass(frozen=True)
class PrudenceContext:
    questions: dict[str, QuestionRecord]
    articles: dict[str, ArticleRecord]
    passages: dict[str, SegmentRecord]
    concepts: dict[str, PrudenceConceptRecord]


def build_prudence_annotation_artifacts() -> dict[str, int]:
    """Build prudence-specific reviewed and candidate annotation artifacts."""

    context = load_prudence_context()
    doctrinal = build_reviewed_doctrinal_annotations(context)
    structural_editorial = build_structural_editorial_annotations(context)
    candidate_mentions = [
        CandidateMentionRecord.model_validate(item) for item in CANDIDATE_MENTIONS
    ]
    candidate_relations = [
        CandidateRelationProposalRecord.model_validate(item)
        for item in CANDIDATE_RELATION_PROPOSALS
    ]

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(GOLD_DIR / "prudence_reviewed_concepts.jsonl", context.concepts.values())
    write_jsonl(GOLD_DIR / "prudence_reviewed_doctrinal_annotations.jsonl", doctrinal)
    write_jsonl(
        GOLD_DIR / "prudence_reviewed_structural_editorial_annotations.jsonl",
        structural_editorial,
    )
    write_jsonl(CANDIDATE_DIR / "prudence_candidate_mentions.jsonl", candidate_mentions)
    write_jsonl(CANDIDATE_DIR / "prudence_candidate_relation_proposals.jsonl", candidate_relations)

    return {
        "reviewed_concepts": len(context.concepts),
        "reviewed_doctrinal_annotations": len(doctrinal),
        "reviewed_structural_editorial_annotations": len(structural_editorial),
        "candidate_mentions": len(candidate_mentions),
        "candidate_relation_proposals": len(candidate_relations),
    }


def load_prudence_context() -> PrudenceContext:
    """Load the prudence tract context from existing interim artifacts."""

    questions: dict[str, QuestionRecord] = {}
    for payload in load_jsonl(INTERIM_DIR / "summa_moral_questions.jsonl"):
        question_record = QuestionRecord(**payload)
        if (
            question_record.part_id == "ii-ii"
            and PRUDENCE_MIN_QUESTION <= question_record.question_number <= PRUDENCE_MAX_QUESTION
        ):
            questions[question_record.question_id] = question_record

    articles: dict[str, ArticleRecord] = {}
    for payload in load_jsonl(INTERIM_DIR / "summa_moral_articles.jsonl"):
        article_record = ArticleRecord(**payload)
        if article_record.question_id in questions:
            articles[article_record.article_id] = article_record

    passages: dict[str, SegmentRecord] = {}
    for payload in load_jsonl(INTERIM_DIR / "summa_moral_segments.jsonl"):
        segment_record = SegmentRecord(**payload)
        if segment_record.article_id in articles:
            passages[segment_record.segment_id] = segment_record

    concepts = {
        record.concept_id: record
        for record in (PrudenceConceptRecord.model_validate(item) for item in REVIEWED_CONCEPTS)
    }
    return PrudenceContext(
        questions=questions,
        articles=articles,
        passages=passages,
        concepts=concepts,
    )


def build_reviewed_doctrinal_annotations(
    context: PrudenceContext,
) -> list[PrudenceAnnotationRecord]:
    """Generate reviewed doctrinal annotations from curated prudence seeds."""

    annotations: list[PrudenceAnnotationRecord] = []
    for source_passage_id, concept_id, support_type, confidence in ARTICLE_TREATED_IN_MAP:
        passage = context.passages[source_passage_id]
        article = context.articles[passage.article_id]
        concept = context.concepts[concept_id]
        evidence_text = extract_evidence_text(
            passage.text,
            CONCEPT_SEARCH_TERMS[concept_id],
            require_match=support_type == "explicit_textual",
        )
        annotations.append(
            PrudenceAnnotationRecord(
                annotation_id=build_annotation_id(
                    source_passage_id,
                    concept_id,
                    "treated_in",
                    article.article_id,
                ),
                source_passage_id=source_passage_id,
                subject_id=concept.concept_id,
                subject_label=concept.label,
                subject_type=concept.node_type,
                relation_type="treated_in",
                object_id=article.article_id,
                object_label=f"{article.citation_label} — {article.article_title}",
                object_type="article",
                evidence_text=evidence_text,
                evidence_rationale=(
                    f"The cited passage explicitly treats {concept.label} within this article."
                ),
                confidence=confidence,
                review_status="approved",
                support_type=support_type,
            )
        )

    for seed in RELATION_SEEDS:
        annotations.append(build_annotation_from_seed(context, seed))

    annotations.sort(key=lambda record: record.annotation_id)
    return annotations


def build_structural_editorial_annotations(
    context: PrudenceContext,
) -> list[PrudenceAnnotationRecord]:
    """Generate reviewed structural-editorial prudence annotations."""

    annotations = [build_annotation_from_seed(context, seed) for seed in STRUCTURAL_EDITORIAL_SEEDS]
    annotations.sort(key=lambda record: record.annotation_id)
    return annotations


def build_annotation_from_seed(
    context: PrudenceContext,
    seed: RelationSeed,
) -> PrudenceAnnotationRecord:
    """Build a reviewed annotation record from a curated seed."""

    passage = context.passages[seed.source_passage_id]
    subject_label, subject_type = resolve_node_label_type(context, seed.subject_id)
    object_label, object_type = resolve_node_label_type(context, seed.object_id)
    evidence_text = extract_evidence_text(
        passage.text,
        seed.evidence_hints,
        require_match=seed.support_type == "explicit_textual",
    )
    return PrudenceAnnotationRecord(
        annotation_id=build_annotation_id(
            seed.source_passage_id,
            seed.subject_id,
            seed.relation_type,
            seed.object_id,
        ),
        source_passage_id=seed.source_passage_id,
        subject_id=seed.subject_id,
        subject_label=subject_label,
        subject_type=subject_type,
        relation_type=seed.relation_type,
        object_id=seed.object_id,
        object_label=object_label,
        object_type=object_type,
        evidence_text=evidence_text,
        evidence_rationale=seed.rationale,
        confidence=seed.confidence,
        review_status="approved",
        support_type=seed.support_type,
    )


def resolve_node_label_type(
    context: PrudenceContext,
    node_id: str,
) -> tuple[str, ConceptNodeType]:
    """Resolve labels and types for concept, article, and question nodes."""

    if node_id in context.concepts:
        concept_record = context.concepts[node_id]
        return concept_record.label, concept_record.node_type
    if node_id in context.articles:
        article_record = context.articles[node_id]
        return (
            f"{article_record.citation_label} — {article_record.article_title}",
            "article",
        )
    if node_id in context.questions:
        question_record = context.questions[node_id]
        return (
            f"II-II q.{question_record.question_number} — {question_record.question_title}",
            "question",
        )
    raise KeyError(f"Unknown prudence node id: {node_id}")


def build_annotation_id(
    source_passage_id: str,
    subject_id: str,
    relation_type: PrudenceRelationType,
    object_id: str,
) -> str:
    """Build a stable semantic annotation id."""

    raw = f"{source_passage_id}.{subject_id}.{relation_type}.{object_id}"
    return "ann." + re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")


def extract_evidence_text(
    passage_text: str,
    hints: Iterable[str],
    *,
    require_match: bool,
) -> str:
    """Extract a stable evidence snippet from a cited passage."""

    hint_list = tuple(hints)
    for hint in hint_list:
        excerpt = excerpt_around_hint(passage_text, hint)
        if excerpt:
            return excerpt
    if require_match:
        raise ValueError(f"Could not match evidence hint in passage: {hint_list}")
    return passage_text[:260].strip()


def excerpt_around_hint(text: str, hint: str) -> str | None:
    """Return a sentence-like excerpt centered on a case-insensitive hint."""

    pattern = re.compile(re.escape(hint), re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    start = max(
        text.rfind(". ", 0, match.start()),
        text.rfind("; ", 0, match.start()),
        text.rfind("? ", 0, match.start()),
        text.rfind("! ", 0, match.start()),
    )
    if start == -1:
        start = 0
    else:
        start += 2
    end_candidates = [
        candidate
        for candidate in (
            text.find(". ", match.end()),
            text.find("; ", match.end()),
            text.find("? ", match.end()),
            text.find("! ", match.end()),
        )
        if candidate != -1
    ]
    end = min(end_candidates) if end_candidates else len(text)
    excerpt = text[start:end].strip()
    return excerpt if excerpt else None
