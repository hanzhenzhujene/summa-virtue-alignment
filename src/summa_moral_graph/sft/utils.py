from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Sequence

TRACT_DISPLAY_NAMES: dict[str, str] = {
    "theological_virtues": "Theological virtues",
    "prudence": "Prudence",
    "justice_core": "Justice core",
    "connected_virtues_109_120": "Connected virtues (II-II qq.109-120)",
    "fortitude_parts_129_135": "Fortitude parts (II-II qq.129-135)",
    "fortitude_closure_136_140": "Fortitude closure (II-II qq.136-140)",
    "temperance_141_160": "Temperance (II-II qq.141-160)",
    "temperance_closure_161_170": "Temperance closure (II-II qq.161-170)",
}

PART_ORDER: dict[str, int] = {
    "i": 0,
    "i-ii": 1,
    "ii-ii": 2,
    "iii": 3,
    "supplement": 4,
}

RELATION_SENTENCES: dict[str, str] = {
    "abuses_role": "{subject} abuses the role of {object}",
    "act_of": "{subject} is an act of {object}",
    "annexed_to": "{subject} is annexed to {object}",
    "case_of": "{subject} is a case of {object}",
    "caused_by": "{subject} is caused by {object}",
    "commands_act_of": "{subject} commands the act of {object}",
    "concerns_anger": "{subject} concerns anger in relation to {object}",
    "concerns_drink": "{subject} concerns drink in relation to {object}",
    "concerns_external_behavior": "{subject} concerns external behavior in relation to {object}",
    "concerns_external_goods": "{subject} concerns external goods in relation to {object}",
    "concerns_food": "{subject} concerns food in relation to {object}",
    "concerns_great_expenditure": "{subject} concerns great expenditure in relation to {object}",
    "concerns_great_work": "{subject} concerns great work in relation to {object}",
    "concerns_honor": "{subject} concerns honor in relation to {object}",
    "concerns_ordered_inquiry": "{subject} concerns ordered inquiry in relation to {object}",
    "concerns_outward_attire": "{subject} concerns outward attire in relation to {object}",
    "concerns_outward_moderation": "{subject} concerns outward moderation in relation to {object}",
    "concerns_self_presentation": "{subject} concerns self-presentation in relation to {object}",
    "concerns_sexual_pleasure": "{subject} concerns sexual pleasure in relation to {object}",
    "concerns_social_interaction": "{subject} concerns social interaction in relation to {object}",
    "concerns_worthiness": "{subject} concerns worthiness in relation to {object}",
    "contrary_to": "{subject} is contrary to {object}",
    "corrects_legal_letter": "{subject} corrects the legal letter in relation to {object}",
    "corresponding_gift_of": "{subject} is the corresponding gift of {object}",
    "corresponds_to": "{subject} corresponds to {object}",
    "corrupts_process": "{subject} corrupts the process of {object}",
    "deficiency_opposed_to": "{subject} is opposed by the deficient vice {object}",
    "directed_to": "{subject} is directed to {object}",
    "excess_opposed_to": "{subject} is opposed by the excessive vice {object}",
    "forbids_opposed_vice_of": "{subject} forbids the opposed vice of {object}",
    "harms_domain": "{subject} harms the domain of {object}",
    "has_act": "{subject} has {object} as an act",
    "has_object": "{subject} has {object} as its object",
    "integral_part_of": "{subject} is an integral part of {object}",
    "opposed_by": "{subject} is opposed by {object}",
    "part_of": "{subject} is part of {object}",
    "part_of_fortitude": "{subject} is part of fortitude through {object}",
    "perfected_by": "{subject} is perfected by {object}",
    "potential_part_of": "{subject} is a potential part of {object}",
    "precept_of": "{subject} is a precept of {object}",
    "preserves_intent_of_law": "{subject} preserves the intent of law in relation to {object}",
    "regulated_by": "{subject} is regulated by {object}",
    "related_to_fortitude": "{subject} is related to fortitude through {object}",
    "requires": "{subject} requires {object}",
    "requires_restitution": "{subject} requires restitution in relation to {object}",
    "resides_in": "{subject} resides in {object}",
    "results_in_punishment": "{subject} results in punishment in relation to {object}",
    "species_of": "{subject} is a species of {object}",
    "subjective_part_of": "{subject} is a subjective part of {object}",
    "tempted_by": "{subject} is tempted by {object}",
    "treated_in": "{subject} is treated in {object}",
}

RELATION_FRAGMENTS: dict[str, str] = {
    "abuses_role": "abuses the role of {object}",
    "act_of": "is an act of {object}",
    "annexed_to": "is annexed to {object}",
    "case_of": "is a case of {object}",
    "caused_by": "is caused by {object}",
    "commands_act_of": "commands the act of {object}",
    "concerns_anger": "concerns anger in relation to {object}",
    "concerns_drink": "concerns drink in relation to {object}",
    "concerns_external_behavior": "concerns external behavior in relation to {object}",
    "concerns_external_goods": "concerns external goods in relation to {object}",
    "concerns_food": "concerns food in relation to {object}",
    "concerns_great_expenditure": "concerns great expenditure in relation to {object}",
    "concerns_great_work": "concerns great work in relation to {object}",
    "concerns_honor": "concerns honor in relation to {object}",
    "concerns_ordered_inquiry": "concerns ordered inquiry in relation to {object}",
    "concerns_outward_attire": "concerns outward attire in relation to {object}",
    "concerns_outward_moderation": "concerns outward moderation in relation to {object}",
    "concerns_self_presentation": "concerns self-presentation in relation to {object}",
    "concerns_sexual_pleasure": "concerns sexual pleasure in relation to {object}",
    "concerns_social_interaction": "concerns social interaction in relation to {object}",
    "concerns_worthiness": "concerns worthiness in relation to {object}",
    "contrary_to": "is contrary to {object}",
    "corrects_legal_letter": "corrects the legal letter in relation to {object}",
    "corresponding_gift_of": "is the corresponding gift of {object}",
    "corresponds_to": "corresponds to {object}",
    "corrupts_process": "corrupts the process of {object}",
    "deficiency_opposed_to": "is opposed by the deficient vice {object}",
    "directed_to": "is directed to {object}",
    "excess_opposed_to": "is opposed by the excessive vice {object}",
    "forbids_opposed_vice_of": "forbids the opposed vice of {object}",
    "harms_domain": "harms the domain of {object}",
    "has_act": "has {object} as an act",
    "has_object": "has {object} as its object",
    "integral_part_of": "is an integral part of {object}",
    "opposed_by": "is opposed by {object}",
    "part_of": "is part of {object}",
    "part_of_fortitude": "is part of fortitude through {object}",
    "perfected_by": "is perfected by {object}",
    "potential_part_of": "is a potential part of {object}",
    "precept_of": "is a precept of {object}",
    "preserves_intent_of_law": "preserves the intent of law in relation to {object}",
    "regulated_by": "is regulated by {object}",
    "related_to_fortitude": "is related to fortitude through {object}",
    "requires": "requires {object}",
    "requires_restitution": "requires restitution in relation to {object}",
    "resides_in": "resides in {object}",
    "results_in_punishment": "results in punishment in relation to {object}",
    "species_of": "is a species of {object}",
    "subjective_part_of": "is a subjective part of {object}",
    "tempted_by": "is tempted by {object}",
    "treated_in": "is treated in {object}",
}

PASSAGE_ID_RE = re.compile(r"st\.(?:i|i-ii|ii-ii|iii|supplement)\.q\d{3}\.a\d{3}\.(?:resp|ad\d+)")
QUESTION_ID_RE = re.compile(r"st\.(?P<part>[a-z-]+)\.q(?P<question>\d{3})$")
SEGMENT_ID_RE = re.compile(
    r"st\.(?P<part>[a-z-]+)\.q(?P<question>\d{3})\.a(?P<article>\d{3})\.(?P<segment>resp|ad(?P<ordinal>\d+))$"
)


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def deterministic_index(key: str, length: int) -> int:
    if length <= 0:
        raise ValueError("length must be positive")
    return int(stable_hash(key), 16) % length


def slugify(value: str) -> str:
    lowered = value.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return cleaned or "item"


def tract_display_name(tract: str) -> str:
    return TRACT_DISPLAY_NAMES.get(tract, tract.replace("_", " ").title())


def relation_sentence(subject: str, relation_type: str, object_label: str) -> str:
    template = RELATION_SENTENCES.get(relation_type)
    if template is None:
        return f"{subject} stands in a {relation_type.replace('_', ' ')} relation to {object_label}"
    return template.format(subject=subject, object=object_label)


def relation_fragment(relation_type: str, object_label: str) -> str:
    template = RELATION_FRAGMENTS.get(relation_type)
    if template is None:
        return f"stands in a {relation_type.replace('_', ' ')} relation to {object_label}"
    return template.format(object=object_label)


def support_signal_sentence(support_type: str) -> str:
    if support_type == "explicit_textual":
        return "The passage states this directly."
    if support_type == "strong_textual_inference":
        return (
            "The reviewed claim is framed as a strong textual inference from Aquinas's wording,"
            " not as a free-standing extrapolation."
        )
    return f"The support type here is {support_type.replace('_', ' ')}."


def dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def format_citation_block(citations: Sequence[tuple[str, str]]) -> str:
    deduped = []
    seen: set[tuple[str, str]] = set()
    for item in citations:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    lines = ["Citations:"]
    for passage_id, citation_label in deduped:
        lines.append(f"- {passage_id} ({citation_label})")
    return "\n".join(lines)


def extract_passage_ids(text: str) -> list[str]:
    return dedupe_preserving_order(PASSAGE_ID_RE.findall(text))


def parse_question_id(question_id: str) -> tuple[str, int]:
    match = QUESTION_ID_RE.match(question_id)
    if match is None:
        raise ValueError(f"Unrecognized question id: {question_id}")
    return match.group("part"), int(match.group("question"))


def question_sort_key(question_id: str) -> tuple[int, int]:
    part_id, question_number = parse_question_id(question_id)
    return (PART_ORDER.get(part_id, 99), question_number)


def segment_sort_key(segment_id: str) -> tuple[int, int, int, int]:
    match = SEGMENT_ID_RE.match(segment_id)
    if match is None:
        raise ValueError(f"Unrecognized segment id: {segment_id}")
    part_id = match.group("part")
    question_number = int(match.group("question"))
    article_number = int(match.group("article"))
    segment_label = match.group("segment")
    if segment_label == "resp":
        segment_rank = 0
    else:
        segment_rank = int(match.group("ordinal") or "0") + 1
    return (
        PART_ORDER.get(part_id, 99),
        question_number,
        article_number,
        segment_rank,
    )


def compact_relation_claims(subject_label: str, fragments: Sequence[str]) -> str:
    if not fragments:
        return f"Aquinas treats {subject_label} directly in the cited material."
    lead, *rest = list(fragments)
    if not rest:
        return f"Aquinas presents {subject_label} as one that {lead}."
    body = [f"Aquinas presents {subject_label} as one that {lead}."]
    for fragment in rest[:-1]:
        body.append(f"It also {fragment}.")
    body.append(f"It also {rest[-1]}.")
    return " ".join(body)
