from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .pilot import PilotNodeType, PilotRelationType, PilotSupportType

FortitudeClosure136140Focus = Literal[
    "patience",
    "perseverance",
    "opposed_vice",
    "gift",
    "precept",
    "synthesis",
]


class FortitudeClosure136140BaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FortitudeClosure136140EdgeRecord(FortitudeClosure136140BaseRecord):
    edge_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    subject_type: PilotNodeType
    relation_type: PilotRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    object_type: PilotNodeType
    support_annotation_ids: list[str] = Field(default_factory=list)
    source_passage_ids: list[str] = Field(default_factory=list)
    support_types: list[PilotSupportType] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    review_layer: Literal["reviewed_doctrinal", "reviewed_structural_editorial", "structural"]
    fortitude_closure_focus: list[FortitudeClosure136140Focus] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_support(self) -> "FortitudeClosure136140EdgeRecord":
        if self.review_layer != "structural":
            if not self.support_annotation_ids:
                raise ValueError("Reviewed edges require support_annotation_ids")
            if not self.source_passage_ids:
                raise ValueError("Reviewed edges require source_passage_ids")
            if not self.support_types:
                raise ValueError("Reviewed edges require support_types")
            if not self.evidence_snippets:
                raise ValueError("Reviewed edges require evidence_snippets")
            if not self.fortitude_closure_focus:
                raise ValueError("Reviewed fortitude-closure edges require focus tags")
        return self


class FortitudeClosure136140CoverageQuestionRecord(FortitudeClosure136140BaseRecord):
    question_id: str
    question_number: int = Field(ge=136, le=140)
    question_title: str = Field(min_length=1)
    parse_status: Literal["ok", "partial"]
    passage_count: int = Field(ge=0)
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    reviewed_structural_editorial_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    major_concepts: list[str] = Field(default_factory=list)
    unresolved_ambiguity_count: int = Field(ge=0)
    focus_usage: dict[str, int] = Field(default_factory=dict)
    schema_extension_usage: dict[str, int] = Field(default_factory=dict)


class FortitudeClosure136140ValidationReport(FortitudeClosure136140BaseRecord):
    status: Literal["ok", "warning"]
    question_count: int = Field(ge=0)
    passage_count: int = Field(ge=0)
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    reviewed_structural_editorial_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    patience_relation_count: int = Field(ge=0)
    perseverance_relation_count: int = Field(ge=0)
    opposed_vice_relation_count: int = Field(ge=0)
    gift_linkage_relation_count: int = Field(ge=0)
    precept_linkage_relation_count: int = Field(ge=0)
    fortitude_synthesis_node_count: int = Field(ge=0)
    fortitude_synthesis_edge_count: int = Field(ge=0)
    duplicate_annotation_flags: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "FortitudeClosure136140ValidationReport":
        if self.status == "ok" and (
            self.duplicate_annotation_flags or self.unresolved_warnings
        ):
            raise ValueError("status=ok is incompatible with unresolved validation issues")
        return self
