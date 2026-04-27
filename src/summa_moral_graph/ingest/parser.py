from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, FeatureNotFound, Tag

from ..utils.segments import USABLE_SEGMENT_TYPES
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
    warnings: list["ParseWarning"] = field(default_factory=list)


@dataclass(frozen=True)
class ParseWarning:
    warning_type: str
    message: str
    article_number: int | None = None


@dataclass(frozen=True)
class ParsedQuestion:
    question_number: int
    question_title: str
    articles: list[ParsedArticle]
    warnings: list[ParseWarning] = field(default_factory=list)


def parse_question_html(question_number: int, html_text: str) -> ParsedQuestion:
    try:
        soup = BeautifulSoup(html_text, "lxml")
    except FeatureNotFound:
        soup = BeautifulSoup(html_text, "html.parser")
    heading = soup.find("h1")
    if not isinstance(heading, Tag):
        raise ValueError("Question page is missing an <h1> heading")
    question_title = clean_question_title(visible_text(heading))

    toc_titles = parse_article_outline(soup)
    articles: list[ParsedArticle] = []
    warnings: list[ParseWarning] = []
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
        segments, article_warnings = parse_article_segments_with_warnings(
            article_number,
            article_paragraphs,
        )
        if not segments:
            raise ValueError(f"Article {article_number} yielded no segments")
        articles.append(
            ParsedArticle(
                article_number=article_number,
                article_title=article_title,
                segments=segments,
                warnings=article_warnings,
            )
        )
        warnings.extend(article_warnings)

    if not articles:
        raise ValueError("Question page yielded no articles")

    return ParsedQuestion(
        question_number=question_number,
        question_title=question_title,
        articles=articles,
        warnings=warnings,
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
    segments, _warnings = parse_article_segments_with_warnings(None, paragraphs)
    return segments


def parse_article_segments_with_warnings(
    article_number: int | None,
    paragraphs: list[Tag],
) -> tuple[list[ParsedSegment], list[ParseWarning]]:
    segments: list[ParsedSegment] = []
    warnings: list[ParseWarning] = []
    current_type: str | None = None
    current_ordinal: int | None = None
    current_paragraphs: list[str] = []
    objection_count = 0
    reply_count = 0
    state_order = {"obj": 0, "sc": 1, "resp": 2, "ad": 3}
    skipped_unlabeled = 0
    relabeled_replies = 0
    repeated_label_continuations = 0

    def flush_current() -> None:
        nonlocal current_type, current_ordinal, current_paragraphs
        if current_type is None:
            return
        text = normalize_text(" ".join(part for part in current_paragraphs if part))
        if not text:
            raise ValueError(f"Segment {current_type} is empty")
        # We keep objection and sed-contra recognition only for boundary detection.
        # The exported corpus retains doctrinally usable content only: respondeo and
        # replies to objections.
        if current_type in USABLE_SEGMENT_TYPES:
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
                skipped_unlabeled += 1
                continue
            current_paragraphs.append(text)
            continue
        segment_type, _source_ordinal, body = classified
        if segment_type == "obj" and current_type in {"resp", "ad"}:
            segment_type = "ad"
            relabeled_replies += 1
        if (
            segment_type in {"sc", "resp"}
            and current_type is not None
            and state_order[segment_type] <= state_order[current_type]
        ):
            current_paragraphs.append(body)
            repeated_label_continuations += 1
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
    present_types = {segment.segment_type for segment in segments}
    if skipped_unlabeled:
        warnings.append(
            ParseWarning(
                warning_type="leading_unlabeled_paragraph_skipped",
                message=(
                    f"Skipped {skipped_unlabeled} unlabeled paragraph(s) before a recognized "
                    "segment label."
                ),
                article_number=article_number,
            )
        )
    if relabeled_replies:
        warnings.append(
            ParseWarning(
                warning_type="late_objection_reinterpreted_as_reply",
                message=(
                    f"Reinterpreted {relabeled_replies} late objection label(s) as replies to "
                    "preserve canonical order."
                ),
                article_number=article_number,
            )
        )
    if repeated_label_continuations:
        warnings.append(
            ParseWarning(
                warning_type="repeated_label_folded_into_current_segment",
                message=(
                    f"Folded {repeated_label_continuations} repeated or out-of-order sed "
                    "contra/respondeo label(s) into the current segment."
                ),
                article_number=article_number,
            )
        )
    for missing_type, warning_type in (
        ("resp", "article_missing_respondeo"),
        ("ad", "article_missing_replies"),
    ):
        if missing_type not in present_types:
            warnings.append(
                ParseWarning(
                    warning_type=warning_type,
                    message=f"Article is missing usable doctrinal `{missing_type}` segment(s).",
                    article_number=article_number,
                )
            )
    return segments, warnings
