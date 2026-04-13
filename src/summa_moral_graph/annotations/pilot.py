from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

from ..models import (
    ArticleRecord,
    ConceptRegistryRecord,
    PilotAnnotationRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..models.pilot import PilotNodeType, PilotRelationType
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import GOLD_DIR, INTERIM_DIR
from .pilot_spec import (
    BASE_PILOT_CONCEPTS,
    DOCTRINAL_RELATION_SEEDS,
    PILOT_SCOPE_SET,
    STRUCTURAL_TREATED_IN_SEEDS,
    DoctrinalSeed,
)


@dataclass(frozen=True)
class PilotContext:
    questions: dict[str, QuestionRecord]
    articles: dict[str, ArticleRecord]
    passages: dict[str, SegmentRecord]


def build_pilot_annotation_artifacts() -> dict[str, int]:
    """Build the pilot concept registry plus reviewed structural/doctrinal annotations."""

    context = load_pilot_context()
    structural_annotations = build_structural_annotations(context)
    doctrinal_annotations = build_doctrinal_annotations(context)
    registry = build_concept_registry(context, structural_annotations, doctrinal_annotations)

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(GOLD_DIR / "pilot_concept_registry.jsonl", registry.values())
    write_jsonl(
        GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl",
        structural_annotations,
    )
    write_jsonl(
        GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl",
        doctrinal_annotations,
    )
    return {
        "concepts": len(registry),
        "structural_annotations": len(structural_annotations),
        "doctrinal_annotations": len(doctrinal_annotations),
    }


def load_pilot_context() -> PilotContext:
    """Load interim question/article/segment records for the fixed pilot scope."""

    questions: dict[str, QuestionRecord] = {}
    for payload in load_jsonl(INTERIM_DIR / "summa_moral_questions.jsonl"):
        question_record = QuestionRecord(**payload)
        if (
            question_record.part_id,
            question_record.question_number,
        ) in PILOT_SCOPE_SET:
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

    return PilotContext(questions=questions, articles=articles, passages=passages)


def build_concept_registry(
    context: PilotContext,
    structural_annotations: list[PilotAnnotationRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
) -> dict[str, ConceptRegistryRecord]:
    """Build the stable pilot registry with derived source_scope fields."""

    question_scope_by_concept: dict[str, set[str]] = defaultdict(set)
    for annotation in [*structural_annotations, *doctrinal_annotations]:
        question_id = context.passages[annotation.source_passage_id].question_id
        for concept_id in (annotation.subject_id, annotation.object_id):
            if concept_id.startswith("concept."):
                question_scope_by_concept[concept_id].add(question_id)

    registry: dict[str, ConceptRegistryRecord] = {}
    for payload in BASE_PILOT_CONCEPTS:
        concept_id = str(payload["concept_id"])
        source_scope_seed = cast(list[str], payload.get("source_scope_seed", []))
        source_scope = sorted(
            {
                *question_scope_by_concept.get(concept_id, set()),
                *source_scope_seed,
            }
        )
        registry[concept_id] = ConceptRegistryRecord.model_validate(
            {
                "concept_id": concept_id,
                "canonical_label": cast(str, payload["canonical_label"]),
                "node_type": cast(PilotNodeType, payload["node_type"]),
                "aliases": cast(list[str], payload["aliases"]),
                "description": cast(str, payload["description"]),
                "notes": cast(list[str], payload["notes"]),
                "source_scope": source_scope,
            }
        )
    return registry


def build_structural_annotations(context: PilotContext) -> list[PilotAnnotationRecord]:
    """Build reviewed structural treated_in annotations for pilot articles."""

    concept_payloads = {str(payload["concept_id"]): payload for payload in BASE_PILOT_CONCEPTS}
    annotations: list[PilotAnnotationRecord] = []
    for seed in STRUCTURAL_TREATED_IN_SEEDS:
        passage = context.passages[seed.source_passage_id]
        article = context.articles[passage.article_id]
        concept = concept_payloads[seed.concept_id]
        canonical_label = cast(str, concept["canonical_label"])
        aliases = cast(list[str], concept["aliases"])
        node_type = cast(PilotNodeType, concept["node_type"])
        hints = seed.evidence_hints or tuple([canonical_label, *aliases])
        evidence_text = extract_evidence_text(
            passage.text,
            hints,
            require_match=False,
        )
        annotations.append(
            PilotAnnotationRecord(
                annotation_id=build_annotation_id(
                    passage.article_id,
                    "treated_in",
                    seed.concept_id,
                    seed.source_passage_id,
                ),
                source_passage_id=seed.source_passage_id,
                subject_id=passage.article_id,
                subject_label=f"{article.citation_label} — {article.article_title}",
                subject_type="article",
                relation_type="treated_in",
                object_id=seed.concept_id,
                object_label=canonical_label,
                object_type=node_type,
                evidence_text=evidence_text,
                evidence_rationale=seed.rationale
                or f"This article's respondeo explicitly treats {canonical_label}.",
                confidence=seed.confidence,
                edge_layer="structural",
                support_type=seed.support_type,
            )
        )
    annotations.sort(key=lambda record: record.annotation_id)
    return annotations


def build_doctrinal_annotations(
    context: PilotContext,
) -> list[PilotAnnotationRecord]:
    """Build reviewed doctrinal concept-to-concept annotations for the pilot slice."""

    registry = {
        record.concept_id: record
        for record in build_concept_registry(context, [], []).values()
    }
    annotations = [
        build_doctrinal_annotation(context, registry, seed)
        for seed in DOCTRINAL_RELATION_SEEDS
    ]
    annotations.sort(key=lambda record: record.annotation_id)
    return annotations


def build_doctrinal_annotation(
    context: PilotContext,
    registry: dict[str, ConceptRegistryRecord],
    seed: DoctrinalSeed,
) -> PilotAnnotationRecord:
    """Build a single doctrinal pilot annotation from a curated seed."""

    passage = context.passages[seed.source_passage_id]
    evidence_text = extract_evidence_text(
        passage.text,
        seed.evidence_hints,
        require_match=seed.support_type == "explicit_textual",
    )
    subject = registry[seed.subject_id]
    obj = registry[seed.object_id]
    return PilotAnnotationRecord(
        annotation_id=build_annotation_id(
            seed.subject_id,
            seed.relation_type,
            seed.object_id,
            seed.source_passage_id,
        ),
        source_passage_id=seed.source_passage_id,
        subject_id=seed.subject_id,
        subject_label=subject.canonical_label,
        subject_type=subject.node_type,
        relation_type=seed.relation_type,
        object_id=seed.object_id,
        object_label=obj.canonical_label,
        object_type=obj.node_type,
        evidence_text=evidence_text,
        evidence_rationale=seed.rationale,
        confidence=seed.confidence,
        edge_layer="doctrinal",
        support_type=seed.support_type,
    )


def build_annotation_id(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
    source_passage_id: str,
) -> str:
    """Build a stable semantic annotation id."""

    raw = f"{subject_id}.{relation_type}.{object_id}.{source_passage_id}"
    return "ann." + re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")


def extract_evidence_text(
    passage_text: str,
    hints: Iterable[str],
    *,
    require_match: bool,
) -> str:
    """Extract a stable sentence-like evidence snippet from the source passage."""

    hint_list = tuple(hint for hint in hints if hint)
    for hint in hint_list:
        excerpt = excerpt_around_hint(passage_text, hint)
        if excerpt:
            return excerpt
    if require_match:
        raise ValueError(f"Could not match evidence hint in passage: {hint_list}")
    return passage_text[:260].strip()


def excerpt_around_hint(text: str, hint: str) -> str | None:
    """Return a short excerpt centered on the first case-insensitive hint match."""

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
    start = 0 if start == -1 else start + 2
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
