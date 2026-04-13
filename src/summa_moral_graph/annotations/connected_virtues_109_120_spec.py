# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import (
    PilotConnectedVirtuesCluster,
    PilotRelationType,
    PilotSupportType,
)

CONNECTED_VIRTUES_109_120_MIN_QUESTION = 109
CONNECTED_VIRTUES_109_120_MAX_QUESTION = 120


def question_id(question_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}"


def article_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}"


def resp_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}.resp"


def cluster_for_question(question_number: int) -> PilotConnectedVirtuesCluster:
    if 109 <= question_number <= 113:
        return "self_presentation"
    if 114 <= question_number <= 116:
        return "social_interaction"
    if 117 <= question_number <= 119:
        return "external_goods"
    if question_number == 120:
        return "legal_equity"
    raise ValueError(f"Question outside connected virtues 109-120 tract: {question_number}")


def cluster_name(value: PilotConnectedVirtuesCluster) -> str:
    return {
        "self_presentation": "self-presentation",
        "social_interaction": "social interaction",
        "external_goods": "external goods",
        "legal_equity": "legal-equity / epikeia",
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
    connected_virtues_cluster: PilotConnectedVirtuesCluster
    evidence_hints: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TreatmentSeed:
    source_passage_id: str
    subject_id: str
    concept_id: str
    support_type: PilotSupportType
    confidence: float
    rationale: str
    connected_virtues_cluster: PilotConnectedVirtuesCluster
    evidence_hints: tuple[str, ...] = field(default_factory=tuple)


RELATION_SEEDS: list[RelationSeed] = []
TREATMENT_SEEDS: list[TreatmentSeed] = []


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
            connected_virtues_cluster=cluster_for_question(question_number),
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
            connected_virtues_cluster=cluster_for_question(question_number),
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
            connected_virtues_cluster=cluster_for_question(question_number),
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


CONNECTED_VIRTUES_109_120_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.truth_self_presentation",
        "Truth",
        "virtue",
        aliases=["truth", "truthfulness"],
        description="The annexed virtue by which a person manifests himself as he is in words and deeds.",
        notes=[
            "This tract-local truth is truthful self-manifestation, not First Truth or theological truth in the faith tract."
        ],
        source_scope=[109],
        disambiguation_notes=[
            "Do not merge this with truth as adequation of intellect and thing or with First Truth."
        ],
        related_concepts=[
            "concept.justice",
            "concept.self_presentation",
            "concept.lying",
        ],
    ),
    concept(
        "concept.lying",
        "Lying",
        "wrong_act",
        aliases=["lying", "lie"],
        description="The sinful false signification of what is in one's mind.",
        source_scope=[110],
        related_concepts=[
            "concept.truth_self_presentation",
            "concept.boasting",
            "concept.irony",
        ],
    ),
    concept(
        "concept.dissimulation",
        "Dissimulation",
        "wrong_act",
        aliases=["dissimulation"],
        description="A lie told by outward deeds or signs through showing oneself otherwise than one is.",
        source_scope=[111],
        related_concepts=[
            "concept.truth_self_presentation",
            "concept.self_presentation",
            "concept.hypocrisy",
            "concept.lying",
        ],
    ),
    concept(
        "concept.hypocrisy",
        "Hypocrisy",
        "wrong_act",
        aliases=["hypocrisy", "hypocrite"],
        description="A species of dissimulation in which a person simulates the character of a just man without being such in reality.",
        source_scope=[111],
        parent_concept_id="concept.dissimulation",
        related_concepts=[
            "concept.dissimulation",
            "concept.truth_self_presentation",
        ],
    ),
    concept(
        "concept.boasting",
        "Boasting",
        "wrong_act",
        aliases=["boasting", "jactantia"],
        description="False self-exaltation by speaking above what one truly is.",
        source_scope=[112],
        related_concepts=[
            "concept.lying",
            "concept.truth_self_presentation",
            "concept.self_presentation",
        ],
    ),
    concept(
        "concept.irony",
        "Irony",
        "wrong_act",
        aliases=["irony"],
        description="False self-belittling by denying or diminishing goods one truly has.",
        notes=["This is the tract's vice of understatement, not modern rhetorical irony."],
        source_scope=[113],
        disambiguation_notes=[
            "Do not read this as generic literary irony; Aquinas is discussing a false mode of self-presentation."
        ],
        related_concepts=[
            "concept.lying",
            "concept.truth_self_presentation",
            "concept.boasting",
        ],
    ),
    concept(
        "concept.self_presentation",
        "Self-Presentation",
        "domain",
        aliases=[
            "self-presentation",
            "outward signs",
            "words or deeds",
            "manifesting oneself",
        ],
        description="The domain of manifesting oneself truthfully or falsely by words or deeds.",
        source_scope=[109, 110, 111, 112, 113],
        related_concepts=[
            "concept.truth_self_presentation",
            "concept.lying",
            "concept.dissimulation",
            "concept.boasting",
            "concept.irony",
        ],
    ),
    concept(
        "concept.friendliness_affability",
        "Friendliness / Affability",
        "virtue",
        aliases=["friendliness", "affability", "amicable friendliness"],
        description="The virtue maintaining becoming conduct in ordinary relations by pleasing others appropriately.",
        source_scope=[114],
        disambiguation_notes=[
            "Do not merge this tract-local social virtue into charity."
        ],
        related_concepts=[
            "concept.justice",
            "concept.social_interaction",
            "concept.flattery",
            "concept.quarreling",
        ],
    ),
    concept(
        "concept.flattery",
        "Flattery",
        "wrong_act",
        aliases=["flattery", "adulation", "complaisance"],
        description="Excessive pleasing of others in ordinary interaction beyond the mode of virtue.",
        source_scope=[115],
        related_concepts=[
            "concept.friendliness_affability",
            "concept.social_interaction",
        ],
    ),
    concept(
        "concept.quarreling",
        "Quarreling",
        "wrong_act",
        aliases=["quarreling", "peevishness"],
        description="Contradictory disagreeableness in ordinary social interaction, opposed to affability.",
        source_scope=[116],
        related_concepts=[
            "concept.friendliness_affability",
            "concept.social_interaction",
        ],
    ),
    concept(
        "concept.social_interaction",
        "Social Interaction",
        "domain",
        aliases=[
            "social interaction",
            "ordinary intercourse",
            "mutual relations",
            "ordinary behavior towards fellows",
        ],
        description="The domain of ordinary human dealings in words and deeds among those with whom one dwells.",
        source_scope=[114, 115, 116],
        related_concepts=[
            "concept.friendliness_affability",
            "concept.flattery",
            "concept.quarreling",
        ],
    ),
    concept(
        "concept.liberality",
        "Liberality",
        "virtue",
        aliases=["liberality", "open-handedness"],
        description="The virtue moderating the use of money or external goods, especially in giving.",
        source_scope=[117],
        disambiguation_notes=[
            "Do not merge liberality into almsgiving, mercy, or generic justice."
        ],
        related_concepts=[
            "concept.justice",
            "concept.external_goods",
            "concept.giving",
            "concept.covetousness",
            "concept.prodigality",
        ],
    ),
    concept(
        "concept.covetousness",
        "Covetousness",
        "vice",
        aliases=["covetousness", "avarice"],
        description="Immoderate love of having possessions or riches.",
        source_scope=[118],
        disambiguation_notes=[
            "Keep this tract-local vice narrower than every possible desire for money across the corpus."
        ],
        related_concepts=[
            "concept.liberality",
            "concept.external_goods",
            "concept.retaining",
        ],
    ),
    concept(
        "concept.prodigality",
        "Prodigality",
        "vice",
        aliases=["prodigality", "wastefulness"],
        description="Excessive giving and deficient retaining or acquiring with respect to riches.",
        source_scope=[119],
        related_concepts=[
            "concept.liberality",
            "concept.covetousness",
            "concept.external_goods",
            "concept.giving",
        ],
    ),
    concept(
        "concept.external_goods",
        "External Goods",
        "domain",
        aliases=["external goods", "money", "riches", "possessions"],
        description="The domain of money and possessions that can be used, given, acquired, or retained.",
        source_scope=[117, 118, 119],
        related_concepts=[
            "concept.liberality",
            "concept.covetousness",
            "concept.prodigality",
            "concept.giving",
            "concept.retaining",
        ],
    ),
    concept(
        "concept.giving",
        "Giving",
        "act_type",
        aliases=["giving", "parting with money"],
        description="The act of parting with money or possessions to another.",
        source_scope=[117, 119],
        related_concepts=[
            "concept.liberality",
            "concept.prodigality",
            "concept.external_goods",
        ],
    ),
    concept(
        "concept.retaining",
        "Retaining",
        "act_type",
        aliases=["retaining", "keeping", "keeping riches"],
        description="The act of keeping or holding possessions instead of parting with them.",
        source_scope=[118, 119],
        related_concepts=[
            "concept.covetousness",
            "concept.external_goods",
        ],
    ),
    concept(
        "concept.epikeia",
        "Epikeia / Equity",
        "virtue",
        aliases=["epikeia", "equity"],
        description="The virtue correcting merely literal legal application in order to preserve justice and the common good in singular cases.",
        source_scope=[120],
        disambiguation_notes=[
            "Do not reduce epikeia to generic fairness or to justice in an undifferentiated sense."
        ],
        related_concepts=[
            "concept.justice",
            "concept.law",
            "concept.legal_letter",
            "concept.intent_of_law",
            "concept.common_good",
        ],
    ),
    concept(
        "concept.legal_letter",
        "Letter of the Law",
        "law",
        aliases=["letter of the law", "literal law"],
        description="The merely literal application of a law in a case where following the words alone would frustrate justice.",
        source_scope=[120],
        related_concepts=[
            "concept.law",
            "concept.epikeia",
            "concept.intent_of_law",
        ],
    ),
    concept(
        "concept.intent_of_law",
        "Intent of Law",
        "doctrine",
        aliases=["intent of law", "what the law has in view", "legislator's intent"],
        description="What the law seeks in view in ordering cases toward justice and the common good.",
        source_scope=[120],
        related_concepts=[
            "concept.law",
            "concept.common_good",
            "concept.epikeia",
        ],
    ),
]


TRACT_CONCEPT_IDS = {
    payload["concept_id"] for payload in CONNECTED_VIRTUES_109_120_EXTRA_CONCEPTS
} | {
    "concept.justice",
    "concept.law",
    "concept.common_good",
}

CONNECTED_VIRTUES_RELATION_TYPES = {
    "concerns_self_presentation",
    "concerns_social_interaction",
    "concerns_external_goods",
    "corrects_legal_letter",
    "preserves_intent_of_law",
}


def is_clustered_relation(edge: dict[str, Any]) -> bool:
    return bool(edge.get("connected_virtues_cluster"))


add_relation(
    109,
    2,
    "concept.truth_self_presentation",
    "concerns_self_presentation",
    "concept.self_presentation",
    rationale="The virtue of truth perfects a person in duly ordering outward words and deeds as signs of what one is.",
    evidence_hints=("words or deeds", "sign to thing signified"),
)
add_relation(
    109,
    3,
    "concept.truth_self_presentation",
    "annexed_to",
    "concept.justice",
    rationale="Aquinas explicitly concludes that truth is annexed to justice as a secondary virtue.",
    evidence_hints=("truth is a part of justice", "being annexed thereto"),
)

add_relation(
    110,
    2,
    "concept.lying",
    "contrary_to",
    "concept.truth_self_presentation",
    rationale="Lying as such is opposed to truth.",
    evidence_hints=("lying as such is opposed to truth",),
)
add_relation(
    110,
    2,
    "concept.truth_self_presentation",
    "opposed_by",
    "concept.lying",
    rationale="The tract on lying treats lying as the contrary vice opposed to the annexed virtue of truth.",
    evidence_hints=("lying as such is opposed to truth",),
)
add_relation(
    110,
    2,
    "concept.boasting",
    "species_of",
    "concept.lying",
    rationale="Boasting is explicitly identified as the kind of lie that goes beyond the truth.",
    evidence_hints=("boasting",),
)
add_relation(
    110,
    2,
    "concept.irony",
    "species_of",
    "concept.lying",
    rationale="Irony is explicitly identified as the kind of lie that stops short of the truth.",
    evidence_hints=("irony",),
)

add_relation(
    111,
    1,
    "concept.dissimulation",
    "species_of",
    "concept.lying",
    rationale="Aquinas explicitly says that dissimulation is properly a lie told by signs of outward deeds.",
    evidence_hints=("dissimulation is properly a lie",),
)
add_relation(
    111,
    1,
    "concept.dissimulation",
    "contrary_to",
    "concept.truth_self_presentation",
    rationale="Dissimulation is directly contrary to the virtue of truth because it signifies outwardly what one is not.",
    evidence_hints=("it is contrary to truth",),
)
add_relation(
    111,
    1,
    "concept.dissimulation",
    "concerns_self_presentation",
    "concept.self_presentation",
    rationale="Dissimulation concerns showing oneself outwardly otherwise than one is by words or deeds.",
    evidence_hints=("show oneself outwardly", "outward signs"),
)
add_relation(
    111,
    3,
    "concept.truth_self_presentation",
    "opposed_by",
    "concept.dissimulation",
    rationale="Aquinas treats dissimulation as directly contrary to the tract's virtue of truth.",
    evidence_hints=("directly opposed to truth",),
)
add_relation(
    111,
    2,
    "concept.hypocrisy",
    "species_of",
    "concept.dissimulation",
    rationale="Aquinas concludes that hypocrisy is a form of dissimulation, though not every kind of dissimulation.",
    evidence_hints=("that hypocrisy is dissimulation",),
)
add_relation(
    111,
    3,
    "concept.hypocrisy",
    "contrary_to",
    "concept.truth_self_presentation",
    rationale="Hypocrisy is directly opposed to truth because it simulates a character that is not one's own.",
    evidence_hints=("it is directly opposed to truth",),
)
add_relation(
    111,
    3,
    "concept.hypocrisy",
    "concerns_self_presentation",
    "concept.self_presentation",
    rationale="Hypocrisy concerns presenting oneself as just without being so in reality.",
    evidence_hints=("simulates a character which is not his",),
)
add_relation(
    111,
    3,
    "concept.truth_self_presentation",
    "opposed_by",
    "concept.hypocrisy",
    rationale="The tract explicitly treats hypocrisy as a directly opposed false self-presentation.",
    evidence_hints=("it is directly opposed to truth",),
)

add_relation(
    112,
    1,
    "concept.boasting",
    "contrary_to",
    "concept.truth_self_presentation",
    rationale="Boasting is opposed to truth by way of excess.",
    evidence_hints=("opposed to truth by way of excess",),
)
add_relation(
    112,
    1,
    "concept.truth_self_presentation",
    "opposed_by",
    "concept.boasting",
    rationale="The truth tract treats boasting as an excessive contrary to truthful self-manifestation.",
    evidence_hints=("opposed to truth by way of excess",),
)
add_relation(
    112,
    1,
    "concept.boasting",
    "concerns_self_presentation",
    "concept.self_presentation",
    rationale="Boasting concerns speaking of oneself above what one truly is.",
    evidence_hints=("talk of oneself above oneself",),
)

add_relation(
    113,
    1,
    "concept.irony",
    "contrary_to",
    "concept.truth_self_presentation",
    rationale="When a person belittles himself by forsaking the truth, that act pertains to irony and is sinful.",
    evidence_hints=("this pertains to irony", "forsaking the truth"),
)
add_relation(
    113,
    1,
    "concept.truth_self_presentation",
    "opposed_by",
    "concept.irony",
    rationale="The tract treats irony as a deficient contrary to truthful self-manifestation.",
    evidence_hints=("this pertains to irony",),
)
add_relation(
    113,
    1,
    "concept.irony",
    "concerns_self_presentation",
    "concept.self_presentation",
    rationale="Irony concerns falsely belittling oneself by denying goods one truly has.",
    evidence_hints=("belittle oneself",),
)
add_relation(
    113,
    2,
    "concept.irony",
    "contrary_to",
    "concept.boasting",
    rationale="Aquinas compares irony and boasting as opposite lies about the same matter affecting the person.",
    evidence_hints=("irony and boasting lie about the same matter",),
)

add_relation(
    114,
    1,
    "concept.friendliness_affability",
    "concerns_social_interaction",
    "concept.social_interaction",
    rationale="Friendliness is the virtue maintaining becoming order in mutual relations of words and deeds.",
    evidence_hints=("mutual relations with one another", "this virtue is called friendliness"),
)
add_relation(
    114,
    2,
    "concept.friendliness_affability",
    "annexed_to",
    "concept.justice",
    rationale="Aquinas explicitly concludes that friendliness or affability is annexed to justice.",
    evidence_hints=("This virtue is a part of justice", "being annexed to it"),
)

add_relation(
    115,
    1,
    "concept.flattery",
    "contrary_to",
    "concept.friendliness_affability",
    rationale="Flattery exceeds the mode of pleasing that belongs to affability.",
    evidence_hints=("would exceed the mode of pleasing",),
)
add_relation(
    115,
    1,
    "concept.friendliness_affability",
    "opposed_by",
    "concept.flattery",
    rationale="The tract treats flattery as the excessive contrary to affability.",
    evidence_hints=("would exceed the mode of pleasing",),
)
add_relation(
    115,
    1,
    "concept.flattery",
    "concerns_social_interaction",
    "concept.social_interaction",
    rationale="Flattery is defined within ordinary behavior toward one's fellows.",
    evidence_hints=("ordinary behavior towards their fellows",),
)

add_relation(
    116,
    1,
    "concept.quarreling",
    "contrary_to",
    "concept.friendliness_affability",
    rationale="Quarreling is opposed to the aforesaid friendship or affability.",
    evidence_hints=("quarreling, which is opposed to the aforesaid friendship or affability",),
)
add_relation(
    116,
    1,
    "concept.friendliness_affability",
    "opposed_by",
    "concept.quarreling",
    rationale="Affability is opposed by peevish or quarrelsome disagreeableness.",
    evidence_hints=("quarreling, which is opposed to the aforesaid friendship or affability",),
)
add_relation(
    116,
    1,
    "concept.quarreling",
    "concerns_social_interaction",
    "concept.social_interaction",
    rationale="Quarreling concerns disagreeable contradiction among those among whom we dwell.",
    evidence_hints=("those among whom we dwell",),
)

add_relation(
    117,
    2,
    "concept.liberality",
    "concerns_external_goods",
    "concept.external_goods",
    rationale="Liberality has money and possessions as its proper matter.",
    evidence_hints=("the proper matter of liberality is money",),
)
add_relation(
    117,
    4,
    "concept.liberality",
    "has_act",
    "concept.giving",
    rationale="Aquinas explicitly says that the liberal man is praised chiefly for giving.",
    evidence_hints=("a liberal man is praised chiefly for giving",),
)
add_relation(
    117,
    5,
    "concept.liberality",
    "annexed_to",
    "concept.justice",
    support_type="strong_textual_inference",
    confidence=0.89,
    rationale="Aquinas states that liberality is reckoned by some as annexed to justice because it is directed to another and concerns external things.",
    evidence_hints=("being annexed thereto as to a principal virtue",),
)

add_relation(
    118,
    3,
    "concept.covetousness",
    "contrary_to",
    "concept.liberality",
    rationale="In its interior affection for riches, covetousness is opposed to liberality.",
    evidence_hints=("covetousness is opposed to liberality",),
)
add_relation(
    118,
    3,
    "concept.liberality",
    "opposed_by",
    "concept.covetousness",
    rationale="Liberality is explicitly treated as the virtue opposed by covetousness in its interior appetite for riches.",
    evidence_hints=("covetousness is opposed to liberality",),
)
add_relation(
    118,
    2,
    "concept.covetousness",
    "concerns_external_goods",
    "concept.external_goods",
    rationale="Covetousness is an immoderate love of possessions or riches, which are external goods.",
    evidence_hints=("riches , as such, come under the head of useful good",),
)
add_relation(
    118,
    3,
    "concept.covetousness",
    "has_act",
    "concept.retaining",
    rationale="Aquinas defines one form of covetousness through keeping or retaining riches beyond due measure.",
    evidence_hints=("retaining another's property",),
)

add_relation(
    119,
    1,
    "concept.prodigality",
    "contrary_to",
    "concept.covetousness",
    rationale="Aquinas explicitly concludes that prodigality is opposed to covetousness.",
    evidence_hints=("prodigality is opposed to covetousness",),
)
add_relation(
    119,
    2,
    "concept.prodigality",
    "contrary_to",
    "concept.liberality",
    support_type="strong_textual_inference",
    confidence=0.9,
    rationale="Prodigality destroys the mean of virtue by excess and deficiency and is therefore opposed to liberality.",
    evidence_hints=("destroys the mean of virtue",),
)
add_relation(
    119,
    2,
    "concept.liberality",
    "opposed_by",
    "concept.prodigality",
    support_type="strong_textual_inference",
    confidence=0.9,
    rationale="The vice of prodigality is treated as the excessive contrary against liberality's mean.",
    evidence_hints=("destroys the mean of virtue",),
)
add_relation(
    119,
    1,
    "concept.prodigality",
    "concerns_external_goods",
    "concept.external_goods",
    rationale="Prodigality concerns affection for riches and external actions of giving, retaining, and acquiring.",
    evidence_hints=("affection for riches",),
)

add_relation(
    120,
    2,
    "concept.epikeia",
    "species_of",
    "concept.justice",
    rationale="Aquinas explicitly says that epikeia is a kind of justice and a subjective part of justice.",
    evidence_hints=("a kind of justice",),
)
add_relation(
    120,
    1,
    "concept.epikeia",
    "corrects_legal_letter",
    "concept.legal_letter",
    rationale="Epikeia sets aside the letter of the law where literal application would frustrate justice.",
    evidence_hints=("set aside the letter of the law",),
)
add_relation(
    120,
    1,
    "concept.epikeia",
    "preserves_intent_of_law",
    "concept.intent_of_law",
    rationale="Epikeia preserves what the law has in view when singular cases fall outside what commonly happens.",
    evidence_hints=("which the law has in view",),
)
add_relation(
    120,
    1,
    "concept.epikeia",
    "directed_to",
    "concept.common_good",
    rationale="Aquinas explicitly says epikeia follows justice and the common good rather than the bare letter in exceptional cases.",
    evidence_hints=("the common good",),
)


QUESTION_TREATMENT_MAP: dict[int, tuple[str, ...]] = {
    109: ("concept.truth_self_presentation", "concept.self_presentation", "concept.justice"),
    110: (
        "concept.lying",
        "concept.boasting",
        "concept.irony",
        "concept.truth_self_presentation",
        "concept.self_presentation",
    ),
    111: (
        "concept.dissimulation",
        "concept.hypocrisy",
        "concept.self_presentation",
        "concept.truth_self_presentation",
    ),
    112: ("concept.boasting", "concept.self_presentation", "concept.truth_self_presentation"),
    113: (
        "concept.irony",
        "concept.self_presentation",
        "concept.truth_self_presentation",
        "concept.lying",
    ),
    114: ("concept.friendliness_affability", "concept.social_interaction", "concept.justice"),
    115: ("concept.flattery", "concept.social_interaction", "concept.friendliness_affability"),
    116: ("concept.quarreling", "concept.social_interaction", "concept.friendliness_affability"),
    117: ("concept.liberality", "concept.external_goods", "concept.giving", "concept.justice"),
    118: (
        "concept.covetousness",
        "concept.external_goods",
        "concept.retaining",
        "concept.liberality",
    ),
    119: ("concept.prodigality", "concept.external_goods", "concept.liberality", "concept.giving"),
    120: ("concept.epikeia", "concept.legal_letter", "concept.intent_of_law", "concept.common_good"),
}

ARTICLE_TREATMENT_MAP: dict[tuple[int, int], tuple[str, ...]] = {
    (109, 1): ("concept.truth_self_presentation",),
    (109, 2): ("concept.truth_self_presentation", "concept.self_presentation"),
    (109, 3): ("concept.truth_self_presentation", "concept.justice", "concept.self_presentation"),
    (109, 4): ("concept.truth_self_presentation", "concept.irony", "concept.boasting"),
    (110, 1): ("concept.lying", "concept.truth_self_presentation"),
    (110, 2): ("concept.lying", "concept.boasting", "concept.irony"),
    (110, 3): ("concept.lying", "concept.truth_self_presentation"),
    (110, 4): ("concept.lying", "concept.truth_self_presentation"),
    (111, 1): ("concept.dissimulation", "concept.truth_self_presentation"),
    (111, 2): ("concept.hypocrisy", "concept.dissimulation"),
    (111, 3): ("concept.hypocrisy", "concept.dissimulation", "concept.truth_self_presentation"),
    (111, 4): ("concept.hypocrisy", "concept.truth_self_presentation"),
    (112, 1): ("concept.boasting", "concept.truth_self_presentation", "concept.self_presentation"),
    (112, 2): ("concept.boasting", "concept.lying"),
    (113, 1): ("concept.irony", "concept.truth_self_presentation", "concept.self_presentation"),
    (113, 2): ("concept.irony", "concept.boasting", "concept.lying"),
    (114, 1): ("concept.friendliness_affability", "concept.social_interaction"),
    (114, 2): ("concept.friendliness_affability", "concept.justice", "concept.social_interaction"),
    (115, 1): ("concept.flattery", "concept.friendliness_affability", "concept.social_interaction"),
    (115, 2): ("concept.flattery",),
    (116, 1): ("concept.quarreling", "concept.friendliness_affability", "concept.social_interaction"),
    (116, 2): ("concept.quarreling", "concept.flattery", "concept.friendliness_affability"),
    (117, 1): ("concept.liberality", "concept.external_goods"),
    (117, 2): ("concept.liberality", "concept.external_goods"),
    (117, 3): ("concept.liberality", "concept.external_goods", "concept.giving"),
    (117, 4): ("concept.liberality", "concept.giving"),
    (117, 5): ("concept.liberality", "concept.justice"),
    (117, 6): ("concept.liberality", "concept.external_goods"),
    (118, 1): ("concept.covetousness", "concept.external_goods"),
    (118, 2): ("concept.covetousness", "concept.external_goods"),
    (118, 3): ("concept.covetousness", "concept.liberality", "concept.retaining"),
    (118, 4): ("concept.covetousness",),
    (118, 5): ("concept.covetousness",),
    (118, 6): ("concept.covetousness",),
    (118, 7): ("concept.covetousness",),
    (118, 8): ("concept.covetousness",),
    (119, 1): ("concept.prodigality", "concept.covetousness", "concept.external_goods"),
    (119, 2): ("concept.prodigality", "concept.liberality", "concept.external_goods"),
    (119, 3): ("concept.prodigality", "concept.covetousness", "concept.liberality"),
    (120, 1): ("concept.epikeia", "concept.legal_letter", "concept.common_good", "concept.intent_of_law"),
    (120, 2): ("concept.epikeia", "concept.justice", "concept.law"),
}

for question_number, concept_ids in QUESTION_TREATMENT_MAP.items():
    for concept_id in concept_ids:
        add_question_treatment(
            question_number,
            concept_id,
            rationale=(
                f"Question {question_number} is structurally centered on "
                f"{concept_id.split('concept.', 1)[1].replace('_', ' ')} within the connected virtues tract."
            ),
        )

for (question_number, article_number), concept_ids in ARTICLE_TREATMENT_MAP.items():
    for concept_id in concept_ids:
        add_article_treatment(
            question_number,
            article_number,
            concept_id,
            rationale=(
                f"Article {article_number} of question {question_number} materially treats "
                f"{concept_id.split('concept.', 1)[1].replace('_', ' ')} in its respondeo."
            ),
        )
