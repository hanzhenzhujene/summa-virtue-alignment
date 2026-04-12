from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PartId = Literal["i", "i-ii", "ii-ii", "iii", "supplement"]
SegmentType = Literal["obj", "sc", "resp", "ad"]


class BaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QuestionRecord(BaseRecord):
    question_id: str
    part_id: PartId
    question_number: int = Field(ge=1)
    question_title: str = Field(min_length=1)
    article_count: int = Field(ge=1)
    source_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    source_part_url: str = Field(min_length=1)
    hash: str = Field(min_length=1)


class ArticleRecord(BaseRecord):
    article_id: str
    question_id: str
    part_id: PartId
    question_number: int = Field(ge=1)
    article_number: int = Field(ge=1)
    article_title: str = Field(min_length=1)
    citation_label: str = Field(min_length=1)
    segment_ids: list[str] = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    hash: str = Field(min_length=1)


class SegmentRecord(BaseRecord):
    segment_id: str
    article_id: str
    question_id: str
    part_id: PartId
    question_number: int = Field(ge=1)
    question_title: str = Field(min_length=1)
    article_number: int = Field(ge=1)
    article_title: str = Field(min_length=1)
    segment_type: SegmentType
    segment_ordinal: int | None = Field(default=None, ge=1)
    citation_label: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    text: str = Field(min_length=1)
    char_count: int = Field(ge=1)
    hash: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_segment_shape(self) -> "SegmentRecord":
        if self.segment_type in {"obj", "ad"} and self.segment_ordinal is None:
            raise ValueError("obj/ad segments require a segment_ordinal")
        if self.segment_type in {"sc", "resp"} and self.segment_ordinal is not None:
            raise ValueError("sc/resp segments must not have a segment_ordinal")
        if self.char_count != len(self.text):
            raise ValueError("char_count must match len(text)")
        return self


class CrossrefRecord(BaseRecord):
    crossref_id: str
    source_segment_id: str
    source_part_id: PartId
    source_question_number: int = Field(ge=1)
    source_article_number: int = Field(ge=1)
    raw_reference: str = Field(min_length=1)
    normalized_reference: str = Field(min_length=1)
    target_part_id: PartId
    target_question_number: int = Field(ge=1)
    target_article_number: int | None = Field(default=None, ge=1)
    source_url: str = Field(min_length=1)
    hash: str = Field(min_length=1)

