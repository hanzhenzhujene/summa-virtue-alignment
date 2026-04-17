from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .utils import (
    compact_relation_claims,
    deterministic_index,
    format_citation_block,
    relation_fragment,
    relation_sentence,
    support_signal_sentence,
)

if TYPE_CHECKING:
    from .builders import JoinedAnnotationRecord


def render_passage_grounded_user_prompt(annotation: "JoinedAnnotationRecord", seed_key: str) -> str:
    prompts = [
        "Explain the doctrinal teaching grounded in this passage.",
        "Using only the cited passage, state the doctrinal point Aquinas makes here.",
        "What Christian-virtue teaching is supported by this passage?",
    ]
    lead = prompts[deterministic_index(seed_key, len(prompts))]
    return (
        f"{lead}\n\n"
        f"Tract: {annotation.tract_display_label}\n"
        f"Question: {annotation.question_title}\n"
        f"Passage id: {annotation.source_passage_id}\n"
        f"Citation label: {annotation.source_passage_citation_label}\n"
        "Passage text:\n"
        f"{annotation.source_passage_text}"
    )


def render_passage_grounded_answer(annotation: "JoinedAnnotationRecord") -> str:
    claim = relation_sentence(
        annotation.subject_label,
        annotation.relation_type,
        annotation.object_label,
    )
    rationale = annotation.evidence_rationale.rstrip(".")
    citations = format_citation_block(
        [(annotation.source_passage_id, annotation.source_passage_citation_label)]
    )
    return (
        f"{claim}. {support_signal_sentence(annotation.support_type)} {rationale}.\n\n{citations}"
    )


def render_relation_explanation_user_prompt(
    annotation: "JoinedAnnotationRecord",
    seed_key: str,
) -> str:
    prompts = [
        "Explain this reviewed doctrinal relation from the cited passage.",
        "Why does this passage support the reviewed doctrinal relation below?",
        "Use the passage to explain the relation between the subject and object.",
    ]
    lead = prompts[deterministic_index(seed_key, len(prompts))]
    return (
        f"{lead}\n\n"
        f"Tract: {annotation.tract_display_label}\n"
        f"Subject: {annotation.subject_label}\n"
        f"Relation type: {annotation.relation_type}\n"
        f"Object: {annotation.object_label}\n"
        f"Passage id: {annotation.source_passage_id}\n"
        f"Passage text:\n{annotation.source_passage_text}"
    )


def render_relation_explanation_answer(annotation: "JoinedAnnotationRecord") -> str:
    claim = relation_sentence(
        annotation.subject_label,
        annotation.relation_type,
        annotation.object_label,
    )
    rationale = annotation.evidence_rationale.rstrip(".")
    citations = format_citation_block(
        [(annotation.source_passage_id, annotation.source_passage_citation_label)]
    )
    return (
        f"The reviewed relation is that {claim}. "
        f"{support_signal_sentence(annotation.support_type)} {rationale}.\n\n"
        f"{citations}"
    )


def render_citation_grounded_question(annotation: "JoinedAnnotationRecord", seed_key: str) -> str:
    relation_questions = {
        "caused_by": f"According to Aquinas, what causes {annotation.subject_label}?",
        "contrary_to": f"According to Aquinas, what is contrary to {annotation.subject_label}?",
        "deficiency_opposed_to": (
            "According to Aquinas, what is the deficient vice opposed to "
            f"{annotation.subject_label}?"
        ),
        "directed_to": f"According to Aquinas, to what is {annotation.subject_label} directed?",
        "excess_opposed_to": (
            "According to Aquinas, what is the excessive vice opposed to "
            f"{annotation.subject_label}?"
        ),
        "has_act": f"According to Aquinas, what act belongs to {annotation.subject_label}?",
        "has_object": f"According to Aquinas, what object does {annotation.subject_label} concern?",
        "opposed_by": f"According to Aquinas, what is opposed to {annotation.subject_label}?",
        "species_of": (
            f"According to Aquinas, of what larger kind is {annotation.subject_label} a species?"
        ),
        "subjective_part_of": (
            f"How does Aquinas classify {annotation.subject_label} "
            f"within {annotation.object_label}?"
        ),
        "potential_part_of": (
            f"How does Aquinas classify {annotation.subject_label} "
            f"within {annotation.object_label}?"
        ),
        "integral_part_of": (
            f"How does Aquinas classify {annotation.subject_label} "
            f"within {annotation.object_label}?"
        ),
        "treated_in": f"Where does Aquinas treat {annotation.subject_label} in this corpus?",
    }
    default_questions = [
        "How is "
        f"{annotation.subject_label} related to {annotation.object_label} "
        "according to Aquinas?",
        "What does Aquinas teach about the relation between "
        f"{annotation.subject_label} and {annotation.object_label}?",
    ]
    if annotation.relation_type in relation_questions:
        return relation_questions[annotation.relation_type]
    return default_questions[deterministic_index(seed_key, len(default_questions))]


def render_citation_grounded_answer(annotation: "JoinedAnnotationRecord") -> str:
    claim = relation_sentence(
        annotation.subject_label,
        annotation.relation_type,
        annotation.object_label,
    )
    rationale = annotation.evidence_rationale.rstrip(".")
    citations = format_citation_block(
        [(annotation.source_passage_id, annotation.source_passage_citation_label)]
    )
    return (
        f"According to the cited passage, {claim}. "
        f"{support_signal_sentence(annotation.support_type)} {rationale}.\n\n"
        f"{citations}"
    )


def render_concept_explanation_user_prompt(
    subject_label: str,
    tract_label: str,
    question_title: str,
    annotations: Sequence["JoinedAnnotationRecord"],
) -> str:
    lines = [
        "Explain this concept using only the supporting passages below.",
        "",
        f"Concept: {subject_label}",
        f"Tract: {tract_label}",
        f"Question context: {question_title}",
        "Supporting passages:",
    ]
    for annotation in annotations:
        lines.extend(
            [
                f"- {annotation.source_passage_id} ({annotation.source_passage_citation_label})",
                annotation.source_passage_text,
            ]
        )
    return "\n".join(lines)


def render_concept_explanation_answer(
    subject_label: str,
    annotations: Sequence["JoinedAnnotationRecord"],
) -> str:
    fragments = [
        relation_fragment(annotation.relation_type, annotation.object_label)
        for annotation in annotations
    ]
    claim = compact_relation_claims(subject_label, fragments)
    citations = format_citation_block(
        [
            (annotation.source_passage_id, annotation.source_passage_citation_label)
            for annotation in annotations
        ]
    )
    return f"{claim}\n\n{citations}"
