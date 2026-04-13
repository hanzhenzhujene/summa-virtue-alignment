from __future__ import annotations

import json
from pathlib import Path

from ..models import (
    ArticleRecord,
    CandidateMentionRecord,
    CandidateRelationProposalRecord,
    PrudenceAnnotationRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR


def build_prudence_review_queue() -> dict[str, object]:
    """Build prudence review queue summaries and one concrete review packet."""

    coverage = json.loads((PROCESSED_DIR / "prudence_coverage.json").read_text(encoding="utf-8"))
    doctrinal_annotations = _load_records(
        GOLD_DIR / "prudence_reviewed_doctrinal_annotations.jsonl",
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
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii" and 47 <= record.question_number <= 56
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

    under_annotated = coverage["under_annotated_questions"]
    low_confidence = [
        annotation.annotation_id
        for annotation in doctrinal_annotations
        if annotation.confidence < 0.9
    ]
    unresolved_ambiguities = [mention.mention_id for mention in candidate_mentions]
    part_taxonomy_items = [
        proposal.proposal_id
        for proposal in candidate_relations
        if proposal.relation_type.endswith("_part_of")
    ]
    queue_payload = {
        "under_annotated_questions": under_annotated,
        "low_confidence_reviewed_annotations": low_confidence,
        "unresolved_concept_ambiguities": unresolved_ambiguities,
        "candidate_relation_proposals": [proposal.proposal_id for proposal in candidate_relations],
        "part_taxonomy_items_needing_review": part_taxonomy_items,
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "prudence_review_queue.json").write_text(
        json.dumps(queue_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    packet_question = under_annotated[-1] if under_annotated else 56
    packet_path = (
        PROCESSED_DIR / "review_packets" / f"prudence_q{packet_question:03d}_review_packet.md"
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text(
        build_review_packet_text(
            packet_question,
            questions,
            articles,
            passages,
            doctrinal_annotations,
            candidate_mentions,
            candidate_relations,
        ),
        encoding="utf-8",
    )
    return {
        "queue_path": str(PROCESSED_DIR / "prudence_review_queue.json"),
        "packet_path": str(packet_path),
    }


def build_review_packet_text(
    question_number: int,
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PrudenceAnnotationRecord],
    candidate_mentions: list[CandidateMentionRecord],
    candidate_relations: list[CandidateRelationProposalRecord],
) -> str:
    """Build a markdown review packet for a single prudence question."""

    question = next(
        record for record in questions.values() if record.question_number == question_number
    )
    article_rows = [
        record for record in articles.values() if record.question_id == question.question_id
    ]
    passage_ids = {
        passage.segment_id
        for passage in passages.values()
        if passage.question_id == question.question_id and passage.segment_type == "resp"
    }
    reviewed = [
        record for record in doctrinal_annotations if record.source_passage_id in passage_ids
    ]
    queued_mentions = [
        record for record in candidate_mentions if record.source_passage_id in passage_ids
    ]
    queued_relations = [
        record for record in candidate_relations if record.source_passage_id in passage_ids
    ]
    lines = [
        f"# Prudence Review Packet: II-II q.{question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Reviewed doctrinal annotations currently in scope: {len(reviewed)}",
        f"Candidate mentions: {len(queued_mentions)}",
        f"Candidate relation proposals: {len(queued_relations)}",
        "",
        "## Articles",
    ]
    for article in sorted(article_rows, key=lambda record: record.article_number):
        lines.append(f"- {article.citation_label}: {article.article_title}")
    lines.extend(["", "## Respondeo Passages To Recheck"])
    for passage in sorted(
        (record for record in passages.values() if record.segment_id in passage_ids),
        key=lambda record: (record.article_number, record.segment_id),
    ):
        lines.append(f"- {passage.segment_id}: {passage.text[:280]}...")
    lines.extend(["", "## Candidate Items"])
    if queued_mentions:
        for mention in queued_mentions:
            lines.append(f"- Mention `{mention.mention_id}`: {mention.note}")
    if queued_relations:
        for proposal in queued_relations:
            lines.append(f"- Relation `{proposal.proposal_id}`: {proposal.rationale}")
    if not queued_mentions and not queued_relations:
        lines.append("- No candidate items are currently queued for this question.")
    lines.extend(
        [
            "",
            "## Review Prompt",
            "- Check whether the current reviewed set adequately distinguishes "
            "doctrinal precepts of prudence from the mere tract frame.",
            "- Confirm whether additional reviewed treated_in edges or stronger "
            "doctrinal relations can be defended from the respondeo passages above.",
            "- Keep editorial synthesis separate from doctrinal review if a "
            "relation is only implied by tract organization.",
        ]
    )
    return "\n".join(lines) + "\n"


def _load_records(path: Path, model_cls):
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
