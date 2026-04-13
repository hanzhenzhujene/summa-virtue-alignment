from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..annotations.fortitude_closure_136_140_spec import (
    FORTITUDE_CLOSURE_136_140_MAX_QUESTION,
    FORTITUDE_CLOSURE_136_140_MIN_QUESTION,
)
from ..models import (
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    PilotAnnotationRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_fortitude_closure_136_140_review_queue() -> dict[str, str]:
    """Build fortitude-closure review queue summaries and one example packet."""

    coverage = json.loads(
        (PROCESSED_DIR / "fortitude_closure_136_140_coverage.json").read_text(encoding="utf-8")
    )
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and FORTITUDE_CLOSURE_136_140_MIN_QUESTION
        <= record.question_number
        <= FORTITUDE_CLOSURE_136_140_MAX_QUESTION
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
        if record.part_id == "ii-ii"
        and FORTITUDE_CLOSURE_136_140_MIN_QUESTION
        <= record.question_number
        <= FORTITUDE_CLOSURE_136_140_MAX_QUESTION
    }
    reviewed_annotations = load_reviewed_annotations()
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

    weak_support_ids = [
        record.annotation_id for record in reviewed_annotations if record.confidence < 0.88
    ]
    queue_payload = {
        "under_annotated_questions": coverage["under_annotated_questions"],
        "low_confidence_reviewed_annotations": weak_support_ids,
        "unresolved_patience_perseverance_issues": [
            record.candidate_id
            for record in candidate_mentions
            if record.ambiguity_flag
            and (
                "patience" in record.normalized_text
                or "perseverance" in record.normalized_text
            )
        ][:160],
        "unresolved_longanimity_constancy_issues": [
            record.candidate_id
            for record in candidate_mentions
            if "longanimity" in record.normalized_text or "constancy" in record.normalized_text
        ][:160],
        "weakly_supported_gift_linkage_edges": [
            record.annotation_id
            for record in reviewed_annotations
            if record.relation_type in {"corresponding_gift_of", "corresponds_to", "regulated_by"}
            and record.confidence < 0.92
        ][:160],
        "weakly_supported_precept_linkage_edges": [
            record.annotation_id
            for record in reviewed_annotations
            if record.relation_type in {"precept_of", "commands_act_of", "forbids_opposed_vice_of"}
            and record.confidence < 0.92
        ][:160],
        "fortitude_concepts_without_gift_or_precept_linkage": concepts_without_linkage(
            reviewed_annotations
        ),
        "candidate_relation_proposals": [record.proposal_id for record in candidate_relations][
            :200
        ],
    }
    queue_path = PROCESSED_DIR / "fortitude_closure_136_140_review_queue.json"
    queue_path.write_text(
        json.dumps(queue_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    packet_question_id = choose_packet_question(
        coverage["questions"],
        under_annotated_questions=[int(value) for value in coverage["under_annotated_questions"]],
    )
    packet_path = (
        PROCESSED_DIR
        / "review_packets"
        / f"{packet_question_id.replace('.', '_')}_fortitude_closure_136_140_review_packet.md"
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(
        build_review_packet(
            question_id=packet_question_id,
            questions=questions,
            passages=passages,
            reviewed_annotations=reviewed_annotations,
            candidate_mentions=candidate_mentions,
            candidate_relations=candidate_relations,
        ),
        encoding="utf-8",
    )
    return {"queue_path": str(queue_path), "packet_path": str(packet_path)}


def load_reviewed_annotations() -> list[PilotAnnotationRecord]:
    combined = [
        *_load_records(
            GOLD_DIR / "fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl",
            PilotAnnotationRecord,
        ),
        *_load_records(
            GOLD_DIR / "fortitude_closure_136_140_reviewed_structural_editorial_annotations.jsonl",
            PilotAnnotationRecord,
        ),
    ]
    deduped: dict[str, PilotAnnotationRecord] = {}
    for record in combined:
        deduped[record.annotation_id] = record
    return sorted(deduped.values(), key=lambda item: item.annotation_id)


def concepts_without_linkage(
    annotations: list[PilotAnnotationRecord],
) -> list[str]:
    linked: set[str] = set()
    fortitude_targets = {
        "concept.patience",
        "concept.perseverance_virtue",
        "concept.fortitude",
        "concept.longanimity_fortitude",
        "concept.constancy_fortitude",
    }
    for annotation in annotations:
        if annotation.relation_type in {
            "corresponding_gift_of",
            "precept_of",
            "commands_act_of",
            "forbids_opposed_vice_of",
        }:
            linked.add(annotation.subject_id)
            linked.add(annotation.object_id)
    return sorted(fortitude_targets - linked)


def choose_packet_question(
    question_rows: list[dict[str, object]],
    *,
    under_annotated_questions: list[int],
) -> str:
    eligible = [
        row
        for row in question_rows
        if coerce_int(row["question_number"]) in set(under_annotated_questions)
    ] or list(question_rows)
    ranked = sorted(
        eligible,
        key=lambda row: (
            coerce_int(row["reviewed_annotation_count"]),
            -coerce_int(row["candidate_relation_count"]),
            -coerce_int(row["candidate_mention_count"]),
            coerce_int(row["question_number"]),
        ),
    )
    return str(ranked[0]["question_id"])


def coerce_int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"Expected int-like value, received {type(value).__name__}")


def build_review_packet(
    *,
    question_id: str,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    reviewed_annotations: list[PilotAnnotationRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> str:
    question = questions[question_id]
    question_passages = [
        passage
        for passage in passages.values()
        if passage.question_id == question_id and passage.segment_type == "resp"
    ]
    question_passages.sort(key=lambda record: (record.article_number, record.segment_id))
    passage_ids = {passage.segment_id for passage in question_passages}
    reviewed_by_passage: dict[str, list[PilotAnnotationRecord]] = defaultdict(list)
    for annotation in reviewed_annotations:
        if annotation.source_passage_id in passage_ids:
            reviewed_by_passage[annotation.source_passage_id].append(annotation)
    mentions_by_passage: dict[str, list[CorpusCandidateMentionRecord]] = defaultdict(list)
    for mention in candidate_mentions:
        if mention.passage_id in passage_ids:
            mentions_by_passage[mention.passage_id].append(mention)
    relations_by_passage: dict[str, list[CorpusCandidateRelationProposalRecord]] = defaultdict(
        list
    )
    for relation in candidate_relations:
        if relation.source_passage_id in passage_ids:
            relations_by_passage[relation.source_passage_id].append(relation)

    lines = [
        f"# Fortitude Closure 136-140 Review Packet: II-II q.{question.question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Respondeo passages in packet: {len(question_passages)}",
        "",
        "Reviewer slots:",
        "- Accept candidate concepts:",
        "- Reject candidate concepts:",
        "- Accept candidate relations:",
        "- Reject candidate relations:",
        "- Patience/perseverance normalization issues:",
        "- Longanimity/constancy issues:",
        "- Gift-linkage issues:",
        "- Precept-linkage issues:",
        "- New reviewed annotations to draft:",
    ]
    for passage in question_passages:
        lines.extend(
            [
                "",
                f"## {passage.citation_label}",
                f"Passage id: `{passage.segment_id}`",
                "",
                passage.text,
                "",
                "### Nearby Reviewed Annotations",
            ]
        )
        if reviewed_by_passage[passage.segment_id]:
            for annotation in sorted(
                reviewed_by_passage[passage.segment_id],
                key=lambda item: item.annotation_id,
            ):
                lines.append(
                    (
                        "- "
                        f"`{annotation.annotation_id}` | "
                        f"{annotation.subject_label} -> {annotation.relation_type} -> "
                        f"{annotation.object_label} | "
                        f"support={annotation.support_type} | "
                        f"confidence={annotation.confidence}"
                    )
                )
        else:
            lines.append("- none")
        lines.extend(["", "### Candidate Mentions"])
        if mentions_by_passage[passage.segment_id]:
            for mention in mentions_by_passage[passage.segment_id]:
                lines.append(
                    "- "
                    f"`{mention.candidate_id}` | match=`{mention.matched_text}` | "
                    f"proposal={mention.proposed_concept_id or 'unresolved'} | "
                    f"ambiguity={mention.ambiguity_flag}"
                )
        else:
            lines.append("- none")
        lines.extend(["", "### Candidate Relations"])
        if relations_by_passage[passage.segment_id]:
            for relation in relations_by_passage[passage.segment_id]:
                lines.append(
                    "- "
                    f"`{relation.proposal_id}` | "
                    f"{relation.subject_id} -> {relation.relation_type} -> {relation.object_id} | "
                    f"confidence={relation.confidence} | ambiguity={relation.ambiguity_flag}"
                )
        else:
            lines.append("- none")
    return "\n".join(lines) + "\n"


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
