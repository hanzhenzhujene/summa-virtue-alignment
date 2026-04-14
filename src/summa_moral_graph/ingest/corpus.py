from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..models import (
    ArticleRecord,
    CorpusArticleManifestRecord,
    CorpusQuestionManifestRecord,
    ParseLogRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..models.corpus import ParseStatus
from ..utils.ids import article_id, question_id
from ..utils.jsonl import load_jsonl, write_jsonl
from ..utils.paths import INTERIM_DIR, PROCESSED_DIR
from ..utils.segments import USABLE_SEGMENT_TYPES
from .parser import ParseWarning, parse_question_html
from .scope import PART_INDEX_URLS, QUESTION_RANGES, ScopeEntry, build_scope_manifest
from .source import NewAdventClient

ModelT = TypeVar("ModelT", bound=BaseModel)

SUSPICIOUS_ARTICLE_CHAR_THRESHOLD = 350
EXPECTED_SEGMENT_TYPES = USABLE_SEGMENT_TYPES


def build_corpus_structural_artifacts(refresh_cache: bool = False) -> dict[str, int]:
    """Build full-corpus structural manifests, indices, and parse diagnostics."""

    manifest = build_scope_manifest(refresh_cache=refresh_cache)
    question_records = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
    }
    article_records = _load_records(INTERIM_DIR / "summa_moral_articles.jsonl", ArticleRecord)
    segment_records = _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)

    articles_by_question: dict[str, list[ArticleRecord]] = {}
    for article_record in article_records:
        articles_by_question.setdefault(article_record.question_id, []).append(article_record)
    segments_by_article: dict[str, list[SegmentRecord]] = {}
    for segment_record in segment_records:
        segments_by_article.setdefault(segment_record.article_id, []).append(segment_record)

    question_rows: list[CorpusQuestionManifestRecord] = []
    article_rows: list[CorpusArticleManifestRecord] = []
    log_rows: list[ParseLogRecord] = []

    with NewAdventClient() as client:
        for entry in manifest:
            (
                question_row,
                question_article_rows,
                question_logs,
            ) = build_question_manifest(
                entry=entry,
                client=client,
                question_records=question_records,
                articles_by_question=articles_by_question,
                segments_by_article=segments_by_article,
                refresh_cache=refresh_cache,
            )
            question_rows.append(question_row)
            article_rows.extend(question_article_rows)
            log_rows.extend(question_logs)

    question_rows.extend(build_excluded_question_rows())
    question_rows.sort(key=lambda record: (record.part_id, record.question_number))
    article_rows.sort(
        key=lambda record: (
            record.part_id,
            record.question_number,
            record.article_number,
        )
    )
    log_rows.sort(
        key=lambda record: (
            record.part_id,
            record.question_number,
            record.article_number or 0,
            record.log_type,
            record.log_id,
        )
    )

    write_jsonl(PROCESSED_DIR / "ingestion_log.jsonl", log_rows)
    write_question_index(PROCESSED_DIR / "question_index.csv", question_rows)
    write_article_index(PROCESSED_DIR / "article_index.csv", article_rows)

    warning_counts = Counter(record.log_type for record in log_rows if record.level == "warning")
    error_counts = Counter(record.log_type for record in log_rows if record.level == "error")
    counts = {
        "questions_expected": sum(
            len(question_range)
            for question_range in QUESTION_RANGES.values()
        ),
        "questions_parsed": len(
            [row for row in question_rows if row.parse_status in {"ok", "partial"}]
        ),
        "articles_expected": len(article_rows),
        "articles_parsed": len(
            [row for row in article_rows if row.parse_status in {"ok", "partial"}]
        ),
        "passages_parsed": len(segment_records),
    }
    manifest_payload = {
        "counts": counts,
        "included_questions": [
            row.model_dump(mode="json")
            for row in question_rows
            if row.parse_status != "excluded"
        ],
        "excluded_questions": [
            row.model_dump(mode="json")
            for row in question_rows
            if row.parse_status == "excluded"
        ],
        "warning_counts_by_type": dict(sorted(warning_counts.items())),
        "error_counts_by_type": dict(sorted(error_counts.items())),
    }
    (PROCESSED_DIR / "corpus_manifest.json").write_text(
        json.dumps(manifest_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return {
        "questions_expected": counts["questions_expected"],
        "questions_parsed": counts["questions_parsed"],
        "articles_expected": counts["articles_expected"],
        "articles_parsed": counts["articles_parsed"],
        "passages_parsed": counts["passages_parsed"],
    }


def build_question_manifest(
    *,
    entry: ScopeEntry,
    client: NewAdventClient,
    question_records: dict[str, QuestionRecord],
    articles_by_question: dict[str, list[ArticleRecord]],
    segments_by_article: dict[str, list[SegmentRecord]],
    refresh_cache: bool,
) -> tuple[
    CorpusQuestionManifestRecord,
    list[CorpusArticleManifestRecord],
    list[ParseLogRecord],
]:
    """Build manifest rows and logs for one in-scope question."""

    question_identifier = question_id(entry.part_id, entry.question_number)
    question_record = question_records.get(question_identifier)
    actual_articles = sorted(
        articles_by_question.get(question_identifier, []),
        key=lambda record: record.article_number,
    )
    actual_article_numbers = {record.article_number for record in actual_articles}

    parse_error: Exception | None = None
    parsed_article_warnings: dict[int, list[ParseWarning]] = {}
    parsed_article_numbers: set[int] = set()
    parsed_question_title = question_record.question_title if question_record else (
        entry.question_title_hint or f"Question {entry.question_number}"
    )

    try:
        html_text = client.fetch_text(entry.source_url, refresh_cache=refresh_cache)
        parsed_question = parse_question_html(entry.question_number, html_text)
        parsed_question_title = parsed_question.question_title
        parsed_article_numbers = {
            article.article_number for article in parsed_question.articles
        }
        parsed_article_warnings = {
            article.article_number: article.warnings
            for article in parsed_question.articles
        }
    except Exception as exc:  # pragma: no cover - exercised in live corpus build
        parse_error = exc

    question_logs: list[ParseLogRecord] = []
    if parse_error is not None:
        question_logs.append(
            ParseLogRecord(
                log_id=f"log.{question_identifier}.question-parse-failure",
                level="error",
                log_type="question_parse_failure",
                part_id=entry.part_id,
                question_number=entry.question_number,
                question_id=question_identifier,
                article_number=None,
                article_id=None,
                message=f"{type(parse_error).__name__}: {parse_error}",
                source_url=entry.source_url,
            )
        )

    expected_article_count = (
        len(parsed_article_numbers)
        if parse_error is None
        else (question_record.article_count if question_record else 0)
    )
    missing_article_numbers = sorted(parsed_article_numbers - actual_article_numbers)
    unexpected_article_numbers = sorted(actual_article_numbers - parsed_article_numbers)

    for article_number in missing_article_numbers:
        missing_article_id = article_id(question_identifier, article_number)
        question_logs.append(
            ParseLogRecord(
                log_id=f"log.{missing_article_id}.missing-from-interim",
                level="error",
                log_type="article_missing_from_interim",
                part_id=entry.part_id,
                question_number=entry.question_number,
                question_id=question_identifier,
                article_number=article_number,
                article_id=missing_article_id,
                message=(
                    "Article was visible in current source parse "
                    "but missing from interim records."
                ),
                source_url=entry.source_url,
            )
        )
    for article_number in unexpected_article_numbers:
        extra_article_id = article_id(question_identifier, article_number)
        question_logs.append(
            ParseLogRecord(
                log_id=f"log.{extra_article_id}.unexpected-in-interim",
                level="warning",
                log_type="article_present_without_current_source_match",
                part_id=entry.part_id,
                question_number=entry.question_number,
                question_id=question_identifier,
                article_number=article_number,
                article_id=extra_article_id,
                message="Article exists in interim records but not in the current source parse.",
                source_url=entry.source_url,
            )
        )

    article_rows: list[CorpusArticleManifestRecord] = []
    for article_record in actual_articles:
        segments = segments_by_article.get(article_record.article_id, [])
        segment_types = [str(segment.segment_type) for segment in segments]
        missing_segment_types = [
            segment_type
            for segment_type in EXPECTED_SEGMENT_TYPES
            if segment_type not in set(segment_types)
        ]
        warning_types = [
            warning.warning_type
            for warning in parsed_article_warnings.get(article_record.article_number, [])
        ]
        char_count = sum(segment.char_count for segment in segments)
        suspiciously_short = char_count < SUSPICIOUS_ARTICLE_CHAR_THRESHOLD
        article_parse_status: ParseStatus = (
            "partial"
            if warning_types or missing_segment_types or suspiciously_short
            else "ok"
        )
        article_rows.append(
            CorpusArticleManifestRecord(
                article_id=article_record.article_id,
                question_id=article_record.question_id,
                part_id=article_record.part_id,
                question_number=article_record.question_number,
                article_number=article_record.article_number,
                article_title=article_record.article_title,
                citation_label=article_record.citation_label,
                parse_status=article_parse_status,
                segment_count=len(segments),
                segment_types=segment_types,
                missing_segment_types=missing_segment_types,
                char_count=char_count,
                warning_types=warning_types,
                suspiciously_short=suspiciously_short,
                source_url=article_record.source_url,
            )
        )
        question_logs.extend(
            build_article_log_rows(
                entry=entry,
                question_identifier=question_identifier,
                article_record=article_record,
                warning_types=warning_types,
                warning_rows=parsed_article_warnings.get(article_record.article_number, []),
                missing_segment_types=missing_segment_types,
                suspiciously_short=suspiciously_short,
            )
        )

    question_warning_count = len(
        [log for log in question_logs if log.level == "warning"]
    )
    question_parse_status: ParseStatus
    if question_record is None:
        question_parse_status = "failed"
    elif parse_error is not None or missing_article_numbers:
        question_parse_status = "partial"
    elif any(row.parse_status == "partial" for row in article_rows):
        question_parse_status = "partial"
    else:
        question_parse_status = "ok"

    question_row = CorpusQuestionManifestRecord(
        question_id=question_identifier,
        part_id=entry.part_id,
        question_number=entry.question_number,
        question_title=question_record.question_title if question_record else parsed_question_title,
        parse_status=question_parse_status,
        expected_article_count=expected_article_count,
        parsed_article_count=len(actual_articles),
        parsed_passage_count=sum(row.segment_count for row in article_rows),
        warning_count=question_warning_count,
        missing_article_numbers=missing_article_numbers,
        source_url=entry.source_url,
    )
    return question_row, article_rows, question_logs


def build_article_log_rows(
    *,
    entry: ScopeEntry,
    question_identifier: str,
    article_record: ArticleRecord,
    warning_types: list[str],
    warning_rows: list[ParseWarning],
    missing_segment_types: list[str],
    suspiciously_short: bool,
) -> list[ParseLogRecord]:
    """Build log rows for one parsed article."""

    rows: list[ParseLogRecord] = []
    for index, warning in enumerate(warning_rows, start=1):
        rows.append(
            ParseLogRecord(
                log_id=(
                    f"log.{article_record.article_id}.{warning.warning_type}.{index:02d}"
                ),
                level="warning",
                log_type=warning.warning_type,
                part_id=entry.part_id,
                question_number=entry.question_number,
                question_id=question_identifier,
                article_number=article_record.article_number,
                article_id=article_record.article_id,
                message=warning.message,
                source_url=article_record.source_url,
            )
        )
    if missing_segment_types:
        rows.append(
            ParseLogRecord(
                log_id=f"log.{article_record.article_id}.missing-segment-types",
                level="warning",
                log_type="article_missing_expected_segment_types",
                part_id=entry.part_id,
                question_number=entry.question_number,
                question_id=question_identifier,
                article_number=article_record.article_number,
                article_id=article_record.article_id,
                message=(
                    "Missing expected segment types: "
                    + ", ".join(sorted(missing_segment_types))
                ),
                source_url=article_record.source_url,
            )
        )
    if suspiciously_short:
        rows.append(
            ParseLogRecord(
                log_id=f"log.{article_record.article_id}.suspiciously-short",
                level="warning",
                log_type="article_suspiciously_short",
                part_id=entry.part_id,
                question_number=entry.question_number,
                question_id=question_identifier,
                article_number=article_record.article_number,
                article_id=article_record.article_id,
                message=(
                    f"Article char_count fell below the conservative audit threshold of "
                    f"{SUSPICIOUS_ARTICLE_CHAR_THRESHOLD}."
                ),
                source_url=article_record.source_url,
            )
        )
    return rows


def build_excluded_question_rows() -> list[CorpusQuestionManifestRecord]:
    """Record explicitly excluded II-II questions in the processed manifest."""

    rows: list[CorpusQuestionManifestRecord] = []
    for question_number in range(183, 190):
        rows.append(
            CorpusQuestionManifestRecord(
                question_id=question_id("ii-ii", question_number),
                part_id="ii-ii",
                question_number=question_number,
                question_title="Excluded by corpus scope",
                parse_status="excluded",
                expected_article_count=0,
                parsed_article_count=0,
                parsed_passage_count=0,
                warning_count=0,
                missing_article_numbers=[],
                source_url=(
                    f"{PART_INDEX_URLS['ii-ii'].rsplit('/', 1)[0]}/3{question_number:03d}.htm"
                ),
                excluded_reason="Explicitly excluded: II-II qq. 183–189 are out of scope.",
            )
        )
    return rows


def write_question_index(path: Path, rows: list[CorpusQuestionManifestRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "question_id",
                "part_id",
                "question_number",
                "question_title",
                "parse_status",
                "expected_article_count",
                "parsed_article_count",
                "parsed_passage_count",
                "warning_count",
                "missing_article_numbers",
                "source_url",
                "excluded_reason",
            ],
        )
        writer.writeheader()
        for row in rows:
            payload = row.model_dump(mode="json")
            payload["missing_article_numbers"] = json.dumps(payload["missing_article_numbers"])
            writer.writerow(payload)


def write_article_index(path: Path, rows: list[CorpusArticleManifestRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "article_id",
                "question_id",
                "part_id",
                "question_number",
                "article_number",
                "article_title",
                "citation_label",
                "parse_status",
                "segment_count",
                "segment_types",
                "missing_segment_types",
                "char_count",
                "warning_types",
                "suspiciously_short",
                "source_url",
            ],
        )
        writer.writeheader()
        for row in rows:
            payload = row.model_dump(mode="json")
            payload["segment_types"] = json.dumps(payload["segment_types"])
            payload["missing_segment_types"] = json.dumps(payload["missing_segment_types"])
            payload["warning_types"] = json.dumps(payload["warning_types"])
            writer.writerow(payload)


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
