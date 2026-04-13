# ruff: noqa: E501

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from ..models import PilotRelationType, PilotSupportType
from ..models.fortitude_closure_136_140 import FortitudeClosure136140Focus

FORTITUDE_CLOSURE_136_140_MIN_QUESTION = 136
FORTITUDE_CLOSURE_136_140_MAX_QUESTION = 140


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


def closure_focus_name(value: FortitudeClosure136140Focus) -> str:
    return {
        "patience": "patience",
        "perseverance": "perseverance",
        "opposed_vice": "opposed vice",
        "gift": "gift",
        "precept": "precept",
        "synthesis": "fortitude synthesis",
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

FORTITUDE_CLOSURE_RELATION_TYPES: set[PilotRelationType] = {
    "part_of_fortitude",
    "corresponding_gift_of",
    "precept_of",
    "commands_act_of",
    "forbids_opposed_vice_of",
}
PATIENCE_RELATION_TYPES: set[PilotRelationType] = {
    "part_of_fortitude",
    "part_of",
    "caused_by",
    "requires",
    "has_object",
    "species_of",
}
PERSEVERANCE_RELATION_TYPES: set[PilotRelationType] = {
    "part_of_fortitude",
    "part_of",
    "requires",
    "directed_to",
    "species_of",
}
GIFT_RELATION_TYPES: set[PilotRelationType] = {
    "corresponding_gift_of",
    "perfected_by",
    "regulated_by",
    "corresponds_to",
}
PRECEPT_RELATION_TYPES: set[PilotRelationType] = {
    "precept_of",
    "commands_act_of",
    "forbids_opposed_vice_of",
}
OPPOSED_VICE_RELATION_TYPES: set[PilotRelationType] = {
    "deficiency_opposed_to",
    "excess_opposed_to",
    "contrary_to",
    "caused_by",
}

PATIENCE_CONCEPT_IDS: set[str] = {
    "concept.patience",
    "concept.longanimity_fortitude",
    "concept.grievous_evil",
}
PERSEVERANCE_CONCEPT_IDS: set[str] = {
    "concept.perseverance_virtue",
    "concept.constancy_fortitude",
    "concept.continuance_in_good",
}
OPPOSED_VICE_CONCEPT_IDS: set[str] = {
    "concept.effeminacy_perseverance",
    "concept.pertinacity_perseverance",
}
GIFT_CONCEPT_IDS: set[str] = {
    "concept.fortitude_gift",
    "concept.counsel_gift",
    "concept.beatitude_hunger_for_justice",
    "concept.arduous_work",
}
PRECEPT_CONCEPT_IDS: set[str] = {
    "concept.precepts_of_fortitude",
    "concept.precepts_of_fortitude_parts",
    "concept.god",
}


def focus_tags_for_edge(
    subject_id: str,
    relation_type: PilotRelationType,
    object_id: str,
) -> list[FortitudeClosure136140Focus]:
    tags: set[FortitudeClosure136140Focus] = set()
    if (
        relation_type in PATIENCE_RELATION_TYPES
        and (
            subject_id in PATIENCE_CONCEPT_IDS
            or object_id in PATIENCE_CONCEPT_IDS
            or object_id == "concept.patience"
        )
    ) or subject_id in PATIENCE_CONCEPT_IDS or object_id in PATIENCE_CONCEPT_IDS:
        tags.add("patience")
    if (
        relation_type in PERSEVERANCE_RELATION_TYPES
        and (
            subject_id in PERSEVERANCE_CONCEPT_IDS
            or object_id in PERSEVERANCE_CONCEPT_IDS
            or object_id == "concept.perseverance_virtue"
        )
    ) or subject_id in PERSEVERANCE_CONCEPT_IDS or object_id in PERSEVERANCE_CONCEPT_IDS:
        tags.add("perseverance")
    if (
        subject_id in OPPOSED_VICE_CONCEPT_IDS
        or object_id in OPPOSED_VICE_CONCEPT_IDS
        or (
            relation_type in OPPOSED_VICE_RELATION_TYPES
            and {subject_id, object_id}.intersection(OPPOSED_VICE_CONCEPT_IDS)
        )
    ):
        tags.add("opposed_vice")
    if (
        relation_type in GIFT_RELATION_TYPES
        or subject_id in GIFT_CONCEPT_IDS
        or object_id in GIFT_CONCEPT_IDS
    ):
        tags.add("gift")
    if (
        relation_type in PRECEPT_RELATION_TYPES
        or subject_id in PRECEPT_CONCEPT_IDS
        or object_id in PRECEPT_CONCEPT_IDS
    ):
        tags.add("precept")
    return sorted(tags)


def add_relation(
    source_passage_id: str,
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
            source_passage_id=source_passage_id,
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
    source_passage_id: str | None = None,
    support_type: PilotSupportType = "structural_editorial",
    confidence: float = 0.9,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    TREATMENT_SEEDS.append(
        TreatmentSeed(
            source_passage_id=source_passage_id or segment_id(question_number, 1, "resp"),
            subject_id=question_id(question_number),
            concept_id=concept_id,
            support_type=support_type,
            confidence=confidence,
            rationale=rationale,
            evidence_hints=evidence_hints,
        )
    )


def add_article_treatment(
    source_passage_id: str,
    concept_id: str,
    *,
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.92,
    rationale: str,
    evidence_hints: tuple[str, ...] = (),
) -> None:
    article_bits = source_passage_id.split(".")[:4]
    TREATMENT_SEEDS.append(
        TreatmentSeed(
            source_passage_id=source_passage_id,
            subject_id=".".join(article_bits),
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


FORTITUDE_CLOSURE_136_140_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    concept(
        "concept.patience",
        "Patience",
        "virtue",
        aliases=["patience"],
        description="The annexed virtue by which one bears grievous evils with an equal mind for the sake of good.",
        notes=["Keep distinct from fruit-level patience in later correspondence work."],
        source_scope=[136, 140],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Do not reduce patience to mere absence of anger.",
            "Do not merge patience with perseverance or with the fruit-level use of patience."
        ],
        related_concepts=[
            "concept.fortitude",
            "concept.longanimity_fortitude",
            "concept.constancy_fortitude",
        ],
    ),
    concept(
        "concept.longanimity_fortitude",
        "Longanimity",
        "habit",
        aliases=["longanimity"],
        description="The habit of tending toward a good that lies far off, compared with patience without being simply identical to it.",
        notes=[
            "Kept tract-local because q.136 explicitly resists collapsing longanimity into patience."
        ],
        source_scope=[136, 139],
        disambiguation_notes=[
            "Do not silently merge longanimity with patience merely because q.136 says it can be comprised under patience under one aspect."
        ],
        related_concepts=["concept.patience", "concept.magnanimity"],
    ),
    concept(
        "concept.grievous_evil",
        "Grievous Evil / Hardship",
        "domain",
        aliases=["grievous evil", "hardship", "toil and pain"],
        description="The difficult evil or sorrow endured by patience and, analogously, by fortitude.",
        notes=[],
        source_scope=[136, 139],
        disambiguation_notes=[],
        related_concepts=["concept.patience", "concept.fortitude"],
    ),
    concept(
        "concept.perseverance_virtue",
        "Perseverance (Fortitude Part)",
        "virtue",
        aliases=["virtue of perseverance", "perseverance as part of fortitude"],
        description="The virtue by which one persists long in a good work despite the difficulty arising from its continuance.",
        notes=[
            "This tract-local concept is kept distinct from the broader act-level `concept.perseverance` already present from the I-II grace pilot."
        ],
        source_scope=[137, 138, 140],
        parent_concept_id="concept.virtue",
        disambiguation_notes=[
            "Do not silently merge this virtue-level perseverance with the earlier act-level `concept.perseverance` registry node."
        ],
        related_concepts=["concept.fortitude", "concept.constancy_fortitude"],
    ),
    concept(
        "concept.constancy_fortitude",
        "Constancy",
        "habit",
        aliases=["constancy"],
        description="The fortitude-related habit of persisting in good against external hindrances rather than the mere duration of the act.",
        notes=[
            "Kept distinct from perseverance even though q.137 closely compares the two."
        ],
        source_scope=[136, 137],
        disambiguation_notes=[
            "Do not merge constancy with perseverance; q.137 explicitly distinguishes them by their difficult matter."
        ],
        related_concepts=["concept.perseverance_virtue", "concept.patience"],
    ),
    concept(
        "concept.continuance_in_good",
        "Continuance in Good",
        "act_type",
        aliases=["persisting in good", "continuance in good", "persistence in good"],
        description="The continued accomplishment of a good work over time that is distinctive of perseverance.",
        notes=[],
        source_scope=[137],
        disambiguation_notes=[],
        related_concepts=["concept.perseverance_virtue"],
    ),
    concept(
        "concept.effeminacy_perseverance",
        "Effeminacy",
        "vice",
        aliases=["effeminacy"],
        description="The vice by which one forsakes a good on account of difficulties that cannot be endured, especially through softness regarding pleasure.",
        notes=[],
        source_scope=[138],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Keep distinct from merely modern gendered language; this tract uses the vice label in a technical moral sense."
        ],
        related_concepts=["concept.perseverance_virtue", "concept.pertinacity_perseverance"],
    ),
    concept(
        "concept.pertinacity_perseverance",
        "Pertinacity",
        "vice",
        aliases=["pertinacity", "self-opinionated persistence", "head-strong persistence"],
        description="The vice by which one persists more than one ought, exceeding the mean of perseverance.",
        notes=[],
        source_scope=[138],
        parent_concept_id="concept.vice",
        disambiguation_notes=[
            "Do not flatten pertinacity into simple steadfastness; q.138 treats it as exceeding the mean."
        ],
        related_concepts=["concept.perseverance_virtue", "concept.effeminacy_perseverance"],
    ),
    concept(
        "concept.arduous_work",
        "Arduous / Difficult Work",
        "act_type",
        aliases=["difficult work", "arduous work", "arduous good"],
        description="The difficult good work whose completion and endurance are explicitly attached to fortitude and the gift of fortitude.",
        notes=[],
        source_scope=[139],
        disambiguation_notes=[],
        related_concepts=["concept.fortitude", "concept.fortitude_gift"],
    ),
    concept(
        "concept.precepts_of_fortitude",
        "Precepts of Fortitude",
        "precept",
        aliases=["precepts of fortitude"],
        description="The precept-complex by which Divine Law directs fortitude itself toward adherence to God and brave endurance.",
        notes=[],
        source_scope=[140],
        parent_concept_id="concept.precept",
        disambiguation_notes=[
            "Keep distinct from precepts concerning patience and perseverance."
        ],
        related_concepts=["concept.fortitude", "concept.god"],
    ),
    concept(
        "concept.precepts_of_fortitude_parts",
        "Precepts of Patience and Perseverance",
        "precept",
        aliases=["precepts of patience and perseverance", "precepts of fortitude's parts"],
        description="The precept-complex by which Divine Law gives directions concerning patience and perseverance as annexed virtues.",
        notes=[],
        source_scope=[140],
        parent_concept_id="concept.precept",
        disambiguation_notes=[
            "Do not auto-expand this node into separate fully reviewed patience and perseverance precept clusters beyond what q.140 supports."
        ],
        related_concepts=["concept.patience", "concept.perseverance_virtue", "concept.fortitude"],
    ),
]


TRACT_CONCEPT_IDS: set[str] = {
    "concept.patience",
    "concept.longanimity_fortitude",
    "concept.grievous_evil",
    "concept.perseverance_virtue",
    "concept.constancy_fortitude",
    "concept.continuance_in_good",
    "concept.effeminacy_perseverance",
    "concept.pertinacity_perseverance",
    "concept.arduous_work",
    "concept.precepts_of_fortitude",
    "concept.precepts_of_fortitude_parts",
    "concept.fortitude",
    "concept.fortitude_gift",
    "concept.counsel_gift",
    "concept.beatitude_hunger_for_justice",
    "concept.charity",
    "concept.grace",
    "concept.god",
    "concept.virtue",
    "concept.vice",
    "concept.sin",
    "concept.magnanimity",
    "concept.magnificence",
    "concept.vainglory",
}


# Question-level treatment correspondences
for question_number, concept_id, source_passage_id, rationale, hints in (
    (136, "concept.patience", segment_id(136, 1, "resp"), "Question 136 treats patience throughout.", ("patience is a virtue", "patience")),
    (136, "concept.longanimity_fortitude", segment_id(136, 5, "resp"), "Question 136 explicitly compares patience with longanimity.", ("longanimity",)),
    (137, "concept.perseverance_virtue", segment_id(137, 1, "resp"), "Question 137 treats perseverance as a fortitude-part virtue.", ("perseverance is a special virtue",)),
    (137, "concept.constancy_fortitude", segment_id(137, 3, "resp"), "Question 137 explicitly compares perseverance and constancy.", ("perseverance and constancy", "constancy")),
    (138, "concept.effeminacy_perseverance", segment_id(138, 1, "resp"), "Question 138 treats effeminacy among the vices opposed to perseverance.", ("effeminacy",)),
    (138, "concept.pertinacity_perseverance", segment_id(138, 2, "resp"), "Question 138 treats pertinacity among the vices opposed to perseverance.", ("pertinacity",)),
    (138, "concept.perseverance_virtue", segment_id(138, 1, "resp"), "Question 138 measures opposed vices against perseverance.", ("perseverance",)),
    (139, "concept.fortitude_gift", segment_id(139, 1, "resp"), "Question 139 treats the gift of fortitude.", ("gift of the Holy Ghost", "fortitude is reckoned a gift")),
    (139, "concept.fortitude", segment_id(139, 1, "resp"), "Question 139 compares the gift of fortitude with the virtue of fortitude.", ("fortitude denotes",)),
    (139, "concept.counsel_gift", segment_id(139, 1, "ad", 3), "Question 139 explicitly directs the gift of fortitude by counsel.", ("directed by the gift of counsel",)),
    (139, "concept.beatitude_hunger_for_justice", segment_id(139, 2, "resp"), "Question 139 explicitly assigns the hunger-and-thirst beatitude to fortitude.", ("hunger and thirst for justice",)),
    (140, "concept.precepts_of_fortitude", segment_id(140, 1, "resp"), "Question 140 article 1 treats the precepts of fortitude itself.", ("precepts of fortitude",)),
    (140, "concept.precepts_of_fortitude_parts", segment_id(140, 2, "resp"), "Question 140 article 2 treats the precepts of patience and perseverance as parts of fortitude.", ("acts of the secondary and annexed virtues",)),
    (140, "concept.patience", segment_id(140, 2, "ad", 1), "Question 140 explicitly says there is need of precepts about patience.", ("precepts of patience",)),
    (140, "concept.perseverance_virtue", segment_id(140, 2, "ad", 1), "Question 140 explicitly says there is need of precepts about perseverance.", ("precepts of patience and perseverance",)),
):
    add_question_treatment(
        question_number,
        concept_id,
        source_passage_id=source_passage_id,
        rationale=rationale,
        evidence_hints=hints,
    )


# Article-level treatment correspondences
for source_passage_id, concept_id, rationale, hints in (
    (segment_id(136, 1, "resp"), "concept.patience", "Article 1 explicitly argues that patience is a virtue.", ("patience is a virtue",)),
    (segment_id(136, 1, "resp"), "concept.grievous_evil", "Article 1 explicitly sets patience against sorrow and hard evil.", ("sorrow is strong to hinder", "bears evil with an equal mind")),
    (segment_id(136, 2, "resp"), "concept.patience", "Article 2 continues the question of patience among the virtues.", ("patience",)),
    (segment_id(136, 3, "resp"), "concept.patience", "Article 3 explicitly treats whether patience can be had without grace.", ("impossible to have patience without the help of grace",)),
    (segment_id(136, 3, "resp"), "concept.charity", "Article 3 explicitly causes patience by charity.", ("patience, as a virtue , is caused by charity",)),
    (segment_id(136, 3, "resp"), "concept.grace", "Article 3 explicitly says patience cannot be had without grace.", ("without the help of grace",)),
    (segment_id(136, 4, "resp"), "concept.patience", "Article 4 explicitly asks whether patience is part of fortitude.", ("patience is a quasi-potential part of fortitude",)),
    (segment_id(136, 4, "resp"), "concept.fortitude", "Article 4 explicitly annexes patience to fortitude.", ("annexed to fortitude", "part of fortitude")),
    (segment_id(136, 5, "resp"), "concept.longanimity_fortitude", "Article 5 explicitly compares longanimity with patience.", ("longanimity",)),
    (segment_id(136, 5, "resp"), "concept.constancy_fortitude", "Article 5 explicitly says constancy can be comprised under patience under a certain aspect.", ("constancy", "comprised under patience")),
    (segment_id(136, 5, "resp"), "concept.patience", "Article 5 clarifies patience's relation to longanimity and constancy.", ("patience", "comprised under patience")),
    (segment_id(137, 1, "resp"), "concept.perseverance_virtue", "Article 1 explicitly argues that perseverance is a special virtue.", ("perseverance is a special virtue",)),
    (segment_id(137, 1, "resp"), "concept.continuance_in_good", "Article 1 explicitly describes perseverance as persisting long in good.", ("persist long in something good",)),
    (segment_id(137, 2, "resp"), "concept.perseverance_virtue", "Article 2 explicitly asks whether perseverance is a part of fortitude.", ("perseverance is annexed to fortitude",)),
    (segment_id(137, 2, "resp"), "concept.fortitude", "Article 2 explicitly annexes perseverance to fortitude.", ("annexed to fortitude",)),
    (segment_id(137, 3, "resp"), "concept.perseverance_virtue", "Article 3 explicitly compares perseverance and constancy.", ("perseverance and constancy",)),
    (segment_id(137, 3, "resp"), "concept.constancy_fortitude", "Article 3 explicitly compares constancy with perseverance as a fortitude part.", ("constancy",)),
    (segment_id(137, 4, "resp"), "concept.perseverance_virtue", "Article 4 explicitly treats perseverance in relation to grace.", ("habit of perseverance", "needs the gift of habitual grace")),
    (segment_id(137, 4, "resp"), "concept.grace", "Article 4 explicitly says perseverance as virtue needs grace.", ("needs the gift of habitual grace",)),
    (segment_id(138, 1, "resp"), "concept.effeminacy_perseverance", "Article 1 explicitly defines effeminacy against perseverance.", ("effeminacy",)),
    (segment_id(138, 1, "resp"), "concept.perseverance_virtue", "Article 1 explicitly opposes effeminacy to perseverance.", ("persevering man is opposed to the effeminate",)),
    (segment_id(138, 2, "resp"), "concept.pertinacity_perseverance", "Article 2 explicitly defines pertinacity against perseverance.", ("pertinacity",)),
    (segment_id(138, 2, "resp"), "concept.perseverance_virtue", "Article 2 explicitly opposes pertinacity to perseverance.", ("pertinacity is opposed to perseverance",)),
    (segment_id(138, 2, "ad", 1), "concept.vainglory", "Article 2 reply 1 explicitly says vainglory causes pertinacity.", ("result of vainglory as its cause",)),
    (segment_id(139, 1, "resp"), "concept.fortitude_gift", "Article 1 explicitly argues that fortitude is a gift.", ("fortitude is reckoned a gift",)),
    (segment_id(139, 1, "resp"), "concept.fortitude", "Article 1 explicitly compares the gift and virtue of fortitude.", ("fortitude denotes a certain firmness of mind",)),
    (segment_id(139, 1, "ad", 3), "concept.counsel_gift", "Article 1 reply 3 explicitly directs fortitude by the gift of counsel.", ("directed by the gift of counsel",)),
    (segment_id(139, 1, "ad", 3), "concept.arduous_work", "Article 1 reply 3 explicitly extends the gift to difficult work.", ("accomplishing any difficult work",)),
    (segment_id(139, 2, "resp"), "concept.fortitude_gift", "Article 2 explicitly connects the gift of fortitude with its corresponding beatitude.", ("the fourth gift , namely fortitude",)),
    (segment_id(139, 2, "resp"), "concept.beatitude_hunger_for_justice", "Article 2 explicitly names the hunger-and-thirst beatitude.", ("hunger and thirst for justice",)),
    (segment_id(140, 1, "resp"), "concept.precepts_of_fortitude", "Article 1 explicitly treats the precepts of fortitude itself.", ("precepts of fortitude",)),
    (segment_id(140, 1, "resp"), "concept.fortitude", "Article 1 explicitly says Divine Law contains precepts of fortitude.", ("contains precepts both of fortitude",)),
    (segment_id(140, 1, "resp"), "concept.god", "Article 1 explicitly directs Divine Law to adhesion to God.", ("adhere to God",)),
    (segment_id(140, 2, "resp"), "concept.precepts_of_fortitude_parts", "Article 2 explicitly treats precepts of annexed virtues.", ("secondary and annexed virtues",)),
    (segment_id(140, 2, "ad", 1), "concept.magnanimity", "Article 2 reply 1 explicitly distinguishes magnanimity from the preceptive matter of patience and perseverance.", ("magnificence and magnanimity",)),
    (segment_id(140, 2, "ad", 1), "concept.magnificence", "Article 2 reply 1 explicitly distinguishes magnificence from the preceptive matter of patience and perseverance.", ("magnificence and magnanimity",)),
    (segment_id(140, 2, "ad", 1), "concept.patience", "Article 2 reply 1 explicitly says there is need of precepts about patience.", ("need of precepts of patience",)),
    (segment_id(140, 2, "ad", 1), "concept.perseverance_virtue", "Article 2 reply 1 explicitly says there is need of precepts about perseverance.", ("precepts of patience and perseverance",)),
):
    add_article_treatment(
        source_passage_id,
        concept_id,
        rationale=rationale,
        evidence_hints=hints,
    )


# Doctrinal relation seeds
for source_passage_id, subject_id, relation_type, object_id, support_type, confidence, rationale, hints in (
    (segment_id(136, 1, "resp"), "concept.patience", "species_of", "concept.virtue", "explicit_textual", 0.98, "Article 1 explicitly concludes that patience is a virtue.", ("patience is a virtue",)),
    (segment_id(136, 1, "resp"), "concept.patience", "has_object", "concept.grievous_evil", "explicit_textual", 0.92, "Article 1 explicitly says patience safeguards reason against sorrow and bears evil with equal mind.", ("safeguard the good of reason against sorrow", "bears evil with an equal mind")),
    (segment_id(136, 3, "resp"), "concept.patience", "caused_by", "concept.charity", "explicit_textual", 0.98, "Article 3 explicitly says patience as a virtue is caused by charity.", ("patience, as a virtue , is caused by charity",)),
    (segment_id(136, 3, "resp"), "concept.patience", "requires", "concept.grace", "explicit_textual", 0.97, "Article 3 explicitly concludes that patience cannot be had without grace.", ("impossible to have patience without the help of grace",)),
    (segment_id(136, 4, "resp"), "concept.patience", "part_of_fortitude", "concept.fortitude", "explicit_textual", 0.98, "Article 4 explicitly says patience is a quasi-potential part of fortitude.", ("patience is a quasi-potential part of fortitude",)),
    (segment_id(136, 5, "resp"), "concept.longanimity_fortitude", "part_of", "concept.patience", "explicit_textual", 0.9, "Article 5 explicitly says longanimity can be comprised under patience under one aspect.", ("longanimity and constancy are both comprised under patience",)),
    (segment_id(136, 5, "resp"), "concept.constancy_fortitude", "part_of", "concept.patience", "explicit_textual", 0.9, "Article 5 explicitly says constancy can be comprised under patience under one aspect.", ("longanimity and constancy are both comprised under patience",)),
    (segment_id(137, 1, "resp"), "concept.perseverance_virtue", "species_of", "concept.virtue", "explicit_textual", 0.97, "Article 1 explicitly says perseverance is a special virtue.", ("perseverance is a special virtue",)),
    (segment_id(137, 1, "resp"), "concept.perseverance_virtue", "directed_to", "concept.continuance_in_good", "explicit_textual", 0.93, "Article 1 explicitly defines perseverance as persisting long in good until it is accomplished.", ("persist long in something good until it is accomplished",)),
    (segment_id(137, 2, "resp"), "concept.perseverance_virtue", "part_of_fortitude", "concept.fortitude", "explicit_textual", 0.98, "Article 2 explicitly says perseverance is annexed to fortitude as secondary to principal virtue.", ("perseverance is annexed to fortitude",)),
    (segment_id(137, 3, "resp"), "concept.constancy_fortitude", "part_of_fortitude", "concept.fortitude", "explicit_textual", 0.93, "Article 3 explicitly describes constancy as a part of fortitude while ranking perseverance before it.", ("perseverance takes precedence of constancy as a part of fortitude",)),
    (segment_id(137, 4, "resp"), "concept.perseverance_virtue", "requires", "concept.grace", "explicit_textual", 0.97, "Article 4 explicitly says perseverance as virtue needs habitual grace.", ("it needs the gift of habitual grace",)),
    (segment_id(138, 1, "sc"), "concept.effeminacy_perseverance", "deficiency_opposed_to", "concept.perseverance_virtue", "explicit_textual", 0.97, "Article 1 sed contra explicitly opposes the persevering man and the effeminate.", ("persevering man is opposed to the effeminate",)),
    (segment_id(138, 1, "resp"), "concept.effeminacy_perseverance", "deficiency_opposed_to", "concept.perseverance_virtue", "explicit_textual", 0.96, "Article 1 respondeo explicitly says effeminacy is directly opposed to perseverance by falling away from good through softness.", ("directly opposed", "effeminacy")),
    (segment_id(138, 2, "sc"), "concept.pertinacity_perseverance", "excess_opposed_to", "concept.perseverance_virtue", "explicit_textual", 0.96, "Article 2 sed contra explicitly opposes pertinacity to perseverance.", ("pertinacity is opposed to perseverance",)),
    (segment_id(138, 2, "resp"), "concept.pertinacity_perseverance", "excess_opposed_to", "concept.perseverance_virtue", "explicit_textual", 0.97, "Article 2 respondeo explicitly says pertinacity exceeds the mean that perseverance keeps.", ("pertinacity is reproved for exceeding the mean",)),
    (segment_id(138, 2, "resp"), "concept.pertinacity_perseverance", "contrary_to", "concept.effeminacy_perseverance", "explicit_textual", 0.93, "Article 2 explicitly contrasts pertinacity as excess with effeminacy as falling short.", ("pertinacity is reproved for exceeding the mean, and effeminacy for falling short",)),
    (segment_id(138, 2, "ad", 1), "concept.pertinacity_perseverance", "caused_by", "concept.vainglory", "explicit_textual", 0.95, "Article 2 reply 1 explicitly says pertinacity results from vainglory as cause.", ("result of vainglory as its cause",)),
    (segment_id(139, 1, "resp"), "concept.fortitude_gift", "corresponding_gift_of", "concept.fortitude", "explicit_textual", 0.98, "Article 1 explicitly distinguishes fortitude as gift from fortitude as virtue while still naming it fortitude.", ("fortitude is reckoned a gift of the Holy Ghost",)),
    (segment_id(139, 1, "ad", 1), "concept.fortitude", "perfected_by", "concept.fortitude_gift", "strong_textual_inference", 0.91, "Article 1 reply 1 says virtue-fortitude does not give the confidence that belongs to the gift, strongly supporting that the gift perfects the virtue in this matter.", ("this belongs to the fortitude that is a gift of the Holy Ghost",)),
    (segment_id(139, 1, "ad", 3), "concept.fortitude_gift", "regulated_by", "concept.counsel_gift", "explicit_textual", 0.97, "Article 1 reply 3 explicitly says the gift of fortitude is directed by the gift of counsel.", ("gift of fortitude is directed by the gift of counsel",)),
    (segment_id(139, 1, "ad", 3), "concept.fortitude_gift", "directed_to", "concept.arduous_work", "explicit_textual", 0.92, "Article 1 reply 3 explicitly extends the gift of fortitude to accomplishing difficult work.", ("accomplishing any difficult work",)),
    (segment_id(139, 1, "resp"), "concept.fortitude_gift", "has_object", "concept.grievous_evil", "strong_textual_inference", 0.88, "Article 1 explicitly says fortitude and the gift of fortitude bear grievous evil, though the gift does so by motion of the Holy Ghost.", ("enduring grievous evil",)),
    (segment_id(139, 2, "resp"), "concept.fortitude_gift", "corresponds_to", "concept.beatitude_hunger_for_justice", "explicit_textual", 0.97, "Article 2 explicitly assigns the beatitude of hunger and thirst for justice to the gift of fortitude.", ("the fourth beatitude", "the fourth gift , namely fortitude")),
    (segment_id(140, 1, "resp"), "concept.precepts_of_fortitude", "precept_of", "concept.fortitude", "explicit_textual", 0.97, "Article 1 explicitly says Divine Law contains precepts of fortitude.", ("contains precepts both of fortitude",)),
    (segment_id(140, 1, "resp"), "concept.precepts_of_fortitude", "directed_to", "concept.god", "explicit_textual", 0.94, "Article 1 explicitly directs the Divine Law, and therefore fortitude's precepts, to man's adhesion to God.", ("adhere to God",)),
    (segment_id(140, 1, "ad", 2), "concept.precepts_of_fortitude", "forbids_opposed_vice_of", "concept.fortitude", "strong_textual_inference", 0.86, "Article 1 reply 2 explicitly says fortitude's precepts are negative rather than affirmative, strongly supporting a prohibitive precept relation around fortitude's opposed matter.", ("precepts of fortitude are negative rather than affirmative",)),
    (segment_id(140, 2, "resp"), "concept.precepts_of_fortitude_parts", "precept_of", "concept.fortitude", "strong_textual_inference", 0.87, "Article 2 says Divine Law contains precepts about secondary and annexed virtues, strongly supporting a fortitude-part precept complex.", ("secondary and annexed virtues",)),
    (segment_id(140, 2, "ad", 1), "concept.precepts_of_fortitude_parts", "commands_act_of", "concept.patience", "explicit_textual", 0.96, "Article 2 reply 1 explicitly says there is need of precepts about patience.", ("need of precepts of patience",)),
    (segment_id(140, 2, "ad", 1), "concept.precepts_of_fortitude_parts", "commands_act_of", "concept.perseverance_virtue", "explicit_textual", 0.96, "Article 2 reply 1 explicitly says there is need of precepts about perseverance.", ("precepts of patience and perseverance",)),
    (segment_id(140, 2, "ad", 1), "concept.precepts_of_fortitude_parts", "precept_of", "concept.patience", "strong_textual_inference", 0.9, "Article 2 reply 1 strongly supports that patience falls under the preceptive matter of fortitude's parts.", ("need of precepts of patience",)),
    (segment_id(140, 2, "ad", 1), "concept.precepts_of_fortitude_parts", "precept_of", "concept.perseverance_virtue", "strong_textual_inference", 0.9, "Article 2 reply 1 strongly supports that perseverance falls under the preceptive matter of fortitude's parts.", ("precepts of patience and perseverance",)),
    (segment_id(140, 2, "ad", 2), "concept.precepts_of_fortitude_parts", "directed_to", "concept.god", "strong_textual_inference", 0.84, "Article 2 reply 2 carries over affirmative precepts of patience within the Divine Law's direction toward God.", ("affirmative precepts", "prepared to fulfil them when necessary")),
):
    add_relation(
        source_passage_id,
        subject_id,
        cast(PilotRelationType, relation_type),
        object_id,
        support_type=cast(PilotSupportType, support_type),
        confidence=confidence,
        rationale=rationale,
        evidence_hints=hints,
    )
