from __future__ import annotations

from dataclasses import asdict, dataclass

from ..models import ArticleRecord, CrossrefRecord, QuestionRecord, SegmentRecord
from ..utils.hashing import record_hash
from ..utils.ids import (
    article_citation_label,
    article_id,
    crossref_id,
    question_id,
    segment_citation_label,
    segment_id,
)
from ..utils.jsonl import write_jsonl
from ..utils.paths import INTERIM_DIR
from .crossrefs import extract_crossrefs
from .parser import ParsedQuestion, parse_question_html
from .scope import ScopeEntry, build_scope_manifest
from .source import NewAdventClient

SOURCE_ID = "newadvent"


@dataclass(frozen=True)
class InterimBuildSummary:
    articles: int
    crossrefs: int
    output_dir: str
    questions: int
    segments: int


def build_interim_artifacts(refresh_cache: bool = False) -> dict[str, int | str]:
    manifest = build_scope_manifest(refresh_cache=refresh_cache)
    questions: list[QuestionRecord] = []
    articles: list[ArticleRecord] = []
    segments: list[SegmentRecord] = []
    crossrefs: list[CrossrefRecord] = []

    with NewAdventClient() as client:
        for entry in manifest:
            html_text = client.fetch_text(entry.source_url, refresh_cache=refresh_cache)
            parsed_question = parse_question_html(entry.question_number, html_text)
            (
                question_record,
                article_records,
                segment_records,
                crossref_records,
            ) = build_records_for_question(entry, parsed_question)
            questions.append(question_record)
            articles.extend(article_records)
            segments.extend(segment_records)
            crossrefs.extend(crossref_records)

    write_jsonl(INTERIM_DIR / "summa_moral_questions.jsonl", questions)
    write_jsonl(INTERIM_DIR / "summa_moral_articles.jsonl", articles)
    write_jsonl(INTERIM_DIR / "summa_moral_segments.jsonl", segments)
    write_jsonl(INTERIM_DIR / "summa_moral_crossrefs.jsonl", crossrefs)

    summary = InterimBuildSummary(
        questions=len(questions),
        articles=len(articles),
        segments=len(segments),
        crossrefs=len(crossrefs),
        output_dir=str(INTERIM_DIR),
    )
    return asdict(summary)


def build_records_for_question(
    scope_entry: ScopeEntry,
    parsed_question: ParsedQuestion,
) -> tuple[QuestionRecord, list[ArticleRecord], list[SegmentRecord], list[CrossrefRecord]]:
    question_identifier = question_id(scope_entry.part_id, parsed_question.question_number)
    question_payload = {
        "question_id": question_identifier,
        "part_id": scope_entry.part_id,
        "question_number": parsed_question.question_number,
        "question_title": parsed_question.question_title,
        "article_count": len(parsed_question.articles),
        "source_id": SOURCE_ID,
        "source_url": scope_entry.source_url,
        "source_part_url": scope_entry.source_part_url,
    }
    question_record = QuestionRecord.model_validate(
        {
            **question_payload,
            "hash": record_hash(question_payload),
        }
    )

    article_records: list[ArticleRecord] = []
    segment_records: list[SegmentRecord] = []
    crossref_records: list[CrossrefRecord] = []

    for article in parsed_question.articles:
        article_identifier = article_id(question_identifier, article.article_number)
        article_source_url = f"{scope_entry.source_url}#article{article.article_number}"
        article_segment_ids: list[str] = []

        for segment in article.segments:
            segment_identifier = segment_id(
                article_identifier,
                segment.segment_type,
                segment.segment_ordinal,
            )
            article_segment_ids.append(segment_identifier)
            segment_payload = {
                "segment_id": segment_identifier,
                "article_id": article_identifier,
                "question_id": question_identifier,
                "part_id": scope_entry.part_id,
                "question_number": parsed_question.question_number,
                "question_title": parsed_question.question_title,
                "article_number": article.article_number,
                "article_title": article.article_title,
                "segment_type": segment.segment_type,
                "segment_ordinal": segment.segment_ordinal,
                "citation_label": segment_citation_label(
                    scope_entry.part_id,
                    parsed_question.question_number,
                    article.article_number,
                    segment.segment_type,
                    segment.segment_ordinal,
                ),
                "source_id": SOURCE_ID,
                "source_url": article_source_url,
                "text": segment.text,
                "char_count": len(segment.text),
            }
            segment_record = SegmentRecord.model_validate(
                {
                    **segment_payload,
                    "hash": record_hash(segment_payload),
                }
            )
            segment_records.append(segment_record)

            matches = extract_crossrefs(segment.text)
            for occurrence, match in enumerate(matches, start=1):
                crossref_payload = {
                    "crossref_id": crossref_id(segment_identifier, occurrence),
                    "source_segment_id": segment_identifier,
                    "source_part_id": scope_entry.part_id,
                    "source_question_number": parsed_question.question_number,
                    "source_article_number": article.article_number,
                    "raw_reference": match.raw_reference,
                    "normalized_reference": match.normalized_reference,
                    "target_part_id": match.target_part_id,
                    "target_question_number": match.target_question_number,
                    "target_article_number": match.target_article_number,
                    "source_url": article_source_url,
                }
                crossref_records.append(
                    CrossrefRecord.model_validate(
                        {
                            **crossref_payload,
                            "hash": record_hash(crossref_payload),
                        }
                    )
                )

        article_payload = {
            "article_id": article_identifier,
            "question_id": question_identifier,
            "part_id": scope_entry.part_id,
            "question_number": parsed_question.question_number,
            "article_number": article.article_number,
            "article_title": article.article_title,
            "citation_label": article_citation_label(
                scope_entry.part_id,
                parsed_question.question_number,
                article.article_number,
            ),
            "segment_ids": article_segment_ids,
            "source_id": SOURCE_ID,
            "source_url": article_source_url,
        }
        article_records.append(
            ArticleRecord.model_validate(
                {
                    **article_payload,
                    "hash": record_hash(article_payload),
                }
            )
        )

    return question_record, article_records, segment_records, crossref_records
