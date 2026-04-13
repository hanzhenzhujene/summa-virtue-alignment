from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from ..models import (
    ArticleRecord,
    CorpusConceptRecord,
    PilotAnnotationRecord,
    PilotNodeType,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR
from .corpus import build_corpus_registry
from .religion_tract_spec import (
    RELATION_SEEDS,
    RELIGION_TRACT_EXTRA_CONCEPTS,
    RELIGION_TRACT_MAX_QUESTION,
    RELIGION_TRACT_MIN_QUESTION,
    TRACT_CONCEPT_IDS,
    TREATMENT_SEEDS,
    RelationSeed,
    TreatmentSeed,
)


@dataclass(frozen=True)
class ReligionTractContext:
    questions: dict[str, QuestionRecord]
    articles: dict[str, ArticleRecord]
    passages: dict[str, SegmentRecord]
    concepts: dict[str, CorpusConceptRecord]


def build_religion_tract_annotation_artifacts() -> dict[str, int]:
    """Build religion-tract reviewed concept and annotation artifacts."""

    context = load_religion_tract_context()
    doctrinal = build_reviewed_doctrinal_annotations(context)
    structural = build_reviewed_structural_editorial_annotations(context)

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(GOLD_DIR / "religion_tract_reviewed_concepts.jsonl", context.concepts.values())
    write_jsonl(GOLD_DIR / "religion_tract_reviewed_doctrinal_annotations.jsonl", doctrinal)
    write_jsonl(
        GOLD_DIR / "religion_tract_reviewed_structural_editorial_annotations.jsonl",
        structural,
    )
    return {
        "reviewed_concepts": len(context.concepts),
        "reviewed_doctrinal_annotations": len(doctrinal),
        "reviewed_structural_editorial_annotations": len(structural),
    }


def load_religion_tract_context() -> ReligionTractContext:
    questions = {
        record.question_id: record
        for record in (
            QuestionRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_questions.jsonl")
        )
        if (
            record.part_id == "ii-ii"
            and RELIGION_TRACT_MIN_QUESTION <= record.question_number <= RELIGION_TRACT_MAX_QUESTION
        )
    }
    articles = {
        record.article_id: record
        for record in (
            ArticleRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_articles.jsonl")
        )
        if record.question_id in questions
    }
    passages = {
        record.segment_id: record
        for record in (
            SegmentRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_segments.jsonl")
        )
        if record.article_id in articles
    }

    registry = build_corpus_registry()
    for payload in RELIGION_TRACT_EXTRA_CONCEPTS:
        concept_record = CorpusConceptRecord.model_validate(payload)
        registry[concept_record.concept_id] = concept_record
    concepts = {
        concept_id: concept_record
        for concept_id, concept_record in registry.items()
        if concept_id in TRACT_CONCEPT_IDS
    }
    return ReligionTractContext(
        questions=questions,
        articles=articles,
        passages=passages,
        concepts=concepts,
    )


def build_reviewed_doctrinal_annotations(
    context: ReligionTractContext,
) -> list[PilotAnnotationRecord]:
    annotations = [build_relation_annotation(context, seed) for seed in RELATION_SEEDS]
    annotations.sort(key=lambda record: record.annotation_id)
    return annotations


def build_reviewed_structural_editorial_annotations(
    context: ReligionTractContext,
) -> list[PilotAnnotationRecord]:
    annotations = [build_treatment_annotation(context, seed) for seed in TREATMENT_SEEDS]
    annotations.sort(key=lambda record: record.annotation_id)
    return annotations


def build_relation_annotation(
    context: ReligionTractContext,
    seed: RelationSeed,
) -> PilotAnnotationRecord:
    passage = context.passages[seed.source_passage_id]
    subject_label, subject_type = resolve_node_label_type(context, seed.subject_id)
    object_label, object_type = resolve_node_label_type(context, seed.object_id)
    evidence_text = extract_evidence_text(
        passage.text,
        seed.evidence_hints,
        require_match=seed.support_type == "explicit_textual",
    )
    return PilotAnnotationRecord(
        annotation_id=build_annotation_id(
            seed.subject_id,
            seed.relation_type,
            seed.object_id,
            seed.source_passage_id,
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
        edge_layer="doctrinal",
        support_type=seed.support_type,
    )


def build_treatment_annotation(
    context: ReligionTractContext,
    seed: TreatmentSeed,
) -> PilotAnnotationRecord:
    passage = context.passages[seed.source_passage_id]
    subject_label, subject_type = resolve_node_label_type(context, seed.subject_id)
    object_label, object_type = resolve_node_label_type(context, seed.concept_id)
    evidence_hints = seed.evidence_hints or tuple(candidate_terms(context, seed.concept_id))
    evidence_text = extract_evidence_text(
        passage.text,
        evidence_hints,
        require_match=False,
    )
    return PilotAnnotationRecord(
        annotation_id=build_annotation_id(
            seed.subject_id,
            "treated_in",
            seed.concept_id,
            seed.source_passage_id,
        ),
        source_passage_id=seed.source_passage_id,
        subject_id=seed.subject_id,
        subject_label=subject_label,
        subject_type=subject_type,
        relation_type="treated_in",
        object_id=seed.concept_id,
        object_label=object_label,
        object_type=object_type,
        evidence_text=evidence_text,
        evidence_rationale=seed.rationale,
        confidence=seed.confidence,
        edge_layer="structural",
        support_type=seed.support_type,
    )


def candidate_terms(context: ReligionTractContext, concept_id: str) -> Iterable[str]:
    concept = context.concepts[concept_id]
    yield concept.canonical_label
    for alias in concept.aliases:
        yield alias


def resolve_node_label_type(
    context: ReligionTractContext,
    node_id: str,
) -> tuple[str, PilotNodeType]:
    if node_id in context.concepts:
        concept_record = context.concepts[node_id]
        return concept_record.canonical_label, concept_record.node_type
    if node_id in context.questions:
        question_record = context.questions[node_id]
        return (
            f"II-II q.{question_record.question_number} — {question_record.question_title}",
            "question",
        )
    if node_id in context.articles:
        article_record = context.articles[node_id]
        return (f"{article_record.citation_label} — {article_record.article_title}", "article")
    raise KeyError(f"Unknown religion-tract node id: {node_id}")


def build_annotation_id(
    subject_id: str,
    relation_type: str,
    object_id: str,
    source_passage_id: str,
) -> str:
    raw = f"{subject_id}.{relation_type}.{object_id}.{source_passage_id}"
    return "ann." + re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")


def extract_evidence_text(
    passage_text: str,
    hints: Iterable[str],
    *,
    require_match: bool,
) -> str:
    hint_list = tuple(hint for hint in hints if hint)
    for hint in hint_list:
        excerpt = excerpt_around_hint(passage_text, hint)
        if excerpt:
            return excerpt
    if require_match:
        raise ValueError(f"Could not match evidence hint in passage: {hint_list}")
    return passage_text[:260].strip()


def excerpt_around_hint(text: str, hint: str) -> str | None:
    pattern = re.compile(re.escape(hint), re.IGNORECASE)
    match = pattern.search(text)
    if match is None:
        return None
    window_start = max(0, match.start() - 120)
    window_end = min(len(text), match.end() + 160)
    return text[window_start:window_end].strip()
