from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..models.records import ArticleRecord, QuestionRecord, SegmentRecord
from ..utils.jsonl import load_jsonl
from .config import CorpusPathsConfig, SourceTractConfig
from .utils import tract_display_name

ModelT = TypeVar("ModelT", bound=BaseModel)


class DoctrinalAnnotationRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    annotation_id: str = Field(min_length=1)
    confidence: float | None = None
    connected_virtues_cluster: str | None = None
    due_mode: str | None = None
    edge_layer: str = Field(default="doctrinal", min_length=1)
    evidence_rationale: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    object_label: str = Field(min_length=1)
    object_type: str = Field(min_length=1)
    relation_type: str = Field(min_length=1)
    review_status: str = Field(min_length=1)
    source_passage_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    subject_label: str = Field(min_length=1)
    subject_type: str = Field(min_length=1)
    support_type: str = Field(min_length=1)


class LoadedAnnotationRecord(DoctrinalAnnotationRecord):
    tract: str = Field(min_length=1)
    tract_display_label: str = Field(min_length=1)
    source_file: str = Field(min_length=1)


@dataclass(frozen=True)
class CorpusContext:
    segments: dict[str, SegmentRecord]
    questions: dict[str, QuestionRecord]
    articles: dict[str, ArticleRecord]


def _load_typed_jsonl(path: Path, model_type: type[ModelT]) -> list[ModelT]:
    rows = load_jsonl(path)
    records: list[ModelT] = []
    for line_number, row in enumerate(rows, start=1):
        try:
            records.append(model_type.model_validate(row))
        except ValidationError as exc:
            raise ValueError(f"Invalid {model_type.__name__} row in {path}:{line_number}") from exc
    return records


def load_corpus_context(paths: CorpusPathsConfig) -> CorpusContext:
    segments = _load_typed_jsonl(paths.segments_path, SegmentRecord)
    questions = _load_typed_jsonl(paths.questions_path, QuestionRecord)
    articles = _load_typed_jsonl(paths.articles_path, ArticleRecord)
    return CorpusContext(
        segments={record.segment_id: record for record in segments},
        questions={record.question_id: record for record in questions},
        articles={record.article_id: record for record in articles},
    )


def load_doctrinal_annotation_sources(
    sources: list[SourceTractConfig],
) -> list[LoadedAnnotationRecord]:
    records: list[LoadedAnnotationRecord] = []
    for source in sources:
        rows = _load_typed_jsonl(source.annotations_path, DoctrinalAnnotationRecord)
        tract_label = tract_display_name(source.tract)
        for row in rows:
            records.append(
                LoadedAnnotationRecord(
                    **row.model_dump(),
                    tract=source.tract,
                    tract_display_label=tract_label,
                    source_file=source.annotations_path.name,
                )
            )
    return records
