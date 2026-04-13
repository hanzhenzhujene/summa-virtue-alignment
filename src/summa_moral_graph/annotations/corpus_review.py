from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from ..annotations.pilot_spec import PILOT_SCOPE_SET
from ..models import (
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR


def build_corpus_review_artifacts(question_id: str | None = None) -> dict[str, str]:
    """Build corpus-scale review queues and one concrete question packet."""

    coverage_payload = json.loads(
        (PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8")
    )
    mentions = [
        CorpusCandidateMentionRecord.model_validate(payload)
        for payload in load_jsonl(CANDIDATE_DIR / "corpus_candidate_mentions.jsonl")
    ]
    relations = [
        CorpusCandidateRelationProposalRecord.model_validate(payload)
        for payload in load_jsonl(
            CANDIDATE_DIR / "corpus_candidate_relation_proposals.jsonl"
        )
    ]
    passages = {
        record.segment_id: record
        for record in (
            SegmentRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_segments.jsonl")
        )
    }
    questions = {
        record.question_id: record
        for record in (
            QuestionRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_questions.jsonl")
        )
    }

    mention_type_counts = Counter(
        mention.proposed_node_type or "unresolved"
        for mention in mentions
    )
    relation_type_counts = Counter(relation.relation_type for relation in relations)
    confidence_buckets = {
        "high": count_bucket(mentions, relations, minimum=0.8),
        "medium": count_bucket(mentions, relations, minimum=0.65, maximum=0.8),
        "low": count_bucket(mentions, relations, minimum=0.0, maximum=0.65),
    }
    ambiguous_mentions = [
        mention.candidate_id
        for mention in sorted(mentions, key=lambda item: item.candidate_id)
        if mention.ambiguity_flag
    ][:80]
    under_annotated_questions = [
        {
            "question_id": row["question_id"],
            "candidate_mentions": row["candidate_mention_count"],
            "candidate_relations": row["candidate_relation_count"],
            "reviewed_annotations": row["reviewed_annotation_count"],
        }
        for row in coverage_payload["questions"]
        if row["parse_status"] != "excluded"
        and row["reviewed_annotation_count"] == 0
        and (
            row["candidate_mention_count"] > 0 or row["candidate_relation_count"] > 0
        )
    ][:40]

    target_question_id = question_id or choose_review_question(coverage_payload["questions"])
    packet_path = build_question_review_packet(
        target_question_id=target_question_id,
        questions=questions,
        passages=passages,
        mentions=mentions,
        relations=relations,
    )

    queue_payload = {
        "questions": [
            {
                "question_id": row["question_id"],
                "parse_status": row["parse_status"],
                "reviewed_annotations": row["reviewed_annotation_count"],
                "candidate_mentions": row["candidate_mention_count"],
                "candidate_relations": row["candidate_relation_count"],
                "ambiguity_count": row["ambiguity_count"],
            }
            for row in coverage_payload["questions"]
            if row["parse_status"] != "excluded"
        ],
        "node_type_counts": dict(sorted(mention_type_counts.items())),
        "relation_type_counts": dict(sorted(relation_type_counts.items())),
        "confidence_buckets": confidence_buckets,
        "ambiguous_mentions": ambiguous_mentions,
        "under_annotated_questions": under_annotated_questions,
        "suggested_question_packet": target_question_id,
        "packet_path": str(packet_path),
    }
    queue_path = PROCESSED_DIR / "corpus_review_queue.json"
    queue_path.write_text(
        json.dumps(queue_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return {"queue_path": str(queue_path), "packet_path": str(packet_path)}


def choose_review_question(question_rows: list[dict[str, int | str]]) -> str:
    """Prefer non-pilot questions with many candidates and no reviewed annotations."""

    eligible = [
        row
        for row in question_rows
        if row["parse_status"] != "excluded"
        and (row["reviewed_annotation_count"] == 0)
        and (
            int(row["candidate_mention_count"]) > 0
            or int(row["candidate_relation_count"]) > 0
        )
        and not is_pilot_question(str(row["question_id"]))
    ]
    if not eligible:
        eligible = [row for row in question_rows if row["parse_status"] != "excluded"]
    eligible.sort(
        key=lambda row: (
            -int(row["candidate_relation_count"]),
            -int(row["candidate_mention_count"]),
            str(row["question_id"]),
        )
    )
    return str(eligible[0]["question_id"])


def build_question_review_packet(
    *,
    target_question_id: str,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    mentions: list[CorpusCandidateMentionRecord],
    relations: list[CorpusCandidateRelationProposalRecord],
) -> Path:
    """Write a markdown packet for reviewing one full-corpus question."""

    question = questions[target_question_id]
    packet_dir = PROCESSED_DIR / "review_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    for existing in packet_dir.glob("st_*_corpus_review_packet.md"):
        existing.unlink()

    question_passages = [
        passage
        for passage in passages.values()
        if passage.question_id == target_question_id
    ]
    question_passages.sort(key=lambda item: (item.article_number, item.segment_id))
    passage_ids = {passage.segment_id for passage in question_passages}

    mentions_by_passage: dict[str, list[CorpusCandidateMentionRecord]] = defaultdict(list)
    for mention in mentions:
        if mention.passage_id in passage_ids:
            mentions_by_passage[mention.passage_id].append(mention)

    relations_by_passage: dict[str, list[CorpusCandidateRelationProposalRecord]] = defaultdict(list)
    for relation in relations:
        if relation.source_passage_id in passage_ids:
            relations_by_passage[relation.source_passage_id].append(relation)

    reviewed_annotations = load_reviewed_annotation_rows()
    reviewed_by_passage: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in reviewed_annotations:
        passage_id = str(row["source_passage_id"])
        if passage_id in passage_ids:
            reviewed_by_passage[passage_id].append(row)

    lines = [
        f"# Corpus Review Packet: {question.part_id.upper()} q.{question.question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Passages in packet: {len(question_passages)}",
        "",
        "Reviewer slots:",
        "- Accepted concept candidates:",
        "- Rejected concept candidates:",
        "- Accepted relation proposals:",
        "- Rejected relation proposals:",
        "- New concept ids needed:",
        "- Notes:",
    ]
    for passage in question_passages:
        passage_mentions = sorted(
            mentions_by_passage.get(passage.segment_id, []),
            key=lambda item: (item.char_start, item.candidate_id),
        )
        passage_relations = sorted(
            relations_by_passage.get(passage.segment_id, []),
            key=lambda item: item.proposal_id,
        )
        reviewed_rows = sorted(
            reviewed_by_passage.get(passage.segment_id, []),
            key=lambda item: str(item["annotation_id"]),
        )
        lines.extend(
            [
                "",
                f"## {passage.citation_label}",
                f"Passage id: `{passage.segment_id}`",
                "",
                passage.text,
                "",
                "### Candidate Concepts",
            ]
        )
        if passage_mentions:
            for mention in passage_mentions:
                concept_display = (
                    mention.proposed_concept_id
                    or ", ".join(mention.proposed_concept_ids)
                    or "unresolved"
                )
                lines.append(
                    f"- `{mention.candidate_id}` | `{mention.match_method}` | "
                    f"`{mention.confidence:.2f}` | `{concept_display}` | "
                    f"ambiguity={mention.ambiguity_flag} | {mention.context_snippet}"
                )
        else:
            lines.append("- None.")
        lines.extend(["", "### Candidate Relations"])
        if passage_relations:
            for relation in passage_relations:
                lines.append(
                    f"- `{relation.proposal_id}` | `{relation.relation_type}` | "
                    f"`{relation.confidence:.2f}` | {relation.subject_label} -> "
                    f"{relation.object_label} | {relation.evidence_text}"
                )
        else:
            lines.append("- None.")
        lines.extend(["", "### Nearby Reviewed Annotations"])
        if reviewed_rows:
            for row in reviewed_rows:
                lines.append(
                    f"- `{row['annotation_id']}` | `{row['relation_type']}` | "
                    f"{row['subject_label']} -> {row['object_label']}"
                )
        else:
            lines.append("- None.")
        lines.extend(
            [
                "",
                "### Reviewer Decisions",
                "- Accept:",
                "- Reject:",
                "- Normalize to:",
                "- Notes:",
            ]
        )

    packet_path = packet_dir / f"{target_question_id.replace('.', '_')}_corpus_review_packet.md"
    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return packet_path


def count_bucket(
    mentions: list[CorpusCandidateMentionRecord],
    relations: list[CorpusCandidateRelationProposalRecord],
    *,
    minimum: float,
    maximum: float | None = None,
) -> dict[str, int]:
    def in_bucket(value: float) -> bool:
        if value < minimum:
            return False
        if maximum is not None and value >= maximum:
            return False
        return True

    return {
        "mentions": sum(1 for mention in mentions if in_bucket(mention.confidence)),
        "relations": sum(1 for relation in relations if in_bucket(relation.confidence)),
    }


def is_pilot_question(question_identifier: str) -> bool:
    parts = question_identifier.split(".")
    if len(parts) < 3:
        return False
    part_id = parts[1]
    question_number = int(parts[2][1:])
    return (part_id, question_number) in PILOT_SCOPE_SET


def load_reviewed_annotation_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in (
        GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl",
        GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl",
        GOLD_DIR / "prudence_reviewed_doctrinal_annotations.jsonl",
        GOLD_DIR / "prudence_reviewed_structural_editorial_annotations.jsonl",
    ):
        if not path.exists():
            continue
        rows.extend(load_jsonl(path))
    return rows
