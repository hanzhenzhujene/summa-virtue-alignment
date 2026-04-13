from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..annotations.temperance_141_160_spec import (
    TEMPERANCE_141_160_MAX_QUESTION,
    TEMPERANCE_141_160_MIN_QUESTION,
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


def build_temperance_141_160_review_queue() -> dict[str, str]:
    """Build temperance tract review queue summaries and one example packet."""

    coverage = json.loads(
        (PROCESSED_DIR / "temperance_141_160_coverage.json").read_text(encoding="utf-8")
    )
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_141_160_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_141_160_MAX_QUESTION
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_141_160_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_141_160_MAX_QUESTION
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
        "unresolved_concept_ambiguities": [
            record.candidate_id for record in candidate_mentions if record.ambiguity_flag
        ][:200],
        "candidate_relation_proposals": [record.proposal_id for record in candidate_relations][
            :200
        ],
        "part_taxonomy_items_needing_review": [
            record.annotation_id
            for record in reviewed_annotations
            if record.relation_type
            in {"integral_part_of", "subjective_part_of", "potential_part_of"}
            and record.confidence < 0.93
        ][:160],
        "matter_domain_items_needing_review": [
            record.annotation_id
            for record in reviewed_annotations
            if record.relation_type
            in {
                "concerns_food",
                "concerns_drink",
                "concerns_sexual_pleasure",
                "concerns_anger",
                "concerns_outward_moderation",
            }
            and record.confidence < 0.93
        ][:160],
        "possible_overmerged_nodes": [
            "concept.abstinence vs concept.fasting",
            "concept.chastity vs concept.virginity",
            "concept.continence vs concept.temperance",
            "concept.meekness vs concept.clemency",
            "concept.anger vs concept.anger_vice",
            "concept.modesty_general vs future humility/modesty nodes",
        ],
    }
    queue_path = PROCESSED_DIR / "temperance_141_160_review_queue.json"
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
        / f"{packet_question_id.replace('.', '_')}_temperance_141_160_review_packet.md"
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
            GOLD_DIR / "temperance_141_160_reviewed_doctrinal_annotations.jsonl",
            PilotAnnotationRecord,
        ),
        *_load_records(
            GOLD_DIR / "temperance_141_160_reviewed_structural_editorial_annotations.jsonl",
            PilotAnnotationRecord,
        ),
    ]
    deduped: dict[str, PilotAnnotationRecord] = {}
    for record in combined:
        deduped[record.annotation_id] = record
    return sorted(deduped.values(), key=lambda item: item.annotation_id)


def choose_packet_question(
    question_rows: list[dict[str, object]],
    *,
    under_annotated_questions: list[int],
) -> str:
    def row_int(row: dict[str, object], key: str) -> int:
        value = row[key]
        if isinstance(value, bool) or not isinstance(value, int | str):
            raise TypeError(f"Expected int-like value for {key}, got {value!r}")
        return int(value)

    eligible = [
        row
        for row in question_rows
        if row_int(row, "question_number") in set(under_annotated_questions)
    ] or list(question_rows)
    ranked = sorted(
        eligible,
        key=lambda row: (
            row_int(row, "reviewed_annotation_count"),
            -row_int(row, "candidate_relation_count"),
            -row_int(row, "candidate_mention_count"),
            row_int(row, "question_number"),
        ),
    )
    return str(ranked[0]["question_id"])


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
        f"# Temperance 141-160 Review Packet: II-II q.{question.question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Respondeo passages in packet: {len(question_passages)}",
        "",
        "Reviewer slots:",
        "- Accept candidate concepts:",
        "- Reject candidate concepts:",
        "- Accept candidate relations:",
        "- Reject candidate relations:",
        "- Part-taxonomy issues:",
        "- Matter-domain issues:",
        "- Over-merged node issues:",
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
                "Reviewed annotations:",
            ]
        )
        reviewed_rows = reviewed_by_passage.get(passage.segment_id, [])
        if reviewed_rows:
            lines.extend(
                (
                    f"- `{row.annotation_id}` :: {row.subject_label} "
                    f"{row.relation_type} {row.object_label}"
                )
                for row in reviewed_rows
            )
        else:
            lines.append("- none")
        lines.append("")
        lines.append("Candidate mentions:")
        mention_rows = mentions_by_passage.get(passage.segment_id, [])
        if mention_rows:
            lines.extend(
                f"- `{row.candidate_id}` :: `{row.matched_text}` -> `{row.proposed_concept_id}`"
                for row in mention_rows[:12]
            )
        else:
            lines.append("- none")
        lines.append("")
        lines.append("Candidate relations:")
        relation_rows = relations_by_passage.get(passage.segment_id, [])
        if relation_rows:
            lines.extend(
                (
                    f"- `{row.proposal_id}` :: {row.subject_label} "
                    f"{row.relation_type} {row.object_label}"
                )
                for row in relation_rows[:12]
            )
        else:
            lines.append("- none")
    return "\n".join(lines) + "\n"


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
