# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from ..models import PilotRelationType, PilotSupportType
from ..models.fortitude_parts_129_135 import FortitudeParts129135Cluster

FORTITUDE_PARTS_129_135_MIN_QUESTION = 129
FORTITUDE_PARTS_129_135_MAX_QUESTION = 135


def question_id(question_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}"


def article_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}"


def resp_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}.resp"


def cluster_for_question(question_number: int) -> FortitudeParts129135Cluster:
    if 129 <= question_number <= 133:
        return "honor_worthiness"
    if 134 <= question_number <= 135:
        return "expenditure_work"
    raise ValueError(f"Question outside fortitude parts 129-135 tract: {question_number}")


def cluster_name(value: FortitudeParts129135Cluster) -> str:
    return {
        "honor_worthiness": "honor / worthiness",
        "expenditure_work": "expenditure / great work",
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

FORTITUDE_PARTS_129_135_RELATION_TYPES: set[PilotRelationType] = {
    "related_to_fortitude",
    "concerns_honor",
    "concerns_worthiness",
    "concerns_great_expenditure",
    "concerns_great_work",
}

HONOR_RELATED_RELATION_TYPES: set[PilotRelationType] = {
    "concerns_honor",
    "concerns_worthiness",
}
EXPENDITURE_RELATED_RELATION_TYPES: set[PilotRelationType] = {
    "concerns_great_expenditure",
    "concerns_great_work",
}
HONOR_RELATED_CONCEPT_IDS: set[str] = {
    "concept.honor_recognition",
    "concept.worthiness",
    "concept.glory",
}
EXPENDITURE_RELATED_CONCEPT_IDS: set[str] = {
    "concept.great_expenditure",
    "concept.great_work",
}
EXCESS_OPPOSITION_RELATIONS: set[PilotRelationType] = {"excess_opposed_to"}
DEFICIENCY_OPPOSITION_RELATIONS: set[PilotRelationType] = {"deficiency_opposed_to"}


def is_honor_related_edge(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> bool:
    return (
        relation_type in HONOR_RELATED_RELATION_TYPES
        or subject_id in HONOR_RELATED_CONCEPT_IDS
        or object_id in HONOR_RELATED_CONCEPT_IDS
    )


def is_expenditure_related_edge(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> bool:
    return (
        relation_type in EXPENDITURE_RELATED_RELATION_TYPES
        or subject_id in EXPENDITURE_RELATED_CONCEPT_IDS
        or object_id in EXPENDITURE_RELATED_CONCEPT_IDS
    )


def add_relation(
    question_number: int,
    article_number: int,
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
    *,
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.94,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    RELATION_SEEDS.append(
        RelationSeed(
            source_passage_id=resp_id(question_number, article_number),
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
            source_passage_id=resp_id(question_number, article_number),
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
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.92,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    TREATMENT_SEEDS.append(
        TreatmentSeed(
            source_passage_id=resp_id(question_number, article_number),
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


FORTITUDE_PARTS_129_135_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.magnanimity",
        "Magnanimity",
        "virtue",
        aliases=["magnanimity", "greatness of soul"],
        description="The fortitude-related virtue by which a person deems himself worthy of great honors and great things in due proportion.",
        notes=[
            "Keep distinct from magnificence: magnanimity is honor- and worthiness-related rather than expenditure-related."
        ],
        source_scope=[129],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Do not reduce magnanimity to generic self-confidence or modern self-esteem."
        ],
        related_concepts=[
            "concept.fortitude",
            "concept.honor_recognition",
            "concept.worthiness",
            "concept.magnificence",
        ],
    ),
    concept(
        "concept.honor_recognition",
        "Honor as Recognition",
        "domain",
        aliases=["honor", "honors", "great honors"],
        description="Honor considered as public recognition or attestation of excellence, especially as the matter of magnanimity.",
        notes=[],
        source_scope=[129, 131, 132],
        disambiguation_notes=[
            "Keep distinct from the act of rendering honor in the owed-relation tract.",
            "Keep distinct from honor as the harmed social good in the verbal-injury questions."
        ],
        related_concepts=[
            "concept.magnanimity",
            "concept.ambition",
            "concept.glory",
        ],
    ),
    concept(
        "concept.worthiness",
        "Worthiness",
        "doctrine",
        aliases=["worthiness", "worthy of great things", "worthy things"],
        description="Proportionate worth or desert in relation to great things and great honors.",
        notes=[],
        source_scope=[129, 133],
        disambiguation_notes=[
            "Use for tract-local proportion and due worth, not for vague moral praise."
        ],
        related_concepts=["concept.magnanimity", "concept.pusillanimity"],
    ),
    concept(
        "concept.presumption_magnanimity",
        "Presumption (Against Magnanimity)",
        "vice",
        aliases=["presumption"],
        description="The vice of exceeding one's own ability by attempting what is above one's power in the magnanimity tract.",
        notes=[],
        source_scope=[130],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from the hope-tract sin of presumption treated in II-II q.21."
        ],
        related_concepts=["concept.magnanimity"],
    ),
    concept(
        "concept.ambition",
        "Ambition",
        "vice",
        aliases=["ambition"],
        description="Inordinate desire of honor opposed to well-ordered magnanimity.",
        notes=[],
        source_scope=[131],
        parent_concept_id="concept.vice",
        disambiguation_notes=[],
        related_concepts=["concept.magnanimity", "concept.honor_recognition"],
    ),
    concept(
        "concept.glory",
        "Glory",
        "domain",
        aliases=["glory"],
        description="The manifest approval or public clarity of someone's good in the sight of others.",
        notes=[],
        source_scope=[132],
        disambiguation_notes=[
            "Keep distinct from divine glory and from vainglory as the inordinate desire for glory."
        ],
        related_concepts=["concept.vainglory", "concept.honor_recognition"],
    ),
    concept(
        "concept.vainglory",
        "Vainglory",
        "vice",
        aliases=["vainglory", "vain glory"],
        description="Inordinate desire for empty glory, opposed in this tract to magnanimity's right use of honor and glory.",
        notes=[],
        source_scope=[132],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Do not collapse vainglory into generic pride without tract-specific support."
        ],
        related_concepts=["concept.glory", "concept.magnanimity"],
    ),
    concept(
        "concept.pusillanimity",
        "Pusillanimity",
        "vice",
        aliases=["pusillanimity", "faintheartedness"],
        description="The vice of shrinking from great things proportionate to one's worth.",
        notes=[],
        source_scope=[133],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Do not merge pusillanimity with humility."
        ],
        related_concepts=["concept.magnanimity", "concept.worthiness"],
    ),
    concept(
        "concept.confidence",
        "Confidence",
        "act_type",
        aliases=["confidence"],
        description="A strength of hope that the magnanimous person has in difficult good.",
        notes=[],
        source_scope=[129],
        disambiguation_notes=[],
        related_concepts=["concept.magnanimity"],
    ),
    concept(
        "concept.security_assurance",
        "Security / Assurance",
        "act_type",
        aliases=["security", "assurance"],
        description="Freedom from fear considered in relation to magnanimity and fortitude.",
        notes=[],
        source_scope=[129],
        disambiguation_notes=[
            "Keep distinct from modern information-security or merely subjective certainty."
        ],
        related_concepts=["concept.magnanimity", "concept.fortitude"],
    ),
    concept(
        "concept.goods_of_fortune",
        "Goods of Fortune",
        "domain",
        aliases=["goods of fortune"],
        description="External goods such as riches, power, and friends that can instrumentally conduce to magnanimity.",
        notes=[],
        source_scope=[129],
        disambiguation_notes=[],
        related_concepts=["concept.magnanimity"],
    ),
    concept(
        "concept.magnificence",
        "Magnificence",
        "virtue",
        aliases=["magnificence"],
        description="The fortitude-related virtue of producing great works with proportionate expenditure.",
        notes=[
            "Keep distinct from magnanimity: magnificence concerns great works and expenditure, not honor as such.",
        ],
        source_scope=[134, 135],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Do not reduce magnificence to liberality or to generic grandeur."
        ],
        related_concepts=[
            "concept.fortitude",
            "concept.great_work",
            "concept.great_expenditure",
            "concept.magnanimity",
        ],
    ),
    concept(
        "concept.great_expenditure",
        "Great Expenditure",
        "domain",
        aliases=["great expenditure", "great expense", "large expense"],
        description="The scale of spending proportionate to a great work in the magnificence tract.",
        notes=[],
        source_scope=[134, 135],
        disambiguation_notes=[],
        related_concepts=["concept.magnificence", "concept.great_work"],
    ),
    concept(
        "concept.great_work",
        "Great Work",
        "object",
        aliases=["great work", "great works"],
        description="The kind of work whose becoming execution and proportionate expense belong to magnificence.",
        notes=[],
        source_scope=[134, 135],
        disambiguation_notes=[],
        related_concepts=["concept.magnificence", "concept.great_expenditure"],
    ),
    concept(
        "concept.meanness_magnificence",
        "Meanness",
        "vice",
        aliases=["meanness", "mean man"],
        description="The vice of spending less than a great work requires, thereby failing proportion.",
        notes=[],
        source_scope=[135],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from generic pettiness or social meanness."
        ],
        related_concepts=[
            "concept.magnificence",
            "concept.great_expenditure",
            "concept.great_work",
            "concept.waste_magnificence",
        ],
    ),
    concept(
        "concept.waste_magnificence",
        "Waste (Banausia / Consumptio)",
        "vice",
        aliases=["banausia", "apyrokalia", "consumptio"],
        description="The vice of spending more than a work requires, thereby exceeding due proportion in the magnificence tract.",
        notes=[],
        source_scope=[135],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from prodigality or generic wastefulness outside the magnificence tract."
        ],
        related_concepts=[
            "concept.magnificence",
            "concept.meanness_magnificence",
            "concept.great_expenditure",
            "concept.great_work",
        ],
    ),
]

TRACT_CONCEPT_IDS: set[str] = {
    payload["concept_id"] for payload in FORTITUDE_PARTS_129_135_EXTRA_CONCEPTS
} | {
    "concept.sin",
    "concept.vice",
    "concept.fortitude",
    "concept.virtue",
}


for question_number, concept_id in (
    (129, "concept.magnanimity"),
    (129, "concept.fortitude"),
    (129, "concept.honor_recognition"),
    (129, "concept.worthiness"),
    (129, "concept.confidence"),
    (129, "concept.security_assurance"),
    (129, "concept.goods_of_fortune"),
    (130, "concept.presumption_magnanimity"),
    (130, "concept.magnanimity"),
    (131, "concept.ambition"),
    (131, "concept.magnanimity"),
    (132, "concept.vainglory"),
    (132, "concept.glory"),
    (132, "concept.magnanimity"),
    (133, "concept.pusillanimity"),
    (133, "concept.magnanimity"),
    (133, "concept.worthiness"),
    (134, "concept.fortitude"),
    (134, "concept.magnificence"),
    (134, "concept.great_work"),
    (134, "concept.great_expenditure"),
    (135, "concept.magnificence"),
    (135, "concept.meanness_magnificence"),
    (135, "concept.waste_magnificence"),
    (135, "concept.great_work"),
    (135, "concept.great_expenditure"),
):
    add_question_treatment(
        question_number,
        concept_id,
        rationale="Question heading and tract structure center this question on the concept.",
    )


for question_number, article_number, concept_id, rationale, hints in (
    (129, 1, "concept.magnanimity", "Article 1 explicitly asks and answers whether magnanimity is about honors.", ("Magnanimity", "magnanimity is about honors")),
    (129, 1, "concept.honor_recognition", "Article 1 explicitly concludes that magnanimity is about honors.", ("magnanimity is about honors", "honor is the greatest")),
    (129, 1, "concept.worthiness", "Article 1 links magnanimity to great things that are proportionate to the soul's stretching toward them.", ("stretching forth of the mind to great things",)),
    (129, 2, "concept.magnanimity", "Article 2 continues the matter of magnanimity in relation to great honors.", ("magnanimity", "great honors")),
    (129, 2, "concept.honor_recognition", "Article 2 continues the relation of magnanimity to honors.", ("great honors", "honors")),
    (129, 2, "concept.worthiness", "Article 2 treats magnanimity as proportioned to what is difficult and good in relation to the agent.", ("difficult and the good", "great honors")),
    (129, 3, "concept.magnanimity", "Article 3 explicitly asks and answers whether magnanimity is a virtue.", ("magnanimity", "is a virtue")),
    (129, 3, "concept.virtue", "Article 3 explicitly concludes that magnanimity is a virtue.", ("magnanimity", "is a virtue")),
    (129, 4, "concept.magnanimity", "Article 4 explicitly asks and answers whether magnanimity is a special virtue.", ("magnanimity", "special virtue")),
    (129, 4, "concept.honor_recognition", "Article 4 states that magnanimity establishes reason's mode in honors.", ("honors", "honor")),
    (129, 4, "concept.virtue", "Article 4 explicitly treats magnanimity as a special virtue.", ("special virtue",)),
    (129, 5, "concept.magnanimity", "Article 5 explicitly asks whether magnanimity is part of fortitude.", ("magnanimity", "part of fortitude")),
    (129, 5, "concept.fortitude", "Article 5 explicitly compares magnanimity with fortitude.", ("fortitude", "part of fortitude")),
    (129, 6, "concept.magnanimity", "Article 6 explicitly asks about magnanimity's relation to confidence.", ("magnanimity",)),
    (129, 6, "concept.confidence", "Article 6 explicitly treats confidence as belonging to magnanimity.", ("confidence", "belongs to magnanimity")),
    (129, 7, "concept.magnanimity", "Article 7 explicitly treats magnanimity in relation to security or assurance.", ("magnanimity",)),
    (129, 7, "concept.security_assurance", "Article 7 explicitly treats security or assurance.", ("security", "assurance")),
    (129, 7, "concept.fortitude", "Article 7 explicitly compares security's direct relation to fortitude with its indirect relation to magnanimity.", ("fortitude", "security belongs immediately to fortitude")),
    (129, 8, "concept.magnanimity", "Article 8 explicitly treats the relation of magnanimity to goods of fortune.", ("magnanimity",)),
    (129, 8, "concept.honor_recognition", "Article 8 restates honor as magnanimity's matter.", ("honor as its matter", "greater honor")),
    (129, 8, "concept.goods_of_fortune", "Article 8 explicitly treats goods of fortune as conducing to magnanimity.", ("goods of fortune", "conduce to magnanimity")),
    (130, 1, "concept.presumption_magnanimity", "Article 1 explicitly asks whether this presumption is a sin.", ("presumption", "is a sin")),
    (130, 1, "concept.sin", "Article 1 explicitly concludes that presumption is a sin.", ("presumption is a sin",)),
    (130, 2, "concept.presumption_magnanimity", "Article 2 explicitly asks whether presumption is opposed to magnanimity by excess.", ("presumption", "opposed to magnanimity by excess")),
    (130, 2, "concept.magnanimity", "Article 2 explicitly compares presumption with magnanimity.", ("magnanimity",)),
    (131, 1, "concept.ambition", "Article 1 explicitly asks whether ambition is a sin.", ("ambition", "always a sin")),
    (131, 1, "concept.honor_recognition", "Article 1 defines ambition through inordinate desire of honor.", ("honor", "desire of honor")),
    (131, 1, "concept.sin", "Article 1 explicitly treats ambition as sinful in its inordinate desire for honor.", ("ambition", "always a sin")),
    (131, 2, "concept.ambition", "Article 2 explicitly asks whether ambition is opposed to magnanimity.", ("ambition", "opposed to magnanimity")),
    (131, 2, "concept.magnanimity", "Article 2 explicitly compares ambition with magnanimity.", ("magnanimity",)),
    (131, 2, "concept.honor_recognition", "Article 2 reiterates ambition as inordinate love of honor in contrast to magnanimity.", ("honor", "inordinate love of honor")),
    (132, 1, "concept.vainglory", "Article 1 explicitly treats vainglory as sinful desire for empty glory.", ("vain glory", "vainglory", "empty or vain glory")),
    (132, 1, "concept.glory", "Article 1 explicitly defines glory.", ("Glory signifies", "glory properly denotes")),
    (132, 2, "concept.vainglory", "Article 2 explicitly asks whether vainglory is opposed to magnanimity.", ("vainglory", "directly opposed to magnanimity")),
    (132, 2, "concept.magnanimity", "Article 2 explicitly compares vainglory with magnanimity.", ("magnanimity",)),
    (132, 2, "concept.glory", "Article 2 explicitly treats glory as an effect of honor.", ("glory is an effect of honor",)),
    (132, 2, "concept.honor_recognition", "Article 2 explicitly states glory is an effect of honor.", ("effect of honor", "honor")),
    (132, 3, "concept.vainglory", "Article 3 explicitly asks whether vainglory is a mortal sin.", ("vainglory", "mortal sin")),
    (132, 3, "concept.sin", "Article 3 explicitly treats vainglory as sinful and asks whether it is mortal.", ("sin of vainglory", "mortal sin")),
    (132, 4, "concept.vainglory", "Article 4 explicitly asks whether vainglory is a capital vice.", ("vainglory", "capital vice")),
    (132, 4, "concept.vice", "Article 4 explicitly treats vainglory as a capital vice.", ("vainglory", "capital vice")),
    (132, 4, "concept.glory", "Article 4 again treats glory as the good most conducive to honor.", ("glory seems to be the most conducive", "honor")),
    (132, 5, "concept.vainglory", "Article 5 explicitly treats the daughters of vainglory.", ("daughters", "vainglory")),
    (132, 5, "concept.glory", "Article 5 explicitly recalls vainglory's end as the manifestation of one's own excellence.", ("manifestation of one's own excellence",)),
    (133, 1, "concept.pusillanimity", "Article 1 explicitly asks whether pusillanimity is a sin.", ("pusillanimity", "is a sin")),
    (133, 1, "concept.sin", "Article 1 explicitly concludes that pusillanimity is a sin.", ("pusillanimity is a sin",)),
    (133, 2, "concept.pusillanimity", "Article 2 explicitly asks to what virtue pusillanimity is opposed.", ("pusillanimity", "opposed to magnanimity")),
    (133, 2, "concept.magnanimity", "Article 2 explicitly compares pusillanimity with magnanimity.", ("magnanimity",)),
    (133, 2, "concept.worthiness", "Article 2 explicitly speaks of shrinking from great things of which one is worthy.", ("worthy", "great things of which one is worthy")),
    (134, 1, "concept.magnificence", "Article 1 explicitly asks whether magnificence is a virtue.", ("magnificence", "denotes a virtue")),
    (134, 1, "concept.virtue", "Article 1 explicitly concludes that magnificence denotes a virtue.", ("magnificence denotes a virtue",)),
    (134, 2, "concept.magnificence", "Article 2 explicitly asks whether magnificence is a special virtue.", ("magnificence", "special virtue")),
    (134, 2, "concept.great_work", "Article 2 explicitly treats magnificence as doing some great work.", ("great work", "something great")),
    (134, 2, "concept.virtue", "Article 2 explicitly treats magnificence as a special virtue.", ("special virtue",)),
    (134, 3, "concept.magnificence", "Article 3 explicitly treats magnificence's matter.", ("magnificence",)),
    (134, 3, "concept.great_work", "Article 3 explicitly treats the great work accomplished in becoming manner.", ("great work", "great works")),
    (134, 3, "concept.great_expenditure", "Article 3 explicitly treats proportionate great expenditure.", ("great expenditure", "spend much")),
    (134, 4, "concept.magnificence", "Article 4 explicitly asks whether magnificence is part of fortitude.", ("magnificence", "part of fortitude")),
    (134, 4, "concept.fortitude", "Article 4 explicitly compares magnificence with fortitude.", ("fortitude", "part of fortitude")),
    (134, 4, "concept.great_work", "Article 4 explicitly reiterates the arduous great work toward which magnificence tends.", ("arduous thing", "magnificence tends")),
    (135, 1, "concept.meanness_magnificence", "Article 1 explicitly asks whether meanness is a vice.", ("mean man", "meanness is a vice")),
    (135, 1, "concept.magnificence", "Article 1 explicitly compares meanness with the magnificent man.", ("magnificent man", "magnificence")),
    (135, 1, "concept.great_work", "Article 1 explicitly treats the work's greatness and result.", ("great work", "magnificent work")),
    (135, 1, "concept.great_expenditure", "Article 1 explicitly treats the due scale of expenditure.", ("expense", "spend least", "great expense")),
    (135, 1, "concept.vice", "Article 1 explicitly treats meanness as a vice.", ("meanness is a vice",)),
    (135, 2, "concept.waste_magnificence", "Article 2 explicitly names the excess vice opposed within the magnificence tract.", ("consumptio", "banausia", "apyrokalia", "vice opposed")),
    (135, 2, "concept.meanness_magnificence", "Article 2 explicitly compares waste with meanness.", ("vice of meanness", "vice opposed to it")),
    (135, 2, "concept.magnificence", "Article 2 continues the proportion required by magnificence.", ("proportion which reason requires",)),
    (135, 2, "concept.great_work", "Article 2 explicitly treats expenditure in comparison with the work.", ("comparison with the work",)),
    (135, 2, "concept.great_expenditure", "Article 2 explicitly treats disproportionate spending.", ("spending more than is proportionate", "expenditure")),
    (135, 2, "concept.vice", "Article 2 explicitly names the excess vice opposed to meanness.", ("This vice is called", "vice opposed")),
):
    add_article_treatment(
        question_number,
        article_number,
        concept_id,
        rationale=rationale,
        evidence_hints=hints,
    )


for question_number, article_number, subject_id, relation_type, object_id, support_type, confidence, rationale, hints in (
    (129, 1, "concept.magnanimity", "concerns_honor", "concept.honor_recognition", "explicit_textual", 0.98, "Article 1 explicitly concludes that magnanimity is about honors.", ("magnanimity is about honors",)),
    (129, 2, "concept.magnanimity", "concerns_honor", "concept.honor_recognition", "explicit_textual", 0.95, "Article 2 continues magnanimity's matter in relation to great honors.", ("great honors", "magnanimity")),
    (129, 3, "concept.magnanimity", "species_of", "concept.virtue", "explicit_textual", 0.97, "Article 3 explicitly says magnanimity is a virtue.", ("magnanimity", "is a virtue")),
    (129, 4, "concept.magnanimity", "species_of", "concept.virtue", "strong_textual_inference", 0.91, "Article 4 explicitly treats magnanimity as a special virtue, which strongly supports the already explicit virtue classification.", ("special virtue",)),
    (129, 4, "concept.magnanimity", "concerns_honor", "concept.honor_recognition", "explicit_textual", 0.94, "Article 4 explicitly says magnanimity establishes reason's mode in honors.", ("honors", "magnanimity")),
    (129, 5, "concept.magnanimity", "related_to_fortitude", "concept.fortitude", "explicit_textual", 0.97, "Article 5 explicitly says magnanimity is reckoned a part of fortitude as secondary to principal.", ("magnanimity is reckoned a part of fortitude", "annexed thereto as secondary to principal")),
    (129, 6, "concept.magnanimity", "has_act", "concept.confidence", "explicit_textual", 0.96, "Article 6 explicitly says confidence belongs to magnanimity.", ("confidence belongs to magnanimity",)),
    (129, 7, "concept.fortitude", "has_act", "concept.security_assurance", "explicit_textual", 0.96, "Article 7 explicitly says security belongs immediately to fortitude.", ("security belongs immediately to fortitude",)),
    (129, 8, "concept.magnanimity", "concerns_honor", "concept.honor_recognition", "explicit_textual", 0.93, "Article 8 restates that honor is magnanimity's matter.", ("honor as its matter",)),
    (130, 1, "concept.presumption_magnanimity", "species_of", "concept.sin", "explicit_textual", 0.96, "Article 1 explicitly concludes that presumption is a sin.", ("presumption is a sin",)),
    (130, 2, "concept.presumption_magnanimity", "excess_opposed_to", "concept.magnanimity", "explicit_textual", 0.98, "Article 2 explicitly says presumption is opposed to magnanimity by excess.", ("presumption is opposed to magnanimity by excess",)),
    (131, 1, "concept.ambition", "concerns_honor", "concept.honor_recognition", "explicit_textual", 0.96, "Article 1 explicitly defines ambition as inordinate desire of honor.", ("desire of honor",)),
    (131, 1, "concept.ambition", "species_of", "concept.sin", "explicit_textual", 0.95, "Article 1 explicitly treats inordinate ambition as sinful.", ("ambition", "always a sin")),
    (131, 1, "concept.ambition", "directed_to", "concept.honor_recognition", "explicit_textual", 0.95, "Article 1 explicitly defines ambition through desire of honor.", ("desire of honor",)),
    (131, 2, "concept.ambition", "concerns_honor", "concept.honor_recognition", "explicit_textual", 0.92, "Article 2 reiterates ambition as inordinate love of honor in contrast to magnanimity.", ("inordinate love of honor",)),
    (131, 2, "concept.ambition", "directed_to", "concept.honor_recognition", "explicit_textual", 0.92, "Article 2 again describes ambition as inordinate love of honor.", ("inordinate love of honor",)),
    (131, 2, "concept.ambition", "excess_opposed_to", "concept.magnanimity", "strong_textual_inference", 0.9, "Article 2 explicitly opposes ambition to magnanimity as inordinate to well ordered, which in this tract is an excess-mode opposition.", ("ambition is opposed to magnanimity", "inordinate love of honor")),
    (132, 1, "concept.vainglory", "directed_to", "concept.glory", "explicit_textual", 0.95, "Article 1 explicitly treats vainglory as desire for glory when that desire is vain.", ("vain glory", "glory")),
    (132, 2, "concept.vainglory", "excess_opposed_to", "concept.magnanimity", "strong_textual_inference", 0.91, "Article 2 explicitly says inordinate desire of glory is directly opposed to magnanimity; this tract treats that inordinate desire as excess.", ("directly opposed to magnanimity", "inordinate desire of glory")),
    (132, 2, "concept.glory", "caused_by", "concept.honor_recognition", "explicit_textual", 0.94, "Article 2 explicitly says glory is an effect of honor and praise.", ("glory is an effect of honor",)),
    (132, 2, "concept.vainglory", "directed_to", "concept.glory", "explicit_textual", 0.95, "Article 2 explicitly describes vainglory as inordinate desire of glory.", ("inordinate desire of glory",)),
    (132, 2, "concept.vainglory", "concerns_honor", "concept.honor_recognition", "strong_textual_inference", 0.89, "Article 2 connects glory to honor and then directly opposes vainglory to magnanimity, which is about honor.", ("glory is an effect of honor", "directly opposed to magnanimity")),
    (132, 4, "concept.vainglory", "species_of", "concept.vice", "explicit_textual", 0.96, "Article 4 explicitly says vainglory is a capital vice.", ("vainglory", "capital vice")),
    (132, 4, "concept.vainglory", "directed_to", "concept.glory", "strong_textual_inference", 0.88, "Article 4 explicitly keeps glory as the good most conducive to honor in explaining vainglory's capital character.", ("glory seems to be the most conducive", "honor")),
    (132, 5, "concept.vainglory", "directed_to", "concept.glory", "strong_textual_inference", 0.9, "Article 5 explicitly recalls the end of vainglory as the manifestation of one's own excellence, which is its glory-seeking object.", ("end of vainglory", "manifestation of one's own excellence")),
    (133, 1, "concept.pusillanimity", "species_of", "concept.sin", "explicit_textual", 0.95, "Article 1 explicitly concludes that pusillanimity is a sin.", ("so is pusillanimity",)),
    (133, 1, "concept.pusillanimity", "deficiency_opposed_to", "concept.magnanimity", "strong_textual_inference", 0.9, "Article 1 explicitly contrasts pusillanimity with presumption as falling short of what is proportionate to one's power, which anticipates its deficiency opposition to magnanimity.", ("fall short of what is proportionate to his power",)),
    (133, 2, "concept.pusillanimity", "deficiency_opposed_to", "concept.magnanimity", "strong_textual_inference", 0.96, "Article 2 explicitly opposes pusillanimity to magnanimity as little to great in the same subject, which in this tract is a deficiency-mode opposition.", ("pusillanimity", "opposed to magnanimity", "great and little differ")),
    (133, 2, "concept.magnanimity", "concerns_worthiness", "concept.worthiness", "strong_textual_inference", 0.9, "Article 2 contrasts the magnanimous person with shrinking from great things of which one is worthy, supporting magnanimity's relation to worthiness.", ("great things of which one is worthy",)),
    (133, 2, "concept.pusillanimity", "concerns_worthiness", "concept.worthiness", "explicit_textual", 0.95, "Article 2 explicitly says pusillanimity shrinks from great things of which one is worthy.", ("great things of which one is worthy",)),
    (134, 1, "concept.magnificence", "species_of", "concept.virtue", "explicit_textual", 0.97, "Article 1 explicitly says magnificence denotes a virtue.", ("magnificence denotes a virtue",)),
    (134, 2, "concept.magnificence", "species_of", "concept.virtue", "strong_textual_inference", 0.91, "Article 2 explicitly treats magnificence as a special virtue, which strongly supports the already explicit virtue classification.", ("special virtue",)),
    (134, 2, "concept.magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.95, "Article 2 explicitly says magnificence is the doing of something great, especially a great work in external matter.", ("great work", "doing of something great")),
    (134, 3, "concept.magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.96, "Article 3 explicitly says magnificence intends doing some great work.", ("doing some great work",)),
    (134, 3, "concept.magnificence", "concerns_great_expenditure", "concept.great_expenditure", "explicit_textual", 0.97, "Article 3 explicitly says magnificence spends much with proportionate expenditure.", ("great expenditure", "spend much")),
    (134, 4, "concept.magnificence", "related_to_fortitude", "concept.fortitude", "explicit_textual", 0.97, "Article 4 explicitly says magnificence is reckoned a part of fortitude as secondary to principal.", ("magnificence is accounted a part of fortitude",)),
    (134, 4, "concept.magnificence", "concerns_great_work", "concept.great_work", "strong_textual_inference", 0.89, "Article 4 explicitly restates the arduous thing toward which magnificence tends, which in this tract remains the great work accomplished by expenditure.", ("arduous thing to which magnificence tends",)),
    (135, 1, "concept.meanness_magnificence", "species_of", "concept.vice", "explicit_textual", 0.95, "Article 1 explicitly asks and answers whether meanness is a vice.", ("meanness is a vice",)),
    (135, 1, "concept.magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.92, "Article 1 explicitly says the magnificent man intends principally the greatness of his work.", ("magnificent man intends principally the greatness of his work",)),
    (135, 1, "concept.magnificence", "concerns_great_expenditure", "concept.great_expenditure", "explicit_textual", 0.91, "Article 1 explicitly says the magnificent man does not shirk the greatness of the expense needed for the work.", ("greatness of the expense", "magnificent man")),
    (135, 1, "concept.meanness_magnificence", "deficiency_opposed_to", "concept.magnificence", "strong_textual_inference", 0.94, "Article 1 shows that meanness spends less than the work requires and so fails the proportion magnificence keeps; this is a deficiency-mode opposition.", ("spend least", "fails to observe the proportion", "magnificent work")),
    (135, 1, "concept.meanness_magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.93, "Article 1 explicitly measures meanness by the smallness of the work relative to what ought to be done.", ("little work", "magnificent work")),
    (135, 1, "concept.meanness_magnificence", "concerns_great_expenditure", "concept.great_expenditure", "explicit_textual", 0.94, "Article 1 explicitly measures meanness by spending least and refusing the needed expense.", ("spend least", "great expense")),
    (135, 2, "concept.waste_magnificence", "species_of", "concept.vice", "explicit_textual", 0.95, "Article 2 explicitly names the vice opposed to meanness.", ("This vice is called", "vice opposed")),
    (135, 2, "concept.waste_magnificence", "contrary_to", "concept.meanness_magnificence", "explicit_textual", 0.94, "Article 2 explicitly says the vice of meanness has a vice opposed to it.", ("vice of meanness", "has a vice opposed to it")),
    (135, 2, "concept.magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.9, "Article 2 explicitly measures due proportion by the relation between expenditure and work, preserving the magnificent mean.", ("comparison with the work", "proportionate to his work")),
    (135, 2, "concept.magnificence", "concerns_great_expenditure", "concept.great_expenditure", "explicit_textual", 0.91, "Article 2 explicitly states the proportion reason requires between expenditure and work.", ("proportion which reason requires", "expenditure and work")),
    (135, 2, "concept.waste_magnificence", "excess_opposed_to", "concept.magnificence", "strong_textual_inference", 0.95, "Article 2 identifies the excess vice of spending more than is proportionate to the work, which in this tract opposes magnificence by excess.", ("spending more than is proportionate", "vice opposed")),
    (135, 2, "concept.meanness_magnificence", "deficiency_opposed_to", "concept.magnificence", "strong_textual_inference", 0.9, "Article 2 restates meanness as the failure to observe due proportion by spending less than the work is worth.", ("spend less than his work is worth", "fails to observe due proportion")),
    (135, 2, "concept.meanness_magnificence", "concerns_great_expenditure", "concept.great_expenditure", "explicit_textual", 0.93, "Article 2 explicitly defines meanness by spending less than the work is worth.", ("spend less than his work is worth",)),
    (135, 2, "concept.meanness_magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.9, "Article 2 explicitly measures meanness by the work to which expenditure ought to be proportionate.", ("comparison with the work", "his work is worth")),
    (135, 2, "concept.waste_magnificence", "concerns_great_expenditure", "concept.great_expenditure", "explicit_textual", 0.94, "Article 2 explicitly defines waste by spending more than is proportionate.", ("spending more than is proportionate",)),
    (135, 2, "concept.waste_magnificence", "concerns_great_work", "concept.great_work", "explicit_textual", 0.9, "Article 2 explicitly measures excess expenditure in comparison with the work.", ("comparison with the work", "proportionate to his work")),
):
    add_relation(
        question_number,
        article_number,
        subject_id,
        cast(PilotRelationType, relation_type),
        object_id,
        support_type=cast(PilotSupportType, support_type),
        confidence=confidence,
        rationale=rationale,
        evidence_hints=hints,
    )
