from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from ..utils.text import clean_article_title, clean_question_title, normalize_text, visible_text

ARTICLE_ID_RE = re.compile(r"^article(\d+)$", re.IGNORECASE)
OBJECTION_RE = re.compile(r"^Objection\s+(\d+)\.\s*(.*)$", re.IGNORECASE)
ON_THE_CONTRARY_RE = re.compile(r"^On the contrary,?\s*(.*)$", re.IGNORECASE)
I_ANSWER_RE = re.compile(r"^I answer that,?\s*(.*)$", re.IGNORECASE)
REPLY_RE = re.compile(r"^Reply to Objection\s+(\d+)\.\s*(.*)$", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedSegment:
    segment_type: str
    segment_ordinal: int | None
    text: str


@dataclass(frozen=True)
class ParsedArticle:
    article_number: int
    article_title: str
    segments: list[ParsedSegment]


@dataclass(frozen=True)
class ParsedQuestion:
    question_number: int
    question_title: str
    articles: list[ParsedArticle]


def parse_question_html(question_number: int, html_text: str) -> ParsedQuestion:
    soup = BeautifulSoup(html_text, "lxml")
    heading = soup.find("h1")
    if not isinstance(heading, Tag):
        raise ValueError("Question page is missing an <h1> heading")
    question_title = clean_question_title(visible_text(heading))

    toc_titles = parse_article_outline(soup)
    articles: list[ParsedArticle] = []
    for article_heading in soup.find_all("h2"):
        article_id = article_heading.get("id")
        if not isinstance(article_id, str):
            continue
        match = ARTICLE_ID_RE.match(article_id)
        if not match:
            continue
        article_number = int(match.group(1))
        header_title = clean_article_title(visible_text(article_heading))
        article_title = toc_titles.get(article_number, header_title)
        article_paragraphs = list(iter_article_paragraphs(article_heading))
        segments = parse_article_segments(article_paragraphs)
        if not segments:
            raise ValueError(f"Article {article_number} yielded no segments")
        articles.append(
            ParsedArticle(
                article_number=article_number,
                article_title=article_title,
                segments=segments,
            )
        )

    if not articles:
        raise ValueError("Question page yielded no articles")

    return ParsedQuestion(
        question_number=question_number,
        question_title=question_title,
        articles=articles,
    )


def parse_article_outline(soup: BeautifulSoup) -> dict[int, str]:
    outline = soup.find("ol")
    titles: dict[int, str] = {}
    if not isinstance(outline, Tag):
        return titles

    for index, item in enumerate(outline.find_all("li", recursive=False), start=1):
        anchor = item.find("a")
        if isinstance(anchor, Tag):
            titles[index] = normalize_text(visible_text(anchor))
        else:
            titles[index] = normalize_text(visible_text(item))
    return titles


def iter_article_paragraphs(article_heading: Tag) -> Iterable[Tag]:
    for sibling in article_heading.next_siblings:
        if isinstance(sibling, Tag) and sibling.name == "h2":
            return
        if isinstance(sibling, Tag) and sibling.name == "p":
            yield sibling


def classify_paragraph(text: str) -> tuple[str, int | None, str] | None:
    for pattern, segment_type in ((OBJECTION_RE, "obj"), (REPLY_RE, "ad")):
        match = pattern.match(text)
        if match:
            return segment_type, int(match.group(1)), normalize_text(match.group(2))

    for pattern, segment_type in ((ON_THE_CONTRARY_RE, "sc"), (I_ANSWER_RE, "resp")):
        match = pattern.match(text)
        if match:
            return segment_type, None, normalize_text(match.group(1))

    return None


def parse_article_segments(paragraphs: list[Tag]) -> list[ParsedSegment]:
    segments: list[ParsedSegment] = []
    current_type: str | None = None
    current_ordinal: int | None = None
    current_paragraphs: list[str] = []
    objection_count = 0
    reply_count = 0
    state_order = {"obj": 0, "sc": 1, "resp": 2, "ad": 3}

    def flush_current() -> None:
        nonlocal current_type, current_ordinal, current_paragraphs
        if current_type is None:
            return
        text = normalize_text(" ".join(part for part in current_paragraphs if part))
        if not text:
            raise ValueError(f"Segment {current_type} is empty")
        segments.append(
            ParsedSegment(
                segment_type=current_type,
                segment_ordinal=current_ordinal,
                text=text,
            )
        )
        current_type = None
        current_ordinal = None
        current_paragraphs = []

    for paragraph in paragraphs:
        text = normalize_text(visible_text(paragraph))
        if not text:
            continue
        classified = classify_paragraph(text)
        if classified is None:
            if current_type is None:
                continue
            current_paragraphs.append(text)
            continue
        segment_type, _source_ordinal, body = classified
        if segment_type == "obj" and current_type in {"resp", "ad"}:
            segment_type = "ad"
        if (
            segment_type in {"sc", "resp"}
            and current_type is not None
            and state_order[segment_type] <= state_order[current_type]
        ):
            current_paragraphs.append(body)
            continue
        flush_current()
        current_type = segment_type
        if current_type == "obj":
            objection_count += 1
            current_ordinal = objection_count
        elif current_type == "ad":
            reply_count += 1
            current_ordinal = reply_count
        else:
            current_ordinal = None
        if body:
            current_paragraphs.append(body)

    flush_current()
    return segments
