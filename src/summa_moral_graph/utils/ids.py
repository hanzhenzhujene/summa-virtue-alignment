from __future__ import annotations

import re

from .segments import USABLE_SEGMENT_TYPES

PART_DISPLAY = {
    "i": "I",
    "i-ii": "I-II",
    "ii-ii": "II-II",
    "iii": "III",
    "supplement": "Suppl.",
}

PART_FROM_DIGIT = {
    "1": "i",
    "2": "i-ii",
    "3": "ii-ii",
    "4": "iii",
    "5": "supplement",
}

SUMMA_URL_RE = re.compile(r"/summa/([1-5]\d{3})\.htm$")


def question_number_from_summa_url(url: str) -> tuple[str, int]:
    match = SUMMA_URL_RE.search(url)
    if not match:
        raise ValueError(f"Could not parse Summa question URL: {url}")
    code = match.group(1)
    part_id = PART_FROM_DIGIT[code[0]]
    question_number = int(code[1:])
    return part_id, question_number


def question_id(part_id: str, question_number: int) -> str:
    return f"st.{part_id}.q{question_number:03d}"


def article_id(question_identifier: str, article_number: int) -> str:
    return f"{question_identifier}.a{article_number:03d}"


def segment_id(article_identifier: str, segment_type: str, segment_ordinal: int | None) -> str:
    if segment_type not in USABLE_SEGMENT_TYPES:
        raise ValueError(f"Unsupported exported segment type: {segment_type}")
    if segment_type == "ad":
        if segment_ordinal is None:
            raise ValueError("reply segments require an ordinal")
        suffix = f"{segment_type}{segment_ordinal}"
    else:
        if segment_ordinal is not None:
            raise ValueError("respondeo segments do not accept an ordinal")
        suffix = segment_type
    return f"{article_identifier}.{suffix}"


def crossref_id(segment_identifier: str, occurrence: int) -> str:
    return f"{segment_identifier}.xref{occurrence:02d}"


def article_citation_label(part_id: str, question_number: int, article_number: int) -> str:
    return f"{PART_DISPLAY[part_id]} q.{question_number} a.{article_number}"


def segment_citation_label(
    part_id: str,
    question_number: int,
    article_number: int,
    segment_type: str,
    segment_ordinal: int | None,
) -> str:
    base = article_citation_label(part_id, question_number, article_number)
    if segment_type not in USABLE_SEGMENT_TYPES:
        raise ValueError(f"Unsupported exported segment type: {segment_type}")
    if segment_type == "ad":
        return f"{base} {segment_type}.{segment_ordinal}"
    return f"{base} {segment_type}"


def canonical_crossref_reference(part_id: str, question_number: int, article_number: int) -> str:
    return f"{PART_DISPLAY[part_id]}:{question_number}:{article_number}"
