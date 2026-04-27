from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..models import PilotRelationType, PilotSupportType

JUSTICE_CORE_MIN_QUESTION = 57
JUSTICE_CORE_MAX_QUESTION = 79


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


JUSTICE_CORE_EXTRA_CONCEPTS: list[dict[str, Any]] = [
    {
        "concept_id": "concept.right",
        "canonical_label": "Right",
        "node_type": "object",
        "aliases": ["right", "the just"],
        "description": "The just or right thing that stands as the object of justice.",
        "notes": ["Keep this juridical sense distinct from moral uprightness in general."],
        "source_scope": [question_id(57)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.justice"],
        "introduced_in_questions": [question_id(57)],
    },
    {
        "concept_id": "concept.natural_right",
        "canonical_label": "Natural Right",
        "node_type": "object",
        "aliases": ["natural right", "natural just"],
        "description": "Right grounded in the nature of the thing and not merely in human enactment.",
        "notes": [],
        "source_scope": [question_id(57)],
        "parent_concept_id": "concept.right",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.positive_right"],
        "introduced_in_questions": [question_id(57)],
    },
    {
        "concept_id": "concept.positive_right",
        "canonical_label": "Positive Right",
        "node_type": "object",
        "aliases": ["positive right", "positive just"],
        "description": "Right arising from human agreement, enactment, or institution.",
        "notes": [],
        "source_scope": [question_id(57)],
        "parent_concept_id": "concept.right",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.natural_right"],
        "introduced_in_questions": [question_id(57)],
    },
    {
        "concept_id": "concept.right_of_nations",
        "canonical_label": "Right of Nations",
        "node_type": "object",
        "aliases": ["right of nations", "jus gentium"],
        "description": "The right common among peoples and treated by Aquinas in relation to natural and positive right.",
        "notes": [],
        "source_scope": [question_id(57)],
        "parent_concept_id": "concept.right",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": ["Its exact relation to natural right remains a normalization point for later review."],
        "related_concepts": ["concept.natural_right", "concept.positive_right"],
        "introduced_in_questions": [question_id(57)],
    },
    {
        "concept_id": "concept.dominion_right",
        "canonical_label": "Right of Dominion",
        "node_type": "object",
        "aliases": ["right of dominion", "dominion right"],
        "description": "A species of right arising from ownership or lordship.",
        "notes": [],
        "source_scope": [question_id(57)],
        "parent_concept_id": "concept.right",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.paternal_right"],
        "introduced_in_questions": [question_id(57)],
    },
    {
        "concept_id": "concept.paternal_right",
        "canonical_label": "Paternal Right",
        "node_type": "object",
        "aliases": ["paternal right"],
        "description": "A species of right reflecting a father's relation to what belongs to the household.",
        "notes": [],
        "source_scope": [question_id(57)],
        "parent_concept_id": "concept.right",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.dominion_right"],
        "introduced_in_questions": [question_id(57)],
    },
    {
        "concept_id": "concept.distributive_justice",
        "canonical_label": "Distributive Justice",
        "node_type": "virtue",
        "aliases": ["distributive justice"],
        "description": "The species of particular justice concerned with proportional distributions from the whole to its parts.",
        "notes": [],
        "source_scope": [question_id(61), question_id(63)],
        "parent_concept_id": "concept.particular_justice",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.commutative_justice", "concept.respect_of_persons"],
        "introduced_in_questions": [question_id(61), question_id(63)],
    },
    {
        "concept_id": "concept.commutative_justice",
        "canonical_label": "Commutative Justice",
        "node_type": "virtue",
        "aliases": ["commutative justice"],
        "description": "The species of particular justice concerned with equality in exchanges between persons.",
        "notes": [],
        "source_scope": [question_id(61), question_id(62)],
        "parent_concept_id": "concept.particular_justice",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.distributive_justice", "concept.restitution"],
        "introduced_in_questions": [question_id(61), question_id(62)],
    },
    {
        "concept_id": "concept.judgment",
        "canonical_label": "Judgment",
        "node_type": "act_type",
        "aliases": ["judgment"],
        "description": "The act of determining what is just in a case.",
        "notes": [],
        "source_scope": [question_id(60)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": ["Keep the act of judgment distinct from the judge as a role."],
        "related_concepts": ["concept.judge_role", "concept.justice"],
        "introduced_in_questions": [question_id(60)],
    },
    {
        "concept_id": "concept.unjust_judgment",
        "canonical_label": "Unjust Judgment",
        "node_type": "wrong_act",
        "aliases": ["unjust judgment"],
        "description": "A perversion of judgment that fails the order of justice.",
        "notes": [],
        "source_scope": [question_id(60), question_id(67)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.rash_judgment", "concept.usurped_judgment"],
        "introduced_in_questions": [question_id(60), question_id(67)],
    },
    {
        "concept_id": "concept.rash_judgment",
        "canonical_label": "Rash Judgment",
        "node_type": "wrong_act",
        "aliases": ["rash judgment", "judgment based on suspicion"],
        "description": "Judgment rendered from insufficient signs or suspicion rather than due certitude.",
        "notes": [],
        "source_scope": [question_id(60)],
        "parent_concept_id": "concept.unjust_judgment",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.judgment"],
        "introduced_in_questions": [question_id(60)],
    },
    {
        "concept_id": "concept.usurped_judgment",
        "canonical_label": "Usurped Judgment",
        "node_type": "wrong_act",
        "aliases": ["usurped judgment"],
        "description": "Judgment wrongfully assumed by one who lacks the proper authority.",
        "notes": [],
        "source_scope": [question_id(60)],
        "parent_concept_id": "concept.unjust_judgment",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.judge_role"],
        "introduced_in_questions": [question_id(60)],
    },
    {
        "concept_id": "concept.restitution",
        "canonical_label": "Restitution",
        "node_type": "act_type",
        "aliases": ["restitution", "restore what was taken"],
        "description": "The act by which commutative equality is re-established through restoration.",
        "notes": [],
        "source_scope": [question_id(62), question_id(78)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.commutative_justice"],
        "introduced_in_questions": [question_id(62), question_id(78)],
    },
    {
        "concept_id": "concept.respect_of_persons",
        "canonical_label": "Respect of Persons",
        "node_type": "sin_type",
        "aliases": ["respect of persons"],
        "description": "Preference given to persons on irrelevant grounds, contrary to distributive justice.",
        "notes": [],
        "source_scope": [question_id(63)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.distributive_justice"],
        "introduced_in_questions": [question_id(63)],
    },
    {
        "concept_id": "concept.public_execution",
        "canonical_label": "Public Execution of Evildoers",
        "node_type": "act_type",
        "aliases": ["public execution", "killing a sinner by public authority"],
        "description": "The punitive killing Aquinas treats as belonging to public authority for the common good.",
        "notes": [],
        "source_scope": [question_id(64)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": ["Keep distinct from unjust killing and from private vengeance."],
        "related_concepts": ["concept.private_execution", "concept.common_good"],
        "introduced_in_questions": [question_id(64)],
    },
    {
        "concept_id": "concept.private_execution",
        "canonical_label": "Private Execution",
        "node_type": "wrong_act",
        "aliases": ["private killing of evildoers", "private execution"],
        "description": "The wrongful private taking of punitive killing into one's own hands.",
        "notes": [],
        "source_scope": [question_id(64)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.public_execution", "concept.judge_role"],
        "introduced_in_questions": [question_id(64)],
    },
    {
        "concept_id": "concept.unjust_killing",
        "canonical_label": "Unjust Killing",
        "node_type": "wrong_act",
        "aliases": ["murder", "unjust killing"],
        "description": "The unjust taking of innocent human life.",
        "notes": [],
        "source_scope": [question_id(64)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": ["Use this normalized node for unjust killing rather than for every discussed case of licit killing."],
        "related_concepts": ["concept.suicide", "concept.life"],
        "introduced_in_questions": [question_id(64)],
    },
    {
        "concept_id": "concept.suicide",
        "canonical_label": "Suicide",
        "node_type": "wrong_act",
        "aliases": ["suicide", "killing oneself"],
        "description": "The killing of oneself, treated as contrary to self-love, the community, and God.",
        "notes": [],
        "source_scope": [question_id(64)],
        "parent_concept_id": "concept.unjust_killing",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.common_good", "concept.life"],
        "introduced_in_questions": [question_id(64)],
    },
    {
        "concept_id": "concept.maiming",
        "canonical_label": "Maiming",
        "node_type": "wrong_act",
        "aliases": ["maiming", "mutilation of members"],
        "description": "Injury that destroys bodily integrity by depriving a member.",
        "notes": [],
        "source_scope": [question_id(65)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.bodily_integrity"],
        "introduced_in_questions": [question_id(65)],
    },
    {
        "concept_id": "concept.assault",
        "canonical_label": "Assault or Blows",
        "node_type": "wrong_act",
        "aliases": ["blows", "assault", "striking"],
        "description": "Injury to the body by blows that inflict pain without destroying the member.",
        "notes": [],
        "source_scope": [question_id(65)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.bodily_integrity"],
        "introduced_in_questions": [question_id(65)],
    },
    {
        "concept_id": "concept.unjust_detention",
        "canonical_label": "Unjust Detention",
        "node_type": "wrong_act",
        "aliases": ["imprisonment", "unjust detention"],
        "description": "The unjust restraint of a person's freedom of movement.",
        "notes": [],
        "source_scope": [question_id(65)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.personal_liberty"],
        "introduced_in_questions": [question_id(65)],
    },
    {
        "concept_id": "concept.theft",
        "canonical_label": "Theft",
        "node_type": "wrong_act",
        "aliases": ["theft", "steal", "thieving"],
        "description": "The secret taking of another's property against the order of justice.",
        "notes": [],
        "source_scope": [question_id(66)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": ["Keep the exceptional necessity case distinct from ordinary theft."],
        "related_concepts": ["concept.robbery", "concept.property", "concept.restitution"],
        "introduced_in_questions": [question_id(66)],
    },
    {
        "concept_id": "concept.robbery",
        "canonical_label": "Robbery",
        "node_type": "wrong_act",
        "aliases": ["robbery", "rob"],
        "description": "The violent taking of another's property.",
        "notes": [],
        "source_scope": [question_id(66)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.theft", "concept.property", "concept.restitution"],
        "introduced_in_questions": [question_id(66)],
    },
    {
        "concept_id": "concept.judge_role",
        "canonical_label": "Judge",
        "node_type": "role",
        "aliases": ["judge"],
        "description": "The judicial role empowered to pronounce sentence publicly.",
        "notes": ["Role-level concept only; do not instantiate individual judges."],
        "source_scope": [question_id(67)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.judgment", "concept.judicial_process"],
        "introduced_in_questions": [question_id(67)],
    },
    {
        "concept_id": "concept.accuser_role",
        "canonical_label": "Accuser",
        "node_type": "role",
        "aliases": ["accuser"],
        "description": "The prosecuting role in a criminal accusation.",
        "notes": ["Role-level concept only; do not instantiate individual accusers."],
        "source_scope": [question_id(68)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.false_accusation", "concept.judicial_process"],
        "introduced_in_questions": [question_id(68)],
    },
    {
        "concept_id": "concept.defendant_role",
        "canonical_label": "Defendant",
        "node_type": "role",
        "aliases": ["defendant"],
        "description": "The role of the accused person in judicial proceedings.",
        "notes": ["Role-level concept only; do not instantiate individual defendants."],
        "source_scope": [question_id(69)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.calumnious_defense", "concept.unjust_appeal"],
        "introduced_in_questions": [question_id(69)],
    },
    {
        "concept_id": "concept.witness_role",
        "canonical_label": "Witness",
        "node_type": "role",
        "aliases": ["witness"],
        "description": "The role of one who gives evidence in a judicial matter.",
        "notes": ["Role-level concept only; do not instantiate individual witnesses."],
        "source_scope": [question_id(70)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.false_witness", "concept.judicial_process"],
        "introduced_in_questions": [question_id(70)],
    },
    {
        "concept_id": "concept.advocate_role",
        "canonical_label": "Advocate",
        "node_type": "role",
        "aliases": ["advocate", "counsel"],
        "description": "The role of legal counsel who defends a party in court.",
        "notes": ["Role-level concept only; do not instantiate individual advocates."],
        "source_scope": [question_id(71)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": ["Keep separate from counsel as prudential deliberation or the gift of counsel."],
        "related_concepts": ["concept.dishonest_advocacy", "concept.extortionate_advocacy"],
        "introduced_in_questions": [question_id(71)],
    },
    {
        "concept_id": "concept.judicial_process",
        "canonical_label": "Judicial Process",
        "node_type": "process",
        "aliases": ["judicial process", "legal proceeding", "judgment process"],
        "description": "The public legal procedure within which judgment, accusation, testimony, and defense occur.",
        "notes": [],
        "source_scope": [question_id(67), question_id(68), question_id(69), question_id(70), question_id(71)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": [
            "concept.judge_role",
            "concept.accuser_role",
            "concept.defendant_role",
            "concept.witness_role",
            "concept.advocate_role",
        ],
        "introduced_in_questions": [
            question_id(67),
            question_id(68),
            question_id(69),
            question_id(70),
            question_id(71),
        ],
    },
    {
        "concept_id": "concept.false_accusation",
        "canonical_label": "False Accusation",
        "node_type": "wrong_act",
        "aliases": ["false accusation", "unjust accusation", "calumny in accusation"],
        "description": "An accusation that wrongfully injures the accused and the common good.",
        "notes": [],
        "source_scope": [question_id(68)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.accuser_role", "concept.judicial_process"],
        "introduced_in_questions": [question_id(68)],
    },
    {
        "concept_id": "concept.calumnious_defense",
        "canonical_label": "Calumnious Defense",
        "node_type": "wrong_act",
        "aliases": ["calumnious defense", "defending oneself with calumnies"],
        "description": "A defense that uses falsehood or calumny rather than truth.",
        "notes": [],
        "source_scope": [question_id(69)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.defendant_role", "concept.truth_in_legal_proceedings"],
        "introduced_in_questions": [question_id(69)],
    },
    {
        "concept_id": "concept.unjust_appeal",
        "canonical_label": "Unjust Appeal",
        "node_type": "wrong_act",
        "aliases": ["unjust appeal", "sinful appeal"],
        "description": "An appeal made not from injustice suffered, but to delay or evade a just sentence.",
        "notes": [],
        "source_scope": [question_id(69)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.defendant_role", "concept.judicial_process"],
        "introduced_in_questions": [question_id(69)],
    },
    {
        "concept_id": "concept.false_witness",
        "canonical_label": "False Witness",
        "node_type": "wrong_act",
        "aliases": ["false witness", "false testimony"],
        "description": "False testimony given under oath in a judicial matter.",
        "notes": [],
        "source_scope": [question_id(70)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.witness_role", "concept.truth_in_legal_proceedings"],
        "introduced_in_questions": [question_id(70)],
    },
    {
        "concept_id": "concept.dishonest_advocacy",
        "canonical_label": "Dishonest Advocacy",
        "node_type": "wrong_act",
        "aliases": ["dishonest advocacy", "defending an unjust cause"],
        "description": "Advocacy that knowingly assists an unjust cause.",
        "notes": [],
        "source_scope": [question_id(71)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.advocate_role", "concept.restitution"],
        "introduced_in_questions": [question_id(71)],
    },
    {
        "concept_id": "concept.extortionate_advocacy",
        "canonical_label": "Extortionate Advocacy",
        "node_type": "wrong_act",
        "aliases": ["extortionate advocacy", "immoderate legal fee"],
        "description": "The unjust exaction of an immoderate fee by an advocate.",
        "notes": [],
        "source_scope": [question_id(71)],
        "parent_concept_id": "concept.dishonest_advocacy",
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.advocate_role", "concept.fairness_in_exchange"],
        "introduced_in_questions": [question_id(71)],
    },
    {
        "concept_id": "concept.reviling",
        "canonical_label": "Reviling",
        "node_type": "wrong_act",
        "aliases": ["reviling"],
        "description": "Verbal injury that dishonors another openly.",
        "notes": [],
        "source_scope": [question_id(72)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.honor", "concept.anger"],
        "introduced_in_questions": [question_id(72)],
    },
    {
        "concept_id": "concept.backbiting",
        "canonical_label": "Backbiting",
        "node_type": "wrong_act",
        "aliases": ["backbiting"],
        "description": "Secret verbal injury that blackens a person's good name.",
        "notes": [],
        "source_scope": [question_id(73)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.reputation"],
        "introduced_in_questions": [question_id(73)],
    },
    {
        "concept_id": "concept.tale_bearing",
        "canonical_label": "Tale-Bearing",
        "node_type": "wrong_act",
        "aliases": ["tale-bearing", "whispering"],
        "description": "Secret evil-speaking ordered chiefly to the breaking of friendship.",
        "notes": [],
        "source_scope": [question_id(74)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.friendship", "concept.backbiting"],
        "introduced_in_questions": [question_id(74)],
    },
    {
        "concept_id": "concept.derision",
        "canonical_label": "Derision",
        "node_type": "wrong_act",
        "aliases": ["derision", "mockery"],
        "description": "Injury by jest or mockery directed to another's shame.",
        "notes": [],
        "source_scope": [question_id(75)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.honor"],
        "introduced_in_questions": [question_id(75)],
    },
    {
        "concept_id": "concept.cursing",
        "canonical_label": "Cursing",
        "node_type": "wrong_act",
        "aliases": ["cursing", "malediction"],
        "description": "Speaking evil of another by way of command or desire.",
        "notes": [],
        "source_scope": [question_id(76)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.charity"],
        "introduced_in_questions": [question_id(76)],
    },
    {
        "concept_id": "concept.just_price",
        "canonical_label": "Just Price",
        "node_type": "doctrine",
        "aliases": ["just price"],
        "description": "The equality of value that should govern buying and selling.",
        "notes": [],
        "source_scope": [question_id(77)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.cheating", "concept.fairness_in_exchange"],
        "introduced_in_questions": [question_id(77)],
    },
    {
        "concept_id": "concept.cheating",
        "canonical_label": "Cheating in Exchange",
        "node_type": "wrong_act",
        "aliases": ["cheating", "fraud in buying and selling", "deceitful sale"],
        "description": "Fraudulent or unequal exchange in buying and selling.",
        "notes": [],
        "source_scope": [question_id(77)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.just_price", "concept.fairness_in_exchange"],
        "introduced_in_questions": [question_id(77)],
    },
    {
        "concept_id": "concept.usury",
        "canonical_label": "Usury",
        "node_type": "wrong_act",
        "aliases": ["usury"],
        "description": "Taking payment for the use of money lent in a way Aquinas judges intrinsically unjust.",
        "notes": [],
        "source_scope": [question_id(78)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.restitution", "concept.fairness_in_exchange"],
        "introduced_in_questions": [question_id(78)],
    },
    {
        "concept_id": "concept.transgression",
        "canonical_label": "Transgression",
        "node_type": "sin_type",
        "aliases": ["transgression"],
        "description": "Sin by stepping beyond the affirmative or negative rule of a precept.",
        "notes": [],
        "source_scope": [question_id(79)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.omission", "concept.justice"],
        "introduced_in_questions": [question_id(79)],
    },
    {
        "concept_id": "concept.omission",
        "canonical_label": "Omission",
        "node_type": "sin_type",
        "aliases": ["omission"],
        "description": "Sin by failing to do a due good.",
        "notes": [],
        "source_scope": [question_id(79)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.transgression", "concept.justice"],
        "introduced_in_questions": [question_id(79)],
    },
    {
        "concept_id": "concept.life",
        "canonical_label": "Life",
        "node_type": "domain",
        "aliases": ["life"],
        "description": "The domain of bodily life harmed by unjust killing.",
        "notes": [],
        "source_scope": [question_id(64)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.unjust_killing", "concept.suicide"],
        "introduced_in_questions": [question_id(64)],
    },
    {
        "concept_id": "concept.bodily_integrity",
        "canonical_label": "Bodily Integrity",
        "node_type": "domain",
        "aliases": ["bodily integrity", "integrity of the body"],
        "description": "The wholeness of the body harmed by maiming and bodily assault.",
        "notes": [],
        "source_scope": [question_id(65)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.maiming", "concept.assault"],
        "introduced_in_questions": [question_id(65)],
    },
    {
        "concept_id": "concept.personal_liberty",
        "canonical_label": "Personal Liberty",
        "node_type": "domain",
        "aliases": ["personal liberty", "freedom of movement"],
        "description": "The domain harmed by unjust detention or imprisonment.",
        "notes": [],
        "source_scope": [question_id(65)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.unjust_detention"],
        "introduced_in_questions": [question_id(65)],
    },
    {
        "concept_id": "concept.property",
        "canonical_label": "Property",
        "node_type": "domain",
        "aliases": ["property", "external goods"],
        "description": "The domain of possession and external goods harmed by theft and robbery.",
        "notes": [],
        "source_scope": [question_id(66)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.theft", "concept.robbery"],
        "introduced_in_questions": [question_id(66)],
    },
    {
        "concept_id": "concept.honor",
        "canonical_label": "Honor",
        "node_type": "domain",
        "aliases": ["honor"],
        "description": "The social good openly injured by reviling and derision.",
        "notes": [],
        "source_scope": [question_id(72), question_id(75)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.reviling", "concept.derision"],
        "introduced_in_questions": [question_id(72), question_id(75)],
    },
    {
        "concept_id": "concept.reputation",
        "canonical_label": "Reputation",
        "node_type": "domain",
        "aliases": ["reputation", "good name"],
        "description": "The good name secretly injured by backbiting.",
        "notes": [],
        "source_scope": [question_id(73)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.backbiting", "concept.false_accusation"],
        "introduced_in_questions": [question_id(73)],
    },
    {
        "concept_id": "concept.friendship",
        "canonical_label": "Friendship",
        "node_type": "domain",
        "aliases": ["friendship"],
        "description": "The social bond chiefly injured by tale-bearing.",
        "notes": [],
        "source_scope": [question_id(74)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.tale_bearing"],
        "introduced_in_questions": [question_id(74)],
    },
    {
        "concept_id": "concept.truth_in_legal_proceedings",
        "canonical_label": "Truth in Legal Proceedings",
        "node_type": "domain",
        "aliases": ["truth in legal proceedings", "judicial truth", "truth in court"],
        "description": "The truthful order on which just accusation, testimony, and defense depend.",
        "notes": [],
        "source_scope": [question_id(67), question_id(68), question_id(69), question_id(70)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.false_accusation", "concept.calumnious_defense", "concept.false_witness"],
        "introduced_in_questions": [question_id(67), question_id(68), question_id(69), question_id(70)],
    },
    {
        "concept_id": "concept.fairness_in_distribution",
        "canonical_label": "Fairness in Distribution",
        "node_type": "domain",
        "aliases": ["fairness in distribution", "proportion in distribution"],
        "description": "The proportional equality proper to distributive justice.",
        "notes": [],
        "source_scope": [question_id(61), question_id(63)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.distributive_justice", "concept.respect_of_persons"],
        "introduced_in_questions": [question_id(61), question_id(63)],
    },
    {
        "concept_id": "concept.fairness_in_exchange",
        "canonical_label": "Fairness in Exchange",
        "node_type": "domain",
        "aliases": ["fairness in exchange", "equality in exchange"],
        "description": "The equality proper to commutative justice and market exchange.",
        "notes": [],
        "source_scope": [question_id(61), question_id(62), question_id(77), question_id(78)],
        "parent_concept_id": None,
        "registry_status": "reviewed_seed",
        "disambiguation_notes": [],
        "related_concepts": ["concept.commutative_justice", "concept.restitution", "concept.cheating", "concept.usury"],
        "introduced_in_questions": [question_id(61), question_id(62), question_id(77), question_id(78)],
    },
]

JUSTICE_SPECIES_CONCEPT_IDS = {
    "concept.right",
    "concept.natural_right",
    "concept.positive_right",
    "concept.right_of_nations",
    "concept.dominion_right",
    "concept.paternal_right",
    "concept.justice",
    "concept.general_justice",
    "concept.particular_justice",
    "concept.distributive_justice",
    "concept.commutative_justice",
    "concept.unjust_judgment",
    "concept.rash_judgment",
    "concept.usurped_judgment",
}
JUSTICE_DOMAIN_CONCEPT_IDS = {
    "concept.life",
    "concept.bodily_integrity",
    "concept.personal_liberty",
    "concept.property",
    "concept.honor",
    "concept.reputation",
    "concept.friendship",
    "concept.truth_in_legal_proceedings",
    "concept.fairness_in_distribution",
    "concept.fairness_in_exchange",
}
JUDICIAL_ROLE_CONCEPT_IDS = {
    "concept.judge_role",
    "concept.accuser_role",
    "concept.defendant_role",
    "concept.witness_role",
    "concept.advocate_role",
}
JUDICIAL_PROCESS_CONCEPT_IDS = {"concept.judicial_process"}
RESTITUTION_RELATED_CONCEPT_IDS = {"concept.restitution"}


for q_num, concept_id, article_num, rationale in (
    (57, "concept.right", 1, "Question 57 is the justice-foundations tract on right itself."),
    (58, "concept.justice", 1, "Question 58 is the main question on justice."),
    (59, "concept.injustice", 1, "Question 59 explicitly treats injustice."),
    (60, "concept.judgment", 1, "Question 60 explicitly treats judgment."),
    (61, "concept.distributive_justice", 1, "Question 61 introduces the species of particular justice."),
    (62, "concept.restitution", 1, "Question 62 explicitly treats restitution."),
    (63, "concept.respect_of_persons", 1, "Question 63 explicitly treats respect of persons."),
    (64, "concept.life", 1, "Question 64 treats acts ordered to or against life."),
    (65, "concept.bodily_integrity", 1, "Question 65 treats injuries against the person."),
    (66, "concept.property", 1, "Question 66 treats property and the wrongs against it."),
    (67, "concept.judicial_process", 1, "Question 67 begins the judicial-process block."),
    (68, "concept.accuser_role", 1, "Question 68 treats accusation and the accuser's role."),
    (69, "concept.defendant_role", 1, "Question 69 treats the defendant's role."),
    (70, "concept.witness_role", 1, "Question 70 treats testimony and the witness."),
    (71, "concept.advocate_role", 1, "Question 71 treats advocacy."),
    (72, "concept.reviling", 1, "Question 72 treats reviling."),
    (73, "concept.backbiting", 1, "Question 73 treats backbiting."),
    (74, "concept.tale_bearing", 1, "Question 74 treats tale-bearing."),
    (75, "concept.derision", 1, "Question 75 treats derision."),
    (76, "concept.cursing", 1, "Question 76 treats cursing."),
    (77, "concept.cheating", 1, "Question 77 treats cheating in buying and selling."),
    (78, "concept.usury", 1, "Question 78 treats usury."),
    (79, "concept.omission", 3, "Question 79 treats omission and transgression within the justice tract."),
):
    add_question_treatment(q_num, concept_id, article_number=article_num, rationale=rationale)


def bulk_article_treatments(
    question_number: int,
    article_numbers: range,
    concept_id: str,
    rationale: str,
) -> None:
    for article_number in article_numbers:
        add_article_treatment(
            question_number,
            article_number,
            concept_id,
            rationale=rationale,
        )


bulk_article_treatments(57, range(1, 5), "concept.right", "Each article of Question 57 treats a mode or division of right.")
add_article_treatment(57, 2, "concept.natural_right", rationale="Article 2 explicitly divides right into natural and positive right.")
add_article_treatment(57, 2, "concept.positive_right", rationale="Article 2 explicitly divides right into natural and positive right.")
add_article_treatment(57, 3, "concept.right_of_nations", rationale="Article 3 explicitly treats the right of nations.")
add_article_treatment(57, 4, "concept.dominion_right", rationale="Article 4 explicitly treats right of dominion.")
add_article_treatment(57, 4, "concept.paternal_right", rationale="Article 4 explicitly treats paternal right.")

bulk_article_treatments(58, range(1, 13), "concept.justice", "Each article of Question 58 explicitly treats justice.")
add_article_treatment(58, 4, "concept.will", rationale="Article 4 explicitly treats justice as residing in the will.")
add_article_treatment(58, 5, "concept.general_justice", rationale="Article 5 explicitly treats general or legal justice.")
add_article_treatment(58, 6, "concept.general_justice", rationale="Article 6 continues the treatment of general justice.")
add_article_treatment(58, 7, "concept.particular_justice", rationale="Article 7 explicitly treats particular justice.")
add_article_treatment(58, 11, "concept.rendering_due", rationale="Article 11 explicitly treats rendering to each one what is his own.")

bulk_article_treatments(59, range(1, 5), "concept.injustice", "Each article of Question 59 explicitly treats injustice.")

bulk_article_treatments(60, range(1, 7), "concept.judgment", "Each article of Question 60 treats judgment.")
add_article_treatment(60, 3, "concept.rash_judgment", rationale="Article 3 explicitly treats judgment based on suspicion.")
add_article_treatment(60, 6, "concept.usurped_judgment", rationale="Article 6 explicitly treats usurped judgment.")
add_article_treatment(60, 5, "concept.law", rationale="Article 5 explicitly treats judgment according to the written law.")

add_article_treatment(61, 1, "concept.distributive_justice", rationale="Article 1 explicitly introduces distributive justice.")
add_article_treatment(61, 1, "concept.commutative_justice", rationale="Article 1 explicitly introduces commutative justice.")
add_article_treatment(61, 2, "concept.fairness_in_distribution", rationale="Article 2 explicitly treats the mean in distributive justice.")
add_article_treatment(61, 2, "concept.fairness_in_exchange", rationale="Article 2 explicitly treats the mean in commutative justice.")
add_article_treatment(61, 3, "concept.particular_justice", rationale="Article 3 continues the treatment of particular justice.")
add_article_treatment(61, 4, "concept.particular_justice", rationale="Article 4 continues the treatment of what is just in particular exchanges and injuries.")

bulk_article_treatments(62, range(1, 9), "concept.restitution", "Each article of Question 62 explicitly treats restitution.")
add_article_treatment(62, 1, "concept.commutative_justice", rationale="Article 1 explicitly treats restitution as an act of commutative justice.")

bulk_article_treatments(63, range(1, 5), "concept.respect_of_persons", "Each article of Question 63 explicitly treats respect of persons.")
add_article_treatment(63, 1, "concept.distributive_justice", rationale="Article 1 explicitly measures respect of persons against distributive justice.")
add_article_treatment(63, 4, "concept.judgment", rationale="Article 4 explicitly treats judicial sentences.")

bulk_article_treatments(64, range(1, 9), "concept.life", "Each article of Question 64 treats acts ordered to life or its loss.")
add_article_treatment(64, 2, "concept.public_execution", rationale="Article 2 explicitly treats the lawful killing of a sinner.")
add_article_treatment(64, 3, "concept.private_execution", rationale="Article 3 distinguishes public from private killing.")
add_article_treatment(64, 5, "concept.suicide", rationale="Article 5 explicitly treats killing oneself.")
add_article_treatment(64, 6, "concept.unjust_killing", rationale="Article 6 explicitly treats the killing of the just.")

bulk_article_treatments(65, range(1, 5), "concept.bodily_integrity", "Each article of Question 65 treats injuries against the person.")
add_article_treatment(65, 1, "concept.maiming", rationale="Article 1 explicitly treats maiming.")
add_article_treatment(65, 2, "concept.assault", rationale="Article 2 explicitly treats blows.")
add_article_treatment(65, 3, "concept.unjust_detention", rationale="Article 3 explicitly treats imprisonment.")
add_article_treatment(65, 3, "concept.personal_liberty", rationale="Article 3 explicitly treats restraint of movement.")

bulk_article_treatments(66, range(1, 10), "concept.property", "Each article of Question 66 treats property or wrongs against it.")
add_article_treatment(66, 3, "concept.theft", rationale="Article 3 explicitly treats theft.")
add_article_treatment(66, 4, "concept.robbery", rationale="Article 4 explicitly treats robbery.")
add_article_treatment(66, 7, "concept.theft", rationale="Article 7 explicitly revisits theft under necessity.")
add_article_treatment(66, 8, "concept.robbery", rationale="Article 8 explicitly treats robbery as a mortal sin.")

bulk_article_treatments(67, range(1, 5), "concept.judicial_process", "Each article of Question 67 treats the judge within judicial procedure.")
add_article_treatment(67, 1, "concept.judge_role", rationale="Article 1 explicitly treats the judge.")
add_article_treatment(67, 3, "concept.accuser_role", rationale="Article 3 explicitly treats the need for an accuser.")

bulk_article_treatments(68, range(1, 5), "concept.accuser_role", "Each article of Question 68 treats accusation and the accuser.")
add_article_treatment(68, 1, "concept.judicial_process", rationale="Article 1 situates accusation within the judicial process.")
add_article_treatment(68, 3, "concept.false_accusation", rationale="Article 3 explicitly treats false accusation.")

bulk_article_treatments(69, range(1, 5), "concept.defendant_role", "Each article of Question 69 treats the defendant in judgment.")
add_article_treatment(69, 2, "concept.calumnious_defense", rationale="Article 2 explicitly treats defending oneself with calumnies.")
add_article_treatment(69, 3, "concept.unjust_appeal", rationale="Article 3 explicitly treats sinful appeals.")

bulk_article_treatments(70, range(1, 5), "concept.witness_role", "Each article of Question 70 treats testimony and the witness.")
add_article_treatment(70, 1, "concept.truth_in_legal_proceedings", rationale="Article 1 explicitly treats evidence as needed for justice.")
add_article_treatment(70, 4, "concept.false_witness", rationale="Article 4 explicitly treats false witness.")

bulk_article_treatments(71, range(1, 5), "concept.advocate_role", "Each article of Question 71 treats advocacy.")
add_article_treatment(71, 3, "concept.dishonest_advocacy", rationale="Article 3 explicitly treats defending an unjust cause.")
add_article_treatment(71, 4, "concept.extortionate_advocacy", rationale="Article 4 explicitly treats an advocate's fee.")

bulk_article_treatments(72, range(1, 5), "concept.reviling", "Each article of Question 72 treats reviling.")
add_article_treatment(72, 1, "concept.honor", rationale="Article 1 explicitly treats the dishonor inflicted by reviling.")

bulk_article_treatments(73, range(1, 5), "concept.backbiting", "Each article of Question 73 treats backbiting.")
add_article_treatment(73, 1, "concept.reputation", rationale="Article 1 explicitly treats secret injury to a good name.")

bulk_article_treatments(74, range(1, 3), "concept.tale_bearing", "Each article of Question 74 treats tale-bearing.")
add_article_treatment(74, 1, "concept.friendship", rationale="Article 1 explicitly treats the severing of friendship.")

bulk_article_treatments(75, range(1, 3), "concept.derision", "Each article of Question 75 treats derision.")
add_article_treatment(75, 1, "concept.honor", rationale="Article 1 explicitly treats derision as shaming speech.")

bulk_article_treatments(76, range(1, 5), "concept.cursing", "Each article of Question 76 treats cursing.")
add_article_treatment(76, 3, "concept.charity", rationale="Article 3 explicitly measures cursing against charity.")

bulk_article_treatments(77, range(1, 5), "concept.cheating", "Each article of Question 77 treats unjust exchange in buying and selling.")
add_article_treatment(77, 1, "concept.just_price", rationale="Article 1 explicitly treats the just price.")
add_article_treatment(77, 2, "concept.property", rationale="Article 2 explicitly treats defects in the thing sold.")
add_article_treatment(77, 4, "concept.fairness_in_exchange", rationale="Article 4 explicitly treats exchange in trading.")

bulk_article_treatments(78, range(1, 5), "concept.usury", "Each article of Question 78 treats usury.")
add_article_treatment(78, 3, "concept.restitution", rationale="Article 3 explicitly treats restitution of gains from usury.")
add_article_treatment(78, 1, "concept.fairness_in_exchange", rationale="Article 1 explicitly treats inequality in lending for gain.")

add_article_treatment(79, 1, "concept.justice", rationale="Article 1 treats good and evil as quasi-integral parts of justice.")
add_article_treatment(79, 2, "concept.transgression", rationale="Article 2 explicitly treats transgression.")
add_article_treatment(79, 3, "concept.omission", rationale="Article 3 explicitly treats omission.")
add_article_treatment(79, 4, "concept.transgression", rationale="Article 4 compares transgression and omission.")
add_article_treatment(79, 4, "concept.omission", rationale="Article 4 compares transgression and omission.")


for payload in (
    (57, 1, "concept.justice", "has_object", "concept.right", "Question 57 opens by explicitly identifying right as the object of justice.", ("right is the object of justice",)),
    (57, 2, "concept.natural_right", "species_of", "concept.right", "Article 2 explicitly divides right into natural and positive right.", ("natural right",)),
    (57, 2, "concept.positive_right", "species_of", "concept.right", "Article 2 explicitly divides right into natural and positive right.", ("positive right",)),
    (57, 3, "concept.right_of_nations", "species_of", "concept.right", "The right of nations is treated as a determinate kind of right in Article 3.", ("right of nations",), "strong_textual_inference", 0.88),
    (57, 4, "concept.dominion_right", "species_of", "concept.right", "Article 4 treats right of dominion as a distinct juridical species.", ("right of dominion",), "strong_textual_inference", 0.88),
    (57, 4, "concept.paternal_right", "species_of", "concept.right", "Article 4 treats paternal right as a distinct juridical species.", ("paternal right",), "strong_textual_inference", 0.88),
    (58, 5, "concept.general_justice", "directed_to", "concept.common_good", "Article 5 explicitly directs legal justice to the common good.", ("common good",)),
    (58, 6, "concept.general_justice", "directed_to", "concept.common_good", "Article 6 explicitly continues the claim that legal justice directs acts to the common good.", ("common good",)),
    (58, 7, "concept.particular_justice", "species_of", "concept.justice", "Article 7 explicitly distinguishes particular justice alongside legal justice.", ("particular justice",), "strong_textual_inference", 0.9),
    (58, 12, "concept.general_justice", "directed_to", "concept.common_good", "Article 12 again measures legal justice by the transcendence of the common good.", ("common good",), "strong_textual_inference", 0.9),
    (59, 1, "concept.injustice", "opposed_by", "concept.justice", "Article 1 treats injustice precisely in relation to the justice it opposes.", ("opposed to legal justice",), "strong_textual_inference", 0.9),
    (59, 4, "concept.injustice", "contrary_to", "concept.charity", "Article 4 explicitly states that injustice is mortal insofar as it is contrary to charity.", ("contrary to charity",)),
    (60, 1, "concept.justice", "has_act", "concept.judgment", "Article 1 explicitly states that judgment belongs properly to justice.", ("belongs properly to justice",)),
    (60, 1, "concept.judgment", "has_object", "concept.right", "Article 1 connects judgment with asserting the right.", ("asserts the right",)),
    (60, 2, "concept.judgment", "requires", "concept.justice", "Article 2 explicitly lists justice among the conditions for lawful judgment.", ("three conditions", "justice"), "strong_textual_inference", 0.9),
    (60, 2, "concept.judgment", "requires", "concept.judge_role", "Article 2 explicitly requires proper authority for lawful judgment.", ("authority of the sovereign",), "strong_textual_inference", 0.9),
    (60, 3, "concept.rash_judgment", "species_of", "concept.unjust_judgment", "Article 3 treats suspicion-based judgment as a perversion of due judgment.", ("suspicion denotes evil thinking",), "strong_textual_inference", 0.88),
    (60, 3, "concept.rash_judgment", "corrupts_process", "concept.judicial_process", "Judgment based on slight signs corrupts the order of due judgment.", ("slight indications", "evil thinking"), "strong_textual_inference", 0.88),
    (60, 5, "concept.judgment", "regulated_by", "concept.law", "Article 5 explicitly treats judgment according to the written law.", ("written law",)),
    (60, 6, "concept.usurped_judgment", "species_of", "concept.unjust_judgment", "Article 6 treats usurped judgment as a perversion of rightful judgment.", ("perverted by being usurped",), "strong_textual_inference", 0.88),
    (60, 6, "concept.usurped_judgment", "abuses_role", "concept.judge_role", "Article 6 explicitly marks usurped judgment as a wrongful seizure of the judge's office.", ("other than the public authority",)),
    (60, 6, "concept.usurped_judgment", "corrupts_process", "concept.judicial_process", "Usurped judgment corrupts the ordered administration of judgment.", ("being usurped",), "strong_textual_inference", 0.88),
    (61, 1, "concept.distributive_justice", "species_of", "concept.particular_justice", "Article 1 explicitly introduces distributive justice as a species of particular justice.", ("distributive justice",)),
    (61, 1, "concept.commutative_justice", "species_of", "concept.particular_justice", "Article 1 explicitly introduces commutative justice as a species of particular justice.", ("commutative justice",)),
    (61, 2, "concept.distributive_justice", "directed_to", "concept.fairness_in_distribution", "Article 2 explicitly treats proportional equality in distributive justice.", ("in proportion",), "strong_textual_inference", 0.9),
    (61, 2, "concept.commutative_justice", "directed_to", "concept.fairness_in_exchange", "Article 2 explicitly treats arithmetic equality in commutative justice.", ("equalizing thing to thing",), "strong_textual_inference", 0.9),
    (62, 1, "concept.commutative_justice", "has_act", "concept.restitution", "Article 1 explicitly states that restitution is an act of commutative justice.", ("act of commutative justice",)),
    (62, 1, "concept.restitution", "directed_to", "concept.fairness_in_exchange", "Article 1 explicitly treats restitution as re-establishing equality.", ("equality of justice",), "strong_textual_inference", 0.9),
    (62, 2, "concept.theft", "requires_restitution", "concept.restitution", "Article 2 explicitly requires restoring what one has taken away unjustly.", ("restore what has been taken unjustly",)),
    (62, 2, "concept.robbery", "requires_restitution", "concept.restitution", "Article 2 establishes the restorative requirement for unjust taking generally, including robbery.", ("restore what one has taken away",), "strong_textual_inference", 0.9),
    (62, 3, "concept.restitution", "directed_to", "concept.fairness_in_exchange", "Article 3 continues to treat restitution by measuring the inequality caused.", ("inequality on the part of the thing",), "strong_textual_inference", 0.88),
    (62, 4, "concept.unjust_detention", "requires_restitution", "concept.restitution", "Article 4 states that whoever brings loss on another is bound to restore the loss.", ("brings a loss upon another person",), "strong_textual_inference", 0.88),
    (62, 6, "concept.theft", "requires_restitution", "concept.restitution", "Article 6 again states that the taker is bound to restore the thing taken.", ("bound to restore",)),
    (62, 8, "concept.robbery", "requires_restitution", "concept.restitution", "Article 8 treats withholding another's property as continuing the injustice that restitution repairs.", ("to withhold the property of another",), "strong_textual_inference", 0.86),
    (63, 1, "concept.respect_of_persons", "opposed_by", "concept.distributive_justice", "Article 1 explicitly opposes respect of persons to distributive justice.", ("opposed to distributive justice",)),
    (63, 1, "concept.respect_of_persons", "harms_domain", "concept.fairness_in_distribution", "Article 1 explicitly treats respect of persons as violating proportional allotment.", ("in proportion to", "respect of persons"), "strong_textual_inference", 0.9),
    (63, 4, "concept.respect_of_persons", "corrupts_process", "concept.judicial_process", "Article 4 explicitly applies respect of persons to judicial sentences.", ("judicial sentences",), "strong_textual_inference", 0.9),
    (63, 4, "concept.judgment", "opposed_by", "concept.respect_of_persons", "Article 4 treats judgment as corrupted by respect of persons.", ("judgment is an act of justice", "respect of persons"), "strong_textual_inference", 0.88),
    (64, 2, "concept.public_execution", "directed_to", "concept.common_good", "Article 2 explicitly directs the lawful killing of evildoers to the good of the whole community.", ("safeguard the common good",)),
    (64, 3, "concept.public_execution", "requires", "concept.judge_role", "Article 3 explicitly reserves punitive killing to public authority.", ("belongs to him alone",), "strong_textual_inference", 0.9),
    (64, 3, "concept.private_execution", "abuses_role", "concept.judge_role", "Article 3 explicitly denies this punitive office to private persons.", ("public person only",), "strong_textual_inference", 0.9),
    (64, 3, "concept.private_execution", "corrupts_process", "concept.judicial_process", "Private punitive killing bypasses the public administration of justice treated in Article 3.", ("public person only",), "strong_textual_inference", 0.86),
    (64, 5, "concept.suicide", "harms_domain", "concept.life", "Article 5 explicitly treats suicide as unlawful killing of oneself.", ("unlawful to kill oneself",)),
    (64, 5, "concept.suicide", "contrary_to", "concept.common_good", "Article 5 explicitly says suicide injures the community.", ("injures the community",)),
    (64, 6, "concept.unjust_killing", "harms_domain", "concept.life", "Article 6 explicitly treats the killing of the innocent as unlawful.", ("unlawful to kill any man",), "strong_textual_inference", 0.9),
    (65, 1, "concept.maiming", "harms_domain", "concept.bodily_integrity", "Article 1 explicitly treats maiming as injury to the body's integrity.", ("member is part of the whole human body",), "strong_textual_inference", 0.9),
    (65, 1, "concept.maiming", "abuses_role", "concept.judge_role", "Article 1 reserves punitive mutilation to public authority acting for the whole.", ("for the sake of the whole",), "strong_textual_inference", 0.84),
    (65, 2, "concept.assault", "harms_domain", "concept.bodily_integrity", "Article 2 explicitly treats blows as bodily harm.", ("harm is done a body by striking it",)),
    (65, 2, "concept.assault", "abuses_role", "concept.judge_role", "Article 2 distinguishes lawful punitive striking from private injury.", ("not lawful for a private individual",), "strong_textual_inference", 0.84),
    (65, 3, "concept.unjust_detention", "harms_domain", "concept.personal_liberty", "Article 3 explicitly treats imprisonment as harming movement and use of the members.", ("movement or use of the members",)),
    (65, 3, "concept.unjust_detention", "abuses_role", "concept.judge_role", "Article 3 reserves imprisonment to public authority according to justice.", ("according to the order of justice",), "strong_textual_inference", 0.84),
    (66, 3, "concept.theft", "harms_domain", "concept.property", "Article 3 explicitly defines theft as taking another's property secretly.", ("taking another's thing secretly",)),
    (66, 3, "concept.theft", "opposed_by", "concept.justice", "Article 3 explicitly says theft is contrary to justice.", ("contrary to justice",)),
    (66, 4, "concept.robbery", "harms_domain", "concept.property", "Article 4 explicitly treats robbery as violent taking of another's property.", ("robbery", "violence"), "strong_textual_inference", 0.9),
    (66, 4, "concept.robbery", "opposed_by", "concept.justice", "Article 4 explicitly says robbery is contrary to justice.", ("contrary to justice",)),
    (66, 5, "concept.theft", "requires_restitution", "concept.restitution", "Article 5 reinforces theft's unjust taking as the kind of act restitution addresses.", ("opposition to justice",), "strong_textual_inference", 0.82),
    (66, 6, "concept.theft", "contrary_to", "concept.charity", "Article 6 explicitly measures theft by its contrariety to charity.", ("contrary to charity",)),
    (66, 8, "concept.robbery", "requires_restitution", "concept.restitution", "Article 8 treats robbery as unjust violent taking, of the kind restitution repairs.", ("taking unjustly",), "strong_textual_inference", 0.82),
    (67, 1, "concept.judicial_process", "requires", "concept.judge_role", "Article 1 treats judgment as requiring a judge with public authority.", ("judge's sentence", "coercive power"), "strong_textual_inference", 0.9),
    (67, 2, "concept.unjust_judgment", "abuses_role", "concept.judge_role", "Article 2 treats judgment against the truth known privately as a misuse of the judge's office.", ("public authority", "private knowledge"), "strong_textual_inference", 0.88),
    (67, 2, "concept.unjust_judgment", "corrupts_process", "concept.judicial_process", "Article 2 treats such judgment as a failure of public judicial order.", ("public authority", "private knowledge"), "strong_textual_inference", 0.88),
    (67, 2, "concept.unjust_judgment", "harms_domain", "concept.truth_in_legal_proceedings", "Article 2 explicitly opposes judgment against public proof to the truth needed in judgment.", ("truth which is known to him",), "strong_textual_inference", 0.9),
    (67, 3, "concept.judicial_process", "requires", "concept.accuser_role", "Article 3 explicitly says a judge should not condemn without an accuser.", ("unless the latter has an accuser",)),
    (67, 3, "concept.judge_role", "directed_to", "concept.justice", "Article 3 explicitly calls the judge the personification and interpreter of justice.", ("personification of justice",)),
    (68, 1, "concept.accuser_role", "directed_to", "concept.common_good", "Article 1 explicitly orders accusation to the common good.", ("good of the commonwealth",)),
    (68, 3, "concept.false_accusation", "abuses_role", "concept.accuser_role", "Article 3 explicitly treats false accusation as a perversion of accusation.", ("accusation is ordered for the common good",), "strong_textual_inference", 0.88),
    (68, 3, "concept.false_accusation", "corrupts_process", "concept.judicial_process", "False accusation corrupts the judicial process by misusing accusation.", ("knowledge of the crime", "injure a person unjustly"), "strong_textual_inference", 0.9),
    (68, 3, "concept.false_accusation", "harms_domain", "concept.truth_in_legal_proceedings", "Article 3 treats false accusation as violating the truthful order of criminal procedure.", ("knowledge of the crime",), "strong_textual_inference", 0.86),
    (68, 3, "concept.false_accusation", "harms_domain", "concept.reputation", "Article 3 explicitly notes the accused is injured by wrongful accusation.", ("injure a person unjustly",), "strong_textual_inference", 0.84),
    (69, 1, "concept.defendant_role", "directed_to", "concept.truth_in_legal_proceedings", "Article 1 treats the defendant as bound by the due order of justice to speak truth when lawfully asked.", ("order of justice", "obey his superior"), "strong_textual_inference", 0.88),
    (69, 2, "concept.calumnious_defense", "abuses_role", "concept.defendant_role", "Article 2 explicitly treats defense by calumny as unlawful.", ("utter a falsehood", "lawful sometimes"), "strong_textual_inference", 0.9),
    (69, 2, "concept.calumnious_defense", "corrupts_process", "concept.judicial_process", "Article 2 treats lying in defense as corrupting judicial order.", ("utter a falsehood",), "strong_textual_inference", 0.88),
    (69, 2, "concept.calumnious_defense", "harms_domain", "concept.truth_in_legal_proceedings", "Article 2 opposes calumnious defense to the truth due in judgment.", ("utter a falsehood",), "strong_textual_inference", 0.88),
    (69, 3, "concept.unjust_appeal", "abuses_role", "concept.defendant_role", "Article 3 treats appeal as sinful when used merely to delay a just sentence.", ("delay a just sentence",), "strong_textual_inference", 0.88),
    (69, 3, "concept.unjust_appeal", "corrupts_process", "concept.judicial_process", "Article 3 treats unjust appeal as a corruption of judicial order.", ("delay a just sentence",), "strong_textual_inference", 0.88),
    (70, 1, "concept.witness_role", "directed_to", "concept.truth_in_legal_proceedings", "Article 1 explicitly treats evidence as ordered to justice in court.", ("evidence is necessary",), "strong_textual_inference", 0.9),
    (70, 2, "concept.judicial_process", "requires", "concept.witness_role", "Article 2 treats witnesses as part of the proof needed in human judgments.", ("two or three witnesses",), "strong_textual_inference", 0.86),
    (70, 4, "concept.false_witness", "abuses_role", "concept.witness_role", "Article 4 explicitly treats false witness as the corruption of witness-bearing.", ("false evidence",), "strong_textual_inference", 0.92),
    (70, 4, "concept.false_witness", "corrupts_process", "concept.judicial_process", "Article 4 explicitly treats false witness as deforming the legal process.", ("false evidence",), "strong_textual_inference", 0.92),
    (70, 4, "concept.false_witness", "harms_domain", "concept.truth_in_legal_proceedings", "Article 4 explicitly treats false witness as falsehood and injustice in testimony.", ("false evidence", "falsehood"), "strong_textual_inference", 0.92),
    (70, 4, "concept.false_witness", "opposed_by", "concept.justice", "Article 4 explicitly lists injustice among the deformities of false witness.", ("injustice",), "strong_textual_inference", 0.84),
    (71, 3, "concept.dishonest_advocacy", "abuses_role", "concept.advocate_role", "Article 3 explicitly treats advocacy for an unjust cause as wrongful cooperation in evil.", ("knowingly he defends an unjust cause",)),
    (71, 3, "concept.dishonest_advocacy", "corrupts_process", "concept.judicial_process", "Article 3 treats unjust advocacy as a corruption of legal process.", ("cooperate in an evil deed",), "strong_textual_inference", 0.9),
    (71, 3, "concept.dishonest_advocacy", "requires_restitution", "concept.restitution", "Article 3 explicitly states the dishonest advocate is bound to restitution.", ("bound to restitution",)),
    (71, 4, "concept.extortionate_advocacy", "abuses_role", "concept.advocate_role", "Article 4 treats immoderate fees as sinful abuse of advocacy.", ("immoderate fee",), "strong_textual_inference", 0.86),
    (71, 4, "concept.extortionate_advocacy", "harms_domain", "concept.fairness_in_exchange", "Article 4 measures excessive advocacy fees by justice in exchange.", ("may justly receive payment", "immoderate"), "strong_textual_inference", 0.84),
    (72, 1, "concept.reviling", "harms_domain", "concept.honor", "Article 1 explicitly defines reviling as dishonoring another.", ("dishonoring of a person",)),
    (72, 2, "concept.reviling", "harms_domain", "concept.honor", "Article 2 again measures reviling by the intention to dishonor.", ("intention", "dishonor"), "strong_textual_inference", 0.88),
    (72, 4, "concept.reviling", "caused_by", "concept.anger", "Article 4 explicitly traces reviling chiefly to anger.", ("source chiefly in", "anger")),
    (73, 1, "concept.backbiting", "harms_domain", "concept.reputation", "Article 1 explicitly treats backbiting as secret injury to a good name.", ("good name",)),
    (73, 2, "concept.backbiting", "harms_domain", "concept.reputation", "Article 2 explicitly says backbiting aims at blackening a man's good name.", ("blackening a man's good name",)),
    (73, 3, "concept.backbiting", "harms_domain", "concept.reputation", "Article 3 explicitly treats good name as a particularly weighty good.", ("good name is more precious",), "strong_textual_inference", 0.88),
    (74, 1, "concept.tale_bearing", "harms_domain", "concept.friendship", "Article 1 explicitly treats tale-bearing as aiming to sever friendship.", ("sever friendship",)),
    (74, 2, "concept.tale_bearing", "harms_domain", "concept.friendship", "Article 2 again measures tale-bearing by the injury done to friendship.", ("friend is better than honor",), "strong_textual_inference", 0.88),
    (75, 1, "concept.derision", "harms_domain", "concept.honor", "Article 1 explicitly treats derision as directed to another's shame.", ("shame",), "strong_textual_inference", 0.86),
    (75, 2, "concept.derision", "harms_domain", "concept.honor", "Article 2 continues to weigh derision by the evil exposed to shame.", ("turned to ridicule",), "strong_textual_inference", 0.86),
    (76, 1, "concept.cursing", "contrary_to", "concept.charity", "Article 1 treats cursing as willing evil against another in speech.", ("command or desire", "evil"), "strong_textual_inference", 0.84),
    (76, 3, "concept.cursing", "contrary_to", "concept.charity", "Article 3 explicitly says that wishing evil to another is contrary to charity.", ("contrary to charity",)),
    (77, 1, "concept.cheating", "harms_domain", "concept.fairness_in_exchange", "Article 1 explicitly treats deceitful overpricing as injuring one's neighbor in exchange.", ("just price", "injure him"), "strong_textual_inference", 0.9),
    (77, 1, "concept.cheating", "opposed_by", "concept.justice", "Article 1 explicitly measures deceitful selling as injustice toward one's neighbor.", ("injure him",), "strong_textual_inference", 0.84),
    (77, 1, "concept.just_price", "directed_to", "concept.fairness_in_exchange", "Article 1 explicitly frames sale by worth or equality of exchange.", ("just price",), "strong_textual_inference", 0.86),
    (77, 2, "concept.cheating", "harms_domain", "concept.property", "Article 2 explicitly treats fraudulent sale of defective goods as harming the buyer.", ("fault in the thing",), "strong_textual_inference", 0.88),
    (77, 3, "concept.cheating", "harms_domain", "concept.fairness_in_exchange", "Article 3 treats concealment of faults as occasioning danger or loss in exchange.", ("danger or loss",), "strong_textual_inference", 0.86),
    (78, 1, "concept.usury", "harms_domain", "concept.fairness_in_exchange", "Article 1 explicitly says usury leads to inequality contrary to justice.", ("inequality which is contrary to justice",)),
    (78, 1, "concept.usury", "contrary_to", "concept.justice", "Article 1 explicitly calls usury unjust in itself.", ("unjust in itself",)),
    (78, 2, "concept.usury", "harms_domain", "concept.fairness_in_exchange", "Article 2 extends the injustice to money-valued consideration for a loan.", ("sin against justice",), "strong_textual_inference", 0.88),
    (78, 3, "concept.usury", "requires_restitution", "concept.restitution", "Article 3 explicitly treats the restoration of gains derived from usury.", ("restore", "usury"), "strong_textual_inference", 0.9),
    (79, 2, "concept.transgression", "contrary_to", "concept.justice", "Article 2 places transgression under the rule that justice concerns what is due.", ("steps beyond",), "strong_textual_inference", 0.82),
    (79, 3, "concept.omission", "contrary_to", "concept.justice", "Article 3 explicitly says due good belongs properly to justice.", ("good that is due", "belongs properly to justice"), "strong_textual_inference", 0.9),
):
    question_number = int(payload[0])
    article_number = int(payload[1])
    subject_id = str(payload[2])
    relation_type = str(payload[3])
    object_id = str(payload[4])
    rationale = str(payload[5])
    evidence_hints = tuple(payload[6])
    support_type = payload[7] if len(payload) > 7 else "explicit_textual"
    confidence = float(payload[8]) if len(payload) > 8 else 0.94
    add_relation(
        question_number,
        article_number,
        subject_id,
        relation_type,  # type: ignore[arg-type]
        object_id,
        support_type=support_type,  # type: ignore[arg-type]
        confidence=confidence,
        rationale=rationale,
        evidence_hints=evidence_hints,
    )


TRACT_CONCEPT_IDS = (
    {payload["concept_id"] for payload in JUSTICE_CORE_EXTRA_CONCEPTS}
    | {
        concept_id
        for seed in RELATION_SEEDS
        for concept_id in (seed.subject_id, seed.object_id)
        if concept_id.startswith("concept.")
    }
    | {seed.concept_id for seed in TREATMENT_SEEDS}
)


def is_justice_species_relation(
    subject_id: str,
    relation_type: str,
    object_id: str,
) -> bool:
    return (
        relation_type == "species_of"
        and subject_id in JUSTICE_SPECIES_CONCEPT_IDS
        and object_id in JUSTICE_SPECIES_CONCEPT_IDS
    )


def is_harmed_domain_relation(
    subject_id: str,
    relation_type: str,
    object_id: str,
) -> bool:
    return relation_type == "harms_domain" and object_id in JUSTICE_DOMAIN_CONCEPT_IDS


def is_restitution_related_relation(
    subject_id: str,
    relation_type: str,
    object_id: str,
) -> bool:
    return relation_type == "requires_restitution" or (
        "concept.restitution" in {subject_id, object_id}
    )


def is_judicial_process_relation(
    subject_id: str,
    relation_type: str,
    object_id: str,
) -> bool:
    return (
        relation_type in {"corrupts_process", "abuses_role"}
        or subject_id in JUDICIAL_ROLE_CONCEPT_IDS
        or object_id in JUDICIAL_ROLE_CONCEPT_IDS
        or subject_id in JUDICIAL_PROCESS_CONCEPT_IDS
        or object_id in JUDICIAL_PROCESS_CONCEPT_IDS
    )
