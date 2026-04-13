from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .pilot import PilotNodeType, PilotRelationType
from .records import PartId

ParseStatus = Literal["ok", "partial", "failed", "excluded"]
CandidateReviewStatus = Literal["unreviewed", "accepted", "rejected"]
RegistryStatus = Literal["reviewed_seed", "seed", "candidate_only"]


class CorpusBaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CorpusConceptRecord(CorpusBaseRecord):
    concept_id: str
    canonical_label: str = Field(min_length=1)
    node_type: PilotNodeType
    aliases: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)
    source_scope: list[str] = Field(default_factory=list)
    parent_concept_id: str | None = None
    registry_status: RegistryStatus = "seed"
    disambiguation_notes: list[str] = Field(default_factory=list)
    related_concepts: list[str] = Field(default_factory=list)
    introduced_in_questions: list[str] = Field(default_factory=list)


class ParseLogRecord(CorpusBaseRecord):
    log_id: str
    level: Literal["warning", "error"]
    log_type: str = Field(min_length=1)
    part_id: PartId
    question_number: int = Field(ge=1)
    question_id: str
    article_number: int | None = Field(default=None, ge=1)
    article_id: str | None = None
    message: str = Field(min_length=1)
    source_url: str = Field(min_length=1)


class CorpusQuestionManifestRecord(CorpusBaseRecord):
    question_id: str
    part_id: PartId
    question_number: int = Field(ge=1)
    question_title: str = Field(min_length=1)
    parse_status: ParseStatus
    expected_article_count: int = Field(ge=0)
    parsed_article_count: int = Field(ge=0)
    parsed_passage_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    missing_article_numbers: list[int] = Field(default_factory=list)
    source_url: str = Field(min_length=1)
    excluded_reason: str | None = None


class CorpusArticleManifestRecord(CorpusBaseRecord):
    article_id: str
    question_id: str
    part_id: PartId
    question_number: int = Field(ge=1)
    article_number: int = Field(ge=1)
    article_title: str = Field(min_length=1)
    citation_label: str = Field(min_length=1)
    parse_status: ParseStatus
    segment_count: int = Field(ge=0)
    segment_types: list[str] = Field(default_factory=list)
    missing_segment_types: list[str] = Field(default_factory=list)
    char_count: int = Field(ge=0)
    warning_types: list[str] = Field(default_factory=list)
    suspiciously_short: bool = False
    source_url: str = Field(min_length=1)


class CorpusCandidateMentionRecord(CorpusBaseRecord):
    candidate_id: str
    passage_id: str
    matched_text: str = Field(min_length=1)
    normalized_text: str = Field(min_length=1)
    proposed_concept_id: str | None = None
    proposed_concept_ids: list[str] = Field(default_factory=list)
    proposed_node_type: PilotNodeType | None = None
    match_method: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    ambiguity_flag: bool = False
    context_snippet: str = Field(min_length=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=1)
    review_status: CandidateReviewStatus = "unreviewed"

    @model_validator(mode="after")
    def validate_span(self) -> "CorpusCandidateMentionRecord":
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        if self.proposed_concept_id and self.proposed_concept_ids:
            if self.proposed_concept_id not in self.proposed_concept_ids:
                raise ValueError("proposed_concept_id must appear in proposed_concept_ids")
        return self


class CorpusCandidateRelationProposalRecord(CorpusBaseRecord):
    proposal_id: str
    source_passage_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    subject_type: PilotNodeType
    relation_type: PilotRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    object_type: PilotNodeType
    proposal_method: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    ambiguity_flag: bool = False
    support_candidate_ids: list[str] = Field(default_factory=list)
    review_status: CandidateReviewStatus = "unreviewed"


class CandidateValidationReport(CorpusBaseRecord):
    status: Literal["ok", "warning"]
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    unresolved_warnings: list[str] = Field(default_factory=list)
    manifest_consistency_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "CandidateValidationReport":
        if self.status == "ok" and (
            self.unresolved_warnings or self.manifest_consistency_warnings
        ):
            raise ValueError("status=ok is incompatible with unresolved warnings")
        return self
