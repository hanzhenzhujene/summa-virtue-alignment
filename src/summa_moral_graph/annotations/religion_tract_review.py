from __future__ import annotations

import json
from collections import defaultdict

from ..annotations.religion_tract_spec import (
    RELIGION_TRACT_MAX_QUESTION,
    RELIGION_TRACT_MIN_QUESTION,
    is_excess_opposition_relation,
    is_positive_act_relation,
    is_sacred_object_relation,
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


def build_religion_tract_review_queue() -> dict[str, str]:
    """Build religion-tract review queue summaries and one example packet."""

    coverage = json.loads(
        (PROCESSED_DIR / "religion_tract_coverage.json").read_text(encoding="utf-8")
    )
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and RELIGION_TRACT_MIN_QUESTION <= record.question_number <= RELIGION_TRACT_MAX_QUESTION
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
        if record.part_id == "ii-ii"
        and RELIGION_TRACT_MIN_QUESTION <= record.question_number <= RELIGION_TRACT_MAX_QUESTION
    }
    reviewed_annotations = load_combined_reviewed_annotations()
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

    queue_payload = {
        "under_annotated_questions": coverage["under_annotated_questions"],
        "low_confidence_reviewed_annotations": [
            record.annotation_id for record in reviewed_annotations if record.confidence < 0.88
        ],
        "unresolved_concept_ambiguities": [
            record.candidate_id for record in candidate_mentions if record.ambiguity_flag
        ][:160],
        "candidate_relation_proposals": [record.proposal_id for record in candidate_relations][
            :200
        ],
        "sacred_object_or_act_taxonomy_items_needing_review": [
            record.proposal_id
            for record in candidate_relations
            if record.relation_type
            in {
                "concerns_sacred_object",
                "misuses_sacred_object",
                "corrupts_spiritual_exchange",
                "annexed_to",
            }
        ][:160],
    }
    queue_path = PROCESSED_DIR / "religion_tract_review_queue.json"
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
        / f"{packet_question_id.replace('.', '_')}_religion_tract_review_packet.md"
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


def load_combined_reviewed_annotations() -> list[PilotAnnotationRecord]:
    combined = [
        *[
            record
            for record in _load_records(
                GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl",
                PilotAnnotationRecord,
            )
            if record.source_passage_id.startswith("st.ii-ii.q")
            and RELIGION_TRACT_MIN_QUESTION
            <= int(record.source_passage_id.split(".q")[1][:3])
            <= RELIGION_TRACT_MAX_QUESTION
        ],
        *[
            record
            for record in _load_records(
                GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl",
                PilotAnnotationRecord,
            )
            if record.source_passage_id.startswith("st.ii-ii.q")
            and RELIGION_TRACT_MIN_QUESTION
            <= int(record.source_passage_id.split(".q")[1][:3])
            <= RELIGION_TRACT_MAX_QUESTION
        ],
        *_load_records(
            GOLD_DIR / "religion_tract_reviewed_doctrinal_annotations.jsonl",
            PilotAnnotationRecord,
        ),
        *_load_records(
            GOLD_DIR / "religion_tract_reviewed_structural_editorial_annotations.jsonl",
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
    relations_by_passage: dict[str, list[CorpusCandidateRelationProposalRecord]] = defaultdict(list)
    for relation in candidate_relations:
        if relation.source_passage_id in passage_ids:
            relations_by_passage[relation.source_passage_id].append(relation)

    lines = [
        f"# Religion Tract Review Packet: II-II q.{question.question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Respondeo passages in packet: {len(question_passages)}",
        "",
        "Reviewer slots:",
        "- Accept candidate concepts:",
        "- Reject candidate concepts:",
        "- Accept candidate relations:",
        "- Reject candidate relations:",
        "- Sacred-object or act-taxonomy issues:",
        "- Excess vs deficiency issues:",
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
                tags: list[str] = []
                if is_positive_act_relation(
                    annotation.subject_id,
                    annotation.relation_type,
                    annotation.object_id,
                ):
                    tags.append("positive_act")
                if is_excess_opposition_relation(
                    annotation.subject_id,
                    annotation.relation_type,
                    annotation.object_id,
                ):
                    tags.append("excess")
                if is_sacred_object_relation(
                    annotation.subject_id,
                    annotation.relation_type,
                    annotation.object_id,
                ):
                    tags.append("sacred_object")
                tag_display = f" [{' | '.join(tags)}]" if tags else ""
                lines.append(
                    f"- `{annotation.annotation_id}` | `{annotation.relation_type}` | "
                    f"{annotation.subject_label} -> {annotation.object_label} | "
                    f"{annotation.support_type}{tag_display}"
                )
        else:
            lines.append("- None.")
        lines.extend(["", "### Candidate Concepts"])
        if mentions_by_passage[passage.segment_id]:
            for mention in sorted(
                mentions_by_passage[passage.segment_id],
                key=lambda item: (item.char_start, item.candidate_id),
            ):
                concept_display = (
                    mention.proposed_concept_id
                    or ", ".join(mention.proposed_concept_ids)
                    or "unresolved"
                )
                lines.append(
                    f"- `{mention.candidate_id}` | `{concept_display}` | "
                    f"`{mention.match_method}` | ambiguity={mention.ambiguity_flag} | "
                    f"{mention.context_snippet}"
                )
        else:
            lines.append("- None.")
        lines.extend(["", "### Candidate Relations"])
        if relations_by_passage[passage.segment_id]:
            for relation in sorted(
                relations_by_passage[passage.segment_id],
                key=lambda item: item.proposal_id,
            ):
                lines.append(
                    f"- `{relation.proposal_id}` | `{relation.relation_type}` | "
                    f"{relation.subject_id} -> {relation.object_id} | "
                    f"`{relation.proposal_method}` | confidence={relation.confidence} | "
                    f"{relation.evidence_text[:220]}"
                )
        else:
            lines.append("- None.")
    return "\n".join(lines) + "\n"


def _load_records(path, model_cls):
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
