# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import PilotDueMode, PilotRelationType, PilotSupportType

OWED_RELATION_TRACT_MIN_QUESTION = 101
OWED_RELATION_TRACT_MAX_QUESTION = 108


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
    due_mode: PilotDueMode | None = None
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
    due_mode: PilotDueMode | None = None,
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
            due_mode=due_mode,
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


OWED_RELATION_TRACT_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.piety",
        "Piety",
        "virtue",
        aliases=["piety"],
        description="The virtue rendering due worship and service to parents and country as proximate principles of being and government.",
        source_scope=[101],
        related_concepts=[
            "concept.justice",
            "concept.parent_role",
            "concept.country",
            "concept.origin_related_due",
        ],
    ),
    concept(
        "concept.observance",
        "Observance",
        "virtue",
        aliases=["observance"],
        description="The virtue paying honor and service to persons who excel in dignity.",
        source_scope=[102],
        related_concepts=[
            "concept.justice",
            "concept.person_in_dignity_role",
            "concept.excellence_related_due",
        ],
    ),
    concept(
        "concept.dulia",
        "Dulia",
        "virtue",
        aliases=["dulia"],
        description="A species of observance rendering due service to a human lord under a created mode of superiority.",
        source_scope=[103],
        parent_concept_id="concept.observance",
        related_concepts=[
            "concept.observance",
            "concept.human_lord_role",
            "concept.excellence_related_due",
        ],
    ),
    concept(
        "concept.obedience",
        "Obedience",
        "virtue",
        aliases=["obedience"],
        description="The virtue by which one follows a superior's command according to divinely established order.",
        source_scope=[104],
        related_concepts=[
            "concept.justice",
            "concept.superior_role",
            "concept.command",
            "concept.authority_related_due",
        ],
    ),
    concept(
        "concept.disobedience",
        "Disobedience",
        "sin_type",
        aliases=["disobedience"],
        description="The sin of refusing obedience due to God or to a superior in rightful command.",
        source_scope=[105],
        related_concepts=[
            "concept.obedience",
            "concept.superior_role",
            "concept.command",
            "concept.authority_related_due",
        ],
    ),
    concept(
        "concept.gratitude",
        "Gratitude",
        "virtue",
        aliases=["gratitude", "thankfulness", "thanksgiving"],
        description="The virtue giving thanks to a benefactor for a favor received.",
        source_scope=[106],
        related_concepts=[
            "concept.justice",
            "concept.benefactor_role",
            "concept.benefaction",
            "concept.benefaction_related_due",
        ],
    ),
    concept(
        "concept.ingratitude",
        "Ingratitude",
        "sin_type",
        aliases=["ingratitude", "thanklessness"],
        description="The sin opposed to gratitude by deficiency in acknowledging, praising, or repaying a favor.",
        source_scope=[107],
        related_concepts=[
            "concept.gratitude",
            "concept.benefactor_role",
            "concept.benefaction",
            "concept.benefaction_related_due",
        ],
    ),
    concept(
        "concept.vengeance",
        "Vengeance",
        "virtue",
        aliases=["vengeance", "vindication"],
        description="The virtue seeking due penal correction or restraint in response to prior wrong.",
        source_scope=[108],
        related_concepts=[
            "concept.justice",
            "concept.prior_wrong",
            "concept.punishment",
            "concept.rectification",
            "concept.rectificatory_due",
        ],
    ),
    concept(
        "concept.honor",
        "Honor",
        "act_type",
        aliases=["honor", "homage"],
        description="The act of acknowledging excellence through fitting signs.",
        source_scope=[101, 102, 103, 106],
        related_concepts=["concept.excellence_related_due"],
    ),
    concept(
        "concept.service",
        "Service",
        "act_type",
        aliases=["service", "duty"],
        description="Fitting service rendered to another according to due relation.",
        source_scope=[101, 102, 103],
        related_concepts=["concept.piety", "concept.observance", "concept.dulia"],
    ),
    concept(
        "concept.benefaction",
        "Benefaction",
        "act_type",
        aliases=["benefaction", "favor", "favor received"],
        description="A favor or freely bestowed benefit generating a moral debt of gratitude.",
        source_scope=[106, 107],
        related_concepts=["concept.gratitude", "concept.ingratitude", "concept.benefactor_role"],
    ),
    concept(
        "concept.punishment",
        "Punishment",
        "act_type",
        aliases=["punishment", "penal evil"],
        description="A penal infliction restoring order or acting medicinally when rightly imposed.",
        source_scope=[108],
        related_concepts=["concept.vengeance", "concept.prior_wrong", "concept.rectification"],
    ),
    concept(
        "concept.rectification",
        "Rectification",
        "doctrine",
        aliases=["rectification", "restoring equality of justice"],
        description="The restoration of order after prior wrong by due punitive or corrective response.",
        source_scope=[108],
        related_concepts=["concept.justice", "concept.vengeance", "concept.prior_wrong"],
    ),
    concept(
        "concept.prior_wrong",
        "Prior Wrong",
        "wrong_act",
        aliases=["prior wrong", "wrong suffered", "sin already committed"],
        description="A prior wrong or sin to which rectificatory response may be due.",
        source_scope=[108],
        related_concepts=["concept.vengeance", "concept.punishment", "concept.wrongdoer_role"],
    ),
    concept(
        "concept.origin_related_due",
        "Origin-Related Due",
        "doctrine",
        aliases=["origin-related debt", "due because of origin", "principle of being and government"],
        description="What is due because another stands as a proximate principle of one's being or upbringing.",
        source_scope=[101],
        related_concepts=["concept.piety", "concept.parent_role", "concept.country"],
    ),
    concept(
        "concept.excellence_related_due",
        "Excellence-Related Due",
        "doctrine",
        aliases=["excellence-related debt", "due because of excellence", "due to dignity or superiority"],
        description="What is due because another excels in dignity, superiority, or governing station.",
        source_scope=[102, 103],
        related_concepts=["concept.observance", "concept.dulia", "concept.honor"],
    ),
    concept(
        "concept.authority_related_due",
        "Authority-Related Due",
        "doctrine",
        aliases=["authority-related debt", "due because of command", "due to superior authority"],
        description="What is due because another rightly commands under divinely ordered authority.",
        source_scope=[104, 105],
        related_concepts=["concept.obedience", "concept.disobedience", "concept.superior_role"],
    ),
    concept(
        "concept.benefaction_related_due",
        "Benefaction-Related Due",
        "doctrine",
        aliases=["benefaction-related debt", "due because of received favor"],
        description="What is due because one has received a freely bestowed benefit from another.",
        source_scope=[106, 107],
        related_concepts=["concept.gratitude", "concept.ingratitude", "concept.benefactor_role"],
    ),
    concept(
        "concept.rectificatory_due",
        "Rectificatory Due",
        "doctrine",
        aliases=["rectificatory debt", "due because of prior wrong"],
        description="What is due because a prior wrong calls for correction, restraint, or punitive restoration of order.",
        source_scope=[108],
        related_concepts=["concept.vengeance", "concept.prior_wrong", "concept.rectification"],
    ),
    concept(
        "concept.parent_role",
        "Parent Role",
        "role",
        aliases=["parent", "father", "mother", "parents"],
        description="Role-level category for parents as proximate principles of being and upbringing.",
        source_scope=[101],
        related_concepts=["concept.piety", "concept.origin_related_due"],
    ),
    concept(
        "concept.country",
        "Country",
        "object",
        aliases=["country", "patria", "fatherland"],
        description="The fatherland or country as an origin-context and object of piety after parents.",
        source_scope=[101],
        related_concepts=["concept.piety", "concept.origin_related_due"],
    ),
    concept(
        "concept.person_in_dignity_role",
        "Person in Dignity",
        "role",
        aliases=["person in dignity", "person in a position of dignity", "dignitary"],
        description="Role-level category for one who excels in dignity and governance.",
        source_scope=[102],
        related_concepts=["concept.observance", "concept.excellence_related_due"],
    ),
    concept(
        "concept.human_lord_role",
        "Human Lord Role",
        "role",
        aliases=["human lord", "master", "lord"],
        description="Role-level category for a created lord to whom due service is paid under dulia.",
        source_scope=[103],
        related_concepts=["concept.dulia", "concept.excellence_related_due"],
    ),
    concept(
        "concept.superior_role",
        "Superior Role",
        "role",
        aliases=["superior", "prelate", "ruler", "authority"],
        description="Role-level category for one who commands or governs others in due order.",
        source_scope=[104, 105],
        related_concepts=["concept.obedience", "concept.disobedience", "concept.authority_related_due"],
    ),
    concept(
        "concept.benefactor_role",
        "Benefactor Role",
        "role",
        aliases=["benefactor", "giver of a favor"],
        description="Role-level category for one from whom a recipient has received a benefit.",
        source_scope=[106, 107],
        related_concepts=["concept.gratitude", "concept.ingratitude", "concept.benefaction_related_due"],
    ),
    concept(
        "concept.wrongdoer_role",
        "Wrongdoer Role",
        "role",
        aliases=["wrongdoer", "offender", "sinner punished for fault"],
        description="Role-level category for one upon whom punishment may be imposed because of prior wrong.",
        source_scope=[108],
        related_concepts=["concept.vengeance", "concept.prior_wrong", "concept.rectificatory_due"],
    ),
]


DUE_MODE_CONCEPT_IDS = {
    "concept.origin_related_due",
    "concept.excellence_related_due",
    "concept.authority_related_due",
    "concept.benefaction_related_due",
    "concept.rectificatory_due",
}
ROLE_CONCEPT_IDS = {
    "concept.parent_role",
    "concept.person_in_dignity_role",
    "concept.human_lord_role",
    "concept.superior_role",
    "concept.benefactor_role",
    "concept.wrongdoer_role",
}
OWED_RELATION_ROLE_CONCEPT_IDS = ROLE_CONCEPT_IDS | {"concept.country"}


TRACT_CONCEPT_IDS = {
    payload["concept_id"] for payload in OWED_RELATION_TRACT_EXTRA_CONCEPTS
} | {
    "concept.justice",
    "concept.command",
}


def due_mode_name(value: PilotDueMode) -> str:
    return {
        "origin": "origin-related due",
        "excellence": "excellence-related due",
        "authority": "authority-related due",
        "benefaction": "benefaction-related due",
        "rectificatory": "rectificatory due",
    }[value]


def is_due_mode_relation(edge: dict[str, Any]) -> bool:
    return bool(edge.get("due_mode"))


def is_role_level_relation(edge: dict[str, Any]) -> bool:
    return str(edge.get("object_type")) == "role"


add_relation(
    101,
    3,
    "concept.piety",
    "annexed_to",
    "concept.justice",
    support_type="strong_textual_inference",
    confidence=0.88,
    rationale="Piety is treated as a special virtue rendering a specific kind of due under the general account of justice.",
    due_mode="origin",
    evidence_hints=("special aspect of something due", "piety is a special virtue"),
)
add_relation(
    101,
    1,
    "concept.piety",
    "concerns_due_to",
    "concept.origin_related_due",
    confidence=0.95,
    rationale="Piety concerns what is due to parents and country as proximate principles of being and government.",
    due_mode="origin",
    evidence_hints=("principles of our being and government", "debtor chiefly to his parents and his country"),
)
add_relation(
    101,
    3,
    "concept.piety",
    "concerns_due_to",
    "concept.origin_related_due",
    confidence=0.95,
    rationale="The respondeo defines piety through a special aspect of what is due to a connatural principle of being and government.",
    due_mode="origin",
    evidence_hints=("special aspect of something due", "principle of being and government"),
)
add_relation(
    101,
    1,
    "concept.piety",
    "owed_to_role",
    "concept.parent_role",
    confidence=0.95,
    rationale="Piety chiefly renders worship to parents after God.",
    due_mode="origin",
    evidence_hints=("debtor chiefly to his parents", "give worship to one's parents"),
)
add_relation(
    101,
    2,
    "concept.piety",
    "owed_to_role",
    "concept.parent_role",
    confidence=0.95,
    rationale="The son owes reverence and service to his father as principle of his being.",
    due_mode="origin",
    evidence_hints=("due to a father as such", "owes him reverence and service"),
)
add_relation(
    101,
    1,
    "concept.piety",
    "directed_to",
    "concept.country",
    confidence=0.94,
    rationale="Piety extends to country after parents as a proximate principle of nourishment and government.",
    due_mode="origin",
    evidence_hints=("our parents and our country", "give worship to one's parents and one's country"),
)
add_relation(
    101,
    2,
    "concept.piety",
    "has_act",
    "concept.honor",
    confidence=0.93,
    rationale="Piety gives homage, reverence, or honor to parents.",
    due_mode="origin",
    evidence_hints=("duty and homage", "reverence or honor"),
)
add_relation(
    101,
    2,
    "concept.piety",
    "has_act",
    "concept.service",
    confidence=0.93,
    rationale="Piety gives duty and service to parents, including support in need.",
    due_mode="origin",
    evidence_hints=("service due", "visit him and see to his cure", "support him"),
)

add_relation(
    102,
    1,
    "concept.observance",
    "annexed_to",
    "concept.justice",
    support_type="strong_textual_inference",
    confidence=0.88,
    rationale="Observance is presented as a special virtue of rendering due honor beneath piety within the justice tract.",
    due_mode="excellence",
    evidence_hints=("under piety we find observance",),
)
add_relation(
    102,
    1,
    "concept.observance",
    "concerns_due_to",
    "concept.excellence_related_due",
    confidence=0.95,
    rationale="Observance answers to what is due to persons excelling in dignity.",
    due_mode="excellence",
    evidence_hints=("various excellences", "persons in positions of dignity"),
)
add_relation(
    102,
    3,
    "concept.observance",
    "concerns_due_to",
    "concept.excellence_related_due",
    confidence=0.94,
    rationale="Observance is distinguished from piety by relation to persons in dignity rather than origin-principles.",
    due_mode="excellence",
    evidence_hints=("persons in positions of dignity", "external government"),
)
add_relation(
    102,
    1,
    "concept.observance",
    "owed_to_role",
    "concept.person_in_dignity_role",
    confidence=0.95,
    rationale="Observance pays worship and honor to persons in positions of dignity.",
    due_mode="excellence",
    evidence_hints=("persons in positions of dignity", "under piety we find observance"),
)
add_relation(
    102,
    2,
    "concept.observance",
    "has_act",
    "concept.honor",
    confidence=0.95,
    rationale="Honor is due to a person in dignity in respect of excellence.",
    due_mode="excellence",
    evidence_hints=("there is due to him honor", "recognition of some kind of excellence"),
)
add_relation(
    102,
    2,
    "concept.observance",
    "has_act",
    "concept.service",
    confidence=0.93,
    rationale="Observance includes worship and service rendered to the dignitary in the exercise of government.",
    due_mode="excellence",
    evidence_hints=("there is due to him worship", "rendering him service"),
)

add_relation(
    103,
    1,
    "concept.honor",
    "concerns_due_to",
    "concept.excellence_related_due",
    confidence=0.95,
    rationale="Honor witnesses to excellence and is due on account of superiority.",
    due_mode="excellence",
    evidence_hints=("witnessing to a person's excellence",),
)
add_relation(
    103,
    2,
    "concept.honor",
    "concerns_due_to",
    "concept.excellence_related_due",
    confidence=0.95,
    rationale="Honor is always due on account of some excellence or superiority.",
    due_mode="excellence",
    evidence_hints=("honor is always due to a person", "some excellence or superiority"),
)
add_relation(
    103,
    3,
    "concept.dulia",
    "species_of",
    "concept.observance",
    confidence=0.96,
    rationale="Dulia is explicitly said to be a species of observance.",
    due_mode="excellence",
    evidence_hints=("It is, moreover, a species of observance",),
)
add_relation(
    103,
    3,
    "concept.dulia",
    "concerns_due_to",
    "concept.excellence_related_due",
    confidence=0.94,
    rationale="Dulia renders due service to a created lord under a specifically human aspect of superiority.",
    due_mode="excellence",
    evidence_hints=("due service to a human lord", "different aspects of that which is due"),
)
add_relation(
    103,
    4,
    "concept.dulia",
    "concerns_due_to",
    "concept.excellence_related_due",
    confidence=0.92,
    rationale="Strict dulia concerns reverence paid to a lord under a created mode of excellence and servitude.",
    due_mode="excellence",
    evidence_hints=("reverence of a servant for his lord",),
)
add_relation(
    103,
    3,
    "concept.dulia",
    "owed_to_role",
    "concept.human_lord_role",
    confidence=0.95,
    rationale="Dulia pays due service to a human lord.",
    due_mode="excellence",
    evidence_hints=("due service to a human lord",),
)
add_relation(
    103,
    4,
    "concept.dulia",
    "owed_to_role",
    "concept.human_lord_role",
    confidence=0.93,
    rationale="Strict dulia denotes the reverence of a servant for his lord.",
    due_mode="excellence",
    evidence_hints=("reverence of a servant for his lord",),
)
add_relation(
    103,
    3,
    "concept.dulia",
    "has_act",
    "concept.service",
    confidence=0.93,
    rationale="Dulia is characterized by due service rendered to a human lord.",
    due_mode="excellence",
    evidence_hints=("pays due service to a human lord",),
)

add_relation(
    104,
    2,
    "concept.obedience",
    "annexed_to",
    "concept.justice",
    support_type="strong_textual_inference",
    confidence=0.87,
    rationale="Obedience is treated as a special moral virtue rendering what is due according to divinely ordered command.",
    due_mode="authority",
    evidence_hints=("obedience is a special virtue", "due in accordance with the divinely established order"),
)
add_relation(
    104,
    1,
    "concept.obedience",
    "concerns_due_to",
    "concept.authority_related_due",
    confidence=0.95,
    rationale="Obedience concerns what inferiors owe to superiors under divinely established authority.",
    due_mode="authority",
    evidence_hints=("divinely established authority", "inferiors are bound to obey their superiors"),
)
add_relation(
    104,
    2,
    "concept.obedience",
    "concerns_due_to",
    "concept.authority_related_due",
    confidence=0.94,
    rationale="Obedience is praised through its specific object of command owed to a superior.",
    due_mode="authority",
    evidence_hints=("obedience to a superior is due", "specific object is a command"),
)
add_relation(
    104,
    1,
    "concept.obedience",
    "owed_to_role",
    "concept.superior_role",
    confidence=0.95,
    rationale="Inferiors are bound to obey their superiors.",
    due_mode="authority",
    evidence_hints=("inferiors are bound to obey their superiors",),
)
add_relation(
    104,
    5,
    "concept.obedience",
    "owed_to_role",
    "concept.superior_role",
    confidence=0.93,
    rationale="A subject is bound to obey a superior within the superior's proper sphere and under higher command.",
    due_mode="authority",
    evidence_hints=("a subject may not be bound to obey his superior in all things", "a subject is not bound to obey his superior"),
)
add_relation(
    104,
    2,
    "concept.obedience",
    "responds_to_command",
    "concept.command",
    confidence=0.96,
    rationale="The specific object of obedience is a command, tacit or express.",
    due_mode="authority",
    evidence_hints=("its specific object is a command tacit or express",),
)
add_relation(
    104,
    4,
    "concept.obedience",
    "responds_to_command",
    "concept.command",
    confidence=0.94,
    rationale="All wills are bound to obey the divine command under necessity of justice.",
    due_mode="authority",
    evidence_hints=("bound to obey the divine command",),
)

add_relation(
    105,
    1,
    "concept.disobedience",
    "concerns_due_to",
    "concept.authority_related_due",
    confidence=0.93,
    rationale="Disobedience concerns a failure in the obedience due to God and to superiors.",
    due_mode="authority",
    evidence_hints=("disobedient to the commandments", "obedience that is his due"),
)
add_relation(
    105,
    1,
    "concept.disobedience",
    "contrary_to",
    "concept.obedience",
    confidence=0.95,
    rationale="Disobedience is treated as contrary to the obedience due under divine and superior command.",
    due_mode="authority",
    evidence_hints=("disobedient", "obedience that is his due"),
)
add_relation(
    105,
    2,
    "concept.disobedience",
    "contrary_to",
    "concept.obedience",
    confidence=0.93,
    rationale="The gravity of disobedience is measured by the superior commanding and by what is commanded, presupposing the contrary virtue of obedience.",
    due_mode="authority",
    evidence_hints=("the greater duty to obey", "the various degrees of disobedience"),
)
add_relation(
    105,
    1,
    "concept.disobedience",
    "owed_to_role",
    "concept.superior_role",
    confidence=0.92,
    rationale="Disobedience withdraws from the superior the obedience that is his due.",
    due_mode="authority",
    evidence_hints=("withdraws from the superior", "obedience that is his due"),
)
add_relation(
    105,
    1,
    "concept.disobedience",
    "responds_to_command",
    "concept.command",
    confidence=0.92,
    rationale="Disobedience is described through refusal of the commandments of God and of a superior.",
    due_mode="authority",
    evidence_hints=("commandments of God", "commands of a superior"),
)

add_relation(
    106,
    1,
    "concept.gratitude",
    "annexed_to",
    "concept.justice",
    support_type="strong_textual_inference",
    confidence=0.88,
    rationale="Gratitude is presented as a distinct virtue of moral debt after religion, piety, and observance within the justice tract.",
    due_mode="benefaction",
    evidence_hints=("there is thankfulness or gratitude", "distinct from the foregoing virtues"),
)
add_relation(
    106,
    1,
    "concept.gratitude",
    "concerns_due_to",
    "concept.benefaction_related_due",
    confidence=0.95,
    rationale="Gratitude concerns the distinct debt arising from a private favor received from a benefactor.",
    due_mode="benefaction",
    evidence_hints=("found in a benefactor", "particular obligation to him"),
)
add_relation(
    106,
    3,
    "concept.gratitude",
    "concerns_due_to",
    "concept.benefaction_related_due",
    confidence=0.93,
    rationale="The beneficiary must turn to his benefactor by repaying the favor according to mode.",
    due_mode="benefaction",
    evidence_hints=("received a favor", "repaying the favor"),
)
add_relation(
    106,
    1,
    "concept.gratitude",
    "owed_to_role",
    "concept.benefactor_role",
    confidence=0.95,
    rationale="Gratitude gives thanks to a benefactor from whom one has received a private favor.",
    due_mode="benefaction",
    evidence_hints=("benefactor", "private favors"),
)
add_relation(
    106,
    3,
    "concept.gratitude",
    "owed_to_role",
    "concept.benefactor_role",
    confidence=0.93,
    rationale="The beneficiary must turn back to his benefactor according to the mode of each favor received.",
    due_mode="benefaction",
    evidence_hints=("turn to his benefactor",),
)
add_relation(
    106,
    1,
    "concept.gratitude",
    "responds_to_benefaction",
    "concept.benefaction",
    confidence=0.95,
    rationale="Gratitude is distinct because it responds to particular favors from a benefactor.",
    due_mode="benefaction",
    evidence_hints=("particular and private favors",),
)
add_relation(
    106,
    3,
    "concept.gratitude",
    "responds_to_benefaction",
    "concept.benefaction",
    confidence=0.94,
    rationale="The natural order requires repayment of the favor received from a benefactor.",
    due_mode="benefaction",
    evidence_hints=("received a favor", "repaying the favor"),
)
add_relation(
    106,
    5,
    "concept.gratitude",
    "responds_to_benefaction",
    "concept.benefaction",
    confidence=0.93,
    rationale="Gratitude judges repayment according to the gratuitous favor bestowed by the giver.",
    due_mode="benefaction",
    evidence_hints=("repayment of a favor belongs", "gratitude regards the favor"),
)
add_relation(
    106,
    3,
    "concept.gratitude",
    "has_act",
    "concept.honor",
    confidence=0.91,
    rationale="A beneficiary owes honor and reverence to his benefactor as principle in that order.",
    due_mode="benefaction",
    evidence_hints=("owes his benefactor", "honor and reverence"),
)

add_relation(
    107,
    1,
    "concept.ingratitude",
    "concerns_due_to",
    "concept.benefaction_related_due",
    confidence=0.93,
    rationale="Ingratitude is a sin because it is contrary to the debt of gratitude required by virtue.",
    due_mode="benefaction",
    evidence_hints=("debt of gratitude", "every ingratitude is a sin"),
)
add_relation(
    107,
    2,
    "concept.ingratitude",
    "concerns_due_to",
    "concept.benefaction_related_due",
    confidence=0.94,
    rationale="Ingratitude is denominated from deficiency in gratitude and its required repayment.",
    due_mode="benefaction",
    evidence_hints=("deficiency of gratitude",),
)
add_relation(
    107,
    1,
    "concept.ingratitude",
    "contrary_to",
    "concept.gratitude",
    confidence=0.95,
    rationale="Every ingratitude is contrary to the virtue of gratitude.",
    due_mode="benefaction",
    evidence_hints=("every ingratitude is a sin", "debt of gratitude"),
)
add_relation(
    107,
    2,
    "concept.ingratitude",
    "contrary_to",
    "concept.gratitude",
    confidence=0.95,
    rationale="Ingratitude is properly denominated from deficiency of gratitude and is a special sin corresponding to the special virtue.",
    due_mode="benefaction",
    evidence_hints=("ingratitude is properly denominated from being a deficiency of gratitude", "gratitude or thankfulness is one special virtue"),
)
add_relation(
    107,
    2,
    "concept.ingratitude",
    "responds_to_benefaction",
    "concept.benefaction",
    confidence=0.92,
    rationale="Ingratitude concerns failure to recognize, thank for, or repay a favor.",
    due_mode="benefaction",
    evidence_hints=("recognize the favor received", "repay the favor"),
)
add_relation(
    107,
    4,
    "concept.ingratitude",
    "owed_to_role",
    "concept.benefactor_role",
    confidence=0.9,
    rationale="The question on withdrawing favors presupposes the relation to a benefactor dealing with an ungrateful recipient.",
    due_mode="benefaction",
    evidence_hints=("benefactor", "bestowing his favors upon him"),
)

add_relation(
    108,
    2,
    "concept.vengeance",
    "annexed_to",
    "concept.justice",
    support_type="strong_textual_inference",
    confidence=0.87,
    rationale="Vengeance is treated as a special virtue corresponding to due rectificatory response within the justice tract.",
    due_mode="rectificatory",
    evidence_hints=("vengeance is a special virtue", "natural right"),
)
add_relation(
    108,
    1,
    "concept.vengeance",
    "concerns_due_to",
    "concept.rectificatory_due",
    confidence=0.94,
    rationale="Vengeance concerns the due response to prior wrong by penal correction ordered to good.",
    due_mode="rectificatory",
    evidence_hints=("infliction of a penal evil", "vengeance may be lawful"),
)
add_relation(
    108,
    2,
    "concept.vengeance",
    "concerns_due_to",
    "concept.rectificatory_due",
    confidence=0.94,
    rationale="Vengeance answers a special natural inclination to remove harm already inflicted.",
    due_mode="rectificatory",
    evidence_hints=("avenges those which have already been inflicted",),
)
add_relation(
    108,
    1,
    "concept.vengeance",
    "rectifies_wrong",
    "concept.prior_wrong",
    confidence=0.95,
    rationale="Lawful vengeance addresses one who has sinned and orders punishment to good.",
    due_mode="rectificatory",
    evidence_hints=("one who has sinned", "punishment of the person who has sinned"),
)
add_relation(
    108,
    2,
    "concept.vengeance",
    "rectifies_wrong",
    "concept.prior_wrong",
    confidence=0.94,
    rationale="Vengeance resists or avenges wrong already inflicted with intent to remove the harm done.",
    due_mode="rectificatory",
    evidence_hints=("wrongs which have already been inflicted", "removing the harm done"),
)
add_relation(
    108,
    4,
    "concept.vengeance",
    "rectifies_wrong",
    "concept.prior_wrong",
    confidence=0.93,
    rationale="Punishment, as punishment, is due only for sin and restores equality of justice after prior wrongdoing.",
    due_mode="rectificatory",
    evidence_hints=("punishment is not due save for sin", "equality of justice is restored"),
)
add_relation(
    108,
    1,
    "concept.vengeance",
    "directed_to",
    "concept.rectification",
    confidence=0.92,
    rationale="Lawful vengeance aims at amendment, restraint, the upholding of justice, and divine honor.",
    due_mode="rectificatory",
    evidence_hints=("that the sinner may amend", "that justice may be upheld"),
)
add_relation(
    108,
    4,
    "concept.vengeance",
    "directed_to",
    "concept.rectification",
    confidence=0.92,
    rationale="Punishment restores equality of justice and can act medicinally toward future good.",
    due_mode="rectificatory",
    evidence_hints=("equality of justice is restored", "a medicine"),
)
add_relation(
    108,
    1,
    "concept.vengeance",
    "has_act",
    "concept.punishment",
    confidence=0.94,
    rationale="Vengeance consists in the infliction of penal evil on one who has sinned.",
    due_mode="rectificatory",
    evidence_hints=("Vengeance consists in the infliction of a penal evil",),
)
add_relation(
    108,
    4,
    "concept.vengeance",
    "has_act",
    "concept.punishment",
    confidence=0.92,
    rationale="The tract treats punishment as the operative means by which equality is restored or medicine applied.",
    due_mode="rectificatory",
    evidence_hints=("Punishment may be considered",),
)

QUESTION_TREATMENTS: dict[int, tuple[str, ...]] = {
    101: (
        "concept.piety",
        "concept.parent_role",
        "concept.country",
        "concept.origin_related_due",
    ),
    102: (
        "concept.observance",
        "concept.person_in_dignity_role",
        "concept.excellence_related_due",
        "concept.honor",
    ),
    103: (
        "concept.dulia",
        "concept.observance",
        "concept.human_lord_role",
        "concept.honor",
    ),
    104: (
        "concept.obedience",
        "concept.superior_role",
        "concept.authority_related_due",
        "concept.command",
    ),
    105: (
        "concept.disobedience",
        "concept.obedience",
        "concept.superior_role",
        "concept.authority_related_due",
    ),
    106: (
        "concept.gratitude",
        "concept.benefactor_role",
        "concept.benefaction",
        "concept.benefaction_related_due",
    ),
    107: (
        "concept.ingratitude",
        "concept.gratitude",
        "concept.benefaction",
        "concept.benefaction_related_due",
    ),
    108: (
        "concept.vengeance",
        "concept.prior_wrong",
        "concept.punishment",
        "concept.rectification",
        "concept.rectificatory_due",
    ),
}

ARTICLE_TREATMENTS: dict[tuple[int, int], tuple[str, ...]] = {
    (101, 1): ("concept.piety", "concept.parent_role", "concept.country"),
    (101, 2): ("concept.piety", "concept.honor", "concept.service"),
    (101, 3): ("concept.piety", "concept.origin_related_due"),
    (101, 4): ("concept.piety",),
    (102, 1): ("concept.observance", "concept.person_in_dignity_role"),
    (102, 2): ("concept.observance", "concept.honor", "concept.service"),
    (102, 3): ("concept.observance", "concept.piety", "concept.person_in_dignity_role"),
    (103, 1): ("concept.honor", "concept.excellence_related_due"),
    (103, 2): ("concept.honor", "concept.excellence_related_due"),
    (103, 3): ("concept.dulia", "concept.observance", "concept.human_lord_role"),
    (103, 4): ("concept.dulia", "concept.observance", "concept.human_lord_role"),
    (104, 1): ("concept.obedience", "concept.superior_role"),
    (104, 2): ("concept.obedience", "concept.command", "concept.authority_related_due"),
    (104, 3): ("concept.obedience",),
    (104, 4): ("concept.obedience", "concept.command"),
    (104, 5): ("concept.obedience", "concept.superior_role", "concept.command"),
    (104, 6): ("concept.obedience", "concept.superior_role"),
    (105, 1): ("concept.disobedience", "concept.obedience", "concept.superior_role"),
    (105, 2): ("concept.disobedience", "concept.command"),
    (106, 1): ("concept.gratitude", "concept.benefactor_role", "concept.benefaction"),
    (106, 2): ("concept.gratitude", "concept.benefaction"),
    (106, 3): ("concept.gratitude", "concept.benefactor_role", "concept.honor"),
    (106, 4): ("concept.gratitude",),
    (106, 5): ("concept.gratitude", "concept.benefaction"),
    (106, 6): ("concept.gratitude", "concept.benefaction"),
    (107, 1): ("concept.ingratitude", "concept.gratitude"),
    (107, 2): ("concept.ingratitude", "concept.gratitude", "concept.benefaction"),
    (107, 3): ("concept.ingratitude",),
    (107, 4): ("concept.ingratitude", "concept.benefactor_role"),
    (108, 1): ("concept.vengeance", "concept.punishment", "concept.rectification"),
    (108, 2): ("concept.vengeance", "concept.prior_wrong", "concept.rectificatory_due"),
    (108, 3): ("concept.vengeance", "concept.punishment"),
    (108, 4): ("concept.vengeance", "concept.punishment", "concept.prior_wrong"),
}


for question_number, concept_ids in QUESTION_TREATMENTS.items():
    for concept_id in concept_ids:
        add_question_treatment(
            question_number,
            concept_id,
            rationale=f"Question {question_number} is structurally centered on {concept_id.split('concept.', 1)[1].replace('_', ' ')} within the owed-relation tract.",
        )


for (question_number, article_number), concept_ids in ARTICLE_TREATMENTS.items():
    for concept_id in concept_ids:
        add_article_treatment(
            question_number,
            article_number,
            concept_id,
            rationale=f"Article {article_number} in question {question_number} directly treats {concept_id.split('concept.', 1)[1].replace('_', ' ')} in the owed-relation tract.",
        )
