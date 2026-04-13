from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SupportType = Literal["explicit_textual", "strong_textual_inference", "structural_editorial"]
ReviewStatus = Literal["approved", "candidate"]
ConceptNodeType = Literal[
    "virtue",
    "gift_holy_spirit",
    "vice",
    "defect",
    "faculty",
    "act",
    "end",
    "beatitude",
    "prudence_part",
    "taxonomy",
    "article",
    "question",
]
PrudenceRelationType = Literal[
    "part_of",
    "treated_in",
    "integral_part_of",
    "subjective_part_of",
    "potential_part_of",
    "corresponds_to",
    "opposed_by",
    "contrary_to",
    "species_of",
    "perfected_by",
    "directed_to",
    "regulated_by",
    "caused_by",
    "requires",
    "has_act",
    "resides_in",
]
PartTaxonomy = Literal["integral", "subjective", "potential"]


class PrudenceBaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PrudenceConceptRecord(PrudenceBaseRecord):
    concept_id: str
    label: str = Field(min_length=1)
    node_type: ConceptNodeType
    aliases: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)
    disambiguation_note: str | None = None
    review_status: ReviewStatus
    part_taxonomy: PartTaxonomy | None = None
    unresolved_note: str | None = None


class PrudenceAnnotationRecord(PrudenceBaseRecord):
    annotation_id: str
    source_passage_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    subject_type: ConceptNodeType
    relation_type: PrudenceRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    object_type: ConceptNodeType
    evidence_text: str = Field(min_length=1)
    evidence_rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    review_status: ReviewStatus
    support_type: SupportType


class CandidateMentionRecord(PrudenceBaseRecord):
    mention_id: str
    source_passage_id: str
    candidate_concept_id: str
    candidate_label: str = Field(min_length=1)
    candidate_type: ConceptNodeType
    mention_text: str = Field(min_length=1)
    note: str = Field(min_length=1)
    review_status: Literal["candidate"] = "candidate"


class CandidateRelationProposalRecord(PrudenceBaseRecord):
    proposal_id: str
    source_passage_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    relation_type: PrudenceRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    review_status: Literal["candidate"] = "candidate"


class PrudenceEdgeRecord(PrudenceBaseRecord):
    edge_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    subject_type: ConceptNodeType
    relation_type: PrudenceRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    object_type: ConceptNodeType
    support_annotation_ids: list[str] = Field(default_factory=list)
    source_passage_ids: list[str] = Field(default_factory=list)
    support_types: list[SupportType] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    review_layer: Literal["reviewed_doctrinal", "reviewed_structural_editorial", "structural"]
    part_taxonomy: PartTaxonomy | None = None

    @model_validator(mode="after")
    def validate_edge_support(self) -> "PrudenceEdgeRecord":
        if self.review_layer != "structural":
            if not self.support_annotation_ids:
                raise ValueError("Reviewed edges require support_annotation_ids")
            if not self.source_passage_ids:
                raise ValueError("Reviewed edges require source_passage_ids")
            if not self.support_types:
                raise ValueError("Reviewed edges require support_types")
            if not self.evidence_snippets:
                raise ValueError("Reviewed edges require evidence_snippets")
        return self


class PrudenceCoverageQuestionRecord(PrudenceBaseRecord):
    question_id: str
    question_number: int = Field(ge=47, le=56)
    parse_status: Literal["ok"]
    passage_count: int = Field(ge=0)
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    major_concepts: list[str]
    unresolved_ambiguity_count: int = Field(ge=0)
    part_taxonomy_usage: dict[str, int]


class PrudenceValidationReport(PrudenceBaseRecord):
    status: Literal["ok", "warning"]
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    reviewed_structural_editorial_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    duplicate_annotation_flags: list[str]
    unresolved_warnings: list[str]

    @model_validator(mode="after")
    def validate_status(self) -> "PrudenceValidationReport":
        if self.status == "ok" and self.unresolved_warnings:
            raise ValueError("status=ok is incompatible with unresolved warnings")
        return self
