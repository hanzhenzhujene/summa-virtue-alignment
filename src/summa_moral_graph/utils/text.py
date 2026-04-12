from __future__ import annotations

import html
import re
import unicodedata

from bs4 import Tag

WHITESPACE_RE = re.compile(r"\s+")
QUESTION_TITLE_RE = re.compile(r"^Question\s+\d+\.\s*", re.IGNORECASE)
ARTICLE_TITLE_RE = re.compile(r"^Article\s+\d+\.\s*", re.IGNORECASE)


def normalize_text(text: str) -> str:
    unescaped = html.unescape(text).replace("\xa0", " ")
    normalized = unicodedata.normalize("NFKC", unescaped)
    return WHITESPACE_RE.sub(" ", normalized).strip()


def visible_text(tag: Tag) -> str:
    return normalize_text(tag.get_text(" ", strip=True))


def clean_question_title(raw_title: str) -> str:
    return normalize_text(QUESTION_TITLE_RE.sub("", raw_title))


def clean_article_title(raw_title: str) -> str:
    return normalize_text(ARTICLE_TITLE_RE.sub("", raw_title))

