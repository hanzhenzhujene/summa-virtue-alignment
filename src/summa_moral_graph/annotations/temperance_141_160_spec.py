# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from ..models import PilotRelationType, PilotSupportType
from ..models.temperance_141_160 import (
    Temperance141160Cluster,
    Temperance141160Focus,
)

TEMPERANCE_141_160_MIN_QUESTION = 141
TEMPERANCE_141_160_MAX_QUESTION = 160


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


def cluster_for_question(question_number: int) -> Temperance141160Cluster:
    if 141 <= question_number <= 142:
        return "temperance_proper"
    if 143 <= question_number <= 145:
        return "general_integral"
    if 146 <= question_number <= 150:
        return "food_drink"
    if 151 <= question_number <= 154:
        return "sexual"
    if 155 <= question_number <= 160:
        return "potential_parts"
    raise ValueError(f"Question outside temperance tract: {question_number}")


def cluster_name(value: Temperance141160Cluster) -> str:
    return {
        "temperance_proper": "temperance proper",
        "general_integral": "general and integral parts",
        "food_drink": "food and drink",
        "sexual": "chastity and lust",
        "potential_parts": "potential parts",
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

INTEGRAL_PART_RELATIONS: set[PilotRelationType] = {"integral_part_of"}
SUBJECTIVE_PART_RELATIONS: set[PilotRelationType] = {"subjective_part_of"}
POTENTIAL_PART_RELATIONS: set[PilotRelationType] = {"potential_part_of"}
FOOD_RELATION_TYPES: set[PilotRelationType] = {"concerns_food"}
DRINK_RELATION_TYPES: set[PilotRelationType] = {"concerns_drink"}
SEX_RELATION_TYPES: set[PilotRelationType] = {"concerns_sexual_pleasure"}
ANGER_RELATION_TYPES: set[PilotRelationType] = {"concerns_anger"}
MODESTY_RELATION_TYPES: set[PilotRelationType] = {"concerns_outward_moderation"}

FOOD_CONCEPT_IDS = {
    "concept.abstinence",
    "concept.fasting",
    "concept.gluttony",
    "concept.food",
}
DRINK_CONCEPT_IDS = {
    "concept.sobriety",
    "concept.drunkenness",
    "concept.drink",
}
SEX_CONCEPT_IDS = {
    "concept.chastity",
    "concept.purity_temperance",
    "concept.virginity",
    "concept.lust",
    "concept.parts_of_lust",
    "concept.simple_fornication",
    "concept.seduction_lust",
    "concept.rape_lust",
    "concept.adultery_lust",
    "concept.incest_lust",
    "concept.sacrilege_lust",
    "concept.unnatural_vice_lust",
    "concept.venereal_touches_kisses",
    "concept.nocturnal_pollution",
    "concept.sexual_pleasure",
}
CONTINENCE_INCONTINENCE_CONCEPT_IDS = {
    "concept.continence",
    "concept.incontinence",
}
MEEKNESS_ANGER_CONCEPT_IDS = {
    "concept.meekness",
    "concept.anger",
    "concept.anger_vice",
}
CLEMENCY_CRUELTY_CONCEPT_IDS = {
    "concept.clemency",
    "concept.cruelty",
    "concept.punishment",
}
MODESTY_GENERAL_CONCEPT_IDS = {
    "concept.modesty_general",
    "concept.outward_moderation",
}
TEMPERANCE_PROPER_CONCEPT_IDS = {
    "concept.temperance",
    "concept.intemperance",
    "concept.insensibility_temperance",
    "concept.pleasures_of_touch",
    "concept.food",
    "concept.drink",
    "concept.sexual_pleasure",
}


def focus_tags_for_edge(
    question_number: int,
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> list[Temperance141160Focus]:
    tags: set[Temperance141160Focus] = {cast(Temperance141160Focus, cluster_for_question(question_number))}
    if relation_type in INTEGRAL_PART_RELATIONS:
        tags.add("integral_part")
    if relation_type in SUBJECTIVE_PART_RELATIONS:
        tags.add("subjective_part")
    if relation_type in POTENTIAL_PART_RELATIONS:
        tags.add("potential_part")
    if (
        relation_type in FOOD_RELATION_TYPES
        or subject_id in FOOD_CONCEPT_IDS
        or object_id in FOOD_CONCEPT_IDS
    ):
        tags.add("food")
    if (
        relation_type in DRINK_RELATION_TYPES
        or subject_id in DRINK_CONCEPT_IDS
        or object_id in DRINK_CONCEPT_IDS
    ):
        tags.add("drink")
    if (
        relation_type in SEX_RELATION_TYPES
        or subject_id in SEX_CONCEPT_IDS
        or object_id in SEX_CONCEPT_IDS
    ):
        tags.add("sex")
    if (
        subject_id in CONTINENCE_INCONTINENCE_CONCEPT_IDS
        or object_id in CONTINENCE_INCONTINENCE_CONCEPT_IDS
    ):
        tags.add("continence_incontinence")
    if (
        relation_type in ANGER_RELATION_TYPES
        or subject_id in MEEKNESS_ANGER_CONCEPT_IDS
        or object_id in MEEKNESS_ANGER_CONCEPT_IDS
    ):
        tags.add("meekness_anger")
    if (
        subject_id in CLEMENCY_CRUELTY_CONCEPT_IDS
        or object_id in CLEMENCY_CRUELTY_CONCEPT_IDS
    ):
        tags.add("clemency_cruelty")
    if (
        relation_type in MODESTY_RELATION_TYPES
        or subject_id in MODESTY_GENERAL_CONCEPT_IDS
        or object_id in MODESTY_GENERAL_CONCEPT_IDS
    ):
        tags.add("modesty_general")
    if subject_id in TEMPERANCE_PROPER_CONCEPT_IDS or object_id in TEMPERANCE_PROPER_CONCEPT_IDS:
        tags.add("temperance_proper")
    if question_number in {143, 144, 145}:
        tags.add("general_integral")
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


TEMPERANCE_141_160_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.insensibility_temperance",
        "Insensibility (Against Temperance)",
        "vice",
        aliases=["insensibility"],
        description="Defective refusal of pleasures that nature requires in due measure, opposed to temperance in q.142.",
        source_scope=[142],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from bodily numbness or psychological insensibility outside the temperance tract."
        ],
        related_concepts=["concept.temperance", "concept.intemperance"],
    ),
    concept(
        "concept.pleasures_of_touch",
        "Pleasures of Touch",
        "domain",
        aliases=["pleasures of touch", "touch pleasures"],
        description="The proper matter of temperance in the restricted sense emphasized in q.141.",
        source_scope=[141, 143],
        related_concepts=["concept.temperance", "concept.food", "concept.drink", "concept.sexual_pleasure"],
    ),
    concept(
        "concept.food",
        "Food",
        "object",
        aliases=["food", "meat", "meats"],
        description="Food as matter for abstinence, fasting, and gluttony within the temperance tract.",
        source_scope=[141, 146, 147, 148],
        related_concepts=["concept.abstinence", "concept.fasting", "concept.gluttony"],
    ),
    concept(
        "concept.drink",
        "Drink",
        "object",
        aliases=["drink", "wine", "intoxicating drink"],
        description="Drink as matter for sobriety and drunkenness in the temperance tract.",
        source_scope=[141, 143, 149, 150],
        related_concepts=["concept.sobriety", "concept.drunkenness"],
    ),
    concept(
        "concept.sexual_pleasure",
        "Venereal / Sexual Pleasure",
        "domain",
        aliases=["venereal pleasure", "sexual pleasure", "venereal pleasures"],
        description="The venereal matter treated by chastity, virginity, lust, and the parts of lust.",
        source_scope=[141, 151, 152, 153, 154, 155, 156],
        related_concepts=[
            "concept.chastity",
            "concept.purity_temperance",
            "concept.virginity",
            "concept.lust",
        ],
    ),
    concept(
        "concept.parts_of_temperance_general",
        "Parts of Temperance (General Taxonomy)",
        "doctrine",
        aliases=["parts of temperance", "temperance parts"],
        description="The tract-level teaching that temperance has integral, subjective, and potential parts.",
        source_scope=[143],
        related_concepts=[
            "concept.shamefacedness",
            "concept.honesty_temperance",
            "concept.abstinence",
            "concept.sobriety",
            "concept.chastity",
            "concept.purity_temperance",
            "concept.continence",
            "concept.meekness",
            "concept.modesty_general",
        ],
    ),
    concept(
        "concept.shamefacedness",
        "Shamefacedness",
        "passion",
        aliases=["shamefacedness", "shame"],
        description="The fear of disgrace that stands as an integral part of temperance while falling short of perfect virtue.",
        source_scope=[143, 144],
        disambiguation_notes=[
            "Keep distinct from modesty in general and from mere social embarrassment."
        ],
        related_concepts=["concept.temperance", "concept.disgrace"],
    ),
    concept(
        "concept.disgrace",
        "Disgrace",
        "domain",
        aliases=["disgrace", "shameful disgrace"],
        description="Disgrace as the feared deformity opposed to temperance and related virtue.",
        source_scope=[144],
        related_concepts=["concept.shamefacedness", "concept.intemperance"],
    ),
    concept(
        "concept.honesty_temperance",
        "Honesty (Temperance Tract)",
        "doctrine",
        aliases=["honesty", "the honest", "honestum"],
        description="Honesty as the honorable comeliness of virtue and an integral part of temperance in this tract.",
        source_scope=[143, 145],
        disambiguation_notes=[
            "Keep distinct from truthfulness or social honesty in the connected-virtues tract."
        ],
        related_concepts=["concept.temperance", "concept.beauty_of_virtue"],
    ),
    concept(
        "concept.beauty_of_virtue",
        "Beauty / Comeliness of Virtue",
        "domain",
        aliases=["beauty", "comeliness", "beauty of virtue"],
        description="The honorable beauty or comeliness especially associated with temperance and honesty.",
        source_scope=[145],
        related_concepts=["concept.honesty_temperance", "concept.temperance"],
    ),
    concept(
        "concept.abstinence",
        "Abstinence",
        "virtue",
        aliases=["abstinence"],
        description="The virtue moderating food by reason.",
        source_scope=[143, 146, 147, 148],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from fasting, which is an act of abstinence."
        ],
        related_concepts=["concept.temperance", "concept.food", "concept.fasting", "concept.gluttony"],
    ),
    concept(
        "concept.fasting",
        "Fasting",
        "act_type",
        aliases=["fasting"],
        description="A virtuous act of abstinence undertaken under the rule of reason.",
        source_scope=[147],
        related_concepts=["concept.abstinence", "concept.food"],
    ),
    concept(
        "concept.gluttony",
        "Gluttony",
        "vice",
        aliases=["gluttony"],
        description="Inordinate desire of eating and drinking opposed to abstinence.",
        source_scope=[148],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from drunkenness, which concerns intoxicating drink more specifically."
        ],
        related_concepts=["concept.abstinence", "concept.food", "concept.drink"],
    ),
    concept(
        "concept.sobriety",
        "Sobriety",
        "virtue",
        aliases=["sobriety"],
        description="The virtue moderating intoxicating drink for the safeguard of reason.",
        source_scope=[143, 149, 150],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from abstinence, which concerns food more broadly."
        ],
        related_concepts=["concept.temperance", "concept.drink", "concept.drunkenness"],
    ),
    concept(
        "concept.drunkenness",
        "Drunkenness",
        "vice",
        aliases=["drunkenness"],
        description="Immoderate use of wine or intoxicating drink resulting in loss of reason.",
        source_scope=[150],
        parent_concept_id="concept.vice",
        related_concepts=["concept.sobriety", "concept.drink"],
    ),
    concept(
        "concept.chastity",
        "Chastity",
        "virtue",
        aliases=["chastity"],
        description="The virtue by which reason chastises concupiscence in venereal pleasures.",
        source_scope=[143, 151, 152, 153],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from virginity, which the tract treats as a further excellence and state."
        ],
        related_concepts=[
            "concept.sexual_pleasure",
            "concept.purity_temperance",
            "concept.virginity",
            "concept.lust",
        ],
    ),
    concept(
        "concept.purity_temperance",
        "Purity (Temperance Tract)",
        "virtue",
        aliases=["purity"],
        description="Purity insofar as it moderates pleasures incidental to venereal acts in the temperance tract.",
        source_scope=[143, 151],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from ritual, sacramental, or merely generic purity outside the temperance tract."
        ],
        related_concepts=["concept.chastity", "concept.sexual_pleasure"],
    ),
    concept(
        "concept.virginity",
        "Virginity",
        "virtue",
        aliases=["virginity"],
        description="The tract's virtue or state of perpetual integrity ordered to freedom from venereal experience.",
        source_scope=[152],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Do not merge virginity into chastity simpliciter."
        ],
        related_concepts=["concept.chastity", "concept.sexual_pleasure"],
    ),
    concept(
        "concept.lust",
        "Lust",
        "vice",
        aliases=["lust"],
        description="Disordered seeking of venereal pleasure against right reason.",
        source_scope=[153, 154],
        parent_concept_id="concept.vice",
        related_concepts=["concept.chastity", "concept.sexual_pleasure", "concept.parts_of_lust"],
    ),
    concept(
        "concept.parts_of_lust",
        "Parts / Species of Lust",
        "doctrine",
        aliases=["parts of lust", "species of lust"],
        description="The tract-level division of lust into distinct species treated in q.154.",
        source_scope=[154],
        related_concepts=[
            "concept.simple_fornication",
            "concept.seduction_lust",
            "concept.rape_lust",
            "concept.adultery_lust",
            "concept.incest_lust",
            "concept.sacrilege_lust",
            "concept.unnatural_vice_lust",
        ],
    ),
    concept(
        "concept.simple_fornication",
        "Simple Fornication",
        "sin_type",
        aliases=["simple fornication", "fornication"],
        description="The union of an unmarried man and an unmarried woman treated as a species of lust in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.venereal_touches_kisses",
        "Venereal Touches / Kisses",
        "sin_type",
        aliases=["touches", "kisses", "venereal touches", "seductive touches"],
        description="Disordered venereal touching and kissing treated in q.154 a.4.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.nocturnal_pollution",
        "Nocturnal Pollution",
        "sin_type",
        aliases=["nocturnal pollution"],
        description="Nocturnal venereal pollution as treated in q.154 a.5.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.seduction_lust",
        "Seduction",
        "sin_type",
        aliases=["seduction"],
        description="Seduction as treated among the species or tracted cases of lust in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.rape_lust",
        "Rape",
        "sin_type",
        aliases=["rape"],
        description="Rape as treated within the species or grave acts of lust in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.adultery_lust",
        "Adultery",
        "sin_type",
        aliases=["adultery"],
        description="Adultery as treated within the species of lust in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.incest_lust",
        "Incest",
        "sin_type",
        aliases=["incest"],
        description="Incest as treated within the species of lust in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.sacrilege_lust",
        "Sacrilege (Lust Tract)",
        "sin_type",
        aliases=["sacrilege"],
        description="Sacrilege insofar as sacred persons or things are violated by venereal sin in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        disambiguation_notes=[
            "Keep distinct from the religion-tract treatment of sacrilege in qq.99 and following."
        ],
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.unnatural_vice_lust",
        "Vice Against Nature",
        "sin_type",
        aliases=["vice against nature", "sin against nature"],
        description="Venereal acts from which generation cannot follow, treated as a species of lust in q.154.",
        source_scope=[154],
        parent_concept_id="concept.sin",
        related_concepts=["concept.lust"],
    ),
    concept(
        "concept.continence",
        "Continence",
        "habit",
        aliases=["continence"],
        description="Reason's resistance to vehement evil desires without the full ease of perfect temperance.",
        source_scope=[143, 155, 156],
        disambiguation_notes=[
            "Keep distinct from temperance, which perfects the appetite rather than merely resisting it."
        ],
        related_concepts=["concept.incontinence", "concept.temperance"],
    ),
    concept(
        "concept.incontinence",
        "Incontinence",
        "sin_type",
        aliases=["incontinence"],
        description="Failure to stand by reason under vehement passion, especially in pleasures of touch and secondarily in anger.",
        source_scope=[156],
        parent_concept_id="concept.sin",
        related_concepts=["concept.continence", "concept.anger", "concept.temperance"],
    ),
    concept(
        "concept.clemency",
        "Clemency",
        "virtue",
        aliases=["clemency"],
        description="The virtue that mitigates punishment under the rule of reason.",
        source_scope=[157, 159],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from meekness: clemency moderates punishment, whereas meekness moderates anger."
        ],
        related_concepts=["concept.meekness", "concept.cruelty", "concept.punishment"],
    ),
    concept(
        "concept.meekness",
        "Meekness",
        "virtue",
        aliases=["meekness"],
        description="The virtue moderating the passion of anger under reason.",
        source_scope=[143, 157, 158],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from clemency and from mere softness."
        ],
        related_concepts=["concept.anger", "concept.anger_vice", "concept.clemency"],
    ),
    concept(
        "concept.punishment",
        "Punishment",
        "process",
        aliases=["punishment"],
        description="Punishment as the matter clemency mitigates under the rule of reason.",
        source_scope=[157],
        related_concepts=["concept.clemency", "concept.cruelty"],
    ),
    concept(
        "concept.anger_vice",
        "Anger (Vice-Level)",
        "vice",
        aliases=["anger", "wrath"],
        description="Anger insofar as it becomes sinful by setting aside the order of reason.",
        source_scope=[158],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from concept.anger, which the base registry uses for the passion."
        ],
        related_concepts=["concept.anger", "concept.meekness", "concept.incontinence"],
    ),
    concept(
        "concept.cruelty",
        "Cruelty",
        "vice",
        aliases=["cruelty"],
        description="The vice opposed to clemency by exceeding due severity in punishment.",
        source_scope=[159],
        parent_concept_id="concept.vice",
        related_concepts=["concept.clemency", "concept.punishment"],
    ),
    concept(
        "concept.savagery_brutality",
        "Savagery / Brutality",
        "vice",
        aliases=["savagery", "brutality"],
        description="Bestial or savage attack distinct from cruelty properly so called in q.159 a.2.",
        source_scope=[159],
        parent_concept_id="concept.vice",
        related_concepts=["concept.cruelty"],
    ),
    concept(
        "concept.modesty_general",
        "Modesty (General)",
        "virtue",
        aliases=["modesty"],
        description="The annexed virtue moderating lesser matters where restraint is easier than in temperance proper.",
        source_scope=[143, 160],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Keep distinct from humility and the later detailed modesty sub-tract."
        ],
        related_concepts=["concept.temperance", "concept.outward_moderation"],
    ),
    concept(
        "concept.outward_moderation",
        "Outward Moderation",
        "domain",
        aliases=["outward moderation", "lesser matters requiring moderation"],
        description="The broader field of lesser matters moderated by modesty in q.160.",
        source_scope=[160],
        related_concepts=["concept.modesty_general"],
    ),
]

TRACT_CONCEPT_IDS: set[str] = {
    payload["concept_id"] for payload in TEMPERANCE_141_160_EXTRA_CONCEPTS
} | {
    "concept.cardinal_virtue",
    "concept.fear_of_lord_gift",
    "concept.temperance",
    "concept.intemperance",
    "concept.reason",
    "concept.virtue",
    "concept.vice",
    "concept.sin",
    "concept.anger",
}


for question_number, concept_ids in {
    141: [
        "concept.temperance",
        "concept.pleasures_of_touch",
        "concept.food",
        "concept.drink",
        "concept.sexual_pleasure",
        "concept.cardinal_virtue",
        "concept.fear_of_lord_gift",
    ],
    142: ["concept.intemperance", "concept.insensibility_temperance"],
    143: [
        "concept.parts_of_temperance_general",
        "concept.shamefacedness",
        "concept.honesty_temperance",
        "concept.abstinence",
        "concept.sobriety",
        "concept.chastity",
        "concept.purity_temperance",
        "concept.continence",
        "concept.meekness",
        "concept.modesty_general",
    ],
    144: ["concept.shamefacedness", "concept.disgrace"],
    145: ["concept.honesty_temperance", "concept.beauty_of_virtue"],
    146: ["concept.abstinence", "concept.food"],
    147: ["concept.fasting", "concept.abstinence", "concept.food"],
    148: ["concept.gluttony", "concept.food"],
    149: ["concept.sobriety", "concept.drink"],
    150: ["concept.drunkenness", "concept.drink"],
    151: ["concept.chastity", "concept.sexual_pleasure"],
    152: ["concept.virginity", "concept.chastity", "concept.sexual_pleasure"],
    153: ["concept.lust", "concept.sexual_pleasure"],
    154: [
        "concept.parts_of_lust",
        "concept.lust",
        "concept.simple_fornication",
        "concept.seduction_lust",
        "concept.rape_lust",
        "concept.adultery_lust",
        "concept.incest_lust",
        "concept.sacrilege_lust",
        "concept.unnatural_vice_lust",
    ],
    155: ["concept.continence", "concept.temperance", "concept.sexual_pleasure"],
    156: ["concept.incontinence", "concept.continence", "concept.anger"],
    157: ["concept.clemency", "concept.meekness", "concept.punishment", "concept.anger"],
    158: ["concept.anger", "concept.anger_vice", "concept.meekness"],
    159: ["concept.cruelty", "concept.clemency", "concept.savagery_brutality"],
    160: ["concept.modesty_general", "concept.outward_moderation", "concept.temperance"],
}.items():
    for concept_id in concept_ids:
        add_question_treatment(
            question_number,
            concept_id,
            rationale="Question heading and tract structure center the question on this concept.",
        )


for question_number, article_number, concept_id, hints in (
    (141, 1, "concept.temperance", ("temperance", "Therefore temperance is a virtue")),
    (141, 2, "concept.temperance", ("temperance", "a special virtue")),
    (141, 3, "concept.temperance", ("temperance", "desires and pleasures")),
    (141, 4, "concept.pleasures_of_touch", ("greatest pleasures", "meat and drink")),
    (141, 5, "concept.food", ("taste", "food")),
    (141, 6, "concept.reason", ("rule of the pleasurable objects", "reason")),
    (141, 7, "concept.cardinal_virtue", ("principal or cardinal virtue",)),
    (141, 8, "concept.temperance", ("temperance", "greatest of virtues")),
    (142, 1, "concept.insensibility_temperance", ("insensibility",)),
    (142, 2, "concept.intemperance", ("intemperance",)),
    (142, 3, "concept.intemperance", ("intemperance", "timidity")),
    (142, 4, "concept.intemperance", ("intemperance", "most disgraceful")),
    (143, 1, "concept.parts_of_temperance_general", ("integral, subjective, and potential",)),
    (144, 1, "concept.shamefacedness", ("shamefacedness",)),
    (144, 2, "concept.disgrace", ("disgrace",)),
    (144, 3, "concept.shamefacedness", ("ashamed",)),
    (144, 4, "concept.shamefacedness", ("are ashamed",)),
    (145, 1, "concept.honesty_temperance", ("honesty", "honorable state")),
    (145, 2, "concept.beauty_of_virtue", ("beauty", "comeliness")),
    (145, 3, "concept.honesty_temperance", ("useful", "pleasant")),
    (145, 4, "concept.honesty_temperance", ("part of temperance", "honesty")),
    (146, 1, "concept.abstinence", ("Abstinence", "regulated by reason")),
    (146, 2, "concept.abstinence", ("special virtue", "pleasures of the table")),
    (147, 1, "concept.fasting", ("fasting", "threefold purpose")),
    (147, 2, "concept.abstinence", ("fasting is an act of abstinence",)),
    (147, 3, "concept.fasting", ("matter of precept", "fasting")),
    (147, 4, "concept.fasting", ("excused", "fasting")),
    (147, 5, "concept.fasting", ("time of fasting", "fasting")),
    (147, 6, "concept.fasting", ("eat but once",)),
    (147, 7, "concept.fasting", ("hour of eating",)),
    (147, 8, "concept.food", ("meats", "abstain")),
    (148, 1, "concept.gluttony", ("gluttony", "inordinate desire")),
    (148, 2, "concept.gluttony", ("gluttony", "mortal sin")),
    (148, 3, "concept.gluttony", ("gluttony", "greatest of sins")),
    (148, 4, "concept.gluttony", ("species", "gluttony")),
    (148, 5, "concept.gluttony", ("capital sin", "gluttony")),
    (148, 6, "concept.gluttony", ("daughters", "gluttony")),
    (149, 1, "concept.sobriety", ("sobriety", "drink")),
    (149, 2, "concept.sobriety", ("special virtue", "intoxicating drink")),
    (149, 3, "concept.drink", ("use of wine",)),
    (149, 4, "concept.sobriety", ("sobriety", "especially becoming")),
    (150, 1, "concept.drunkenness", ("Drunkenness", "sin")),
    (150, 2, "concept.drunkenness", ("mortal sin", "drunkenness")),
    (150, 3, "concept.drunkenness", ("most grievous sin", "drunkenness")),
    (150, 4, "concept.drunkenness", ("excuse", "drunkenness")),
    (151, 1, "concept.chastity", ("Chastity", "is a virtue")),
    (151, 2, "concept.chastity", ("special virtue", "venereal pleasures")),
    (151, 3, "concept.chastity", ("distinct from abstinence", "chastity")),
    (151, 4, "concept.purity_temperance", ("purity", "chastity")),
    (152, 1, "concept.virginity", ("Virginity", "concupiscence")),
    (152, 2, "concept.virginity", ("lawful", "virginity")),
    (152, 3, "concept.virginity", ("virginity", "is a virtue")),
    (152, 4, "concept.virginity", ("comparison with marriage", "virginity")),
    (152, 5, "concept.virginity", ("other virtues", "virginity")),
    (153, 1, "concept.lust", ("lust", "venereal pleasures")),
    (153, 2, "concept.lust", ("copulation", "unlawful")),
    (153, 3, "concept.lust", ("lust", "mortal sin")),
    (153, 4, "concept.lust", ("capital vice", "lust")),
    (153, 5, "concept.lust", ("daughters", "lust")),
    (154, 1, "concept.parts_of_lust", ("species of lust", "vice against nature")),
    (154, 2, "concept.simple_fornication", ("simple fornication",)),
    (154, 3, "concept.simple_fornication", ("greatest of sins", "fornication")),
    (154, 4, "concept.venereal_touches_kisses", ("touches, kisses", "seduction")),
    (154, 5, "concept.nocturnal_pollution", ("nocturnal pollution",)),
    (154, 6, "concept.seduction_lust", ("seduction",)),
    (154, 7, "concept.rape_lust", ("Rape", "rape")),
    (154, 8, "concept.adultery_lust", ("Adultery", "adultery")),
    (154, 9, "concept.incest_lust", ("Incest", "incest")),
    (154, 10, "concept.sacrilege_lust", ("Sacrilege", "sacrilege")),
    (154, 11, "concept.unnatural_vice_lust", ("sin against nature", "vice against nature")),
    (154, 12, "concept.parts_of_lust", ("order of gravity", "sins")),
    (155, 1, "concept.continence", ("continence",)),
    (155, 2, "concept.continence", ("continence", "passions")),
    (155, 3, "concept.continence", ("subject", "continence")),
    (155, 4, "concept.continence", ("continence", "temperance")),
    (156, 1, "concept.incontinence", ("incontinence",)),
    (156, 2, "concept.incontinence", ("incontinence", "is a sin")),
    (156, 3, "concept.incontinence", ("incontinence", "intemperance")),
    (156, 4, "concept.anger", ("incontinence in anger",)),
    (157, 1, "concept.clemency", ("clemency", "meekness")),
    (157, 2, "concept.clemency", ("is each of them a virtue", "clemency")),
    (157, 2, "concept.meekness", ("is each of them a virtue", "meekness")),
    (157, 3, "concept.clemency", ("parts thereof", "clemency")),
    (157, 3, "concept.meekness", ("parts thereof", "meekness")),
    (157, 4, "concept.clemency", ("comparison with the other virtues", "clemency")),
    (158, 1, "concept.anger", ("anger is a passion",)),
    (158, 2, "concept.anger_vice", ("anger", "is a sin")),
    (158, 3, "concept.anger_vice", ("mortal sin", "anger")),
    (158, 4, "concept.anger_vice", ("grievous", "anger")),
    (158, 5, "concept.anger_vice", ("species", "anger")),
    (158, 6, "concept.anger_vice", ("capital vice", "anger")),
    (158, 7, "concept.anger_vice", ("daughters", "anger")),
    (158, 8, "concept.anger_vice", ("lack of anger", "vice")),
    (159, 1, "concept.cruelty", ("Cruelty", "opposed to clemency")),
    (159, 2, "concept.savagery_brutality", ("Savagery", "brutality")),
    (160, 1, "concept.modesty_general", ("modesty", "annexed to temperance")),
    (160, 2, "concept.outward_moderation", ("modesty", "remaining ordinary matters")),
):
    add_article_treatment(
        question_number,
        article_number,
        concept_id,
        rationale="The article heading and respondeo text explicitly treat this concept in the temperance tract.",
        evidence_hints=hints,
    )


for seed in (
    (141, 1, "concept.temperance", "species_of", "concept.virtue", "Temperance is explicitly concluded to be a virtue.", ("Therefore temperance is a virtue",)),
    (141, 4, "concept.temperance", "has_object", "concept.pleasures_of_touch", "Temperance is explicitly said to be about the greatest pleasures, namely pleasures of touch.", ("temperance must needs be about desires for the greatest pleasures", "temperance is properly about pleasures of touch")),
    (141, 4, "concept.temperance", "concerns_food", "concept.food", "The respondeo explicitly places meat and drink under the matter of temperance.", ("meat and drink",)),
    (141, 4, "concept.temperance", "concerns_drink", "concept.drink", "The respondeo explicitly places meat and drink under the matter of temperance.", ("meat and drink",)),
    (141, 4, "concept.temperance", "concerns_sexual_pleasure", "concept.sexual_pleasure", "The respondeo explicitly includes the union of the sexes among temperance's matter.", ("union of the sexes",)),
    (141, 6, "concept.temperance", "regulated_by", "concept.reason", "The rule of temperance is explicitly identified through the order of reason to the necessities of life.", ("good of moral virtue consists chiefly in the order of reason", "uses them according to the requirements of this life")),
    (141, 7, "concept.temperance", "species_of", "concept.cardinal_virtue", "Temperance is explicitly reckoned a principal or cardinal virtue.", ("principal or cardinal virtue", "temperance is reckoned a principal or cardinal virtue")),
    (142, 1, "concept.insensibility_temperance", "deficiency_opposed_to", "concept.temperance", "Insensibility is treated as the defect contrary to temperate use of natural pleasures.", ("insensibility", "defect")),
    (142, 2, "concept.intemperance", "excess_opposed_to", "concept.temperance", "Intemperance is the tract's excess vice opposed to temperance.", ("sin of intemperance",)),
    (143, 1, "concept.shamefacedness", "integral_part_of", "concept.temperance", "Question 143 explicitly lists shamefacedness as an integral part of temperance.", ("integral parts of temperance", "shamefacedness")),
    (143, 1, "concept.honesty_temperance", "integral_part_of", "concept.temperance", "Question 143 explicitly lists honesty as an integral part of temperance.", ("integral parts of temperance", "honesty")),
    (143, 1, "concept.abstinence", "subjective_part_of", "concept.temperance", "Question 143 explicitly assigns abstinence among temperance's subjective parts.", ("abstinence",)),
    (143, 1, "concept.sobriety", "subjective_part_of", "concept.temperance", "Question 143 explicitly assigns sobriety among temperance's subjective parts.", ("sobriety",)),
    (143, 1, "concept.chastity", "subjective_part_of", "concept.temperance", "Question 143 explicitly assigns chastity among temperance's subjective parts.", ("chastity",)),
    (143, 1, "concept.purity_temperance", "subjective_part_of", "concept.temperance", "Question 143 explicitly assigns purity among temperance's subjective parts incidental to venereal pleasure.", ("purity",)),
    (143, 1, "concept.continence", "potential_part_of", "concept.temperance", "Question 143 explicitly assigns continence among temperance's potential parts.", ("continence",)),
    (143, 1, "concept.meekness", "potential_part_of", "concept.temperance", "Question 143 explicitly assigns meekness among temperance's potential parts.", ("meekness",)),
    (143, 1, "concept.modesty_general", "potential_part_of", "concept.temperance", "Question 143 explicitly assigns modesty among temperance's potential parts.", ("modesty",)),
    (144, 2, "concept.shamefacedness", "has_object", "concept.disgrace", "Shamefacedness is explicitly said to be about disgrace.", ("disgrace", "fear is properly about an arduous evil")),
    (145, 4, "concept.honesty_temperance", "integral_part_of", "concept.temperance", "Question 145 concludes that honesty is reckoned a part of temperance.", ("part of temperance", "honesty")),
    (145, 2, "concept.honesty_temperance", "has_object", "concept.beauty_of_virtue", "Question 145 explicitly treats honesty in relation to beauty and comeliness.", ("beauty or comeliness", "beautiful")),
    (146, 1, "concept.abstinence", "species_of", "concept.virtue", "Abstinence regulated by reason is explicitly said to signify a virtue.", ("it signifies a virtue", "regulated by reason")),
    (146, 2, "concept.abstinence", "subjective_part_of", "concept.temperance", "Abstinence is treated as a special virtue under temperance with respect to food.", ("special virtue", "pleasures of the table")),
    (146, 2, "concept.abstinence", "concerns_food", "concept.food", "The special matter of abstinence is food or pleasures of the table.", ("pleasures of the table", "food")),
    (147, 2, "concept.fasting", "act_of", "concept.abstinence", "The respondeo explicitly states that fasting is an act of abstinence.", ("fasting is an act of abstinence",)),
    (147, 2, "concept.fasting", "concerns_food", "concept.food", "Fasting is explicitly concerned with food.", ("fasting is concerned with food",)),
    (148, 1, "concept.gluttony", "species_of", "concept.vice", "Gluttony is explicitly said to be a sin contrary to virtue.", ("gluttony is a sin",)),
    (148, 1, "concept.gluttony", "excess_opposed_to", "concept.abstinence", "Gluttony is the excess contrary to abstinence in food.", ("inordinate desire", "gluttony")),
    (148, 2, "concept.gluttony", "concerns_food", "concept.food", "Gluttony is explicitly considered with respect to eating and drinking as matter regulated by reason.", ("things directed to the end", "concupiscence")),
    (149, 1, "concept.sobriety", "concerns_drink", "concept.drink", "Sobriety takes its name from drink and its matter is intoxicating drink.", ("sobriety takes its name from drink",)),
    (149, 2, "concept.sobriety", "species_of", "concept.virtue", "Sobriety is explicitly argued to be a special virtue.", ("special virtue", "intoxicating drink")),
    (149, 2, "concept.sobriety", "subjective_part_of", "concept.temperance", "Sobriety is one of the subjective parts of temperance in drink.", ("special virtue", "intoxicating drink")),
    (150, 1, "concept.drunkenness", "species_of", "concept.vice", "Drunkenness as an immoderate act is treated as sin in the tract.", ("drunkenness denotes the act", "sin")),
    (150, 1, "concept.drunkenness", "concerns_drink", "concept.drink", "Drunkenness explicitly concerns much wine or intoxicating drink.", ("much wine", "drinking much wine")),
    (150, 2, "concept.drunkenness", "excess_opposed_to", "concept.sobriety", "Drunkenness is the excess opposed to sobriety in intoxicating drink.", ("sin of drunkenness", "immoderate use and concupiscence of wine")),
    (151, 1, "concept.chastity", "species_of", "concept.virtue", "The respondeo explicitly concludes that chastity is a virtue.", ("Therefore it is evident that chastity is a virtue",)),
    (151, 2, "concept.chastity", "subjective_part_of", "concept.temperance", "Chastity is treated as a special virtue under temperance with venereal matter.", ("special virtue", "venereal pleasures")),
    (151, 2, "concept.chastity", "concerns_sexual_pleasure", "concept.sexual_pleasure", "Chastity's special matter is explicitly venereal pleasure.", ("venereal pleasures",)),
    (152, 3, "concept.virginity", "species_of", "concept.virtue", "Question 152 explicitly concludes that virginity is a virtue.", ("virginity", "is a virtue")),
    (153, 1, "concept.lust", "concerns_sexual_pleasure", "concept.sexual_pleasure", "Lust is explicitly said to be concerned especially with venereal pleasures.", ("lust is especially concerned", "venereal pleasures")),
    (153, 3, "concept.lust", "species_of", "concept.vice", "Lust is treated as mortal sin contrary to reason, and so as a vice in the tract.", ("lust", "mortal sin")),
    (153, 1, "concept.lust", "excess_opposed_to", "concept.chastity", "Lust is the disordered contrary of chastity in venereal matter.", ("lust", "venereal pleasures")),
    (154, 1, "concept.simple_fornication", "species_of", "concept.lust", "Question 154 article 1 explicitly lists simple fornication among the species of lust.", ("simple fornication",)),
    (154, 1, "concept.seduction_lust", "species_of", "concept.lust", "Question 154 treats seduction among the tracted species or cases of lust.", ("seduction",)),
    (154, 1, "concept.rape_lust", "species_of", "concept.lust", "Question 154 article 1 includes rape among the species of lust by relation to another person.", ("rape",)),
    (154, 1, "concept.adultery_lust", "species_of", "concept.lust", "Question 154 article 1 includes adultery among the species of lust.", ("adultery",)),
    (154, 1, "concept.incest_lust", "species_of", "concept.lust", "Question 154 article 1 includes incest among the species of lust.", ("incest",)),
    (154, 1, "concept.sacrilege_lust", "species_of", "concept.lust", "Question 154 article 1 includes sacrilege among the species of lust.", ("sacrilege",)),
    (154, 1, "concept.unnatural_vice_lust", "species_of", "concept.lust", "Question 154 article 1 explicitly includes vice against nature among the species of lust.", ("vice against nature",)),
    (155, 4, "concept.continence", "potential_part_of", "concept.temperance", "Question 155 compares continence to temperance as imperfect to perfect, supporting its annexed status.", ("continence is compared to temperance", "imperfect to the perfect")),
    (155, 4, "concept.continence", "contrary_to", "concept.incontinence", "Continence and incontinence are treated as opposed states within this tract.", ("continence", "temperance")),
    (156, 2, "concept.incontinence", "species_of", "concept.sin", "Question 156 explicitly concludes that incontinence is a sin.", ("incontinence is a sin",)),
    (156, 2, "concept.incontinence", "contrary_to", "concept.continence", "Incontinence is tracted as the contrary failure to continence.", ("incontinence", "sin")),
    (156, 4, "concept.incontinence", "concerns_anger", "concept.anger", "Question 156 explicitly compares incontinence in anger with incontinence in desire.", ("incontinence in anger",)),
    (157, 1, "concept.clemency", "has_object", "concept.punishment", "Clemency directly moderates punishment, as the respondeo states.", ("clemency to mitigate punishment", "mitigate punishment")),
    (157, 1, "concept.meekness", "concerns_anger", "concept.anger", "Meekness explicitly mitigates the passion of anger.", ("meekness properly mitigates the passion of anger",)),
    (157, 2, "concept.clemency", "species_of", "concept.virtue", "Question 157 asks and answers that clemency is a virtue.", ("clemency", "virtue")),
    (157, 2, "concept.meekness", "species_of", "concept.virtue", "Question 157 asks and answers that meekness is a virtue.", ("meekness", "virtue")),
    (157, 3, "concept.clemency", "potential_part_of", "concept.temperance", "Question 157 explicitly reckons clemency a part annexed to temperance.", ("annexed to temperance", "parts thereof")),
    (157, 3, "concept.meekness", "potential_part_of", "concept.temperance", "Question 157 explicitly reckons meekness a part annexed to temperance.", ("annexed to temperance", "parts thereof")),
    (158, 2, "concept.anger_vice", "species_of", "concept.vice", "Question 158 treats anger as evil when it sets the order of reason aside.", ("it is evil if it set the order of reason aside",)),
    (158, 2, "concept.anger_vice", "concerns_anger", "concept.anger", "The vice-level treatment of anger explicitly presupposes the passion of anger as its matter.", ("anger is properly the name of a passion", "order of reason in regard to anger")),
    (158, 2, "concept.anger_vice", "excess_opposed_to", "concept.meekness", "Vice-level anger is the excessive contrary opposed to meekness in the tract.", ("anger", "order of reason in regard to anger")),
    (159, 1, "concept.cruelty", "contrary_to", "concept.clemency", "Question 159 explicitly treats cruelty as opposed to clemency.", ("opposed to clemency",)),
    (159, 1, "concept.cruelty", "species_of", "concept.vice", "Cruelty is treated as a vice opposed to clemency.", ("cruelty", "opposed")),
    (160, 1, "concept.modesty_general", "potential_part_of", "concept.temperance", "Question 160 explicitly calls modesty annexed to temperance as principal.", ("modesty", "annexed to temperance")),
    (160, 2, "concept.modesty_general", "concerns_outward_moderation", "concept.outward_moderation", "Question 160 explains that modesty concerns the remaining ordinary matters requiring moderation.", ("remaining ordinary matters", "modesty")),
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

add_relation(
    141,
    1,
    "concept.fear_of_lord_gift",
    "corresponding_gift_of",
    "concept.temperance",
    segment_type="ad",
    ordinal=3,
    rationale="The reply explicitly states that the gift of fear corresponds to temperance.",
    evidence_hints=(
        "Temperance also has a corresponding gift",
        "wherefore the gift of fear corresponds to temperance also",
    ),
)
