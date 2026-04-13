# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import PilotRelationType, PilotSupportType

RELIGION_TRACT_MIN_QUESTION = 80
RELIGION_TRACT_MAX_QUESTION = 100


def question_id(question_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}"


def article_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}"


def resp_id(question_number: int, article_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}.a{article_number:03d}.resp"


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


RELIGION_TRACT_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.religion",
        "Religion",
        "virtue",
        aliases=["religion", "worship of God"],
        description="The virtue annexed to justice that renders due worship to God.",
        notes=[
            "Treat religion as the positive virtue of divine worship, not as generic creed or confession."
        ],
        source_scope=[80, 81],
        related_concepts=["concept.justice", "concept.devotion", "concept.prayer"],
    ),
    concept(
        "concept.devotion",
        "Devotion",
        "act_type",
        aliases=["devotion"],
        description="The ready will to do what pertains to the worship and service of God.",
        source_scope=[82],
        related_concepts=["concept.religion", "concept.prayer"],
    ),
    concept(
        "concept.prayer",
        "Prayer",
        "act_type",
        aliases=["prayer"],
        description="The act whereby a rational creature asks or petitions God.",
        source_scope=[83],
        related_concepts=["concept.religion", "concept.devotion"],
    ),
    concept(
        "concept.adoration",
        "Adoration",
        "act_type",
        aliases=["adoration", "bodily adoration"],
        description="An act of reverence offered to God, inwardly and outwardly.",
        source_scope=[84],
        related_concepts=["concept.religion", "concept.divine_worship"],
    ),
    concept(
        "concept.sacrifice",
        "Sacrifice",
        "act_type",
        aliases=["sacrifice"],
        description="An offering made to God in sign of man's subjection and honor.",
        source_scope=[85],
        related_concepts=["concept.religion", "concept.divine_worship"],
    ),
    concept(
        "concept.oblation",
        "Oblation",
        "act_type",
        aliases=["oblation", "offering"],
        description="A thing offered for divine worship, whether or not it is destroyed as sacrifice.",
        source_scope=[86],
        related_concepts=["concept.religion", "concept.first_fruits"],
    ),
    concept(
        "concept.first_fruits",
        "First-Fruits",
        "act_type",
        aliases=["first-fruits", "first fruits"],
        description="A special oblation offered to God in acknowledgment of divine favor.",
        source_scope=[86],
        parent_concept_id="concept.oblation",
        related_concepts=["concept.oblation", "concept.divine_worship"],
    ),
    concept(
        "concept.tithes",
        "Tithes",
        "act_type",
        aliases=["tithes", "paying tithes"],
        description="The giving of a fixed proportion for the support of ministers of divine worship.",
        source_scope=[87],
        related_concepts=["concept.religion", "concept.divine_worship"],
    ),
    concept(
        "concept.vow",
        "Vow",
        "act_type",
        aliases=["vow"],
        description="A promise made to God about something acceptable to Him.",
        source_scope=[88],
        related_concepts=["concept.religion", "concept.promise_to_god"],
    ),
    concept(
        "concept.oath",
        "Oath",
        "act_type",
        aliases=["oath"],
        description="The calling of God to witness in confirmation of what one says.",
        source_scope=[89],
        related_concepts=["concept.religion", "concept.divine_name", "concept.sworn_assertion"],
    ),
    concept(
        "concept.adjuration",
        "Adjuration",
        "act_type",
        aliases=["adjuration"],
        description="A reverential calling on the divine name or a holy thing in order to obtain or command something.",
        source_scope=[90],
        related_concepts=["concept.divine_name", "concept.sacred_thing"],
    ),
    concept(
        "concept.praise_of_god",
        "Praise of God",
        "act_type",
        aliases=["praise of God", "divine praise", "praise"],
        description="Vocal praise directed to God in order to stir devotion and reverence.",
        source_scope=[91],
        related_concepts=["concept.religion", "concept.divine_worship"],
    ),
    concept(
        "concept.superstition",
        "Superstition",
        "vice",
        aliases=["superstition"],
        description="The vice opposed to religion by excess in divine worship.",
        source_scope=[92],
        related_concepts=["concept.religion", "concept.idolatry", "concept.divination"],
    ),
    concept(
        "concept.undue_worship_of_true_god",
        "Undue Worship of the True God",
        "sin_type",
        aliases=["undue worship of the true God"],
        description="Superstition that offers worship to the true God in an undue mode.",
        source_scope=[93],
        parent_concept_id="concept.superstition",
        related_concepts=["concept.superstition", "concept.divine_worship"],
    ),
    concept(
        "concept.idolatry",
        "Idolatry",
        "sin_type",
        aliases=["idolatry"],
        description="The superstitious giving of divine worship to a creature.",
        source_scope=[94],
        parent_concept_id="concept.superstition",
        related_concepts=["concept.superstition", "concept.divine_worship"],
    ),
    concept(
        "concept.divination",
        "Divination",
        "sin_type",
        aliases=["divination"],
        description="Superstitious foretelling or seeking knowledge of the future from unlawful sources.",
        source_scope=[95],
        parent_concept_id="concept.superstition",
        related_concepts=["concept.superstition"],
    ),
    concept(
        "concept.superstitious_observance",
        "Superstitious Observance",
        "sin_type",
        aliases=["observances", "superstitious observances"],
        description="Superstitious observances that direct human acts by vain signs rather than divine authority.",
        source_scope=[96],
        parent_concept_id="concept.superstition",
        related_concepts=["concept.superstition"],
    ),
    concept(
        "concept.temptation_of_god",
        "Temptation of God",
        "sin_type",
        aliases=["temptation of God"],
        description="The sin of testing God and thereby showing irreverence toward Him.",
        source_scope=[97],
        related_concepts=["concept.religion"],
    ),
    concept(
        "concept.perjury",
        "Perjury",
        "sin_type",
        aliases=["perjury"],
        description="The perversity of swearing falsely and so irreverently calling God to witness.",
        source_scope=[98],
        related_concepts=["concept.oath", "concept.religion", "concept.divine_name"],
    ),
    concept(
        "concept.sacrilege",
        "Sacrilege",
        "sin_type",
        aliases=["sacrilege"],
        description="The irreverent treatment of a sacred thing, person, place, or sacrament.",
        source_scope=[99],
        related_concepts=["concept.religion", "concept.sacred_thing", "concept.sacrament"],
    ),
    concept(
        "concept.simony",
        "Simony",
        "sin_type",
        aliases=["simony"],
        description="The buying or selling of spiritual things or their sacred annexes.",
        source_scope=[100],
        related_concepts=["concept.religion", "concept.spiritual_thing", "concept.sacrament"],
    ),
    concept(
        "concept.divine_worship",
        "Divine Worship",
        "domain",
        aliases=["divine worship", "worship of God", "divine honor", "reverence to God"],
        description="The domain of honor, reverence, and worship that is due to God alone.",
        source_scope=[81, 92],
        related_concepts=["concept.religion", "concept.divine_name"],
    ),
    concept(
        "concept.divine_name",
        "Divine Name",
        "object",
        aliases=["divine name", "God's name", "name of God"],
        description="The holy name invoked in oath, adjuration, praise, and perjury.",
        source_scope=[89, 90, 91, 98],
        related_concepts=["concept.oath", "concept.adjuration", "concept.perjury"],
    ),
    concept(
        "concept.promise_to_god",
        "Promise to God",
        "object",
        aliases=["promise to God", "promise made to God"],
        description="The promised matter and divine addressee that complete the nature of a vow.",
        source_scope=[88],
        related_concepts=["concept.vow"],
    ),
    concept(
        "concept.sworn_assertion",
        "Sworn Assertion",
        "object",
        aliases=["sworn assertion", "human assertion confirmed by oath"],
        description="The human assertion or promise confirmed by calling God to witness.",
        source_scope=[89],
        related_concepts=["concept.oath", "concept.perjury"],
    ),
    concept(
        "concept.sacred_thing",
        "Sacred Thing",
        "object",
        aliases=["sacred thing", "holy thing"],
        description="A thing deputed to divine worship and therefore owed reverence.",
        source_scope=[90, 99],
        related_concepts=["concept.sacrilege", "concept.divine_worship"],
    ),
    concept(
        "concept.sacred_person",
        "Sacred Person",
        "object",
        aliases=["sacred person"],
        description="A person consecrated to divine worship and therefore protected against sacrilege.",
        source_scope=[99],
        parent_concept_id="concept.sacred_thing",
        related_concepts=["concept.sacrilege"],
    ),
    concept(
        "concept.sacred_place",
        "Sacred Place",
        "object",
        aliases=["sacred place", "holy place"],
        description="A place consecrated for divine worship and therefore a possible object of sacrilege.",
        source_scope=[99],
        parent_concept_id="concept.sacred_thing",
        related_concepts=["concept.sacrilege"],
    ),
    concept(
        "concept.spiritual_thing",
        "Spiritual Thing",
        "object",
        aliases=["spiritual thing", "spiritual goods"],
        description="A spiritual good that cannot be appraised by earthly price and so cannot be lawfully sold.",
        source_scope=[100],
        related_concepts=["concept.simony", "concept.sacrament", "concept.spiritual_action"],
    ),
    concept(
        "concept.sacrament",
        "Sacrament",
        "object",
        aliases=["sacrament", "sacraments"],
        description="A most spiritual thing of the New Law that causes spiritual grace.",
        source_scope=[99, 100],
        parent_concept_id="concept.spiritual_thing",
        related_concepts=["concept.simony", "concept.sacrilege"],
    ),
    concept(
        "concept.spiritual_action",
        "Spiritual Action",
        "object",
        aliases=["spiritual action", "spiritual actions"],
        description="A spiritual action flowing from grace or disposing to grace and not lawfully saleable.",
        source_scope=[100],
        parent_concept_id="concept.spiritual_thing",
        related_concepts=["concept.simony"],
    ),
    concept(
        "concept.spiritual_office",
        "Spiritual Office",
        "object",
        aliases=["spiritual office", "clerical office"],
        description="A sacred office dependent on spiritual things and therefore not lawfully sold.",
        source_scope=[100],
        parent_concept_id="concept.spiritual_thing",
        related_concepts=["concept.simony"],
    ),
    concept(
        "concept.divination_by_demons",
        "Divination by Demons",
        "sin_type",
        aliases=["divination by demons", "necromancy", "prestigiation", "pythons"],
        description="Divination that invokes demons explicitly for knowledge of the future.",
        source_scope=[95],
        parent_concept_id="concept.divination",
        related_concepts=["concept.divination"],
    ),
    concept(
        "concept.astrological_divination",
        "Astrological Divination",
        "sin_type",
        aliases=["astrological divination", "astrologers", "genethliacs"],
        description="Unlawful foreknowledge sought from the stars beyond what they can naturally signify.",
        source_scope=[95],
        parent_concept_id="concept.divination",
        related_concepts=["concept.divination"],
    ),
    concept(
        "concept.divination_by_dreams",
        "Divination by Dreams",
        "sin_type",
        aliases=["divination by dreams"],
        description="Superstitious use of dreams for unlawful foreknowledge when it exceeds natural or divine causes.",
        source_scope=[95],
        parent_concept_id="concept.divination",
        related_concepts=["concept.divination"],
    ),
    concept(
        "concept.augury",
        "Augury",
        "sin_type",
        aliases=["augury", "auguries", "omens"],
        description="Divination that reads birds, signs, or omens beyond the lawful order of nature or providence.",
        source_scope=[95],
        parent_concept_id="concept.divination",
        related_concepts=["concept.divination"],
    ),
    concept(
        "concept.sortilege",
        "Sortilege",
        "sin_type",
        aliases=["sortilege", "divination by lots"],
        description="Divination that seeks hidden knowledge by lots or similar acts beyond lawful necessity and reverence.",
        source_scope=[95],
        parent_concept_id="concept.divination",
        related_concepts=["concept.divination"],
    ),
    concept(
        "concept.magical_observance",
        "Magical Observance",
        "sin_type",
        aliases=["magic art", "magical observance"],
        description="A vain and unlawful observance that seeks knowledge through magical signs and words.",
        source_scope=[96],
        parent_concept_id="concept.superstitious_observance",
        related_concepts=["concept.superstitious_observance"],
    ),
    concept(
        "concept.healing_observance",
        "Superstitious Healing Observance",
        "sin_type",
        aliases=["superstitious healing observance"],
        description="An unlawful observance that seeks bodily effects through signs rather than natural causes.",
        source_scope=[96],
        parent_concept_id="concept.superstitious_observance",
        related_concepts=["concept.superstitious_observance"],
    ),
    concept(
        "concept.fortune_telling_observance",
        "Fortune-Telling Observance",
        "sin_type",
        aliases=["fortune-telling observance", "lucky and unlucky days"],
        description="A vain observance that treats arbitrary signs as indicators of future good or evil fortune.",
        source_scope=[96],
        parent_concept_id="concept.superstitious_observance",
        related_concepts=["concept.superstitious_observance"],
    ),
    concept(
        "concept.written_charm_observance",
        "Written-Charm Observance",
        "sin_type",
        aliases=["wearing sacred words at the neck", "written charms", "incantations"],
        description="A superstitious observance that relies on written words or charms apart from due reverence to God.",
        source_scope=[96],
        parent_concept_id="concept.superstitious_observance",
        related_concepts=["concept.superstitious_observance", "concept.divine_name"],
    ),
]

LABEL_BY_CONCEPT_ID = {
    payload["concept_id"]: str(payload["canonical_label"])
    for payload in RELIGION_TRACT_EXTRA_CONCEPTS
}

TRACT_CONCEPT_IDS: set[str] = set(LABEL_BY_CONCEPT_ID) | {"concept.justice"}

QUESTION_PRIMARY_CONCEPTS: dict[int, str] = {
    80: "concept.religion",
    81: "concept.religion",
    82: "concept.devotion",
    83: "concept.prayer",
    84: "concept.adoration",
    85: "concept.sacrifice",
    86: "concept.oblation",
    87: "concept.tithes",
    88: "concept.vow",
    89: "concept.oath",
    90: "concept.adjuration",
    91: "concept.praise_of_god",
    92: "concept.superstition",
    93: "concept.undue_worship_of_true_god",
    94: "concept.idolatry",
    95: "concept.divination",
    96: "concept.superstitious_observance",
    97: "concept.temptation_of_god",
    98: "concept.perjury",
    99: "concept.sacrilege",
    100: "concept.simony",
}

QUESTION_ARTICLE_COUNTS: dict[int, int] = {
    80: 1,
    81: 8,
    82: 4,
    83: 17,
    84: 3,
    85: 4,
    86: 4,
    87: 4,
    88: 12,
    89: 10,
    90: 3,
    91: 2,
    92: 2,
    93: 2,
    94: 4,
    95: 8,
    96: 4,
    97: 4,
    98: 4,
    99: 4,
    100: 6,
}


def concept_label(concept_id: str) -> str:
    if concept_id == "concept.justice":
        return "Justice"
    return LABEL_BY_CONCEPT_ID[concept_id]


for question_number, concept_id in QUESTION_PRIMARY_CONCEPTS.items():
    add_question_treatment(
        question_number,
        concept_id,
        rationale=(
            f"Question {question_number} is principally organized around {concept_label(concept_id)}."
        ),
        evidence_hints=(concept_label(concept_id),),
    )
    for article_number in range(1, QUESTION_ARTICLE_COUNTS[question_number] + 1):
        add_article_treatment(
            question_number,
            article_number,
            concept_id,
            rationale=(
                f"Article {article_number} contributes to the tract's treatment of "
                f"{concept_label(concept_id)}."
            ),
            evidence_hints=(concept_label(concept_id),),
        )

add_question_treatment(
    80,
    "concept.justice",
    rationale="Q80 is the structural gateway from justice into the annexed virtue of religion.",
    evidence_hints=("justice",),
)
add_article_treatment(
    80,
    1,
    "concept.justice",
    rationale="Q80 a.1 explicitly frames religion as annexed to justice.",
    evidence_hints=("justice",),
)
add_article_treatment(
    86,
    4,
    "concept.first_fruits",
    rationale="Q86 a.4 treats first-fruits as a distinct offering within oblation.",
    evidence_hints=("first-fruits",),
)
add_article_treatment(
    88,
    1,
    "concept.promise_to_god",
    rationale="Q88 a.1 defines a vow by its promise to God.",
    evidence_hints=("promise", "God"),
)
add_article_treatment(
    89,
    1,
    "concept.sworn_assertion",
    rationale="Q89 a.1 treats the assertion confirmed by oath as a distinct object of analysis.",
    evidence_hints=("confirmation", "asserts"),
)
add_article_treatment(
    89,
    4,
    "concept.divine_name",
    rationale="Q89 a.4 treats swearing as invoking God as witness.",
    evidence_hints=("God", "witness"),
)
add_article_treatment(
    90,
    1,
    "concept.divine_name",
    rationale="Q90 a.1 turns on adjuring through reverence for the divine name.",
    evidence_hints=("Divine name",),
)
add_article_treatment(
    90,
    1,
    "concept.sacred_thing",
    rationale="Q90 a.1 also treats adjuration through reverence for some holy thing.",
    evidence_hints=("holy thing",),
)
add_article_treatment(
    95,
    3,
    "concept.divination_by_demons",
    rationale="Q95 a.3 explicitly enumerates demon-invoking kinds of divination.",
    evidence_hints=("necromancy", "pythons"),
)
add_article_treatment(
    95,
    3,
    "concept.astrological_divination",
    rationale="Q95 a.3 explicitly names astrologers as one route of unlawful divination.",
    evidence_hints=("astrologers",),
)
add_article_treatment(
    95,
    3,
    "concept.divination_by_dreams",
    rationale="Q95 a.3 explicitly names divination by dreams.",
    evidence_hints=("divination by dreams",),
)
add_article_treatment(
    95,
    3,
    "concept.augury",
    rationale="Q95 a.3 explicitly names augury and omen-reading.",
    evidence_hints=("augury", "omen"),
)
add_article_treatment(
    95,
    3,
    "concept.sortilege",
    rationale="Q95 a.3 explicitly names sortilege.",
    evidence_hints=("sortilege",),
)
add_article_treatment(
    96,
    1,
    "concept.magical_observance",
    rationale="Q96 a.1 treats the magic art as a distinct observance.",
    evidence_hints=("magic art",),
)
add_article_treatment(
    96,
    2,
    "concept.healing_observance",
    rationale="Q96 a.2 treats observances aimed at bodily effects.",
    evidence_hints=("bodily effect",),
)
add_article_treatment(
    96,
    3,
    "concept.fortune_telling_observance",
    rationale="Q96 a.3 treats fortune-telling observances and lucky or unlucky days.",
    evidence_hints=("future events", "lucky and unlucky days"),
)
add_article_treatment(
    96,
    4,
    "concept.written_charm_observance",
    rationale="Q96 a.4 treats written words and charms worn on the person.",
    evidence_hints=("written words", "superstitious"),
)
add_article_treatment(
    99,
    1,
    "concept.sacred_thing",
    rationale="Q99 a.1 defines sacrilege through irreverence toward sacred things.",
    evidence_hints=("sacred",),
)
add_article_treatment(
    99,
    3,
    "concept.sacred_person",
    rationale="Q99 a.3 explicitly distinguishes sacrilege against sacred persons.",
    evidence_hints=("sacred persons",),
)
add_article_treatment(
    99,
    3,
    "concept.sacred_place",
    rationale="Q99 a.3 explicitly distinguishes sacrilege against sacred places.",
    evidence_hints=("sacred places",),
)
add_article_treatment(
    99,
    3,
    "concept.sacrament",
    rationale="Q99 a.3 explicitly places the sacraments at the highest grade among sacred things.",
    evidence_hints=("sacraments",),
)
add_article_treatment(
    100,
    1,
    "concept.spiritual_thing",
    rationale="Q100 a.1 defines simony by the buying and selling of spiritual things.",
    evidence_hints=("spiritual thing",),
)
add_article_treatment(
    100,
    2,
    "concept.sacrament",
    rationale="Q100 a.2 explicitly treats sacraments within simony.",
    evidence_hints=("sacraments",),
)
add_article_treatment(
    100,
    3,
    "concept.spiritual_action",
    rationale="Q100 a.3 explicitly treats spiritual actions within simony.",
    evidence_hints=("spiritual actions",),
)
add_article_treatment(
    100,
    4,
    "concept.spiritual_office",
    rationale="Q100 a.4 explicitly treats things dependent on clerical office within simony.",
    evidence_hints=("clerical office",),
)
add_article_treatment(
    100,
    4,
    "concept.spiritual_thing",
    rationale="Q100 a.4 treats annexes directed to spiritual things.",
    evidence_hints=("spiritual things",),
)

# Doctrinal relation seeds
add_relation(
    80,
    1,
    "concept.religion",
    "annexed_to",
    "concept.justice",
    rationale="Q80 a.1 explicitly names religion as annexed to justice.",
    evidence_hints=("annexed to justice",),
)

add_relation(
    81,
    2,
    "concept.religion",
    "directed_to",
    "concept.divine_worship",
    rationale="Q81 a.2 grounds religion in paying due honor to God.",
    evidence_hints=("pay due honor to someone, namely, to God",),
)
add_relation(
    81,
    4,
    "concept.religion",
    "directed_to",
    "concept.divine_worship",
    rationale="Q81 a.4 states that religion is directed to giving due honor to God.",
    evidence_hints=("give due honor to God",),
)
add_relation(
    81,
    5,
    "concept.religion",
    "directed_to",
    "concept.divine_worship",
    rationale="Q81 a.5 restates religion as paying due worship to God.",
    evidence_hints=("religion pays due worship to God",),
)
add_relation(
    81,
    7,
    "concept.religion",
    "has_act",
    "concept.adoration",
    support_type="strong_textual_inference",
    confidence=0.84,
    rationale="Q81 a.7 states that religion has internal and external acts, with adoration later supplying the tract's main external sign of reverence.",
    evidence_hints=("external acts", "internal acts of religion"),
)

add_relation(
    82,
    1,
    "concept.devotion",
    "directed_to",
    "concept.divine_worship",
    rationale="Q82 a.1 defines devotion by readiness for the service of God.",
    evidence_hints=("service of God",),
)
add_relation(
    82,
    2,
    "concept.religion",
    "has_act",
    "concept.devotion",
    rationale="Q82 a.2 explicitly states that devotion is an act of religion.",
    evidence_hints=("devotion is an act of religion",),
)

add_relation(
    83,
    3,
    "concept.religion",
    "has_act",
    "concept.prayer",
    rationale="Q83 a.3 explicitly states that prayer is properly an act of religion.",
    evidence_hints=("prayer is properly an act of religion",),
)
add_relation(
    83,
    3,
    "concept.prayer",
    "directed_to",
    "concept.divine_worship",
    rationale="Q83 a.3 says prayer shows reverence to God and confesses dependence on Him.",
    evidence_hints=("shows reverence to God", "needs Him"),
)

add_relation(
    84,
    1,
    "concept.religion",
    "has_act",
    "concept.adoration",
    rationale="Q84 a.1 explicitly states that adoration of God is an act of religion.",
    evidence_hints=("act of religion",),
)
add_relation(
    84,
    2,
    "concept.adoration",
    "directed_to",
    "concept.divine_worship",
    rationale="Q84 a.2 presents adoration as a twofold act offered to God.",
    evidence_hints=("we offer God a twofold adoration",),
)

add_relation(
    85,
    1,
    "concept.sacrifice",
    "directed_to",
    "concept.divine_worship",
    rationale="Q85 a.1 defines sacrifice as a sensible offering signifying man's subjection and honor to God.",
    evidence_hints=("offering them to God", "this is what we mean by a sacrifice"),
)
add_relation(
    85,
    2,
    "concept.sacrifice",
    "directed_to",
    "concept.divine_worship",
    rationale="Q85 a.2 explicitly says outward sacrifices are to be offered to God alone.",
    evidence_hints=("offer outward sacrifices to Him alone",),
)
add_relation(
    85,
    3,
    "concept.religion",
    "has_act",
    "concept.sacrifice",
    rationale="Q85 a.3 explicitly says sacrifice belongs to the definite virtue of religion.",
    evidence_hints=("belongs to a definite virtue , viz. religion",),
)
add_relation(
    85,
    3,
    "concept.sacrifice",
    "directed_to",
    "concept.divine_worship",
    rationale="Q85 a.3 says sacrifice is praiseworthy insofar as it is done out of reverence for God.",
    evidence_hints=("done out of reverence for God",),
)

add_relation(
    86,
    1,
    "concept.religion",
    "has_act",
    "concept.oblation",
    support_type="strong_textual_inference",
    confidence=0.85,
    rationale="Q86 a.1 treats oblation as a stable offering for divine worship within the religion tract.",
    evidence_hints=("offered for the Divine worship",),
)
add_relation(
    86,
    1,
    "concept.oblation",
    "directed_to",
    "concept.divine_worship",
    rationale="Q86 a.1 explicitly defines oblation by its offering for divine worship.",
    evidence_hints=("offered for the Divine worship",),
)
add_relation(
    86,
    4,
    "concept.first_fruits",
    "species_of",
    "concept.oblation",
    rationale="Q86 a.4 explicitly states that first-fruits are a kind of oblation.",
    evidence_hints=("First-fruits are a kind of oblation",),
)
add_relation(
    86,
    4,
    "concept.first_fruits",
    "directed_to",
    "concept.divine_worship",
    rationale="Q86 a.4 presents first-fruits as offered to God in acknowledgment of divine favor.",
    evidence_hints=("offered to God", "offer God his first-fruits"),
)

add_relation(
    87,
    1,
    "concept.religion",
    "has_act",
    "concept.tithes",
    support_type="strong_textual_inference",
    confidence=0.84,
    rationale="Q87 a.1 treats the payment of tithes as a stable obligation connected to divine worship and its ministers.",
    evidence_hints=("tithes were paid", "divine worship"),
)
add_relation(
    87,
    1,
    "concept.tithes",
    "directed_to",
    "concept.divine_worship",
    rationale="Q87 a.1 grounds tithes in support for those who minister divine worship.",
    evidence_hints=("ministers of divine worship",),
)

add_relation(
    88,
    1,
    "concept.vow",
    "concerns_sacred_object",
    "concept.promise_to_god",
    rationale="Q88 a.1 presents a vow as a promise made to God.",
    evidence_hints=("promise", "made to God"),
)
add_relation(
    88,
    5,
    "concept.religion",
    "has_act",
    "concept.vow",
    rationale="Q88 a.5 explicitly says that taking a vow is properly an act of religion or latria.",
    evidence_hints=("an act of latria or religion",),
)
add_relation(
    88,
    5,
    "concept.vow",
    "concerns_sacred_object",
    "concept.promise_to_god",
    rationale="Q88 a.5 reiterates that vow directs the promised thing to the worship or service of God.",
    evidence_hints=("promise made to God", "worship or service of God"),
)
add_relation(
    88,
    5,
    "concept.vow",
    "directed_to",
    "concept.divine_worship",
    rationale="Q88 a.5 says a vow directs what is vowed to the worship or service of God.",
    evidence_hints=("worship or service of God",),
)

add_relation(
    89,
    1,
    "concept.oath",
    "concerns_sacred_object",
    "concept.sworn_assertion",
    rationale="Q89 a.1 treats oath as the confirmation of a human assertion.",
    evidence_hints=("confirmation", "human assertion"),
)
add_relation(
    89,
    1,
    "concept.oath",
    "concerns_sacred_object",
    "concept.divine_name",
    rationale="Q89 a.1 defines oath by calling God to witness.",
    evidence_hints=("call God to witness",),
)
add_relation(
    89,
    4,
    "concept.religion",
    "has_act",
    "concept.oath",
    rationale="Q89 a.4 explicitly says that an oath is an act of religion or latria.",
    evidence_hints=("an oath is an act of religion or latria",),
)
add_relation(
    89,
    4,
    "concept.oath",
    "concerns_sacred_object",
    "concept.divine_name",
    rationale="Q89 a.4 restates oath as invoking God as witness and showing reverence to Him.",
    evidence_hints=("calls God to witness", "shows reverence to God"),
)
add_relation(
    89,
    4,
    "concept.oath",
    "directed_to",
    "concept.divine_worship",
    support_type="strong_textual_inference",
    confidence=0.84,
    rationale="Q89 a.4 roots oath in reverence to God, which is the proper domain of religion.",
    evidence_hints=("shows reverence to God",),
)

add_relation(
    90,
    1,
    "concept.religion",
    "has_act",
    "concept.adjuration",
    support_type="strong_textual_inference",
    confidence=0.82,
    rationale="Q90 treats adjuration as a reverential use of the divine name and holy things within the religion tract.",
    evidence_hints=("adjuration", "Divine name"),
)
add_relation(
    90,
    1,
    "concept.adjuration",
    "concerns_sacred_object",
    "concept.divine_name",
    rationale="Q90 a.1 explicitly treats adjuration through reverence for the divine name.",
    evidence_hints=("Divine name",),
)
add_relation(
    90,
    1,
    "concept.adjuration",
    "concerns_sacred_object",
    "concept.sacred_thing",
    rationale="Q90 a.1 explicitly treats adjuration through reverence for some holy thing.",
    evidence_hints=("holy thing",),
)

add_relation(
    91,
    1,
    "concept.religion",
    "has_act",
    "concept.praise_of_god",
    support_type="strong_textual_inference",
    confidence=0.84,
    rationale="Q91 treats vocal praise as a stable positive act within religion.",
    evidence_hints=("praise God with our lips",),
)
add_relation(
    91,
    1,
    "concept.praise_of_god",
    "directed_to",
    "concept.divine_worship",
    rationale="Q91 a.1 says we praise God with our lips to bring ourselves and our hearers to reverence Him.",
    evidence_hints=("reverence Him", "praise God with our lips"),
)

add_relation(
    92,
    1,
    "concept.superstition",
    "excess_opposed_to",
    "concept.religion",
    rationale="Q92 a.1 explicitly says superstition is contrary to religion by excess.",
    evidence_hints=("superstition is a vice contrary to religion by excess",),
)
add_relation(
    92,
    2,
    "concept.undue_worship_of_true_god",
    "species_of",
    "concept.superstition",
    rationale="Q92 a.2 explicitly names undue worship of the true God as a first species of superstition.",
    evidence_hints=("first species of superstition",),
)
add_relation(
    92,
    2,
    "concept.idolatry",
    "species_of",
    "concept.superstition",
    rationale="Q92 a.2 explicitly names idolatry as a species of superstition.",
    evidence_hints=("idolatry", "species"),
)
add_relation(
    92,
    2,
    "concept.divination",
    "species_of",
    "concept.superstition",
    rationale="Q92 a.2 explicitly names divinatory superstition as a species of superstition.",
    evidence_hints=("divinatory", "species"),
)
add_relation(
    92,
    2,
    "concept.superstitious_observance",
    "species_of",
    "concept.superstition",
    rationale="Q92 a.2 explicitly names observances as a species of superstition.",
    evidence_hints=("observances", "species"),
)

add_relation(
    93,
    1,
    "concept.undue_worship_of_true_god",
    "excess_opposed_to",
    "concept.religion",
    rationale="Q93 a.1 treats false outward worship as a pernicious distortion of religion.",
    evidence_hints=("outward worship", "pernicious"),
)
add_relation(
    93,
    1,
    "concept.undue_worship_of_true_god",
    "misuses_sacred_object",
    "concept.divine_worship",
    rationale="Q93 a.1 treats worship contrary to Church and divine authority as a false use of outward worship.",
    evidence_hints=("outward worship", "contrary to the manner established"),
)
add_relation(
    93,
    2,
    "concept.undue_worship_of_true_god",
    "misuses_sacred_object",
    "concept.divine_worship",
    rationale="Q93 a.2 defines superstitious excess by worship not proportionate to its end.",
    evidence_hints=("excessive and superstitious", "worship of God"),
)

add_relation(
    94,
    1,
    "concept.idolatry",
    "species_of",
    "concept.superstition",
    rationale="Q94 a.1 explicitly says all such worship comes under the superstition of idolatry.",
    evidence_hints=("superstition of idolatry",),
)
add_relation(
    94,
    1,
    "concept.idolatry",
    "excess_opposed_to",
    "concept.religion",
    rationale="Q94 a.1 describes idolatry as giving divine worship to whom it should not be given.",
    evidence_hints=("divine worship is given to whom it should not be given",),
)
add_relation(
    94,
    1,
    "concept.idolatry",
    "misuses_sacred_object",
    "concept.divine_worship",
    rationale="Q94 a.1 defines idolatry by the misdirection of divine worship to creatures.",
    evidence_hints=("divine worship", "creature"),
)

add_relation(
    95,
    2,
    "concept.divination",
    "species_of",
    "concept.superstition",
    rationale="Q95 a.2 explicitly concludes that divination is a species of superstition.",
    evidence_hints=("divination is a species of superstition",),
)
add_relation(
    95,
    2,
    "concept.divination",
    "excess_opposed_to",
    "concept.religion",
    support_type="strong_textual_inference",
    confidence=0.86,
    rationale="Q95 a.2 places divination within undue divine worship and so on the excess side opposed to religion.",
    evidence_hints=("superstition denotes undue divine worship",),
)
add_relation(
    95,
    3,
    "concept.divination_by_demons",
    "species_of",
    "concept.divination",
    rationale="Q95 a.3 explicitly lists demon-invoking species of divination.",
    evidence_hints=("necromancy", "pythons"),
)
add_relation(
    95,
    3,
    "concept.astrological_divination",
    "species_of",
    "concept.divination",
    rationale="Q95 a.3 explicitly names astrologers within divination.",
    evidence_hints=("astrologers",),
)
add_relation(
    95,
    3,
    "concept.divination_by_dreams",
    "species_of",
    "concept.divination",
    rationale="Q95 a.3 explicitly names divination by dreams.",
    evidence_hints=("divination by dreams",),
)
add_relation(
    95,
    3,
    "concept.augury",
    "species_of",
    "concept.divination",
    rationale="Q95 a.3 explicitly names augury and omen-reading within divination.",
    evidence_hints=("augury", "omen"),
)
add_relation(
    95,
    3,
    "concept.sortilege",
    "species_of",
    "concept.divination",
    rationale="Q95 a.3 explicitly names sortilege within divination.",
    evidence_hints=("sortilege",),
)

add_relation(
    96,
    3,
    "concept.superstitious_observance",
    "species_of",
    "concept.superstition",
    rationale="Q96 a.3 reiterates that these observances are superstitious and unlawful.",
    evidence_hints=("all these observances are superstitious",),
)
add_relation(
    96,
    3,
    "concept.superstitious_observance",
    "excess_opposed_to",
    "concept.religion",
    support_type="strong_textual_inference",
    confidence=0.84,
    rationale="Q96 a.3 places fortune-telling observances inside the superstitious excess opposed to religion.",
    evidence_hints=("superstitious and unlawful",),
)
add_relation(
    96,
    1,
    "concept.magical_observance",
    "species_of",
    "concept.superstitious_observance",
    support_type="strong_textual_inference",
    confidence=0.82,
    rationale="Q96 a.1 treats the magic art as a distinct observance within superstition.",
    evidence_hints=("magic art",),
)
add_relation(
    96,
    2,
    "concept.healing_observance",
    "species_of",
    "concept.superstitious_observance",
    support_type="strong_textual_inference",
    confidence=0.82,
    rationale="Q96 a.2 treats bodily-effect observances as unlawful where they rely on signs rather than natural causes.",
    evidence_hints=("bodily effect", "compact by tokens"),
)
add_relation(
    96,
    3,
    "concept.fortune_telling_observance",
    "species_of",
    "concept.superstitious_observance",
    support_type="strong_textual_inference",
    confidence=0.82,
    rationale="Q96 a.3 treats fortune-telling observances and lucky or unlucky days as a distinct observance cluster.",
    evidence_hints=("lucky and unlucky days",),
)
add_relation(
    96,
    4,
    "concept.written_charm_observance",
    "species_of",
    "concept.superstitious_observance",
    support_type="strong_textual_inference",
    confidence=0.82,
    rationale="Q96 a.4 treats written words and charms as a distinct superstitious observance when they rely on vain signs.",
    evidence_hints=("written words", "superstitious"),
)

add_relation(
    97,
    3,
    "concept.temptation_of_god",
    "deficiency_opposed_to",
    "concept.religion",
    rationale="Q97 a.3 explicitly says tempting God is a sin opposed to religion.",
    evidence_hints=("a sin opposed to religion",),
)

add_relation(
    98,
    1,
    "concept.perjury",
    "deficiency_opposed_to",
    "concept.oath",
    support_type="strong_textual_inference",
    confidence=0.88,
    rationale="Q98 a.1 defines perjury by the falsity that annuls the end of an oath.",
    evidence_hints=("end of an oath", "perjury"),
)
add_relation(
    98,
    2,
    "concept.perjury",
    "deficiency_opposed_to",
    "concept.religion",
    rationale="Q98 a.2 explicitly says perjury is a sin opposed to religion.",
    evidence_hints=("a sin opposed to religion",),
)
add_relation(
    98,
    2,
    "concept.perjury",
    "misuses_sacred_object",
    "concept.divine_name",
    rationale="Q98 a.2 says perjury irreverently calls God to witness to a falsehood.",
    evidence_hints=("call Him to witness to a falsehood",),
)

add_relation(
    99,
    1,
    "concept.sacrilege",
    "misuses_sacred_object",
    "concept.sacred_thing",
    rationale="Q99 a.1 defines sacrilege through irreverence toward sacred things.",
    evidence_hints=("irreverence for sacred things",),
)
add_relation(
    99,
    2,
    "concept.sacrilege",
    "deficiency_opposed_to",
    "concept.religion",
    rationale="Q99 a.2 explicitly says sacrilege is opposed to religion.",
    evidence_hints=("opposed to religion",),
)
add_relation(
    99,
    3,
    "concept.sacrilege",
    "misuses_sacred_object",
    "concept.sacred_person",
    rationale="Q99 a.3 explicitly distinguishes sacrilege against sacred persons.",
    evidence_hints=("sacred persons",),
)
add_relation(
    99,
    3,
    "concept.sacrilege",
    "misuses_sacred_object",
    "concept.sacred_place",
    rationale="Q99 a.3 explicitly distinguishes sacrilege against sacred places.",
    evidence_hints=("sacred places",),
)
add_relation(
    99,
    3,
    "concept.sacrilege",
    "misuses_sacred_object",
    "concept.sacrament",
    rationale="Q99 a.3 explicitly gives the highest place among sacred things to the sacraments.",
    evidence_hints=("the sacraments",),
)

add_relation(
    100,
    1,
    "concept.simony",
    "deficiency_opposed_to",
    "concept.religion",
    rationale="Q100 a.1 explicitly concludes that simony is a sin of irreligion.",
    evidence_hints=("sin of irreligion",),
)
add_relation(
    100,
    1,
    "concept.simony",
    "misuses_sacred_object",
    "concept.spiritual_thing",
    rationale="Q100 a.1 defines simony by the buying or selling of a spiritual thing.",
    evidence_hints=("spiritual thing", "buying or selling"),
)
add_relation(
    100,
    2,
    "concept.simony",
    "misuses_sacred_object",
    "concept.sacrament",
    rationale="Q100 a.2 explicitly treats taking money for the sacraments as simony.",
    evidence_hints=("for the sacraments", "simony"),
)
add_relation(
    100,
    3,
    "concept.simony",
    "misuses_sacred_object",
    "concept.spiritual_action",
    rationale="Q100 a.3 explicitly treats buying or selling spiritual actions as simoniacal.",
    evidence_hints=("spiritual actions", "simoniacal"),
)
add_relation(
    100,
    4,
    "concept.simony",
    "misuses_sacred_object",
    "concept.spiritual_office",
    rationale="Q100 a.4 explicitly forbids selling things dependent on clerical office as annexed to spiritual things.",
    evidence_hints=("clerical office", "sale of things spiritual"),
)
add_relation(
    100,
    5,
    "concept.simony",
    "corrupts_spiritual_exchange",
    "concept.spiritual_thing",
    rationale="Q100 a.5 explicitly extends simony beyond money to service and other remunerations of pecuniary value.",
    evidence_hints=("pecuniary value", "service rendered"),
)

POSITIVE_ACT_CONCEPT_IDS: set[str] = {
    "concept.devotion",
    "concept.prayer",
    "concept.adoration",
    "concept.sacrifice",
    "concept.oblation",
    "concept.first_fruits",
    "concept.tithes",
    "concept.vow",
    "concept.oath",
    "concept.adjuration",
    "concept.praise_of_god",
}

EXCESS_CONCEPT_IDS: set[str] = {
    "concept.superstition",
    "concept.undue_worship_of_true_god",
    "concept.idolatry",
    "concept.divination",
    "concept.superstitious_observance",
    "concept.divination_by_demons",
    "concept.astrological_divination",
    "concept.divination_by_dreams",
    "concept.augury",
    "concept.sortilege",
    "concept.magical_observance",
    "concept.healing_observance",
    "concept.fortune_telling_observance",
    "concept.written_charm_observance",
}

DEFICIENCY_CONCEPT_IDS: set[str] = {
    "concept.temptation_of_god",
    "concept.perjury",
    "concept.sacrilege",
    "concept.simony",
}

SACRED_OBJECT_CONCEPT_IDS: set[str] = {
    "concept.divine_worship",
    "concept.divine_name",
    "concept.promise_to_god",
    "concept.sworn_assertion",
    "concept.sacred_thing",
    "concept.sacred_person",
    "concept.sacred_place",
    "concept.spiritual_thing",
    "concept.sacrament",
    "concept.spiritual_action",
    "concept.spiritual_office",
}

DIVINE_NAME_RELATED_CONCEPT_IDS: set[str] = {
    "concept.oath",
    "concept.adjuration",
    "concept.praise_of_god",
    "concept.perjury",
    "concept.divine_name",
}

OFFERING_PROMISE_EXCHANGE_CONCEPT_IDS: set[str] = {
    "concept.sacrifice",
    "concept.oblation",
    "concept.first_fruits",
    "concept.tithes",
    "concept.vow",
    "concept.oath",
    "concept.promise_to_god",
    "concept.sworn_assertion",
    "concept.spiritual_thing",
    "concept.sacrament",
    "concept.spiritual_action",
    "concept.spiritual_office",
    "concept.simony",
}


def is_positive_act_relation(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> bool:
    return (
        relation_type == "has_act"
        and subject_id == "concept.religion"
        and object_id in POSITIVE_ACT_CONCEPT_IDS
    ) or (
        relation_type in {"directed_to", "concerns_sacred_object"}
        and subject_id in POSITIVE_ACT_CONCEPT_IDS
    )


def is_excess_opposition_relation(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> bool:
    return relation_type == "excess_opposed_to" and subject_id in EXCESS_CONCEPT_IDS


def is_deficiency_opposition_relation(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> bool:
    return relation_type == "deficiency_opposed_to" and subject_id in DEFICIENCY_CONCEPT_IDS


def is_sacred_object_relation(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> bool:
    return relation_type in {
        "concerns_sacred_object",
        "misuses_sacred_object",
        "corrupts_spiritual_exchange",
    } or (relation_type == "directed_to" and object_id in SACRED_OBJECT_CONCEPT_IDS)
