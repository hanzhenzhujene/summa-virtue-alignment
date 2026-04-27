from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .pilot import (
    PilotConnectedVirtuesCluster,
    PilotNodeType,
    PilotRelationType,
    PilotSupportType,
)


class ConnectedVirtues109120BaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ConnectedVirtues109120EdgeRecord(ConnectedVirtues109120BaseRecord):
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
    connected_virtues_cluster: PilotConnectedVirtuesCluster | None = None

    @model_validator(mode="after")
    def validate_support(self) -> "ConnectedVirtues109120EdgeRecord":
        if self.review_layer != "structural":
            if not self.support_annotation_ids:
                raise ValueError("Reviewed edges require support_annotation_ids")
            if not self.source_passage_ids:
                raise ValueError("Reviewed edges require source_passage_ids")
            if not self.support_types:
                raise ValueError("Reviewed edges require support_types")
            if not self.evidence_snippets:
                raise ValueError("Reviewed edges require evidence_snippets")
            if self.connected_virtues_cluster is None:
                raise ValueError(
                    "Reviewed connected-virtues edges require connected_virtues_cluster"
                )
        return self


class ConnectedVirtues109120CoverageQuestionRecord(ConnectedVirtues109120BaseRecord):
    question_id: str
    question_number: int = Field(ge=109, le=120)
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
    subcluster: PilotConnectedVirtuesCluster
    cluster_usage: dict[str, int] = Field(default_factory=dict)
    schema_extension_usage: dict[str, int] = Field(default_factory=dict)


class ConnectedVirtues109120ValidationReport(ConnectedVirtues109120BaseRecord):
    status: Literal["ok", "warning"]
    question_count: int = Field(ge=0)
    passage_count: int = Field(ge=0)
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    reviewed_structural_editorial_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    self_presentation_relation_count: int = Field(ge=0)
    social_interaction_relation_count: int = Field(ge=0)
    external_goods_relation_count: int = Field(ge=0)
    legal_equity_relation_count: int = Field(ge=0)
    duplicate_annotation_flags: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "ConnectedVirtues109120ValidationReport":
        if self.status == "ok" and (
            self.duplicate_annotation_flags or self.unresolved_warnings
        ):
            raise ValueError("status=ok is incompatible with unresolved validation issues")
        return self
