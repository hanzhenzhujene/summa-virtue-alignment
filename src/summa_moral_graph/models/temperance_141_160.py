from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .pilot import PilotNodeType, PilotRelationType, PilotSupportType

Temperance141160Cluster = Literal[
    "temperance_proper",
    "general_integral",
    "food_drink",
    "sexual",
    "potential_parts",
]
Temperance141160Focus = Literal[
    "temperance_proper",
    "general_integral",
    "food_drink",
    "sexual",
    "potential_parts",
    "integral_part",
    "subjective_part",
    "potential_part",
    "food",
    "drink",
    "sex",
    "continence_incontinence",
    "meekness_anger",
    "clemency_cruelty",
    "modesty_general",
    "synthesis",
]


class Temperance141160BaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Temperance141160EdgeRecord(Temperance141160BaseRecord):
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
    temperance_cluster: Temperance141160Cluster | None = None
    temperance_focus: list[Temperance141160Focus] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_support(self) -> "Temperance141160EdgeRecord":
        if self.review_layer != "structural":
            if not self.support_annotation_ids:
                raise ValueError("Reviewed edges require support_annotation_ids")
            if not self.source_passage_ids:
                raise ValueError("Reviewed edges require source_passage_ids")
            if not self.support_types:
                raise ValueError("Reviewed edges require support_types")
            if not self.evidence_snippets:
                raise ValueError("Reviewed edges require evidence_snippets")
            if self.temperance_cluster is None:
                raise ValueError("Reviewed temperance edges require temperance_cluster")
            if not self.temperance_focus:
                raise ValueError("Reviewed temperance edges require temperance_focus")
        return self


class Temperance141160CoverageQuestionRecord(Temperance141160BaseRecord):
    question_id: str
    question_number: int = Field(ge=141, le=160)
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
    subcluster: Temperance141160Cluster
    part_taxonomy_usage: dict[str, int] = Field(default_factory=dict)
    matter_domain_usage: dict[str, int] = Field(default_factory=dict)
    schema_extension_usage: dict[str, int] = Field(default_factory=dict)


class Temperance141160ValidationReport(Temperance141160BaseRecord):
    status: Literal["ok", "warning"]
    question_count: int = Field(ge=0)
    passage_count: int = Field(ge=0)
    reviewed_annotation_count: int = Field(ge=0)
    reviewed_doctrinal_edge_count: int = Field(ge=0)
    reviewed_structural_editorial_count: int = Field(ge=0)
    candidate_mention_count: int = Field(ge=0)
    candidate_relation_count: int = Field(ge=0)
    integral_part_relation_count: int = Field(ge=0)
    subjective_part_relation_count: int = Field(ge=0)
    potential_part_relation_count: int = Field(ge=0)
    food_related_relation_count: int = Field(ge=0)
    drink_related_relation_count: int = Field(ge=0)
    sex_related_relation_count: int = Field(ge=0)
    continence_incontinence_relation_count: int = Field(ge=0)
    meekness_anger_relation_count: int = Field(ge=0)
    clemency_cruelty_relation_count: int = Field(ge=0)
    modesty_general_relation_count: int = Field(ge=0)
    temperance_phase1_synthesis_node_count: int = Field(ge=0)
    temperance_phase1_synthesis_edge_count: int = Field(ge=0)
    duplicate_annotation_flags: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "Temperance141160ValidationReport":
        if self.status == "ok" and (
            self.duplicate_annotation_flags or self.unresolved_warnings
        ):
            raise ValueError("status=ok is incompatible with unresolved validation issues")
        return self
