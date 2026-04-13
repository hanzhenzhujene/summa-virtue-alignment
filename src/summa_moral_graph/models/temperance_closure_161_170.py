from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .pilot import PilotNodeType, PilotRelationType, PilotSupportType

TemperanceClosure161170Cluster = Literal[
    "humility_pride",
    "adams_first_sin",
    "study_curiosity",
    "external_modesty",
    "precept",
]
TemperanceClosure161170Focus = Literal[
    "humility_pride",
    "adams_first_sin",
    "study_curiosity",
    "external_modesty",
    "precept",
    "adam_case",
    "external_behavior",
    "external_attire",
    "precept_linkage",
    "synthesis",
]


class TemperanceClosure161170BaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TemperanceClosure161170EdgeRecord(TemperanceClosure161170BaseRecord):
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
    temperance_closure_cluster: TemperanceClosure161170Cluster | None = None
    temperance_closure_focus: list[TemperanceClosure161170Focus] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_support(self) -> "TemperanceClosure161170EdgeRecord":
        if self.review_layer != "structural":
            if not self.support_annotation_ids:
                raise ValueError("Reviewed edges require support_annotation_ids")
            if not self.source_passage_ids:
                raise ValueError("Reviewed edges require source_passage_ids")
            if not self.support_types:
                raise ValueError("Reviewed edges require support_types")
            if not self.evidence_snippets:
                raise ValueError("Reviewed edges require evidence_snippets")
            if self.temperance_closure_cluster is None:
                raise ValueError(
                    "Reviewed temperance-closure edges require temperance_closure_cluster"
                )
            if not self.temperance_closure_focus:
                raise ValueError(
                    "Reviewed temperance-closure edges require temperance_closure_focus"
                )
        return self


class TemperanceClosure161170CoverageQuestionRecord(TemperanceClosure161170BaseRecord):
    question_id: str
    question_number: int = Field(ge=161, le=170)
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
    subcluster: TemperanceClosure161170Cluster
    focus_usage: dict[str, int] = Field(default_factory=dict)
    schema_extension_usage: dict[str, int] = Field(default_factory=dict)


class TemperanceClosure161170ValidationReport(TemperanceClosure161170BaseRecord):
    status: Literal["ok", "warning"]
    question_count: int = Field(ge=0)
    passage_count: int = Field(ge=0)
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    reviewed_structural_editorial_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    humility_pride_relation_count: int = Field(ge=0)
    adams_first_sin_case_relation_count: int = Field(ge=0)
    studiousness_curiosity_relation_count: int = Field(ge=0)
    external_modesty_relation_count: int = Field(ge=0)
    precept_linkage_relation_count: int = Field(ge=0)
    temperance_full_synthesis_node_count: int = Field(ge=0)
    temperance_full_synthesis_edge_count: int = Field(ge=0)
    duplicate_annotation_flags: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "TemperanceClosure161170ValidationReport":
        if self.status == "ok" and (
            self.duplicate_annotation_flags or self.unresolved_warnings
        ):
            raise ValueError("status=ok is incompatible with unresolved validation issues")
        return self
