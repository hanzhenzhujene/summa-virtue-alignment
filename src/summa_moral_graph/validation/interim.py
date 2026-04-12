from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from ..models import ArticleRecord, CrossrefRecord, QuestionRecord, SegmentRecord
from ..utils.jsonl import load_jsonl
from ..utils.paths import INTERIM_DIR


def validate_interim_artifacts() -> dict[str, int | str]:
    question_records = load_model_records(
        INTERIM_DIR / "summa_moral_questions.jsonl",
        QuestionRecord,
    )
    article_records = load_model_records(
        INTERIM_DIR / "summa_moral_articles.jsonl",
        ArticleRecord,
    )
    segment_records = load_model_records(
        INTERIM_DIR / "summa_moral_segments.jsonl",
        SegmentRecord,
    )
    crossref_records = load_model_records(
        INTERIM_DIR / "summa_moral_crossrefs.jsonl",
        CrossrefRecord,
    )

    assert_unique_ids(question_records, "question_id")
    assert_unique_ids(article_records, "article_id")
    assert_unique_ids(segment_records, "segment_id")
    assert_unique_ids(crossref_records, "crossref_id")

    question_ids = {record.question_id for record in question_records}
    article_ids = {record.article_id for record in article_records}
    segment_ids = {record.segment_id for record in segment_records}

    for article in article_records:
        if article.question_id not in question_ids:
            raise ValueError(
                f"Article {article.article_id} points to missing question "
                f"{article.question_id}"
            )

    for segment in segment_records:
        if not segment.text.strip():
            raise ValueError(f"Segment {segment.segment_id} has empty text")
        if segment.article_id not in article_ids:
            raise ValueError(
                f"Segment {segment.segment_id} points to missing article "
                f"{segment.article_id}"
            )
        if segment.question_id not in question_ids:
            raise ValueError(
                f"Segment {segment.segment_id} points to missing question "
                f"{segment.question_id}"
            )

    for crossref in crossref_records:
        if crossref.source_segment_id not in segment_ids:
            raise ValueError(
                f"Cross-reference {crossref.crossref_id} points to missing segment "
                f"{crossref.source_segment_id}"
            )

    article_segments = defaultdict(list)
    for segment in segment_records:
        article_segments[segment.article_id].append(segment)

    question_articles = defaultdict(list)
    for article in article_records:
        question_articles[article.question_id].append(article)
        expected_segment_ids = [
            segment.segment_id for segment in article_segments[article.article_id]
        ]
        if article.segment_ids != expected_segment_ids:
            raise ValueError(f"Article {article.article_id} has mismatched segment_ids")
        validate_segment_order(article.article_id, article_segments[article.article_id])

    for question in question_records:
        article_count = len(question_articles[question.question_id])
        if question.article_count != article_count:
            raise ValueError(
                f"Question {question.question_id} expected {question.article_count} "
                f"articles but found {article_count}"
            )

    return {
        "status": "ok",
        "questions": len(question_records),
        "articles": len(article_records),
        "segments": len(segment_records),
        "crossrefs": len(crossref_records),
    }


def load_model_records(path, model_cls):
    return [model_cls.model_validate(item) for item in load_jsonl(path)]


def assert_unique_ids(records: Sequence[Any], field_name: str) -> None:
    seen: set[str] = set()
    for record in records:
        value = getattr(record, field_name)
        if value in seen:
            raise ValueError(f"Duplicate {field_name}: {value}")
        seen.add(value)


def validate_segment_order(article_id: str, segments: list[SegmentRecord]) -> None:
    seen_sc = 0
    seen_resp = 0
    state_order = {"obj": 0, "sc": 1, "resp": 2, "ad": 3}
    previous_state = -1
    expected_obj = 1
    expected_ad = 1

    for segment in segments:
        state = state_order[segment.segment_type]
        if state < previous_state:
            raise ValueError(f"Article {article_id} has invalid segment ordering")
        previous_state = state

        if segment.segment_type == "obj":
            if segment.segment_ordinal != expected_obj:
                raise ValueError(f"Article {article_id} has non-consecutive objections")
            expected_obj += 1
        elif segment.segment_type == "sc":
            seen_sc += 1
            if seen_sc > 1:
                raise ValueError(f"Article {article_id} has more than one sed contra")
        elif segment.segment_type == "resp":
            seen_resp += 1
            if seen_resp > 1:
                raise ValueError(f"Article {article_id} has more than one respondeo")
        elif segment.segment_type == "ad":
            if segment.segment_ordinal != expected_ad:
                raise ValueError(f"Article {article_id} has non-consecutive replies")
            expected_ad += 1
