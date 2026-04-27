from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PilotSupportType = Literal[
    "explicit_textual",
    "strong_textual_inference",
    "structural_editorial",
]
PilotDueMode = Literal[
    "origin",
    "excellence",
    "authority",
    "benefaction",
    "rectificatory",
]
PilotConnectedVirtuesCluster = Literal[
    "self_presentation",
    "social_interaction",
    "external_goods",
    "legal_equity",
]
PilotNodeType = Literal[
    "end",
    "beatitude",
    "act_type",
    "wrong_act",
    "passion",
    "habit",
    "virtue",
    "vice",
    "sin_type",
    "law",
    "law_type",
    "grace",
    "grace_type",
    "gift_holy_spirit",
    "charism",
    "precept",
    "faculty",
    "object",
    "domain",
    "role",
    "process",
    "doctrine",
    "question",
    "article",
]
PilotRelationType = Literal[
    "contains_article",
    "treated_in",
    "annexed_to",
    "contrary_to",
    "opposed_by",
    "excess_opposed_to",
    "deficiency_opposed_to",
    "integral_part_of",
    "subjective_part_of",
    "potential_part_of",
    "act_of",
    "part_of_fortitude",
    "corresponding_gift_of",
    "precept_of",
    "commands_act_of",
    "forbids_opposed_vice_of",
    "case_of",
    "results_in_punishment",
    "tempted_by",
    "corresponds_to",
    "perfected_by",
    "regulated_by",
    "directed_to",
    "related_to_fortitude",
    "species_of",
    "part_of",
    "caused_by",
    "requires",
    "defined_as",
    "resides_in",
    "has_act",
    "has_object",
    "concerns_honor",
    "concerns_worthiness",
    "concerns_great_expenditure",
    "concerns_great_work",
    "requires_restitution",
    "harms_domain",
    "corrupts_process",
    "abuses_role",
    "concerns_sacred_object",
    "misuses_sacred_object",
    "corrupts_spiritual_exchange",
    "concerns_due_to",
    "owed_to_role",
    "responds_to_benefaction",
    "responds_to_command",
    "rectifies_wrong",
    "concerns_self_presentation",
    "concerns_social_interaction",
    "concerns_external_goods",
    "corrects_legal_letter",
    "preserves_intent_of_law",
    "concerns_food",
    "concerns_drink",
    "concerns_sexual_pleasure",
    "concerns_anger",
    "concerns_outward_moderation",
    "concerns_ordered_inquiry",
    "concerns_external_behavior",
    "concerns_outward_attire",
]
PilotEdgeLayer = Literal["structural", "doctrinal"]


class PilotBaseRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ConceptRegistryRecord(PilotBaseRecord):
    concept_id: str
    canonical_label: str = Field(min_length=1)
    node_type: PilotNodeType
    aliases: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)
    source_scope: list[str] = Field(default_factory=list)


class PilotAnnotationRecord(PilotBaseRecord):
    annotation_id: str
    source_passage_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    subject_type: PilotNodeType
    relation_type: PilotRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    object_type: PilotNodeType
    evidence_text: str = Field(min_length=1)
    evidence_rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    edge_layer: PilotEdgeLayer
    support_type: PilotSupportType
    due_mode: PilotDueMode | None = None
    connected_virtues_cluster: PilotConnectedVirtuesCluster | None = None
    review_status: Literal["approved"] = "approved"


class PilotEdgeRecord(PilotBaseRecord):
    edge_id: str
    subject_id: str
    subject_label: str = Field(min_length=1)
    subject_type: PilotNodeType
    relation_type: PilotRelationType
    object_id: str
    object_label: str = Field(min_length=1)
    object_type: PilotNodeType
    edge_layer: PilotEdgeLayer
    support_annotation_ids: list[str] = Field(default_factory=list)
    source_passage_ids: list[str] = Field(default_factory=list)
    support_types: list[PilotSupportType] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    due_mode: PilotDueMode | None = None
    connected_virtues_cluster: PilotConnectedVirtuesCluster | None = None

    @model_validator(mode="after")
    def validate_support(self) -> "PilotEdgeRecord":
        if self.edge_layer == "doctrinal" and not self.support_annotation_ids:
            raise ValueError("Doctrinal edges require support_annotation_ids")
        if self.edge_layer == "doctrinal" and not self.source_passage_ids:
            raise ValueError("Doctrinal edges require source_passage_ids")
        return self


class PilotValidationReport(PilotBaseRecord):
    status: Literal["ok", "warning"]
    passage_count: int = Field(ge=0)
    concept_count: int = Field(ge=0)
    annotation_count: int = Field(ge=0)
    doctrinal_edge_count: int = Field(ge=0)
    structural_edge_count: int = Field(ge=0)
    duplicate_annotations: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    alias_collisions: list[str] = Field(default_factory=list)
    unresolved_warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> "PilotValidationReport":
        if self.status == "ok" and (
            self.duplicate_annotations
            or self.missing_evidence
            or self.alias_collisions
            or self.unresolved_warnings
        ):
            raise ValueError("status=ok is incompatible with unresolved validation issues")
        return self
