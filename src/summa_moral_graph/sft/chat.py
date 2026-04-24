"""Interactive chat helpers for talking to local Christian virtue adapters.

The SFT benchmark answers are intentionally terse and citation-shaped, which is useful for
evaluation but can make direct chat feel robotic. This module adds a chat-specific evidence and
style layer so the same local adapter answers user questions more like a careful teacher:

- retrieve likely relevant reviewed evidence and source passages;
- ask the model to answer directly in natural prose rather than benchmark boilerplate;
- rewrite or scrub low-quality outputs when they still sound like benchmark templates.
"""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..models.records import SegmentRecord
from ..utils.paths import REPO_ROOT
from .config import InferenceConfig, SourceTractConfig, load_dataset_build_config
from .filters import apply_annotation_filters
from .inference import (
    _align_generation_config,
    _clean_assistant_text,
    _detect_runtime,
    _render_prompt,
    ensure_inference_dependencies,
)
from .loaders import load_corpus_context, load_doctrinal_annotation_sources
from .run_layout import (
    build_environment_snapshot,
    create_timestamped_run_dir,
    dataset_manifest_path,
    iso_timestamp,
    run_artifacts_for_dir,
    write_config_snapshot,
    write_json,
)
from .utils import relation_sentence

DEFAULT_CHAT_OUTPUT_ROOT = (
    REPO_ROOT / "runs" / "christian_virtue" / "qwen2_5_1_5b_instruct" / "full_corpus_chat"
)
DEFAULT_CHAT_EVIDENCE_CONFIG_PATH = REPO_ROOT / "configs" / "sft" / "christian_virtue_v1.yaml"
DEFAULT_CHAT_SUPPLEMENTAL_ANNOTATION_PATHS = (
    REPO_ROOT / "data" / "gold" / "pilot_reviewed_doctrinal_annotations.jsonl",
)
DEFAULT_CHAT_SYSTEM_PROMPT = (
    "You are an Aquinas-grounded Christian virtue assistant trained on reviewed, passage-grounded "
    "Summa Moral Graph supervision. Answer like a careful teacher, not like a benchmark template. "
    "Answer the user's question in the first sentence, then give one to three sentences of "
    "Aquinas-grounded explanation or distinction. Use natural prose, Aquinas's own categories, "
    "and concise citation blocks. Never say 'According to the reviewed passage', "
    "'According to the cited passage', 'The passage states this directly', "
    "'The reviewed claim is framed as...', or 'Article X explicitly says'. Do not talk about "
    "support types, review layers, or dataset metadata. For why or how questions, explain the "
    "reason or practical implication instead of giving only a label. If the reviewed evidence is "
    "partial or unclear, say so plainly instead of pretending certainty."
)
CHAT_TEMPLATE_MARKERS = (
    "according to the reviewed passage",
    "according to the cited passage",
    "the passage states this directly",
    "the reviewed claim is framed as",
    "support type",
    "review layer",
)
CHAT_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "according",
        "an",
        "and",
        "are",
        "as",
        "at",
        "by",
        "does",
        "from",
        "for",
        "how",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "question",
        "the",
        "their",
        "them",
        "this",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
    }
)
WORD_RE = re.compile(r"[a-z0-9]+")
PASSAGE_ID_RE = re.compile(r"st\.(?:i|i-ii|ii-ii|iii|supplement)\.q\d{3}\.a\d{3}\.(?:resp|ad\d+)")
BOILERPLATE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(?i)\bAccording to the (?:reviewed|cited) passage,\s*"),
        "",
    ),
    (
        re.compile(r"(?i)\bThe passage states this directly\.?\s*"),
        "",
    ),
    (
        re.compile(
            r"(?i)\bThe reviewed claim is framed as a strong textual inference from "
            r"Aquinas's wording, not as a free-standing extrapolation\.?\s*"
        ),
        "",
    ),
    (
        re.compile(r"(?i)\b(?:Article|Question)\s+\d+\s+explicitly\s+(?:says|states|treats|describes)\s+(?:that\s+)?"),
        "",
    ),
    (
        re.compile(r"(?i)\bAquinas\s+explicitly\s+(?:says|states|concludes|treats|describes)\s+(?:that\s+)?"),
        "",
    ),
)


@dataclass(frozen=True)
class ChatEvidenceAnnotation:
    annotation_id: str
    subject_label: str
    subject_type: str
    relation_type: str
    object_label: str
    object_type: str
    support_type: str
    evidence_rationale: str
    evidence_text: str
    tract_display_label: str
    question_title: str
    article_title: str
    source_passage_id: str
    source_passage_citation_label: str
    source_passage_text: str
    source_passage_url: str
    subject_tokens: frozenset[str]
    object_tokens: frozenset[str]
    question_tokens: frozenset[str]
    article_tokens: frozenset[str]
    evidence_tokens: frozenset[str]


@dataclass(frozen=True)
class ChatPassageEntry:
    record: SegmentRecord
    question_tokens: frozenset[str]
    article_tokens: frozenset[str]
    text_tokens: frozenset[str]


@dataclass(frozen=True)
class ChatEvidenceStore:
    annotations: tuple[ChatEvidenceAnnotation, ...]
    passages: tuple[ChatPassageEntry, ...]
    passage_lookup: dict[str, ChatPassageEntry]


@dataclass(frozen=True)
class ChatEvidenceBundle:
    query: str
    annotations: tuple[ChatEvidenceAnnotation, ...]
    passages: tuple[ChatPassageEntry, ...]


@dataclass(frozen=True)
class ChatCuratedDefinitionAnswer:
    passage_ids: tuple[str, ...]
    lead: str
    explanation: tuple[str, ...] = ()
    required_snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChatCuratedComparisonAnswer:
    passage_ids: tuple[str, ...]
    body: tuple[str, ...]
    required_snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChatCuratedWhyAnswer:
    passage_ids: tuple[str, ...]
    body: tuple[str, ...]
    required_snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChatCuratedGuidanceAnswer:
    passage_ids: tuple[str, ...]
    body: tuple[str, ...]
    required_snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChatCuratedPracticalAnswer:
    passage_ids: tuple[str, ...]
    body: tuple[str, ...]
    required_snippets: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChatRelationQuery:
    subject_phrase: str
    object_phrase: str | None = None
    relation_types: frozenset[str] = frozenset()
    preferred_object_type: str | None = None


CURATED_DEFINITION_ANSWERS: dict[str, ChatCuratedDefinitionAnswer] = {
    "justice": ChatCuratedDefinitionAnswer(
        passage_ids=("st.ii-ii.q058.a001.resp",),
        lead="Justice is the virtue by which a person renders to each one what is due.",
        explanation=(
            "For Aquinas, its proper matter is our dealings with others, and the just act must be "
            "voluntary, stable, and firm.",
        ),
        required_snippets=("rendering to each one his right",),
    ),
    "mercy": ChatCuratedDefinitionAnswer(
        passage_ids=("st.ii-ii.q030.a001.resp", "st.ii-ii.q030.a003.resp"),
        lead="Mercy is compassionate sorrow for another's distress, moving us to help if we can.",
        explanation=(
            "Aquinas treats mercy as a virtue when this compassion is ruled by reason and does not "
            "undo justice.",
        ),
        required_snippets=(
            "mercy is heartfelt sympathy for another's distress",
            "justice is safeguarded",
        ),
    ),
    "prudence": ChatCuratedDefinitionAnswer(
        passage_ids=("st.ii-ii.q047.a008.resp", "st.ii-ii.q047.a002.resp"),
        lead="Prudence is right reason applied to action.",
        explanation=(
            "For Aquinas, it belongs to the practical reason: it takes counsel well, judges well, "
            "and directs action toward the good.",
        ),
        required_snippets=(
            "prudence is right reason applied to action",
            "prudence resides only in the practical reason",
        ),
    ),
    "sin": ChatCuratedDefinitionAnswer(
        passage_ids=("st.i-ii.q071.a006.resp",),
        lead="Sin is a bad human act contrary to reason and to the eternal law.",
        explanation=(
            "In Aquinas's account, it is a voluntary act that departs from its proper rule and "
            "measure.",
        ),
        required_snippets=(
            "sin is nothing else than a bad human act",
            "contrary to the eternal law",
        ),
    ),
}

CURATED_COMPARISON_ANSWERS: dict[tuple[str, str], ChatCuratedComparisonAnswer] = {
    ("justice", "mercy"): ChatCuratedComparisonAnswer(
        passage_ids=(
            "st.ii-ii.q058.a001.resp",
            "st.ii-ii.q030.a001.resp",
            "st.ii-ii.q030.a003.resp",
        ),
        body=(
            "Justice gives each person what is due, whereas mercy responds to another's distress "
            "with compassionate help.",
            "In Aquinas, mercy is virtuous when it is ruled by reason and does not violate "
            "justice, so mercy perfects rather than cancels justice.",
        ),
        required_snippets=(
            "rendering to each one his right",
            "mercy is heartfelt sympathy for another's distress",
            "justice is safeguarded",
        ),
    ),
}

CURATED_WHY_ANSWERS: dict[str, ChatCuratedWhyAnswer] = {
    "prudence": ChatCuratedWhyAnswer(
        passage_ids=(
            "st.ii-ii.q047.a008.resp",
            "st.ii-ii.q047.a006.resp",
            "st.ii-ii.q047.a007.resp",
        ),
        body=(
            (
                "Prudence is necessary for the moral life because it is right reason "
                "applied to action."
            ),
            "For Aquinas, the moral virtues aim at the good according to reason, but prudence "
            "judges the fitting means and directs action in concrete cases.",
        ),
        required_snippets=(
            "prudence is right reason applied to action",
            "it belongs to the ruling of prudence to decide in what manner and by what means",
        ),
    ),
    "envy": ChatCuratedWhyAnswer(
        passage_ids=("st.ii-ii.q036.a001.resp", "st.ii-ii.q036.a004.resp"),
        body=(
            (
                "Envy is a vice because it grieves over another person's good as "
                "though that good were your own loss."
            ),
            (
                "Aquinas treats that sorrow as disordered, since it resents a "
                "neighbor's excellence instead of rejoicing in what is good."
            ),
        ),
        required_snippets=(
            "envy grieves for another's good",
            "another's good may be reckoned as being one's own evil",
        ),
    ),
}

CURATED_GUIDANCE_ANSWERS: dict[str | tuple[str, str], ChatCuratedGuidanceAnswer] = {
    "temperance": ChatCuratedGuidanceAnswer(
        passage_ids=("st.ii-ii.q141.a001.resp", "st.ii-ii.q141.a006.resp"),
        body=(
            (
                "To practice temperance, Aquinas would have you let reason set the "
                "measure of pleasure instead of letting pleasure rule you."
            ),
            (
                "Temperance moderates desire, and it uses pleasurable things only as "
                "far as the needs of life rightly require."
            ),
        ),
        required_snippets=(
            "moderation or temperateness, which reason causes",
            "uses them only for as much as the need of this life requires",
        ),
    ),
    ("justice", "mercy"): ChatCuratedGuidanceAnswer(
        passage_ids=(
            "st.ii-ii.q058.a001.resp",
            "st.ii-ii.q030.a001.resp",
            "st.ii-ii.q030.a003.resp",
        ),
        body=(
            (
                "A Christian should not treat justice and mercy as rivals: justice "
                "gives what is due, and mercy responds to distress with compassionate help."
            ),
            (
                "In Aquinas, mercy is virtuous precisely when it is ruled by reason "
                "and justice is safeguarded."
            ),
        ),
        required_snippets=(
            "rendering to each one his right",
            "mercy is heartfelt sympathy for another's distress",
            "justice is safeguarded",
        ),
    ),
}

CURATED_PRACTICAL_ANSWERS: dict[str, ChatCuratedPracticalAnswer] = {
    "anger": ChatCuratedPracticalAnswer(
        passage_ids=("st.ii-ii.q158.a001.resp", "st.ii-ii.q157.a001.resp"),
        body=(
            (
                "Aquinas would not tell you simply to suppress anger, but to bring "
                "it under right reason."
            ),
            (
                "Anger can be fitting when it follows reason, but meekness checks "
                "the first onrush of anger so the desire for revenge does not outrun "
                "what is just."
            ),
        ),
        required_snippets=(
            "if one is angry in accordance with right reason, one's anger is deserving of praise",
            "meekness properly mitigates the passion of anger",
        ),
    ),
    "envy": ChatCuratedPracticalAnswer(
        passage_ids=("st.ii-ii.q036.a001.resp", "st.ii-ii.q028.a001.resp"),
        body=(
            (
                "Aquinas would first tell you to name that movement honestly: if "
                "another person's good feels like your own loss, that is envy."
            ),
            (
                "The remedy is to reorder the heart by charity, because charity "
                "rejoices in a neighbor's good, whereas envy sorrows over it."
            ),
        ),
        required_snippets=(
            "envy grieves for another's good",
            "joy is caused by love",
        ),
    ),
    "temperance": ChatCuratedPracticalAnswer(
        passage_ids=("st.ii-ii.q141.a001.resp", "st.ii-ii.q141.a006.resp"),
        body=(
            (
                "To practice temperance, let reason set the measure of pleasure "
                "instead of letting pleasure rule you."
            ),
            (
                "Aquinas treats temperance as moderated desire, so pleasurable "
                "things should be used only as far as the needs of life rightly require."
            ),
        ),
        required_snippets=(
            "temperance evidently inclines man to this",
            "uses them only for as much as the need of this life requires",
        ),
    ),
    "fear_and_courage": ChatCuratedPracticalAnswer(
        passage_ids=("st.ii-ii.q123.a001.resp", "st.ii-ii.q123.a012.resp"),
        body=(
            (
                "Aquinas would not say courage means feeling no fear; he would say "
                "fortitude keeps you from abandoning reason because of difficulty or danger."
            ),
            (
                "So the question is not whether the situation feels hard, but "
                "whether fear is pulling you away from the good that right reason requires."
            ),
        ),
        required_snippets=(
            "through the will being disinclined to follow that which is in accordance with reason",
            (
                "fear of dangers of death has the greatest power to make man "
                "recede from the good of reason"
            ),
        ),
    ),
}


def _chat_tokens(text: str) -> frozenset[str]:
    tokens = [
        token
        for token in WORD_RE.findall(text.lower())
        if len(token) > 1 and token not in CHAT_STOPWORDS
    ]
    return frozenset(tokens)


def _normalized_label(text: str) -> str:
    return " ".join(WORD_RE.findall(text.lower()))


def _question_phrases(query: str) -> list[str]:
    normalized = " ".join(query.lower().split())
    phrases: list[str] = []
    patterns = [
        r"what is (?P<value>.+?)(?: according to aquinas)?\??$",
        r"who is (?P<value>.+?)(?: according to aquinas)?\??$",
        r"what are (?P<value>.+?)(?: according to aquinas)?\??$",
        r"define (?P<value>.+?)\??$",
        r"how does (?P<left>.+?) differ from (?P<right>.+?)\??$",
        r"what is the difference between (?P<left>.+?) and (?P<right>.+?)\??$",
    ]
    for pattern in patterns:
        match = re.match(pattern, normalized)
        if match is None:
            continue
        for value in match.groupdict().values():
            cleaned = value.strip(" ?.,")
            if cleaned:
                phrases.append(cleaned)
    return phrases


def _query_mode(query: str) -> str:
    normalized = " ".join(query.lower().split())
    if re.match(r"what is .+|who is .+|what are .+|define .+", normalized):
        return "definition"
    if " differ from " in normalized or "difference between" in normalized:
        return "comparison"
    if (
        normalized.startswith("i ")
        or "what should i do" in normalized
        or "how should i respond" in normalized
        or "hard situation" in normalized
    ):
        return "practical"
    if normalized.startswith("why "):
        return "why"
    if normalized.startswith("how "):
        if any(
            marker in normalized
            for marker in (
                " classify ",
                " related to ",
                " relation to ",
                " annexed to ",
                " part of ",
            )
        ):
            return "relation"
        return "guidance"
    if any(
        marker in normalized
        for marker in (
            "what virtue opposes",
            "what vice opposes",
            "what is opposed to",
            "where does ",
            "where is ",
            "what is annexed to",
            "how is ",
            "what kind of part",
        )
    ):
        return "relation"
    return "generic"


def _extract_why_phrase(query: str) -> str | None:
    normalized = " ".join(query.lower().split())
    patterns = [
        r"why is (?P<value>.+?) necessary(?: for .+)?\??$",
        r"why is (?P<value>.+?) a vice\??$",
        r"why is (?P<value>.+?) virtuous\??$",
        r"why is (?P<value>.+?) important\??$",
        r"why is (?P<value>.+?)\??$",
        r"why does (?P<value>.+?) matter\??$",
    ]
    for pattern in patterns:
        match = re.match(pattern, normalized)
        if match is not None:
            return match.group("value").strip(" ?.,")
    return None


def _extract_practical_key(query: str) -> str | None:
    normalized = " ".join(query.lower().split())
    if any(token in normalized for token in ("anger", "angry", "revenge")):
        return "anger"
    if any(token in normalized for token in ("jealous", "envy", "envious")):
        return "envy"
    if "temperance" in normalized or any(
        token in normalized for token in ("overindulge", "indulge", "pleasure")
    ):
        return "temperance"
    if "fear" in normalized and any(
        token in normalized for token in ("courage", "fortitude", "hard situation", "hard")
    ):
        return "fear_and_courage"
    return None


def _extract_guidance_key(query: str) -> str | tuple[str, str] | None:
    normalized = " ".join(query.lower().split())
    pair_patterns = [
        (
            r"how should (?:a christian )?think about (?P<left>.+?) and "
            r"(?P<right>.+?)(?: together)?\??$"
        ),
        r"how should we think about (?P<left>.+?) and (?P<right>.+?)(?: together)?\??$",
        r"how do (?P<left>.+?) and (?P<right>.+?) fit together\??$",
    ]
    for pattern in pair_patterns:
        match = re.match(pattern, normalized)
        if match is not None:
            left = match.group("left").strip(" ?.,")
            right = match.group("right").strip(" ?.,")
            return (
                min(_normalized_label(left), _normalized_label(right)),
                max(_normalized_label(left), _normalized_label(right)),
            )

    single_patterns = [
        r"how can i practice (?P<value>.+?)(?: according to aquinas)?\??$",
        r"how should i practice (?P<value>.+?)(?: according to aquinas)?\??$",
        r"how can someone practice (?P<value>.+?)(?: according to aquinas)?\??$",
    ]
    for pattern in single_patterns:
        match = re.match(pattern, normalized)
        if match is not None:
            return _normalized_label(match.group("value").strip(" ?.,"))
    return None


def _extract_relation_query(query: str) -> ChatRelationQuery | None:
    normalized = " ".join(query.lower().split())
    pair_patterns = [
        (
            r"how does aquinas classify (?P<subject>.+?) within (?P<object>.+?)\??$",
            frozenset(
                {
                    "subjective_part_of",
                    "integral_part_of",
                    "potential_part_of",
                    "species_of",
                }
            ),
            None,
        ),
        (
            r"how is (?P<subject>.+?) related to (?P<object>.+?)\??$",
            frozenset(
                {
                    "annexed_to",
                    "directed_to",
                    "caused_by",
                    "resides_in",
                    "subjective_part_of",
                    "potential_part_of",
                    "integral_part_of",
                    "species_of",
                }
            ),
            None,
        ),
    ]
    for pattern, relation_types, preferred_object_type in pair_patterns:
        match = re.match(pattern, normalized)
        if match is not None:
            return ChatRelationQuery(
                subject_phrase=match.group("subject").strip(" ?.,"),
                object_phrase=match.group("object").strip(" ?.,"),
                relation_types=relation_types,
                preferred_object_type=preferred_object_type,
            )

    single_patterns = [
        (
            r"what virtue opposes (?P<subject>.+?)\??$",
            frozenset({"opposed_by", "contrary_to", "excess_opposed_to", "deficiency_opposed_to"}),
            "virtue",
        ),
        (
            r"what vice opposes (?P<subject>.+?)\??$",
            frozenset({"opposed_by", "contrary_to", "excess_opposed_to", "deficiency_opposed_to"}),
            "vice",
        ),
        (
            r"what is opposed to (?P<subject>.+?)\??$",
            frozenset({"opposed_by", "contrary_to", "excess_opposed_to", "deficiency_opposed_to"}),
            None,
        ),
        (
            r"where does (?P<subject>.+?) reside\??$",
            frozenset({"resides_in"}),
            None,
        ),
        (
            r"where is (?P<subject>.+?)\??$",
            frozenset({"resides_in"}),
            None,
        ),
        (
            r"what is (?P<subject>.+?) annexed to\??$",
            frozenset({"annexed_to"}),
            None,
        ),
    ]
    for pattern, relation_types, preferred_object_type in single_patterns:
        match = re.match(pattern, normalized)
        if match is not None:
            return ChatRelationQuery(
                subject_phrase=match.group("subject").strip(" ?.,"),
                relation_types=relation_types,
                preferred_object_type=preferred_object_type,
            )
    return None


def _overlap_score(
    query_tokens: frozenset[str],
    candidate_tokens: frozenset[str],
    weight: float,
) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    return weight * float(len(query_tokens & candidate_tokens))


def _annotation_score(
    annotation: ChatEvidenceAnnotation,
    *,
    query: str,
    query_tokens: frozenset[str],
    query_phrases: list[str],
) -> float:
    lowered_query = _normalized_label(query)
    score = 0.0
    score += _overlap_score(query_tokens, annotation.subject_tokens, 4.0)
    score += _overlap_score(query_tokens, annotation.object_tokens, 3.5)
    score += _overlap_score(query_tokens, annotation.question_tokens, 2.5)
    score += _overlap_score(query_tokens, annotation.article_tokens, 1.75)
    score += _overlap_score(query_tokens, annotation.evidence_tokens, 1.0)
    for phrase in query_phrases:
        if phrase == _normalized_label(annotation.subject_label):
            score += 14.0
        elif phrase and phrase in _normalized_label(annotation.subject_label):
            score += 10.0
        if phrase == _normalized_label(annotation.object_label):
            score += 11.0
        elif phrase and phrase in _normalized_label(annotation.object_label):
            score += 7.0
        if phrase and phrase in _normalized_label(annotation.question_title):
            score += 4.0
    if _normalized_label(annotation.subject_label) in lowered_query:
        score += 6.0
    if _normalized_label(annotation.object_label) in lowered_query:
        score += 4.0
    if annotation.relation_type == "treated_in":
        score -= 3.0
    if annotation.support_type == "explicit_textual":
        score += 0.25
    return score


def _passage_score(
    passage: ChatPassageEntry,
    *,
    query: str,
    query_tokens: frozenset[str],
    query_phrases: list[str],
) -> float:
    lowered_query = _normalized_label(query)
    question_label = _normalized_label(passage.record.question_title)
    article_label = _normalized_label(passage.record.article_title)
    score = 0.0
    score += _overlap_score(query_tokens, passage.question_tokens, 5.0)
    score += _overlap_score(query_tokens, passage.article_tokens, 3.0)
    score += _overlap_score(query_tokens, passage.text_tokens, 1.0)
    if question_label and question_label in lowered_query:
        score += 6.0
    if article_label and article_label in lowered_query:
        score += 3.0
    for phrase in query_phrases:
        if phrase and phrase in question_label:
            score += 9.0
        if phrase and phrase in article_label:
            score += 5.0
    if passage.record.segment_type == "resp":
        score += 1.0
    return score


def _truncate_for_prompt(text: str, *, limit: int = 720) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "…"


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"])", " ".join(text.split()))
    return [part.strip() for part in parts if part.strip()]


def _clean_extracted_sentence(sentence: str) -> str:
    cleaned = sentence.strip()
    cleaned = re.sub(r"^As [^,]+,\s*", "", cleaned)
    cleaned = re.sub(r"^(Hence|Wherefore|Therefore|Accordingly|Consequently)\s+", "", cleaned)
    cleaned = re.sub(r"^It follows therefore that\s+", "", cleaned)
    cleaned = re.sub(r"^(Now|And)\s+", "", cleaned)
    cleaned = re.sub(r"^it is evident that\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^it is manifest that\s+", "", cleaned, flags=re.IGNORECASE)
    if "rendering to each one his right" in cleaned.lower():
        cleaned = "Justice renders to each one his right."
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _sentence_score_for_phrase(sentence: str, phrase: str) -> float:
    lowered_sentence = _normalized_label(sentence)
    lowered_phrase = _normalized_label(phrase)
    score = 0.0
    if lowered_phrase and lowered_phrase in lowered_sentence:
        score += 8.0
    if any(name in lowered_sentence for name in ("augustine", "philosopher", "isidore")):
        score -= 5.0
    if any(
        marker in lowered_sentence
        for marker in (
            "aforesaid definition",
            "as stated above",
            "reply to objection",
            "article ",
        )
    ):
        score -= 3.0
    if " is " in lowered_sentence or "nothing else than" in lowered_sentence:
        score += 2.0
    if any(token in lowered_sentence for token in ("because", "therefore", "hence", "wherefore")):
        score += 1.0
    score -= len(sentence) / 500.0
    return score


def _best_sentence_for_phrase(text: str, phrase: str) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return ""
    ranked = sorted(
        sentences,
        key=lambda sentence: _sentence_score_for_phrase(sentence, phrase),
        reverse=True,
    )
    return _clean_extracted_sentence(ranked[0])


def _top_sentences_for_phrase(text: str, phrase: str, limit: int = 2) -> list[str]:
    sentences = _split_sentences(text)
    ranked = sorted(
        sentences,
        key=lambda sentence: _sentence_score_for_phrase(sentence, phrase),
        reverse=True,
    )
    cleaned: list[str] = []
    for sentence in ranked:
        normalized = _clean_extracted_sentence(sentence)
        if not normalized or normalized in cleaned:
            continue
        cleaned.append(normalized)
        if len(cleaned) >= limit:
            break
    return cleaned


def _phrase_match_score(passage: ChatPassageEntry, phrase: str) -> float:
    lowered_phrase = _normalized_label(phrase)
    question_label = _normalized_label(passage.record.question_title)
    article_label = _normalized_label(passage.record.article_title)
    score = 0.0
    if question_label == lowered_phrase:
        score += 24.0
    elif lowered_phrase and lowered_phrase in question_label:
        score += 16.0
    if article_label == lowered_phrase:
        score += 18.0
    elif lowered_phrase and lowered_phrase in article_label:
        score += 12.0
    if lowered_phrase and lowered_phrase in _normalized_label(passage.record.text):
        score += 6.0
    if passage.record.segment_type == "resp":
        score += 1.0
    return score


def _best_passage_for_phrase(bundle: ChatEvidenceBundle, phrase: str) -> ChatPassageEntry | None:
    ranked = sorted(
        bundle.passages,
        key=lambda passage: _phrase_match_score(passage, phrase),
        reverse=True,
    )
    if not ranked:
        return None
    if _phrase_match_score(ranked[0], phrase) <= 0:
        return None
    return ranked[0]


def _top_phrase_passages(
    bundle: ChatEvidenceBundle,
    phrase: str,
    limit: int = 2,
) -> list[ChatPassageEntry]:
    ranked = sorted(
        bundle.passages,
        key=lambda passage: _phrase_match_score(passage, phrase),
        reverse=True,
    )
    return [passage for passage in ranked[:limit] if _phrase_match_score(passage, phrase) > 0]


def _global_passage_score_for_phrase(
    passage: ChatPassageEntry,
    phrase: str,
    *,
    mode: str,
) -> float:
    lowered_phrase = _normalized_label(phrase)
    question_label = _normalized_label(passage.record.question_title)
    article_label = _normalized_label(passage.record.article_title)
    score = _phrase_match_score(passage, phrase)
    if question_label.startswith(lowered_phrase):
        score += 12.0
    if article_label.startswith(f"what is {lowered_phrase}"):
        score += 18.0
    if f"definition of {lowered_phrase}" in article_label:
        score += 20.0
    if f"is {lowered_phrase}" in article_label:
        score += 10.0
    best_sentence = _best_sentence_for_phrase(passage.record.text, phrase)
    score += _sentence_score_for_phrase(best_sentence, phrase)
    if passage.record.segment_type != "resp":
        score -= 8.0
    score -= float(passage.record.article_number) / 4.0
    if mode == "definition" and "definition" in article_label:
        score += 6.0
    return score


def _global_annotation_score(
    annotation: ChatEvidenceAnnotation,
    *,
    subject_phrase: str,
    object_phrase: str | None,
    relation_types: frozenset[str],
    preferred_object_type: str | None,
) -> float:
    normalized_subject = _normalized_label(subject_phrase)
    normalized_object = _normalized_label(object_phrase or "")
    subject_label = _normalized_label(annotation.subject_label)
    object_label = _normalized_label(annotation.object_label)
    score = 0.0
    if subject_label == normalized_subject:
        score += 18.0
    elif normalized_subject and normalized_subject in subject_label:
        score += 10.0
    elif normalized_subject and normalized_subject in object_label:
        score += 6.0
    if normalized_object:
        if object_label == normalized_object:
            score += 12.0
        elif normalized_object in object_label:
            score += 7.0
        if normalized_object and normalized_object in subject_label:
            score += 3.0
    if relation_types and annotation.relation_type in relation_types:
        score += 10.0
    if preferred_object_type is not None and annotation.object_type == preferred_object_type:
        score += 5.0
    return score


def _find_global_relation_annotations(
    relation_query: ChatRelationQuery,
    *,
    limit: int = 3,
) -> list[ChatEvidenceAnnotation]:
    store = load_chat_evidence_store()
    candidate_annotations = [
        annotation
        for annotation in store.annotations
        if (
            not relation_query.relation_types
            or annotation.relation_type in relation_query.relation_types
        )
    ]
    ranked = sorted(
        candidate_annotations,
        key=lambda annotation: _global_annotation_score(
            annotation,
            subject_phrase=relation_query.subject_phrase,
            object_phrase=relation_query.object_phrase,
            relation_types=relation_query.relation_types,
            preferred_object_type=relation_query.preferred_object_type,
        ),
        reverse=True,
    )
    return [
        annotation
        for annotation in ranked[:limit]
        if _global_annotation_score(
            annotation,
            subject_phrase=relation_query.subject_phrase,
            object_phrase=relation_query.object_phrase,
            relation_types=relation_query.relation_types,
            preferred_object_type=relation_query.preferred_object_type,
        )
        > 0
    ]


def _find_global_phrase_passages(
    phrase: str,
    *,
    mode: str,
    limit: int = 2,
) -> list[ChatPassageEntry]:
    store = load_chat_evidence_store()
    ranked = sorted(
        store.passages,
        key=lambda passage: _global_passage_score_for_phrase(passage, phrase, mode=mode),
        reverse=True,
    )
    return [
        passage
        for passage in ranked[:limit]
        if _global_passage_score_for_phrase(passage, phrase, mode=mode) > 0
    ]


@lru_cache(maxsize=1)
def load_chat_evidence_store(
    dataset_config_path: str = str(DEFAULT_CHAT_EVIDENCE_CONFIG_PATH),
) -> ChatEvidenceStore:
    config = load_dataset_build_config(dataset_config_path)
    corpus = load_corpus_context(config.corpus)
    loaded_annotations = load_doctrinal_annotation_sources(config.sources)
    supplemental_sources = [
        SourceTractConfig(tract="pilot", annotations_path=path)
        for path in DEFAULT_CHAT_SUPPLEMENTAL_ANNOTATION_PATHS
        if path.exists()
    ]
    if supplemental_sources:
        supplemental_annotations = load_doctrinal_annotation_sources(supplemental_sources)
        combined_annotations = [*loaded_annotations, *supplemental_annotations]
    else:
        combined_annotations = list(loaded_annotations)
    filtered_annotations = apply_annotation_filters(
        combined_annotations,
        config.filters,
    ).annotations
    deduped_annotations: list[Any] = []
    seen_annotation_ids: set[str] = set()
    for annotation in filtered_annotations:
        if annotation.annotation_id in seen_annotation_ids:
            continue
        seen_annotation_ids.add(annotation.annotation_id)
        deduped_annotations.append(annotation)

    annotations: list[ChatEvidenceAnnotation] = []
    for annotation in deduped_annotations:
        segment = corpus.segments.get(annotation.source_passage_id)
        if segment is None:
            continue
        annotations.append(
            ChatEvidenceAnnotation(
                annotation_id=annotation.annotation_id,
                subject_label=annotation.subject_label,
                subject_type=annotation.subject_type,
                relation_type=annotation.relation_type,
                object_label=annotation.object_label,
                object_type=annotation.object_type,
                support_type=annotation.support_type,
                evidence_rationale=annotation.evidence_rationale,
                evidence_text=annotation.evidence_text,
                tract_display_label=annotation.tract_display_label,
                question_title=segment.question_title,
                article_title=segment.article_title,
                source_passage_id=segment.segment_id,
                source_passage_citation_label=segment.citation_label,
                source_passage_text=segment.text,
                source_passage_url=segment.source_url,
                subject_tokens=_chat_tokens(annotation.subject_label),
                object_tokens=_chat_tokens(annotation.object_label),
                question_tokens=_chat_tokens(segment.question_title),
                article_tokens=_chat_tokens(segment.article_title),
                evidence_tokens=_chat_tokens(
                    f"{annotation.evidence_text} {annotation.evidence_rationale}"
                ),
            )
        )

    passages = tuple(
        ChatPassageEntry(
            record=segment,
            question_tokens=_chat_tokens(segment.question_title),
            article_tokens=_chat_tokens(segment.article_title),
            text_tokens=_chat_tokens(segment.text),
        )
        for segment in corpus.segments.values()
    )
    ordered_passages = tuple(
        sorted(
            passages,
            key=lambda row: (
                row.record.part_id,
                row.record.question_number,
                row.record.article_number,
                row.record.segment_type,
                row.record.segment_ordinal or 0,
            ),
        )
    )
    return ChatEvidenceStore(
        annotations=tuple(annotations),
        passages=ordered_passages,
        passage_lookup={row.record.segment_id: row for row in ordered_passages},
    )


def retrieve_chat_evidence(
    query: str,
    *,
    max_annotations: int = 3,
    max_passages: int = 3,
) -> ChatEvidenceBundle:
    store = load_chat_evidence_store()
    query_tokens = _chat_tokens(query)
    query_phrases = _question_phrases(query)

    ranked_annotations = sorted(
        (
            (
                _annotation_score(
                    annotation,
                    query=query,
                    query_tokens=query_tokens,
                    query_phrases=query_phrases,
                ),
                annotation,
            )
            for annotation in store.annotations
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    selected_annotations = tuple(
        annotation
        for score, annotation in ranked_annotations
        if score > 0
    )[:max_annotations]

    referenced_passage_ids = {annotation.source_passage_id for annotation in selected_annotations}
    ranked_passages = sorted(
        (
            (
                _passage_score(
                    passage,
                    query=query,
                    query_tokens=query_tokens,
                    query_phrases=query_phrases,
                )
                + (4.0 if passage.record.segment_id in referenced_passage_ids else 0.0),
                passage,
            )
            for passage in store.passages
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    selected_passages: list[ChatPassageEntry] = []
    for score, passage in ranked_passages:
        if score <= 0 and passage.record.segment_id not in referenced_passage_ids:
            continue
        if passage.record.segment_id in {row.record.segment_id for row in selected_passages}:
            continue
        selected_passages.append(passage)
        if len(selected_passages) >= max_passages:
            break
    return ChatEvidenceBundle(
        query=query,
        annotations=selected_annotations,
        passages=tuple(selected_passages),
    )


def render_chat_evidence_context(bundle: ChatEvidenceBundle) -> str:
    if not bundle.annotations and not bundle.passages:
        return ""

    lines = [
        "Use the reviewed evidence below to answer naturally.",
        "",
        "Answering rules:",
        "- First sentence: answer the question directly.",
        "- Then give one to three sentences of Aquinas-grounded explanation or distinction.",
        (
            "- Do not use benchmark phrases like 'According to the reviewed passage' or "
            "'The passage states this directly'."
        ),
        "- End with a short `Citations:` block.",
        "",
    ]
    if bundle.annotations:
        lines.append("Reviewed doctrinal clues:")
        for annotation in bundle.annotations:
            claim = relation_sentence(
                annotation.subject_label,
                annotation.relation_type,
                annotation.object_label,
            )
            lines.extend(
                [
                    (
                        f"- {claim} "
                        f"({annotation.source_passage_id}; "
                        f"{annotation.source_passage_citation_label})"
                    ),
                    f"  Why it matters: {annotation.evidence_rationale}",
                ]
            )
        lines.append("")
    if bundle.passages:
        lines.append("Relevant passage excerpts:")
        for passage in bundle.passages:
            lines.extend(
                [
                    (
                        f"- {passage.record.segment_id} ({passage.record.citation_label}) — "
                        f"{passage.record.question_title}"
                    ),
                    f"  {_truncate_for_prompt(passage.record.text)}",
                ]
            )
    return "\n".join(lines).strip()


def _has_explicit_evidence_context(text: str) -> bool:
    lowered = text.lower()
    return (
        "supporting passages:" in lowered
        or "passage text:" in lowered
        or "citation label:" in lowered
        or bool(PASSAGE_ID_RE.search(text))
    )


def _augment_chat_messages(
    messages: list[dict[str, str]],
) -> tuple[list[dict[str, str]], ChatEvidenceBundle | None]:
    if not messages:
        return messages, None
    last_index = -1
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].get("role") == "user":
            last_index = index
            break
    if last_index < 0:
        return messages, None

    user_text = str(messages[last_index].get("content", "")).strip()
    if not user_text or _has_explicit_evidence_context(user_text):
        return messages, None

    evidence_bundle = retrieve_chat_evidence(user_text)
    evidence_context = render_chat_evidence_context(evidence_bundle)
    if not evidence_context:
        return messages, evidence_bundle

    augmented_messages = list(messages)
    augmented_messages[last_index] = {
        **augmented_messages[last_index],
        "content": f"{user_text}\n\n{evidence_context}",
    }
    return augmented_messages, evidence_bundle


def _citation_block_from_bundle(bundle: ChatEvidenceBundle | None) -> str:
    if bundle is None:
        return ""
    seen: set[str] = set()
    citations: list[tuple[str, str]] = []
    for annotation in bundle.annotations:
        key = f"{annotation.source_passage_id}|{annotation.source_passage_citation_label}"
        if key in seen:
            continue
        seen.add(key)
        citations.append((annotation.source_passage_id, annotation.source_passage_citation_label))
    for passage in bundle.passages:
        key = f"{passage.record.segment_id}|{passage.record.citation_label}"
        if key in seen:
            continue
        seen.add(key)
        citations.append((passage.record.segment_id, passage.record.citation_label))
    if not citations:
        return ""
    lines = ["Citations:"]
    for passage_id, citation_label in citations[:4]:
        lines.append(f"- {passage_id} ({citation_label})")
    return "\n".join(lines)


def _citation_block_for_passages(passages: Sequence[ChatPassageEntry]) -> str:
    if not passages:
        return ""
    lines = ["Citations:"]
    seen: set[str] = set()
    for passage in passages:
        line = f"- {passage.record.segment_id} ({passage.record.citation_label})"
        if line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return "\n".join(lines)


def _preferred_passages_by_id(passage_ids: Sequence[str]) -> list[ChatPassageEntry]:
    store = load_chat_evidence_store()
    return [
        store.passage_lookup[passage_id]
        for passage_id in passage_ids
        if passage_id in store.passage_lookup
    ]


def _passages_cover_required_snippets(
    passages: Sequence[ChatPassageEntry],
    required_snippets: Sequence[str],
) -> bool:
    normalized_text = " ".join(_normalized_label(passage.record.text) for passage in passages)
    return all(_normalized_label(snippet) in normalized_text for snippet in required_snippets)


def _render_curated_answer(lines: Sequence[str], passages: Sequence[ChatPassageEntry]) -> str:
    body = " ".join(line.strip() for line in lines if line.strip()).strip()
    citation_block = _citation_block_for_passages(passages)
    return f"{body}\n\n{citation_block}".strip()


def _annotation_passages(
    annotation: ChatEvidenceAnnotation,
) -> list[ChatPassageEntry]:
    return _preferred_passages_by_id((annotation.source_passage_id,))


def _clean_rationale_sentence(text: str) -> str:
    cleaned = text.strip()
    replacements = (
        (r"^Q\d+\s+explicitly\s+", "Aquinas "),
        (r"^Question\s+\d+\s+explicitly\s+", "Aquinas "),
        (r"^The passage explicitly concludes that\s+", "Aquinas concludes that "),
        (r"^The passage says\s+", "Aquinas says "),
        (r"^The Augustinian definition explicitly says\s+", "Aquinas says "),
        (r"^Aquinas\s+(?:says|states|concludes)\s+that\s+", ""),
    )
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned and cleaned[-1] not in ".!?":
        cleaned = f"{cleaned}."
    return cleaned


def _relation_lead_sentence(
    annotation: ChatEvidenceAnnotation,
    query: str,
) -> str:
    normalized_query = " ".join(query.lower().split())
    subject = annotation.subject_label
    obj = annotation.object_label
    relation_type = annotation.relation_type

    if relation_type == "opposed_by":
        if any(
            marker in normalized_query
            for marker in ("what virtue opposes", "what vice opposes", "what is opposed to")
        ):
            return f"{obj} is opposed to {subject}."
        return f"{subject} is opposed by {obj}."
    if relation_type == "contrary_to":
        return f"{subject} is contrary to {obj}."
    if relation_type == "subjective_part_of":
        return f"{subject} is a subjective part of {obj} in Aquinas's classification."
    if relation_type == "integral_part_of":
        return (
            f"{subject} is an integral part of {obj}, meaning it belongs to the "
            f"conditions required for {obj}'s complete act."
        )
    if relation_type == "potential_part_of":
        return (
            f"{subject} is a potential part of {obj}, an annexed virtue that shares "
            f"{obj}'s mode in a secondary matter."
        )
    if relation_type == "annexed_to":
        return f"{subject} is annexed to {obj} as a secondary virtue."
    if relation_type == "resides_in":
        return f"{subject} resides in {obj}."
    if relation_type == "directed_to":
        return f"{subject} is directed to {obj}."
    if relation_type == "caused_by":
        return f"{subject} arises from {obj}."
    if relation_type == "species_of":
        return f"{subject} is a species of {obj}."
    return relation_sentence(subject, relation_type, obj) + "."


def _preferred_summary_from_passage(phrase: str, passage: ChatPassageEntry) -> str | None:
    normalized_phrase = _normalized_label(phrase)
    normalized_text = _normalized_label(passage.record.text)
    preferred_patterns = {
        "justice": ("rendering to each one his right", "Justice renders to each one his right."),
        "mercy": (
            "heartfelt sympathy for another's distress",
            "Mercy is heartfelt sympathy for another's distress.",
        ),
        "prudence": (
            "prudence properly speaking is in the reason",
            "Prudence, properly speaking, is in the reason.",
        ),
        "sin": (
            "sin is nothing else than a bad human act",
            "Sin is nothing else than a bad human act.",
        ),
    }
    pattern = preferred_patterns.get(normalized_phrase)
    if pattern is None:
        return None
    needle, rewritten = pattern
    if needle in normalized_text:
        return rewritten
    return None


def _deterministic_definition_answer(
    query: str,
    bundle: ChatEvidenceBundle,
) -> str | None:
    phrases = _question_phrases(query)
    if not phrases:
        return None
    phrase = phrases[0]
    normalized_phrase = _normalized_label(phrase)
    curated = CURATED_DEFINITION_ANSWERS.get(normalized_phrase)
    if curated is not None:
        curated_passages = _preferred_passages_by_id(curated.passage_ids)
        if curated_passages and _passages_cover_required_snippets(
            curated_passages,
            curated.required_snippets,
        ):
            return _render_curated_answer(
                [curated.lead, *curated.explanation],
                curated_passages,
            )

    passages = _find_global_phrase_passages(phrase, mode="definition", limit=3)
    if not passages:
        return None

    lowered_phrase = normalized_phrase

    def definition_priority(sentence: str) -> float:
        lowered = _normalized_label(sentence)
        score = 0.0
        if lowered.startswith(f"{lowered_phrase} is"):
            score += 10.0
        if lowered.startswith(lowered_phrase):
            score += 4.0
        if "nothing else than" in lowered:
            score += 6.0
        score -= len(sentence) / 250.0
        return score

    candidates: list[tuple[float, ChatPassageEntry, str, list[str]]] = []
    for passage in passages:
        top_sentences = _top_sentences_for_phrase(passage.record.text, phrase, limit=3)
        if not top_sentences:
            continue
        preferred = _preferred_summary_from_passage(phrase, passage)
        lead_sentence = preferred or max(top_sentences, key=definition_priority)
        lead_score = definition_priority(lead_sentence)
        if preferred is not None:
            lead_score += 4.0
        candidates.append((lead_score, passage, lead_sentence, top_sentences))
    if not candidates:
        return None

    _, chosen_passage, lead_sentence, chosen_top_sentences = max(
        candidates,
        key=lambda item: item[0],
    )
    answer_lines = [lead_sentence]
    seen_normalized = {_normalized_label(lead_sentence)}
    extra_candidates: list[tuple[float, str]] = []
    for sentence in chosen_top_sentences:
        normalized_sentence = _normalized_label(sentence)
        if normalized_sentence in seen_normalized:
            continue
        if any(name in normalized_sentence for name in ("augustine", "philosopher", "isidore")):
            continue
        extra_candidates.append((_sentence_score_for_phrase(sentence, phrase), sentence))
    for passage in passages:
        if passage.record.segment_id == chosen_passage.record.segment_id:
            continue
        for sentence in _top_sentences_for_phrase(passage.record.text, phrase, limit=2):
            normalized_sentence = _normalized_label(sentence)
            if normalized_sentence in seen_normalized:
                continue
            if any(name in normalized_sentence for name in ("augustine", "philosopher", "isidore")):
                continue
            extra_candidates.append((_sentence_score_for_phrase(sentence, phrase), sentence))
    if extra_candidates:
        _, best_extra = max(extra_candidates, key=lambda item: item[0])
        answer_lines.append(best_extra)
        seen_normalized.add(_normalized_label(best_extra))

    citation_block = _citation_block_for_passages([chosen_passage])
    return f"{' '.join(answer_lines)}\n\n{citation_block}".strip()


def _deterministic_comparison_answer(
    query: str,
    bundle: ChatEvidenceBundle,
) -> str | None:
    phrases = _question_phrases(query)
    if len(phrases) < 2:
        return None
    left_phrase, right_phrase = phrases[0], phrases[1]
    normalized_pair = (
        min(_normalized_label(left_phrase), _normalized_label(right_phrase)),
        max(_normalized_label(left_phrase), _normalized_label(right_phrase)),
    )
    curated = CURATED_COMPARISON_ANSWERS.get(normalized_pair)
    if curated is not None:
        curated_passages = _preferred_passages_by_id(curated.passage_ids)
        if curated_passages and _passages_cover_required_snippets(
            curated_passages,
            curated.required_snippets,
        ):
            return _render_curated_answer(curated.body, curated_passages)

    left_candidates = _find_global_phrase_passages(left_phrase, mode="comparison", limit=2)
    right_candidates = _find_global_phrase_passages(right_phrase, mode="comparison", limit=2)
    left_passage = left_candidates[0] if left_candidates else None
    right_passage = right_candidates[0] if right_candidates else None
    if left_passage is None or right_passage is None:
        return None

    left_options = _top_sentences_for_phrase(left_passage.record.text, left_phrase, limit=3)
    right_options = _top_sentences_for_phrase(right_passage.record.text, right_phrase, limit=3)
    left_sentence = _preferred_summary_from_passage(left_phrase, left_passage) or (
        min(left_options, key=len) if left_options else ""
    )
    right_sentence = _preferred_summary_from_passage(right_phrase, right_passage) or (
        min(right_options, key=len) if right_options else ""
    )
    if not left_sentence or not right_sentence:
        return None

    left_label = left_phrase.strip().capitalize()
    right_label = right_phrase.strip().capitalize()
    body = [
        f"{left_label} and {right_label} are distinct in Aquinas.",
        left_sentence,
        f"By contrast, {right_sentence[0].lower() + right_sentence[1:]}"
        if right_sentence
        else right_sentence,
    ]
    citation_block = _citation_block_for_passages([left_passage, right_passage])
    return f"{' '.join(body)}\n\n{citation_block}".strip()


def _deterministic_why_answer(
    query: str,
    bundle: ChatEvidenceBundle,
) -> str | None:
    phrase = _extract_why_phrase(query)
    if not phrase:
        return None
    normalized_phrase = _normalized_label(phrase)
    curated = CURATED_WHY_ANSWERS.get(normalized_phrase)
    if curated is not None:
        curated_passages = _preferred_passages_by_id(curated.passage_ids)
        if curated_passages and _passages_cover_required_snippets(
            curated_passages,
            curated.required_snippets,
        ):
            return _render_curated_answer(curated.body, curated_passages)

    definition = _deterministic_definition_answer(f"What is {phrase}?", bundle)
    if definition is None:
        return None
    definition_body = _chat_body(definition)
    passages = _find_global_phrase_passages(phrase, mode="definition", limit=3)
    reason_candidates: list[tuple[float, str]] = []
    for passage in passages:
        for sentence in _top_sentences_for_phrase(passage.record.text, phrase, limit=3):
            normalized_sentence = _normalized_label(sentence)
            score = _sentence_score_for_phrase(sentence, phrase)
            if any(
                marker in normalized_sentence
                for marker in (
                    "because",
                    "hence",
                    "wherefore",
                    "consequently",
                    "belongs",
                    "directs",
                )
            ):
                score += 3.0
            reason_candidates.append((score, sentence))
    if not reason_candidates:
        return definition
    _, reason_sentence = max(reason_candidates, key=lambda item: item[0])
    body = f"{definition_body} {reason_sentence}".strip()
    citation_block = _citation_block_for_passages(passages[:2])
    return f"{body}\n\n{citation_block}".strip()


def _deterministic_guidance_answer(
    query: str,
    bundle: ChatEvidenceBundle,
) -> str | None:
    key = _extract_guidance_key(query)
    if key is None:
        return None
    curated = CURATED_GUIDANCE_ANSWERS.get(key)
    if curated is not None:
        curated_passages = _preferred_passages_by_id(curated.passage_ids)
        if curated_passages and _passages_cover_required_snippets(
            curated_passages,
            curated.required_snippets,
        ):
            return _render_curated_answer(curated.body, curated_passages)
    return None


def _deterministic_practical_answer(
    query: str,
    bundle: ChatEvidenceBundle,
) -> str | None:
    key = _extract_practical_key(query)
    if key is None:
        return None
    curated = CURATED_PRACTICAL_ANSWERS.get(key)
    if curated is None:
        return None
    curated_passages = _preferred_passages_by_id(curated.passage_ids)
    if not curated_passages:
        return None
    if not _passages_cover_required_snippets(curated_passages, curated.required_snippets):
        return None
    return _render_curated_answer(curated.body, curated_passages)


def _deterministic_relation_answer(
    query: str,
    bundle: ChatEvidenceBundle,
) -> str | None:
    relation_query = _extract_relation_query(query)
    if bundle.annotations:
        candidate_annotations = list(bundle.annotations)
    else:
        candidate_annotations = []
    if relation_query is not None:
        global_candidates = _find_global_relation_annotations(relation_query)
        if global_candidates:
            candidate_annotations = global_candidates
    if not candidate_annotations:
        return None
    normalized_query = " ".join(query.lower().split())

    def annotation_priority(annotation: ChatEvidenceAnnotation) -> float:
        score = 0.0
        if "what virtue opposes" in normalized_query and annotation.object_type == "virtue":
            score += 6.0
        if "what vice opposes" in normalized_query and annotation.object_type == "vice":
            score += 6.0
        if (
            normalized_query.startswith(("where does ", "where is "))
            and annotation.relation_type == "resides_in"
        ):
            score += 4.0
        if "classify" in normalized_query and annotation.relation_type in {
            "subjective_part_of",
            "integral_part_of",
            "potential_part_of",
            "species_of",
        }:
            score += 4.0
        if "annexed" in normalized_query and annotation.relation_type == "annexed_to":
            score += 4.0
        if "related to" in normalized_query or "relation to" in normalized_query:
            if annotation.relation_type in {
                "annexed_to",
                "directed_to",
                "caused_by",
                "resides_in",
                "subjective_part_of",
                "potential_part_of",
                "integral_part_of",
            }:
                score += 2.0
        return score

    annotation = max(candidate_annotations, key=annotation_priority)
    passages = _annotation_passages(annotation)
    if not passages:
        return None
    lead = _relation_lead_sentence(annotation, query)
    rationale = _clean_rationale_sentence(annotation.evidence_rationale)
    lines = [lead]
    normalized_lead = _normalized_label(lead)
    normalized_rationale = _normalized_label(rationale)
    if normalized_rationale and normalized_rationale not in normalized_lead:
        lines.append(rationale)
    return _render_curated_answer(lines, passages)


def _normalize_citation_block(text: str, fallback_block: str) -> str:
    stripped = text.strip()
    match = re.search(r"(?im)^citations:\s*$", stripped)
    if match is None:
        if not fallback_block:
            return stripped
        return f"{stripped}\n\n{fallback_block}".strip()
    body = stripped[: match.start()].rstrip()
    citation_lines: list[str] = []
    seen: set[str] = set()
    for line in stripped[match.end() :].splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.startswith("- "):
            line = f"- {line.lstrip('- ').strip()}"
        if line in seen:
            continue
        seen.add(line)
        citation_lines.append(line)
    if not citation_lines and fallback_block:
        return f"{body}\n\n{fallback_block}".strip()
    citation_block = "Citations:\n" + "\n".join(citation_lines)
    return f"{body}\n\n{citation_block}".strip()


def _strip_template_boilerplate(text: str) -> str:
    cleaned = _clean_assistant_text(text)
    for pattern, replacement in BOILERPLATE_REPLACEMENTS:
        cleaned = pattern.sub(replacement, cleaned)
    kept_lines: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if lowered.startswith(
            (
                "- explanation:",
                "- tract:",
                "- question parts:",
                "- relation type:",
                "- object of species:",
            )
        ):
            continue
        kept_lines.append(line)
    cleaned = "\n".join(kept_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\.\s*\.", ".", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"(?m)^\s*-\s*$", "", cleaned)
    return cleaned.strip()


def _chat_body(text: str) -> str:
    lowered = text.lower()
    marker = lowered.find("citations:")
    if marker < 0:
        return text.strip()
    return text[:marker].strip()


def _needs_chat_rewrite(user_text: str, assistant_text: str) -> bool:
    body = _chat_body(assistant_text).lower()
    if any(marker in body for marker in CHAT_TEMPLATE_MARKERS):
        return True
    word_count = len(body.split())
    if word_count < 16:
        return True
    if user_text.strip().lower().startswith(
        ("what is", "who is", "what are")
    ) and " is " not in body:
        return True
    if "differ" in user_text.lower() and not any(
        phrase in body for phrase in ("whereas", "while", "differs", "but", "by contrast")
    ):
        return True
    return False


def _rewrite_chat_answer(
    *,
    model: Any,
    tokenizer: Any,
    config: InferenceConfig,
    user_text: str,
    draft_answer: str,
    evidence_bundle: ChatEvidenceBundle | None,
) -> str:
    evidence_context = render_chat_evidence_context(evidence_bundle) if evidence_bundle else ""
    rewrite_messages = [
        {
            "role": "system",
            "content": (
                "Rewrite the draft answer into natural, direct Thomistic prose. Start by answering "
                "the question itself. Then give one to three brief sentences of explanation from "
                "the evidence. Never use benchmark filler like "
                "'According to the reviewed passage', 'The passage states this directly', "
                "'The reviewed claim is framed as...', or 'Article X explicitly says'. "
                "Keep the answer concise and keep a short `Citations:` block."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question:\n{user_text}\n\n"
                f"Draft answer:\n{draft_answer}\n\n"
                f"{evidence_context}"
            ).strip(),
        },
    ]
    return _generate_chat_response(
        model=model,
        tokenizer=tokenizer,
        config=config,
        messages=rewrite_messages,
    )


def _finalize_chat_answer(
    *,
    user_text: str,
    assistant_text: str,
    evidence_bundle: ChatEvidenceBundle | None,
) -> str:
    cleaned = _strip_template_boilerplate(assistant_text)
    cleaned = _normalize_citation_block(cleaned, _citation_block_from_bundle(evidence_bundle))
    if _needs_chat_rewrite(user_text, cleaned):
        cleaned = _normalize_citation_block(cleaned, _citation_block_from_bundle(evidence_bundle))
    return cleaned.strip()


@dataclass(frozen=True)
class ChatSessionPaths:
    run_dir: Path
    transcript_jsonl_path: Path
    transcript_markdown_path: Path


@dataclass(frozen=True)
class ChatModelBundle:
    model: Any
    tokenizer: Any
    runtime: Any


@dataclass
class LiveChatSession:
    run_dir: Path
    config_snapshot_path: Path
    environment: dict[str, Any]
    session_paths: ChatSessionPaths
    start_time: str
    system_prompt: str | None
    history: list[dict[str, str]]
    transcript_entries: list[dict[str, Any]]
    turn_count: int = 0


def chat_session_paths(run_dir: Path) -> ChatSessionPaths:
    return ChatSessionPaths(
        run_dir=run_dir,
        transcript_jsonl_path=run_dir / "chat_transcript.jsonl",
        transcript_markdown_path=run_dir / "chat_transcript.md",
    )


def describe_chat_plan(
    config: InferenceConfig,
    *,
    output_root: Path,
    system_prompt: str | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    runtime = _detect_runtime(config)
    return {
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "chat_output_root": str(output_root),
        "dataset_dir": str(config.dataset_dir),
        "max_new_tokens": config.max_new_tokens,
        "model_name_or_path": config.model_name_or_path,
        "one_shot": one_shot,
        "resolved_device": runtime.device_type if runtime is not None else None,
        "run_name": config.run_name,
        "runtime_warnings": list(runtime.warnings) if runtime is not None else [],
        "system_prompt": system_prompt,
        "torch_dtype": runtime.torch_dtype_name if runtime is not None else None,
    }


def render_chat_transcript_markdown(entries: list[dict[str, Any]]) -> str:
    lines = [
        "# Christian Virtue Chat Transcript",
        "",
    ]
    for entry in entries:
        role = str(entry["role"])
        content = str(entry["content"]).strip()
        if role == "user":
            lines.extend(["## User", "", content, ""])
        elif role == "assistant":
            lines.extend(["## Assistant", "", content, ""])
        elif role == "command":
            lines.extend(["## Session Event", "", f"`{content}`", ""])
        else:
            lines.extend([f"## {role.title()}", "", content, ""])
    return "\n".join(lines).rstrip() + "\n"


def _write_transcript(paths: ChatSessionPaths, entries: list[dict[str, Any]]) -> None:
    with paths.transcript_jsonl_path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
    paths.transcript_markdown_path.write_text(
        render_chat_transcript_markdown(entries),
        encoding="utf-8",
    )


def _write_command_log(run_dir: Path, argv: list[str]) -> None:
    command_path = run_artifacts_for_dir(run_dir).command_log_path
    command_path.write_text(f"$ {shlex.join(argv)}\n", encoding="utf-8")


def load_chat_model_bundle(config: InferenceConfig) -> ChatModelBundle:
    ensure_inference_dependencies(config)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    runtime = _detect_runtime(config)
    if runtime is None:
        raise RuntimeError("Torch is required for chat runtime detection.")

    tokenizer = AutoTokenizer.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token

    torch_dtype = getattr(torch, runtime.torch_dtype_name)
    model: Any = AutoModelForCausalLM.from_pretrained(
        config.model_name_or_path,
        trust_remote_code=config.trust_remote_code,
        device_map="auto" if runtime.device_type == "cuda" else None,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
    )
    if config.adapter_path is not None:
        if not config.adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {config.adapter_path}")
        model = PeftModel.from_pretrained(model, str(config.adapter_path))
    if runtime.device_type != "cuda":
        model = model.to(runtime.device_type)
    _align_generation_config(model, config)
    model.eval()
    return ChatModelBundle(model=model, tokenizer=tokenizer, runtime=runtime)


def _generate_chat_response(
    *,
    model: Any,
    tokenizer: Any,
    config: InferenceConfig,
    messages: list[dict[str, str]],
) -> str:
    import torch

    prompt_text = _render_prompt(tokenizer, messages)
    device = next(model.parameters()).device
    tokenized = tokenizer(prompt_text, return_tensors="pt")
    tokenized = {key: value.to(device) for key, value in tokenized.items()}
    generation_kwargs = {
        "max_new_tokens": config.max_new_tokens,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
        "repetition_penalty": config.repetition_penalty,
    }
    if config.do_sample:
        generation_kwargs.update(
            {
                "do_sample": True,
                "temperature": config.temperature,
                "top_p": config.top_p,
            }
        )
    else:
        generation_kwargs["do_sample"] = False
    with torch.no_grad():
        generated = model.generate(**tokenized, **generation_kwargs)
    input_length = int(tokenized["input_ids"].shape[-1])
    generated_ids = generated[0][input_length:]
    return _clean_assistant_text(tokenizer.decode(generated_ids, skip_special_tokens=True))


def generate_chat_reply(
    bundle: ChatModelBundle,
    config: InferenceConfig,
    *,
    messages: list[dict[str, str]],
) -> str:
    prepared_messages, evidence_bundle = _augment_chat_messages(messages)
    user_messages = [item for item in messages if item.get("role") == "user"]
    current_user_text = str(user_messages[-1]["content"]).strip() if user_messages else ""
    deterministic = generate_deterministic_chat_reply(
        current_user_text,
        evidence_bundle=evidence_bundle,
    )
    if deterministic is not None:
        return deterministic

    draft = _generate_chat_response(
        model=bundle.model,
        tokenizer=bundle.tokenizer,
        config=config,
        messages=prepared_messages,
    )
    final_text = draft
    if _needs_chat_rewrite(current_user_text, draft):
        rewritten = _rewrite_chat_answer(
            model=bundle.model,
            tokenizer=bundle.tokenizer,
            config=config,
            user_text=current_user_text,
            draft_answer=draft,
            evidence_bundle=evidence_bundle,
        )
        if rewritten.strip():
            final_text = rewritten
    return _finalize_chat_answer(
        user_text=current_user_text,
        assistant_text=final_text,
        evidence_bundle=evidence_bundle,
    )


def generate_deterministic_chat_reply(
    query: str,
    *,
    evidence_bundle: ChatEvidenceBundle | None = None,
) -> str | None:
    current_query = query.strip()
    if not current_query:
        return None
    bundle = evidence_bundle or retrieve_chat_evidence(current_query)
    query_mode = _query_mode(current_query)

    if query_mode == "definition":
        return _deterministic_definition_answer(current_query, bundle)
    if query_mode == "comparison":
        return _deterministic_comparison_answer(current_query, bundle)
    if query_mode == "relation":
        return _deterministic_relation_answer(current_query, bundle)
    if query_mode == "practical":
        return _deterministic_practical_answer(current_query, bundle)
    if query_mode == "why":
        return _deterministic_why_answer(current_query, bundle)
    if query_mode == "guidance":
        return _deterministic_guidance_answer(current_query, bundle)
    return None


def _chat_manifest(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    artifacts = run_artifacts_for_dir(session.run_dir)
    package_versions = session.environment["versions"]
    dataset_manifest = dataset_manifest_path(config.dataset_dir)
    return {
        "accelerate_version": package_versions["accelerate"],
        "adapter_path": str(config.adapter_path) if config.adapter_path is not None else None,
        "command_log_path": str(artifacts.command_log_path),
        "config_snapshot_path": str(session.config_snapshot_path),
        "dataset_dir": str(config.dataset_dir),
        "dataset_manifest_path": str(dataset_manifest) if dataset_manifest is not None else None,
        "end_time": iso_timestamp(),
        "environment_path": str(artifacts.environment_path),
        "git_commit": session.environment["git_commit"],
        "model_name_or_path": config.model_name_or_path,
        "one_shot": one_shot,
        "peft_version": package_versions["peft"],
        "python_version": session.environment["platform"]["python_version"],
        "resolved_device": runtime.device_type if runtime is not None else None,
        "run_dir": str(session.run_dir),
        "run_id": session.run_dir.name,
        "run_manifest_path": str(artifacts.run_manifest_path),
        "run_name": config.run_name,
        "runtime_warnings": list(runtime.warnings) if runtime is not None else [],
        "start_time": session.start_time,
        "system_prompt": session.system_prompt,
        "torch_dtype": runtime.torch_dtype_name if runtime is not None else None,
        "torch_version": package_versions["torch"],
        "transcript_jsonl_path": str(session.session_paths.transcript_jsonl_path),
        "transcript_markdown_path": str(session.session_paths.transcript_markdown_path),
        "transformers_version": package_versions["transformers"],
        "trl_version": package_versions["trl"],
        "turn_count": session.turn_count,
    }


def persist_live_chat_session(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    _write_transcript(session.session_paths, session.transcript_entries)
    manifest = _chat_manifest(session, config, runtime=runtime, one_shot=one_shot)
    write_json(run_artifacts_for_dir(session.run_dir).run_manifest_path, manifest)
    return manifest


def create_live_chat_session(
    config: InferenceConfig,
    *,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    system_prompt: str | None = DEFAULT_CHAT_SYSTEM_PROMPT,
    command_argv: list[str] | None = None,
    runtime: Any | None = None,
) -> LiveChatSession:
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = create_timestamped_run_dir(output_root)
    artifacts = run_artifacts_for_dir(run_dir)
    session_paths = chat_session_paths(run_dir)
    if command_argv is not None:
        _write_command_log(run_dir, command_argv)

    config_snapshot_path = write_config_snapshot(
        run_dir,
        config_path=config.config_path,
        payload=config.model_dump(mode="json", exclude={"config_path"}),
    )
    environment = build_environment_snapshot(
        workspace_root=REPO_ROOT,
        resolved_device=runtime.device_type if runtime is not None else None,
        torch_dtype=runtime.torch_dtype_name if runtime is not None else None,
    )
    write_json(artifacts.environment_path, environment)

    start_time = iso_timestamp()
    transcript_entries: list[dict[str, Any]] = []
    if system_prompt:
        transcript_entries.append(
            {
                "content": system_prompt,
                "role": "system",
                "timestamp": start_time,
            }
        )

    session = LiveChatSession(
        run_dir=run_dir,
        config_snapshot_path=config_snapshot_path,
        environment=environment,
        session_paths=session_paths,
        start_time=start_time,
        system_prompt=system_prompt,
        history=[],
        transcript_entries=transcript_entries,
    )
    persist_live_chat_session(session, config, runtime=runtime)
    return session


def record_chat_reset(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    one_shot: str | None = None,
) -> dict[str, Any]:
    session.history.clear()
    session.transcript_entries.append(
        {
            "content": "/reset",
            "role": "command",
            "timestamp": iso_timestamp(),
        }
    )
    return persist_live_chat_session(session, config, runtime=runtime, one_shot=one_shot)


def record_chat_exchange(
    session: LiveChatSession,
    config: InferenceConfig,
    *,
    runtime: Any | None,
    user_text: str,
    assistant_text: str,
    one_shot: str | None = None,
) -> dict[str, Any]:
    session.turn_count += 1
    session.transcript_entries.extend(
        [
            {
                "content": user_text,
                "role": "user",
                "timestamp": iso_timestamp(),
                "turn_index": session.turn_count,
            },
            {
                "content": assistant_text,
                "role": "assistant",
                "timestamp": iso_timestamp(),
                "turn_index": session.turn_count,
            },
        ]
    )
    session.history.extend(
        [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ]
    )
    return persist_live_chat_session(session, config, runtime=runtime, one_shot=one_shot)


def run_interactive_chat(
    config: InferenceConfig,
    *,
    output_root: Path = DEFAULT_CHAT_OUTPUT_ROOT,
    system_prompt: str | None = DEFAULT_CHAT_SYSTEM_PROMPT,
    one_shot: str | None = None,
    command_argv: list[str] | None = None,
) -> dict[str, Any]:
    bundle = load_chat_model_bundle(config)
    session = create_live_chat_session(
        config,
        output_root=output_root,
        system_prompt=system_prompt,
        command_argv=command_argv,
        runtime=bundle.runtime,
    )

    print(f"Chat session: {session.run_dir}")
    print(f"Model: {config.model_name_or_path}")
    if config.adapter_path is not None:
        print(f"Adapter: {config.adapter_path}")
    print("Commands: /reset, /exit")

    pending_one_shot = one_shot

    while True:
        try:
            if pending_one_shot is not None:
                user_text = pending_one_shot.strip()
                pending_one_shot = None
                print(f"\nYou> {user_text}")
            else:
                user_text = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break

        if not user_text:
            continue
        if user_text in {"/exit", "/quit"}:
            break
        if user_text == "/reset":
            record_chat_reset(session, config, runtime=bundle.runtime, one_shot=one_shot)
            print("Conversation history cleared.")
            continue

        prompt_messages: list[dict[str, str]] = []
        if system_prompt:
            prompt_messages.append({"role": "system", "content": system_prompt})
        prompt_messages.extend(session.history)
        prompt_messages.append({"role": "user", "content": user_text})
        assistant_text = generate_chat_reply(
            bundle,
            config=config,
            messages=prompt_messages,
        )
        print(f"\nAssistant> {assistant_text}")
        record_chat_exchange(
            session,
            config,
            runtime=bundle.runtime,
            user_text=user_text,
            assistant_text=assistant_text,
            one_shot=one_shot,
        )
        if one_shot is not None:
            break

    return persist_live_chat_session(session, config, runtime=bundle.runtime, one_shot=one_shot)
