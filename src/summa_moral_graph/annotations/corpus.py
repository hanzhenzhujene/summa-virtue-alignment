from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from ..models import (
    ArticleRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..models.pilot import PilotNodeType
from ..ontology import load_alias_overrides, load_pilot_registry, normalize_lookup_text
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR
from .corpus_spec import (
    DETECTION_LABEL_OVERRIDES,
    EXTRA_CORPUS_CONCEPTS,
    RELATION_CUE_PATTERNS,
    SUPPRESSED_SINGLE_TOKEN_LABELS,
)


@dataclass(frozen=True)
class CorpusContext:
    questions: dict[str, QuestionRecord]
    articles: dict[str, ArticleRecord]
    passages: dict[str, SegmentRecord]


@dataclass(frozen=True)
class CandidateTerm:
    label: str
    concept_ids: tuple[str, ...]
    proposed_node_type: PilotNodeType | None
    match_method: str
    ambiguity_flag: bool
    pattern: re.Pattern[str]


def build_corpus_candidate_artifacts() -> dict[str, int]:
    """Build corpus-wide concept registry and unreviewed candidate artifacts."""

    context = load_corpus_context()
    registry = build_corpus_registry()
    mentions = build_candidate_mentions(context, registry)
    proposals = build_candidate_relation_proposals(context, registry, mentions)

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(GOLD_DIR / "corpus_concept_registry.jsonl", registry.values())
    write_jsonl(CANDIDATE_DIR / "corpus_candidate_mentions.jsonl", mentions)
    write_jsonl(CANDIDATE_DIR / "corpus_candidate_relation_proposals.jsonl", proposals)
    return {
        "concepts": len(registry),
        "candidate_mentions": len(mentions),
        "candidate_relation_proposals": len(proposals),
    }


def load_corpus_context() -> CorpusContext:
    """Load the full in-scope structural corpus from interim exports."""

    questions = {
        record.question_id: record
        for record in (
            QuestionRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_questions.jsonl")
        )
    }
    articles = {
        record.article_id: record
        for record in (
            ArticleRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_articles.jsonl")
        )
    }
    passages = {
        record.segment_id: record
        for record in (
            SegmentRecord.model_validate(payload)
            for payload in load_jsonl(INTERIM_DIR / "summa_moral_segments.jsonl")
        )
    }
    return CorpusContext(questions=questions, articles=articles, passages=passages)


def build_corpus_registry() -> dict[str, CorpusConceptRecord]:
    """Build a broader corpus registry from pilot reviewed concepts plus extra seeds."""

    registry: dict[str, CorpusConceptRecord] = {}
    for record in load_pilot_registry().values():
        registry[record.concept_id] = CorpusConceptRecord.model_validate(
            {
                "concept_id": record.concept_id,
                "canonical_label": record.canonical_label,
                "node_type": record.node_type,
                "aliases": record.aliases,
                "description": record.description,
                "notes": record.notes,
                "source_scope": record.source_scope,
                "parent_concept_id": None,
                "registry_status": "reviewed_seed",
                "disambiguation_notes": [],
                "related_concepts": [],
                "introduced_in_questions": record.source_scope,
            }
        )
    for payload in EXTRA_CORPUS_CONCEPTS:
        concept_record = CorpusConceptRecord.model_validate(payload)
        registry[concept_record.concept_id] = concept_record
    return dict(sorted(registry.items()))


def build_candidate_mentions(
    context: CorpusContext,
    registry: dict[str, CorpusConceptRecord],
) -> list[CorpusCandidateMentionRecord]:
    """Extract conservative full-corpus concept mention candidates."""

    alias_overrides = load_alias_overrides(GOLD_DIR / "corpus_alias_overrides.yml")
    candidate_terms = build_candidate_terms(registry, alias_overrides)
    mentions: list[CorpusCandidateMentionRecord] = []

    for passage in sorted(context.passages.values(), key=lambda record: record.segment_id):
        raw_matches: list[tuple[int, int, str, CandidateTerm]] = []
        for term in candidate_terms:
            for match in term.pattern.finditer(passage.text):
                raw_matches.append((match.start(), match.end(), match.group(0), term))
        if not raw_matches:
            continue
        accepted_matches = select_non_overlapping_matches(raw_matches)
        for index, (start, end, matched_text, term) in enumerate(accepted_matches, start=1):
            normalized_text = normalize_lookup_text(matched_text)
            proposed_concept_id = (
                term.concept_ids[0]
                if len(term.concept_ids) == 1 and not term.ambiguity_flag
                else None
            )
            mentions.append(
                CorpusCandidateMentionRecord(
                    candidate_id=f"candidate.mention.{passage.segment_id}.m{index:02d}",
                    passage_id=passage.segment_id,
                    matched_text=matched_text,
                    normalized_text=normalized_text,
                    proposed_concept_id=proposed_concept_id,
                    proposed_concept_ids=list(term.concept_ids),
                    proposed_node_type=term.proposed_node_type,
                    match_method=term.match_method,
                    confidence=mention_confidence(term),
                    ambiguity_flag=term.ambiguity_flag or len(term.concept_ids) > 1,
                    context_snippet=context_snippet(passage.text, start, end),
                    char_start=start,
                    char_end=end,
                )
            )
    mentions.sort(key=lambda record: (record.passage_id, record.char_start, record.candidate_id))
    return mentions


def build_candidate_relation_proposals(
    context: CorpusContext,
    registry: dict[str, CorpusConceptRecord],
    mentions: list[CorpusCandidateMentionRecord],
) -> list[CorpusCandidateRelationProposalRecord]:
    """Generate cautious relation proposals from exact cues and structural patterns."""

    mentions_by_passage: dict[str, list[CorpusCandidateMentionRecord]] = defaultdict(list)
    for mention in mentions:
        mentions_by_passage[mention.passage_id].append(mention)

    proposal_payloads: list[dict[str, object]] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    for passage_id, passage_mentions in sorted(mentions_by_passage.items()):
        passage = context.passages[passage_id]
        resolved_mentions = [
            mention
            for mention in sorted(passage_mentions, key=lambda item: item.char_start)
            if mention.proposed_concept_id is not None and not mention.ambiguity_flag
        ]
        if not resolved_mentions:
            continue

        grouped_mentions = group_mentions_by_article(passage, resolved_mentions)
        for concept_id, support_mentions in grouped_mentions.items():
            if not should_propose_article_treated_in(passage, support_mentions):
                continue
            concept = registry[concept_id]
            add_proposal(
                proposal_payloads,
                seen,
                {
                    "source_passage_id": passage_id,
                    "subject_id": passage.article_id,
                    "subject_label": context.articles[passage.article_id].citation_label,
                    "subject_type": "article",
                    "relation_type": "treated_in",
                    "object_id": concept_id,
                    "object_label": concept.canonical_label,
                    "object_type": concept.node_type,
                    "proposal_method": "structural_article_treated_in",
                    "evidence_text": support_mentions[0].context_snippet,
                    "confidence": 0.72 if passage.segment_type == "resp" else 0.64,
                    "ambiguity_flag": False,
                    "support_candidate_ids": [mention.candidate_id for mention in support_mentions],
                },
            )

        for proposal_method, relation_type, cue_pattern in RELATION_CUE_PATTERNS:
            cue_regex = re.compile(cue_pattern, re.IGNORECASE)
            for cue_match in cue_regex.finditer(passage.text):
                left_mention = nearest_mention_before(resolved_mentions, cue_match.start())
                right_mention = nearest_mention_after(resolved_mentions, cue_match.end())
                if left_mention is None or right_mention is None:
                    continue
                if left_mention.proposed_concept_id == right_mention.proposed_concept_id:
                    continue
                left_concept_id = left_mention.proposed_concept_id
                right_concept_id = right_mention.proposed_concept_id
                if left_concept_id is None or right_concept_id is None:
                    continue
                left_concept = registry[left_concept_id]
                right_concept = registry[right_concept_id]
                add_proposal(
                    proposal_payloads,
                    seen,
                    {
                        "source_passage_id": passage_id,
                        "subject_id": left_concept_id,
                        "subject_label": left_concept.canonical_label,
                        "subject_type": left_concept.node_type,
                        "relation_type": relation_type,
                        "object_id": right_concept_id,
                        "object_label": right_concept.canonical_label,
                        "object_type": right_concept.node_type,
                        "proposal_method": proposal_method,
                        "evidence_text": context_snippet(
                            passage.text,
                            left_mention.char_start,
                            right_mention.char_end,
                        ),
                        "confidence": 0.82,
                        "ambiguity_flag": False,
                        "support_candidate_ids": [
                            left_mention.candidate_id,
                            right_mention.candidate_id,
                        ],
                    },
                )

    question_groupings: dict[
        tuple[str, str],
        list[CorpusCandidateMentionRecord],
    ] = defaultdict(list)
    for mention in mentions:
        if mention.proposed_concept_id is None or mention.ambiguity_flag:
            continue
        passage = context.passages[mention.passage_id]
        question_groupings[(passage.question_id, mention.proposed_concept_id)].append(mention)

    for (question_identifier, concept_id), question_mentions in sorted(
        question_groupings.items()
    ):
        article_ids = {
            context.passages[mention.passage_id].article_id
            for mention in question_mentions
        }
        if len(article_ids) < 2:
            continue
        question_record = context.questions[question_identifier]
        concept = registry[concept_id]
        first_support = sorted(question_mentions, key=lambda item: item.candidate_id)[0]
        add_proposal(
            proposal_payloads,
            seen,
            {
                "source_passage_id": first_support.passage_id,
                "subject_id": question_identifier,
                "subject_label": (
                    f"{question_record.part_id.upper()} q.{question_record.question_number}"
                ),
                "subject_type": "question",
                "relation_type": "treated_in",
                "object_id": concept_id,
                "object_label": concept.canonical_label,
                "object_type": concept.node_type,
                "proposal_method": "structural_question_treated_in",
                "evidence_text": first_support.context_snippet,
                "confidence": 0.68,
                "ambiguity_flag": False,
                "support_candidate_ids": [
                    mention.candidate_id
                    for mention in sorted(
                        question_mentions,
                        key=lambda item: item.candidate_id,
                    )
                ],
            },
        )

    proposal_payloads.sort(
        key=lambda payload: (
            str(payload["source_passage_id"]),
            str(payload["subject_id"]),
            str(payload["relation_type"]),
            str(payload["object_id"]),
            str(payload["proposal_method"]),
        )
    )
    proposals: list[CorpusCandidateRelationProposalRecord] = []
    counters: dict[str, int] = defaultdict(int)
    for payload in proposal_payloads:
        passage_id = str(payload["source_passage_id"])
        counters[passage_id] += 1
        proposals.append(
            CorpusCandidateRelationProposalRecord.model_validate(
                {
                    "proposal_id": f"candidate.proposal.{passage_id}.r{counters[passage_id]:02d}",
                    **payload,
                }
            )
        )
    return proposals


def build_candidate_terms(
    registry: dict[str, CorpusConceptRecord],
    alias_overrides: dict[str, dict[str, object]],
) -> list[CandidateTerm]:
    """Compile deterministic candidate term patterns from the registry and alias overrides."""

    terms: list[CandidateTerm] = []
    seen: set[tuple[str, tuple[str, ...], str]] = set()

    for label, target in sorted(alias_overrides["exact"].items()):
        if not isinstance(target, str):
            continue
        concept = registry.get(target)
        if concept is None:
            continue
        terms.append(
            make_candidate_term(
                label=label,
                concept_ids=(target,),
                proposed_node_type=concept.node_type,
                match_method="override_exact",
                ambiguity_flag=False,
                seen=seen,
            )
        )
    for label, targets in sorted(alias_overrides["ambiguous"].items()):
        if not isinstance(targets, list):
            continue
        concept_ids = tuple(sorted(str(item) for item in targets))
        proposed_node_type = infer_shared_node_type(registry, concept_ids)
        terms.append(
            make_candidate_term(
                label=label,
                concept_ids=concept_ids,
                proposed_node_type=proposed_node_type,
                match_method="override_ambiguous",
                ambiguity_flag=True,
                seen=seen,
            )
        )
    for concept in sorted(registry.values(), key=lambda item: item.concept_id):
        labels = DETECTION_LABEL_OVERRIDES.get(
            concept.concept_id,
            detection_labels_for_concept(concept),
        )
        for label in labels:
            terms.append(
                make_candidate_term(
                    label=label,
                    concept_ids=(concept.concept_id,),
                    proposed_node_type=concept.node_type,
                    match_method="registry_label",
                    ambiguity_flag=False,
                    seen=seen,
                )
            )
    return sorted(
        [term for term in terms if term.label],
        key=lambda item: (-len(item.label), item.label.casefold(), item.concept_ids),
    )


def make_candidate_term(
    *,
    label: str,
    concept_ids: tuple[str, ...],
    proposed_node_type: PilotNodeType | None,
    match_method: str,
    ambiguity_flag: bool,
    seen: set[tuple[str, tuple[str, ...], str]],
) -> CandidateTerm:
    key = (normalize_lookup_text(label), concept_ids, match_method)
    if key in seen:
        return CandidateTerm("", tuple(), None, match_method, ambiguity_flag, re.compile(r"$^"))
    seen.add(key)
    pattern = compile_label_pattern(label)
    return CandidateTerm(
        label=label,
        concept_ids=concept_ids,
        proposed_node_type=proposed_node_type,
        match_method=match_method,
        ambiguity_flag=ambiguity_flag,
        pattern=pattern,
    )


def detection_labels_for_concept(concept: CorpusConceptRecord) -> list[str]:
    """Choose conservative detection labels for one registry concept."""

    labels = [concept.canonical_label, *concept.aliases]
    chosen: list[str] = []
    for label in labels:
        normalized_label = normalize_lookup_text(label)
        if " " not in normalized_label and normalized_label in SUPPRESSED_SINGLE_TOKEN_LABELS:
            continue
        chosen.append(label)
    return chosen


def compile_label_pattern(label: str) -> re.Pattern[str]:
    escaped = re.escape(label)
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def select_non_overlapping_matches(
    matches: list[tuple[int, int, str, CandidateTerm]]
) -> list[tuple[int, int, str, CandidateTerm]]:
    """Keep longest deterministic matches when labels overlap."""

    accepted: list[tuple[int, int, str, CandidateTerm]] = []
    for match in sorted(
        matches,
        key=lambda item: (
            item[0],
            -(item[1] - item[0]),
            item[3].ambiguity_flag,
            item[2].casefold(),
        ),
    ):
        start, end, _matched_text, _term = match
        if any(
            not (end <= existing_start or start >= existing_end)
            for existing_start, existing_end, *_ in accepted
        ):
            continue
        accepted.append(match)
    accepted.sort(key=lambda item: (item[0], item[1], item[2].casefold()))
    return accepted


def mention_confidence(term: CandidateTerm) -> float:
    if term.ambiguity_flag:
        return 0.52
    if term.match_method.startswith("override"):
        return 0.9
    return 0.78


def context_snippet(text: str, start: int, end: int, window: int = 90) -> str:
    snippet_start = max(0, start - window)
    snippet_end = min(len(text), end + window)
    return text[snippet_start:snippet_end].strip()


def infer_shared_node_type(
    registry: dict[str, CorpusConceptRecord],
    concept_ids: tuple[str, ...],
) -> PilotNodeType | None:
    node_types = {
        registry[concept_id].node_type
        for concept_id in concept_ids
        if concept_id in registry
    }
    if len(node_types) == 1:
        return next(iter(node_types))
    return None


def group_mentions_by_article(
    passage: SegmentRecord,
    mentions: list[CorpusCandidateMentionRecord],
) -> dict[str, list[CorpusCandidateMentionRecord]]:
    grouped: dict[str, list[CorpusCandidateMentionRecord]] = defaultdict(list)
    for mention in mentions:
        if mention.proposed_concept_id is None:
            continue
        grouped[mention.proposed_concept_id].append(mention)
    return grouped


def should_propose_article_treated_in(
    passage: SegmentRecord,
    support_mentions: list[CorpusCandidateMentionRecord],
) -> bool:
    if passage.segment_type == "resp":
        return True
    return len(support_mentions) >= 2


def nearest_mention_before(
    mentions: list[CorpusCandidateMentionRecord],
    index: int,
) -> CorpusCandidateMentionRecord | None:
    candidates = [mention for mention in mentions if mention.char_end <= index]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.char_end)


def nearest_mention_after(
    mentions: list[CorpusCandidateMentionRecord],
    index: int,
) -> CorpusCandidateMentionRecord | None:
    candidates = [mention for mention in mentions if mention.char_start >= index]
    if not candidates:
        return None
    return min(candidates, key=lambda item: item.char_start)


def add_proposal(
    payloads: list[dict[str, object]],
    seen: set[tuple[str, str, str, str, str]],
    payload: dict[str, object],
) -> None:
    key = (
        str(payload["source_passage_id"]),
        str(payload["subject_id"]),
        str(payload["relation_type"]),
        str(payload["object_id"]),
        str(payload["proposal_method"]),
    )
    if key in seen:
        return
    seen.add(key)
    payloads.append(payload)
