from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..annotations.temperance_closure_161_170_spec import (
    TEMPERANCE_CLOSURE_161_170_MAX_QUESTION,
    TEMPERANCE_CLOSURE_161_170_MIN_QUESTION,
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


def build_temperance_closure_161_170_review_queue() -> dict[str, str]:
    """Build temperance-closure review queue summaries and one example packet."""

    coverage = json.loads(
        (PROCESSED_DIR / "temperance_closure_161_170_coverage.json").read_text(encoding="utf-8")
    )
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_CLOSURE_161_170_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_CLOSURE_161_170_MAX_QUESTION
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_CLOSURE_161_170_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_CLOSURE_161_170_MAX_QUESTION
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

    precept_link_ids = {
        record.annotation_id
        for record in reviewed_annotations
        if record.relation_type in {"precept_of", "commands_act_of", "forbids_opposed_vice_of"}
    }
    linked_concepts = {
        record.object_id
        for record in reviewed_annotations
        if record.relation_type == "precept_of" and record.object_id.startswith("concept.")
    }
    tracked_temperance_concepts = {
        "concept.temperance",
        "concept.humility",
        "concept.studiousness",
        "concept.meekness",
        "concept.chastity",
        "concept.abstinence",
        "concept.modesty_general",
    }
    queue_payload = {
        "under_annotated_questions": coverage["under_annotated_questions"],
        "low_confidence_reviewed_annotations": [
            record.annotation_id for record in reviewed_annotations if record.confidence < 0.9
        ],
        "unresolved_humility_pride_issues": [
            record.candidate_id
            for record in candidate_mentions
            if record.ambiguity_flag and record.passage_id.startswith(("st.ii-ii.q161", "st.ii-ii.q162"))
        ][:200],
        "unresolved_adams_first_sin_case_issues": [
            record.candidate_id
            for record in candidate_mentions
            if record.ambiguity_flag
            and record.passage_id.startswith(("st.ii-ii.q163", "st.ii-ii.q164", "st.ii-ii.q165"))
        ][:200],
        "unresolved_studiousness_curiosity_issues": [
            record.candidate_id
            for record in candidate_mentions
            if record.ambiguity_flag and record.passage_id.startswith(("st.ii-ii.q166", "st.ii-ii.q167"))
        ][:200],
        "weak_precept_linkage_edges": sorted(
            record.annotation_id
            for record in reviewed_annotations
            if record.annotation_id in precept_link_ids and record.confidence < 0.93
        ),
        "temperance_concepts_lacking_precept_linkage": sorted(
            tracked_temperance_concepts.difference(linked_concepts)
        ),
        "candidate_relation_proposals": [
            record.proposal_id for record in candidate_relations if record.ambiguity_flag
        ][:200],
        "possible_overmerged_modesty_nodes": [
            "concept.modesty_general vs concept.humility",
            "concept.modesty_general vs concept.external_behavior_modesty",
            "concept.modesty_general vs concept.outward_attire_modesty",
        ],
    }
    queue_path = PROCESSED_DIR / "temperance_closure_161_170_review_queue.json"
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
        / f"{packet_question_id.replace('.', '_')}_temperance_closure_161_170_review_packet.md"
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
            GOLD_DIR / "temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl",
            PilotAnnotationRecord,
        ),
        *_load_records(
            GOLD_DIR / "temperance_closure_161_170_reviewed_structural_editorial_annotations.jsonl",
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
        if int(row["question_number"]) in set(under_annotated_questions)
    ] or list(question_rows)
    ranked = sorted(
        eligible,
        key=lambda row: (
            int(row["reviewed_annotation_count"]),
            -int(row["candidate_relation_count"]),
            -int(row["candidate_mention_count"]),
            int(row["question_number"]),
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
        f"# Temperance Closure 161-170 Review Packet: II-II q.{question.question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Respondeo passages in packet: {len(question_passages)}",
        "",
        "Reviewer slots:",
        "- Accept candidate concepts:",
        "- Reject candidate concepts:",
        "- Accept candidate relations:",
        "- Reject candidate relations:",
        "- Humility / pride issues:",
        "- Adam's-first-sin case issues:",
        "- Studiousness / curiosity issues:",
        "- Modesty-node issues:",
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
                    f"- `{row.proposal_id}` :: {row.subject_id or row.subject_candidate_id} "
                    f"{row.relation_type} {row.object_id or row.object_candidate_id}"
                )
                for row in relation_rows[:12]
            )
        else:
            lines.append("- none")
    return "\n".join(lines) + "\n"


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
