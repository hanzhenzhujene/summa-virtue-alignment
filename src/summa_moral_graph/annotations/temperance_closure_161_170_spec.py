# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from ..models import PilotRelationType, PilotSupportType
from ..models.temperance_closure_161_170 import (
    TemperanceClosure161170Cluster,
    TemperanceClosure161170Focus,
)

TEMPERANCE_CLOSURE_161_170_MIN_QUESTION = 161
TEMPERANCE_CLOSURE_161_170_MAX_QUESTION = 170


def question_id(question_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}"


def article_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}"


def segment_id(
    question_number: int,
    article_number: int,
    segment_type: str = "resp",
    ordinal: int | None = None,
) -> str:
    base = f"st.ii-ii.q{question_number:03d}.a{article_number:03d}"
    if segment_type in {"obj", "ad"}:
        if ordinal is None:
            raise ValueError(f"{segment_type} segments require an ordinal")
        return f"{base}.{segment_type}{ordinal}"
    if ordinal is not None:
        raise ValueError(f"{segment_type} does not accept an ordinal")
    return f"{base}.{segment_type}"


def cluster_for_question(question_number: int) -> TemperanceClosure161170Cluster:
    if 161 <= question_number <= 162:
        return "humility_pride"
    if 163 <= question_number <= 165:
        return "adams_first_sin"
    if 166 <= question_number <= 167:
        return "study_curiosity"
    if 168 <= question_number <= 169:
        return "external_modesty"
    if question_number == 170:
        return "precept"
    raise ValueError(f"Question outside temperance closure tract: {question_number}")


def cluster_name(value: TemperanceClosure161170Cluster) -> str:
    return {
        "humility_pride": "humility and pride",
        "adams_first_sin": "Adam's first sin",
        "study_curiosity": "studiousness and curiosity",
        "external_modesty": "external modesty",
        "precept": "precepts of temperance",
    }[value]


@dataclass(frozen=True)
class RelationSeed:
    source_passage_id: str
    subject_id: str
    relation_type: PilotRelationType
    object_id: str
    support_type: PilotSupportType
    confidence: float
    rationale: str
    evidence_hints: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TreatmentSeed:
    source_passage_id: str
    subject_id: str
    concept_id: str
    support_type: PilotSupportType
    confidence: float
    rationale: str
    evidence_hints: tuple[str, ...] = field(default_factory=tuple)


RELATION_SEEDS: list[RelationSeed] = []
TREATMENT_SEEDS: list[TreatmentSeed] = []

ADAM_CASE_RELATION_TYPES: set[PilotRelationType] = {
    "case_of",
    "results_in_punishment",
    "tempted_by",
}
ORDERED_INQUIRY_RELATION_TYPES: set[PilotRelationType] = {"concerns_ordered_inquiry"}
EXTERNAL_BEHAVIOR_RELATION_TYPES: set[PilotRelationType] = {"concerns_external_behavior"}
OUTWARD_ATTIRE_RELATION_TYPES: set[PilotRelationType] = {"concerns_outward_attire"}
PRECEPT_RELATION_TYPES: set[PilotRelationType] = {
    "precept_of",
    "commands_act_of",
    "forbids_opposed_vice_of",
}

HUMILITY_PRIDE_CONCEPT_IDS = {
    "concept.humility",
    "concept.pride",
    "concept.truth_about_self",
    "concept.own_excellence",
}
ADAM_CASE_CONCEPT_IDS = {
    "concept.adams_first_sin",
    "concept.divine_likeness",
    "concept.knowledge_good_and_evil",
    "concept.death_first_sin",
    "concept.bodily_defects_first_sin",
    "concept.rebellion_of_carnal_appetite",
    "concept.loss_of_paradise",
    "concept.first_parents_temptation",
}
STUDY_CURIOSITY_CONCEPT_IDS = {
    "concept.studiousness",
    "concept.curiosity",
    "concept.ordered_inquiry",
    "concept.disordered_inquiry",
}
EXTERNAL_MODESTY_CONCEPT_IDS = {
    "concept.external_behavior_modesty",
    "concept.outward_behavior",
    "concept.eutrapelia",
    "concept.playful_actions",
    "concept.excessive_play",
    "concept.boorishness",
    "concept.outward_attire_modesty",
    "concept.outward_apparel",
    "concept.excessive_adornment",
}
PRECEPT_NODE_IDS = {
    "concept.precepts_of_temperance",
    "concept.precepts_of_temperance_parts",
}


def focus_tags_for_edge(
    question_number: int,
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> list[TemperanceClosure161170Focus]:
    tags: set[TemperanceClosure161170Focus] = {
        cast(TemperanceClosure161170Focus, cluster_for_question(question_number))
    }
    if (
        question_number in {163, 164, 165}
        or relation_type in ADAM_CASE_RELATION_TYPES
        or subject_id in ADAM_CASE_CONCEPT_IDS
        or object_id in ADAM_CASE_CONCEPT_IDS
    ):
        tags.add("adam_case")
        tags.add("adams_first_sin")
    if (
        question_number in {166, 167}
        or relation_type in ORDERED_INQUIRY_RELATION_TYPES
        or subject_id in STUDY_CURIOSITY_CONCEPT_IDS
        or object_id in STUDY_CURIOSITY_CONCEPT_IDS
    ):
        tags.add("study_curiosity")
    if (
        question_number in {168, 169}
        or subject_id in EXTERNAL_MODESTY_CONCEPT_IDS
        or object_id in EXTERNAL_MODESTY_CONCEPT_IDS
    ):
        tags.add("external_modesty")
    if (
        relation_type in EXTERNAL_BEHAVIOR_RELATION_TYPES
        or subject_id in {
            "concept.external_behavior_modesty",
            "concept.eutrapelia",
            "concept.playful_actions",
            "concept.excessive_play",
            "concept.boorishness",
            "concept.outward_behavior",
        }
        or object_id
        in {
            "concept.external_behavior_modesty",
            "concept.eutrapelia",
            "concept.playful_actions",
            "concept.excessive_play",
            "concept.boorishness",
            "concept.outward_behavior",
        }
    ):
        tags.add("external_behavior")
    if (
        relation_type in OUTWARD_ATTIRE_RELATION_TYPES
        or subject_id
        in {
            "concept.outward_attire_modesty",
            "concept.outward_apparel",
            "concept.excessive_adornment",
        }
        or object_id
        in {
            "concept.outward_attire_modesty",
            "concept.outward_apparel",
            "concept.excessive_adornment",
        }
    ):
        tags.add("external_attire")
    if (
        question_number == 170
        or relation_type in PRECEPT_RELATION_TYPES
        or subject_id in PRECEPT_NODE_IDS
        or object_id in PRECEPT_NODE_IDS
    ):
        tags.add("precept")
        tags.add("precept_linkage")
    return sorted(tags)


def add_relation(
    question_number: int,
    article_number: int,
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
    *,
    segment_type: str = "resp",
    ordinal: int | None = None,
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.94,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    RELATION_SEEDS.append(
        RelationSeed(
            source_passage_id=segment_id(
                question_number,
                article_number,
                segment_type=segment_type,
                ordinal=ordinal,
            ),
            subject_id=subject_id,
            relation_type=relation_type,
            object_id=object_id,
            support_type=support_type,
            confidence=confidence,
            rationale=rationale,
            evidence_hints=evidence_hints,
        )
    )


def add_question_treatment(
    question_number: int,
    concept_id: str,
    *,
    article_number: int = 1,
    support_type: PilotSupportType = "structural_editorial",
    confidence: float = 0.9,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    TREATMENT_SEEDS.append(
        TreatmentSeed(
            source_passage_id=segment_id(question_number, article_number),
            subject_id=question_id(question_number),
            concept_id=concept_id,
            support_type=support_type,
            confidence=confidence,
            rationale=rationale,
            evidence_hints=evidence_hints,
        )
    )


def add_article_treatment(
    question_number: int,
    article_number: int,
    concept_id: str,
    *,
    segment_type: str = "resp",
    ordinal: int | None = None,
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.92,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    TREATMENT_SEEDS.append(
        TreatmentSeed(
            source_passage_id=segment_id(
                question_number,
                article_number,
                segment_type=segment_type,
                ordinal=ordinal,
            ),
            subject_id=article_id(question_number, article_number),
            concept_id=concept_id,
            support_type=support_type,
            confidence=confidence,
            rationale=rationale,
            evidence_hints=evidence_hints,
        )
    )


def concept(
    concept_id: str,
    canonical_label: str,
    node_type: str,
    *,
    aliases: list[str] | None = None,
    description: str,
    notes: list[str] | None = None,
    source_scope: list[int] | None = None,
    parent_concept_id: str | None = None,
    disambiguation_notes: list[str] | None = None,
    related_concepts: list[str] | None = None,
    introduced_in_questions: list[int] | None = None,
) -> dict[str, Any]:
    scope_ids = [question_id(number) for number in (source_scope or [])]
    introduced_ids = [
        question_id(number) for number in (introduced_in_questions or source_scope or [])
    ]
    return {
        "concept_id": concept_id,
        "canonical_label": canonical_label,
        "node_type": node_type,
        "aliases": aliases or [],
        "description": description,
        "notes": notes or [],
        "source_scope": scope_ids,
        "parent_concept_id": parent_concept_id,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": disambiguation_notes or [],
        "related_concepts": related_concepts or [],
        "introduced_in_questions": introduced_ids,
    }


TEMPERANCE_CLOSURE_161_170_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.humility",
        "Humility",
        "virtue",
        aliases=["humility"],
        description="The virtue that restrains a person from aiming above due measure and submits the spirit under God.",
        source_scope=[161],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from modesty in general, from outward modesty, and from self-deprecating rhetoric."
        ],
        related_concepts=["concept.pride", "concept.modesty_general", "concept.temperance"],
    ),
    concept(
        "concept.truth_about_self",
        "Truth About Oneself",
        "doctrine",
        aliases=["knowledge of one's own deficiency", "truth about oneself"],
        description="The rule by which humility knows and acknowledges one's proportion and deficiency.",
        source_scope=[161],
        related_concepts=["concept.humility"],
    ),
    concept(
        "concept.pride",
        "Pride",
        "vice",
        aliases=["pride", "superbia"],
        description="Inordinate self-exaltation by which a person aims above what is proportionate under the divine rule.",
        source_scope=[162],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from confidence, greatness of soul, and from Adam's first sin as a tract-local doctrinal case."
        ],
        related_concepts=["concept.humility", "concept.own_excellence"],
    ),
    concept(
        "concept.own_excellence",
        "One's Own Excellence",
        "domain",
        aliases=["one's own excellence", "own excellence"],
        description="The difficult good or excellence inordinately desired by pride.",
        source_scope=[162],
        related_concepts=["concept.pride"],
    ),
    concept(
        "concept.adams_first_sin",
        "Adam's First Sin",
        "doctrine",
        aliases=["the first man's first sin", "first man's sin", "Adam's first sin"],
        description="The tract-local doctrinal case of the first sin of the first man, treated under pride without collapsing into the generic vice node.",
        source_scope=[163, 164, 165],
        disambiguation_notes=[
            "Keep distinct from the generic vice concept `concept.pride`."
        ],
        related_concepts=[
            "concept.pride",
            "concept.divine_likeness",
            "concept.knowledge_good_and_evil",
            "concept.first_parents_temptation",
        ],
    ),
    concept(
        "concept.divine_likeness",
        "Divine Likeness",
        "doctrine",
        aliases=["likeness to God", "divine likeness", "God's likeness"],
        description="The likeness to God that the first man inordinately coveted beyond due measure.",
        source_scope=[163, 165],
        related_concepts=["concept.adams_first_sin", "concept.first_parents_temptation"],
    ),
    concept(
        "concept.knowledge_good_and_evil",
        "Knowledge of Good and Evil",
        "doctrine",
        aliases=["knowledge of good and evil"],
        description="The knowledge-related likeness to God especially coveted in the first sin narrative as interpreted in this tract.",
        source_scope=[163, 165],
        related_concepts=["concept.adams_first_sin", "concept.first_parents_temptation"],
    ),
    concept(
        "concept.death_first_sin",
        "Death (Punishment of the First Sin)",
        "doctrine",
        aliases=["death"],
        description="Death as the common punishment flowing from the first sin.",
        source_scope=[164],
        disambiguation_notes=[
            "This tract-local label is for the first-sin punishment context, not every reference to death in the corpus."
        ],
        related_concepts=["concept.adams_first_sin"],
    ),
    concept(
        "concept.bodily_defects_first_sin",
        "Bodily Defects (Punishments of the First Sin)",
        "doctrine",
        aliases=["bodily defects", "defects of the body"],
        description="Bodily corruption, sickness, and defect as punishments following the loss of original integrity.",
        source_scope=[164],
        related_concepts=["concept.adams_first_sin", "concept.death_first_sin"],
    ),
    concept(
        "concept.rebellion_of_carnal_appetite",
        "Rebellion of the Carnal Appetite",
        "doctrine",
        aliases=["rebellion of the carnal appetite", "rebellion of the flesh"],
        description="The disorder whereby the lower appetite rebels against reason as punishment of the first sin.",
        source_scope=[164],
        related_concepts=["concept.adams_first_sin"],
    ),
    concept(
        "concept.loss_of_paradise",
        "Loss of Paradise",
        "doctrine",
        aliases=["loss of paradise", "expulsion from paradise"],
        description="The deprivation of the place and state befitting original innocence after the first sin.",
        source_scope=[164],
        related_concepts=["concept.adams_first_sin"],
    ),
    concept(
        "concept.first_parents_temptation",
        "Temptation of the First Parents",
        "doctrine",
        aliases=["temptation of the first parents", "first parents' temptation"],
        description="The tract-local temptation case leading toward Adam's first sin by intellective and sensitive incentives.",
        source_scope=[165],
        related_concepts=[
            "concept.adams_first_sin",
            "concept.divine_likeness",
            "concept.knowledge_good_and_evil",
        ],
    ),
    concept(
        "concept.studiousness",
        "Studiousness",
        "virtue",
        aliases=["studiousness", "study"],
        description="The virtue moderating the soul's natural desire to know.",
        source_scope=[166],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from curiosity and from generic learning or scholarship."
        ],
        related_concepts=["concept.curiosity", "concept.modesty_general", "concept.temperance"],
    ),
    concept(
        "concept.ordered_inquiry",
        "Ordered Inquiry",
        "domain",
        aliases=["ordered inquiry", "ordered pursuit of knowledge"],
        description="The rightly ordered pursuit of knowledge under reason and due end.",
        source_scope=[166, 167],
        related_concepts=["concept.studiousness", "concept.curiosity"],
    ),
    concept(
        "concept.curiosity",
        "Curiosity",
        "vice",
        aliases=["curiosity"],
        description="Disordered pursuit of knowledge or inquiry, opposed to studiousness in this temperance tract.",
        source_scope=[167],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from neutral modern curiosity and from the simple desire to know taken in itself."
        ],
        related_concepts=["concept.studiousness", "concept.disordered_inquiry"],
    ),
    concept(
        "concept.disordered_inquiry",
        "Disordered Inquiry",
        "domain",
        aliases=["disordered inquiry", "sinful study"],
        description="The inordinate study or pursuit of knowledge treated under curiosity.",
        source_scope=[167],
        related_concepts=["concept.curiosity", "concept.ordered_inquiry"],
    ),
    concept(
        "concept.external_behavior_modesty",
        "Modesty in Outward Movements",
        "virtue",
        aliases=[
            "modesty in outward movements",
            "modesty in the outward movements of the body",
        ],
        description="The tract-local species of modesty governing outward bodily movements and serious external behavior.",
        source_scope=[168],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from modesty in outward apparel and from humility."
        ],
        related_concepts=["concept.modesty_general", "concept.outward_behavior", "concept.eutrapelia"],
    ),
    concept(
        "concept.outward_behavior",
        "Outward Behavior",
        "domain",
        aliases=["outward movements", "outward movements of the body", "external behavior"],
        description="The field of bodily bearing, gesture, and exterior deportment moderated under this part of modesty.",
        source_scope=[168],
        related_concepts=["concept.external_behavior_modesty", "concept.playful_actions"],
    ),
    concept(
        "concept.eutrapelia",
        "Wittiness / Eutrapelia",
        "virtue",
        aliases=["wittiness", "eutrapelia"],
        description="The virtue governing games and playful actions according to reason as part of external modesty.",
        source_scope=[168],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Do not reduce this tract-local virtue to generic humor or entertainment."
        ],
        related_concepts=[
            "concept.external_behavior_modesty",
            "concept.playful_actions",
            "concept.excessive_play",
            "concept.boorishness",
        ],
    ),
    concept(
        "concept.playful_actions",
        "Playful Actions",
        "act_type",
        aliases=["games", "playful actions", "play"],
        description="Words or deeds whose immediate end is delight and rest of soul in play.",
        source_scope=[168],
        related_concepts=["concept.eutrapelia", "concept.excessive_play", "concept.boorishness"],
    ),
    concept(
        "concept.excessive_play",
        "Excessive Play",
        "vice",
        aliases=["excessive play", "immoderate fun"],
        description="The vice of going beyond reason in playful words or deeds.",
        source_scope=[168],
        parent_concept_id="concept.vice",
        related_concepts=["concept.eutrapelia", "concept.playful_actions"],
    ),
    concept(
        "concept.boorishness",
        "Boorishness / Rudeness",
        "vice",
        aliases=["boorishness", "rudeness", "boorish", "rude"],
        description="The vice of deficient playfulness that makes a person burdensome to others in ordinary intercourse.",
        source_scope=[168],
        parent_concept_id="concept.vice",
        related_concepts=["concept.eutrapelia", "concept.playful_actions"],
    ),
    concept(
        "concept.outward_attire_modesty",
        "Modesty in Outward Apparel",
        "virtue",
        aliases=["modesty in outward apparel", "outward apparel modesty"],
        description="The tract-local exterior-modesty species governing attire, ornament, and dress under reason and fitting custom.",
        source_scope=[169],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from humility and from modesty in outward movements."
        ],
        related_concepts=["concept.modesty_general", "concept.outward_apparel", "concept.excessive_adornment"],
    ),
    concept(
        "concept.outward_apparel",
        "Outward Apparel",
        "object",
        aliases=["outward apparel", "apparel", "dress", "attire"],
        description="Dress, ornament, and outward attire as matter moderated under exterior modesty.",
        source_scope=[169],
        related_concepts=["concept.outward_attire_modesty", "concept.excessive_adornment"],
    ),
    concept(
        "concept.excessive_adornment",
        "Excessive Adornment",
        "vice",
        aliases=["excessive adornment", "immoderate apparel", "excessive attention to dress"],
        description="Immoderate attention to outward apparel seeking glory, pleasure, or excessive solicitude.",
        source_scope=[169],
        parent_concept_id="concept.vice",
        related_concepts=["concept.outward_attire_modesty", "concept.outward_apparel"],
    ),
    concept(
        "concept.precepts_of_temperance",
        "Precepts of Temperance",
        "precept",
        aliases=["precepts of temperance"],
        description="The tract-local synthesis of precepts directly bearing on temperance itself.",
        source_scope=[170],
        related_concepts=["concept.temperance", "concept.adultery_lust", "concept.decalogue"],
    ),
    concept(
        "concept.precepts_of_temperance_parts",
        "Precepts of the Parts of Temperance",
        "precept",
        aliases=["precepts of the parts of temperance", "temperance-part precepts"],
        description="The tract-local synthesis of precepts touching the annexed virtues and opposed vices of temperance's parts.",
        source_scope=[170],
        related_concepts=[
            "concept.meekness",
            "concept.anger_vice",
            "concept.humility",
            "concept.pride",
        ],
    ),
]

TRACT_CONCEPT_IDS: set[str] = {
    payload["concept_id"] for payload in TEMPERANCE_CLOSURE_161_170_EXTRA_CONCEPTS
} | {
    "concept.temperance",
    "concept.modesty_general",
    "concept.virtue",
    "concept.vice",
    "concept.god",
    "concept.knowledge",
    "concept.meekness",
    "concept.anger_vice",
    "concept.adultery_lust",
    "concept.decalogue",
    "concept.commandments",
}


for question_number, concept_ids in {
    161: [
        "concept.humility",
        "concept.truth_about_self",
        "concept.modesty_general",
        "concept.temperance",
        "concept.god",
    ],
    162: ["concept.pride", "concept.humility", "concept.own_excellence", "concept.god"],
    163: [
        "concept.adams_first_sin",
        "concept.pride",
        "concept.divine_likeness",
        "concept.knowledge_good_and_evil",
    ],
    164: [
        "concept.adams_first_sin",
        "concept.death_first_sin",
        "concept.bodily_defects_first_sin",
        "concept.rebellion_of_carnal_appetite",
        "concept.loss_of_paradise",
    ],
    165: [
        "concept.first_parents_temptation",
        "concept.adams_first_sin",
        "concept.divine_likeness",
        "concept.knowledge_good_and_evil",
    ],
    166: [
        "concept.studiousness",
        "concept.ordered_inquiry",
        "concept.modesty_general",
        "concept.temperance",
        "concept.knowledge",
    ],
    167: [
        "concept.curiosity",
        "concept.studiousness",
        "concept.disordered_inquiry",
        "concept.knowledge",
    ],
    168: [
        "concept.external_behavior_modesty",
        "concept.outward_behavior",
        "concept.eutrapelia",
        "concept.playful_actions",
        "concept.excessive_play",
        "concept.boorishness",
    ],
    169: [
        "concept.outward_attire_modesty",
        "concept.outward_apparel",
        "concept.excessive_adornment",
    ],
    170: [
        "concept.precepts_of_temperance",
        "concept.precepts_of_temperance_parts",
        "concept.temperance",
        "concept.adultery_lust",
        "concept.meekness",
        "concept.anger_vice",
        "concept.humility",
        "concept.pride",
        "concept.decalogue",
    ],
}.items():
    for concept_id in concept_ids:
        add_question_treatment(
            question_number,
            concept_id,
            rationale="Question heading and tract structure center the question on this concept.",
        )


for question_number, article_number, concept_id, hints in (
    (161, 1, "concept.humility", ("Therefore humility is a virtue", "humility is a virtue")),
    (161, 2, "concept.humility", ("belongs properly to humility",)),
    (161, 2, "concept.truth_about_self", ("knowledge of one's own deficiency",)),
    (161, 3, "concept.humility", ("Whatever pertains to defect is man's",)),
    (161, 4, "concept.humility", ("humility is accounted a part of temperance",)),
    (161, 4, "concept.modesty_general", ("the one under which humility is comprised is modesty",)),
    (161, 5, "concept.humility", ("Humility makes a man a good subject",)),
    (161, 6, "concept.humility", ("humility has essentially to do with the appetite",)),
    (162, 1, "concept.pride", ("Pride", "proud")),
    (162, 2, "concept.pride", ("special sin", "one's own excellence")),
    (162, 2, "concept.own_excellence", ("desire of one's own excellence",)),
    (162, 3, "concept.pride", ("pride must needs pertain",)),
    (162, 4, "concept.pride", ("pride denotes immoderate desire",)),
    (162, 5, "concept.pride", ("Pride is opposed to humility",)),
    (162, 6, "concept.pride", ("pride being the greatest of sins", "pride being the beginning")),
    (162, 7, "concept.pride", ("the beginning of all sins",)),
    (162, 8, "concept.pride", ("capital vice", "pride")),
    (163, 1, "concept.adams_first_sin", ("man's first sin", "was pride")),
    (163, 1, "concept.pride", ("man's first sin was pride",)),
    (163, 2, "concept.divine_likeness", ("coveted God's likeness",)),
    (163, 2, "concept.knowledge_good_and_evil", ("knowledge of good and evil",)),
    (163, 2, "concept.adams_first_sin", ("the first man sinned chiefly",)),
    (163, 3, "concept.adams_first_sin", ("gravity to be observed in sin",)),
    (163, 4, "concept.adams_first_sin", ("the man's sin is the more grievous",)),
    (164, 1, "concept.death_first_sin", ("death and other bodily defects",)),
    (164, 1, "concept.bodily_defects_first_sin", ("defects of the body",)),
    (164, 1, "concept.rebellion_of_carnal_appetite", ("rebellion of the carnal appetite",)),
    (164, 2, "concept.loss_of_paradise", ("sent him out of the paradise",)),
    (164, 2, "concept.death_first_sin", ("Dust thou art", "garments of skin")),
    (165, 1, "concept.first_parents_temptation", ("fitting for man to be tempted",)),
    (165, 2, "concept.first_parents_temptation", ("twofold incentive to sin",)),
    (165, 2, "concept.divine_likeness", ("promising the Divine likeness",)),
    (165, 2, "concept.knowledge_good_and_evil", ("acquisition of knowledge",)),
    (166, 1, "concept.studiousness", ("study denotes keen application",)),
    (166, 1, "concept.ordered_inquiry", ("mind's application to knowledge",)),
    (166, 2, "concept.studiousness", ("virtue of studiousness",)),
    (166, 2, "concept.modesty_general", ("it is comprised under modesty",)),
    (167, 1, "concept.curiosity", ("curiosity", "sinful study")),
    (167, 1, "concept.studiousness", ("studiousness is directly",)),
    (167, 1, "concept.disordered_inquiry", ("study directed to the learning of truth being itself inordinate",)),
    (167, 2, "concept.curiosity", ("knowledge of sensible things",)),
    (168, 1, "concept.external_behavior_modesty", ("there is a moral virtue concerned with the direction of these movements",)),
    (168, 1, "concept.outward_behavior", ("outward movements of man",)),
    (168, 2, "concept.eutrapelia", ("The Philosopher gives it the name of wittiness", "eutrapelia")),
    (168, 2, "concept.playful_actions", ("playful or humorous",)),
    (168, 3, "concept.excessive_play", ("excessive play", "mortal sin")),
    (168, 4, "concept.boorishness", ("boorish or rude",)),
    (169, 1, "concept.outward_attire_modesty", ("outward apparel", "virtues in connection with outward attire")),
    (169, 1, "concept.outward_apparel", ("outward apparel",)),
    (169, 1, "concept.excessive_adornment", ("excessive attention to dress",)),
    (169, 2, "concept.excessive_adornment", ("adornment of women", "incite men to lust")),
    (170, 1, "concept.precepts_of_temperance", ("precepts of temperance", "special prohibition of adultery")),
    (170, 1, "concept.adultery_lust", ("special prohibition of adultery",)),
    (170, 1, "concept.decalogue", ("the decalogue contains",)),
    (170, 2, "concept.precepts_of_temperance_parts", ("virtues annexed to temperance", "precepts that relate")),
    (170, 2, "concept.meekness", ("anger", "opposed to meekness")),
    (170, 2, "concept.pride", ("result of pride",)),
    (170, 2, "concept.humility", ("due honor to his parents",)),
):
    add_article_treatment(
        question_number,
        article_number,
        concept_id,
        rationale="The article heading and respondeo text explicitly treat this concept in the temperance closure tract.",
        evidence_hints=hints,
    )


for seed in (
    (161, 1, "concept.humility", "species_of", "concept.virtue", "Question 161 explicitly concludes that humility is a virtue.", ("Therefore humility is a virtue",)),
    (161, 2, "concept.humility", "regulated_by", "concept.truth_about_self", "Humility is essentially in the appetite but is ruled by knowledge of one's own deficiency.", ("knowledge of one's own deficiency belongs to humility", "rule guiding the appetite")),
    (161, 3, "concept.humility", "directed_to", "concept.god", "Humility properly regards reverent subjection to God in man.", ("whatever pertains to man's welfare and perfection is God's", "subject oneself")),
    (161, 4, "concept.humility", "potential_part_of", "concept.temperance", "Question 161 article 4 explicitly accounts humility a part of temperance.", ("humility is accounted a part of temperance",)),
    (161, 4, "concept.humility", "species_of", "concept.modesty_general", "The article explicitly says humility is comprised under modesty as moderation of spirit.", ("the one under which humility is comprised is modesty", "moderation of spirit")),
    (162, 1, "concept.pride", "species_of", "concept.vice", "Question 162 article 1 concludes that pride is a sin against right reason.", ("Pride", "sin")),
    (162, 2, "concept.pride", "directed_to", "concept.own_excellence", "Pride is explicitly described as the inordinate desire of one's own excellence.", ("desire of one's own excellence",)),
    (162, 5, "concept.pride", "contrary_to", "concept.humility", "Article 5 explicitly states that pride is opposed to humility.", ("Pride is opposed to humility",)),
    (163, 1, "concept.adams_first_sin", "case_of", "concept.pride", "Question 163 article 1 explicitly concludes that the first man's first sin was pride.", ("man's first sin was pride",)),
    (163, 2, "concept.adams_first_sin", "directed_to", "concept.divine_likeness", "Article 2 explains that the first man coveted God's likeness inordinately.", ("coveted God's likeness inordinately",)),
    (163, 2, "concept.adams_first_sin", "directed_to", "concept.knowledge_good_and_evil", "Article 2 says the first man sinned chiefly by coveting God's likeness as knowledge of good and evil.", ("knowledge of good and evil",)),
    (164, 1, "concept.adams_first_sin", "results_in_punishment", "concept.death_first_sin", "Question 164 article 1 explicitly names death as punishment of the first sin.", ("death", "punishment")),
    (164, 1, "concept.adams_first_sin", "results_in_punishment", "concept.bodily_defects_first_sin", "Article 1 explicitly names bodily defects as punishment of the first sin.", ("defects of the body",)),
    (164, 1, "concept.adams_first_sin", "results_in_punishment", "concept.rebellion_of_carnal_appetite", "Article 1 explicitly treats rebellion of the carnal appetite against reason as punishment of the first sin.", ("rebellion of the carnal appetite",)),
    (164, 2, "concept.adams_first_sin", "results_in_punishment", "concept.loss_of_paradise", "Article 2 explicitly includes expulsion from paradise among the first punishments.", ("sent him out of the paradise",)),
    (165, 2, "concept.adams_first_sin", "tempted_by", "concept.first_parents_temptation", "Question 165 details the temptation that led to the first sin.", ("twofold incentive to sin",)),
    (165, 2, "concept.first_parents_temptation", "directed_to", "concept.divine_likeness", "The temptation promised divine likeness.", ("promising the Divine likeness",)),
    (165, 2, "concept.first_parents_temptation", "directed_to", "concept.knowledge_good_and_evil", "The temptation promised likeness through acquisition of knowledge.", ("acquisition of knowledge",)),
    (166, 2, "concept.studiousness", "species_of", "concept.virtue", "Question 166 article 2 explicitly names the virtue of studiousness.", ("virtue of studiousness",)),
    (166, 2, "concept.studiousness", "potential_part_of", "concept.temperance", "Question 166 article 2 explicitly concludes that studiousness is a potential part of temperance.", ("studiousness is a potential part of temperance",)),
    (166, 2, "concept.studiousness", "species_of", "concept.modesty_general", "Question 166 article 2 explicitly says studiousness is comprised under modesty.", ("it is comprised under modesty",)),
    (166, 1, "concept.studiousness", "concerns_ordered_inquiry", "concept.ordered_inquiry", "Studiousness orders the mind's application to knowledge and what is directed by that knowledge.", ("study denotes keen application of the mind",)),
    (167, 1, "concept.curiosity", "species_of", "concept.vice", "Question 167 treats curiosity as the vice opposed to right study.", ("sinful study", "curiosity")),
    (167, 1, "concept.curiosity", "contrary_to", "concept.studiousness", "Question 167 contrasts curiosity with the ordered desire governed by studiousness.", ("studiousness is directly", "curiosity")),
    (167, 1, "concept.curiosity", "concerns_ordered_inquiry", "concept.disordered_inquiry", "Curiosity is the inordinate pursuit of knowledge in several tract-local ways.", ("study directed to the learning of truth being itself inordinate",)),
    (168, 1, "concept.external_behavior_modesty", "species_of", "concept.modesty_general", "Question 168 treats a tract-local species of modesty about outward bodily movement.", ("there is a moral virtue concerned with the direction of these movements",)),
    (168, 1, "concept.external_behavior_modesty", "concerns_external_behavior", "concept.outward_behavior", "Question 168 article 1 explicitly treats virtue in the outward movements of the body.", ("outward movements of man",)),
    (168, 2, "concept.eutrapelia", "species_of", "concept.external_behavior_modesty", "Question 168 article 2 names wittiness/eutrapelia as the play-related virtue comprised under modesty.", ("The Philosopher gives it the name of wittiness", "comprised under modesty")),
    (168, 2, "concept.eutrapelia", "concerns_external_behavior", "concept.playful_actions", "The play-related virtue explicitly governs words or deeds whose end is delight and rest of soul.", ("playful or humorous", "games")),
    (168, 3, "concept.excessive_play", "excess_opposed_to", "concept.eutrapelia", "Question 168 article 3 explicitly treats excessive play as going beyond reason.", ("excessive play",)),
    (168, 4, "concept.boorishness", "deficiency_opposed_to", "concept.eutrapelia", "Question 168 article 4 explicitly treats boorishness or rudeness as the lack of due play.", ("boorish or rude",)),
    (169, 1, "concept.outward_attire_modesty", "species_of", "concept.modesty_general", "Question 169 treats tract-local modesty in outward apparel as a species under temperance's modesty material.", ("outward apparel", "virtues in connection with outward attire")),
    (169, 1, "concept.outward_attire_modesty", "concerns_outward_attire", "concept.outward_apparel", "Question 169 article 1 explicitly treats virtue and vice in connection with outward apparel.", ("outward apparel",)),
    (169, 1, "concept.excessive_adornment", "excess_opposed_to", "concept.outward_attire_modesty", "Article 1 explicitly treats excessive attention to dress as immoderate use of outward apparel.", ("excessive attention to dress",)),
    (169, 1, "concept.excessive_adornment", "concerns_outward_attire", "concept.outward_apparel", "The immoderation treated in article 1 concerns outward apparel and dress.", ("outward apparel", "attention to dress")),
    (170, 1, "concept.precepts_of_temperance", "precept_of", "concept.temperance", "Question 170 article 1 treats the precepts of temperance itself.", ("precepts of temperance itself",)),
    (170, 1, "concept.precepts_of_temperance", "forbids_opposed_vice_of", "concept.adultery_lust", "Question 170 article 1 explicitly says the Decalogue specially prohibits adultery as a vice opposed to temperance.", ("special prohibition of adultery",)),
    (170, 2, "concept.precepts_of_temperance_parts", "precept_of", "concept.humility", "Question 170 article 2 links due honor to parents to pride's effect and so to humility by strong textual inference.", ("refuses due honor to his parents", "result of pride")),
    (170, 2, "concept.precepts_of_temperance_parts", "precept_of", "concept.meekness", "Question 170 article 2 links the prohibition of murder to anger opposed to meekness.", ("effect of anger", "opposed to meekness")),
    (170, 2, "concept.precepts_of_temperance_parts", "forbids_opposed_vice_of", "concept.pride", "Question 170 article 2 explicitly notes that pride leads many to transgress first-table precepts.", ("result of pride",)),
    (170, 2, "concept.precepts_of_temperance_parts", "forbids_opposed_vice_of", "concept.anger_vice", "Question 170 article 2 explicitly notes that the effect of anger can proceed to murder, which the Decalogue forbids.", ("effect of anger", "commit murder")),
):
    question_number, article_number, subject_id, relation_type, object_id, rationale, hints = seed
    add_relation(
        question_number,
        article_number,
        subject_id,
        cast(PilotRelationType, relation_type),
        object_id,
        rationale=rationale,
        evidence_hints=cast(tuple[str, ...], hints),
    )
