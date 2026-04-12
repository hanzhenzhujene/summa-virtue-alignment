from __future__ import annotations

import re
from dataclasses import dataclass

from ..utils.ids import canonical_crossref_reference

PART_TOKEN_RE = r"I-II|II-II|III|I|Suppl\.?|Supplement"
CROSSREF_RE = re.compile(
    rf"\b(?P<part>{PART_TOKEN_RE})\s*:\s*(?P<question>\d+)\s*:\s*(?P<article>\d+)\b",
    re.IGNORECASE,
)

TOKEN_TO_PART_ID = {
    "I": "i",
    "I-II": "i-ii",
    "II-II": "ii-ii",
    "III": "iii",
    "SUPPL": "supplement",
    "SUPPL.": "supplement",
    "SUPPLEMENT": "supplement",
}


@dataclass(frozen=True)
class CrossrefMatch:
    raw_reference: str
    normalized_reference: str
    target_part_id: str
    target_question_number: int
    target_article_number: int
    start: int


def normalize_part_token(token: str) -> str:
    normalized = token.strip().upper()
    return TOKEN_TO_PART_ID[normalized]


def extract_crossrefs(text: str) -> list[CrossrefMatch]:
    matches: list[CrossrefMatch] = []
    for match in CROSSREF_RE.finditer(text):
        target_part_id = normalize_part_token(match.group("part"))
        target_question_number = int(match.group("question"))
        target_article_number = int(match.group("article"))
        raw_reference = match.group(0)
        matches.append(
            CrossrefMatch(
                raw_reference=raw_reference,
                normalized_reference=canonical_crossref_reference(
                    target_part_id,
                    target_question_number,
                    target_article_number,
                ),
                target_part_id=target_part_id,
                target_question_number=target_question_number,
                target_article_number=target_article_number,
                start=match.start(),
            )
        )
    return matches

