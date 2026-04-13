from __future__ import annotations

from dataclasses import dataclass

from ..models.pilot import PilotNodeType, PilotRelationType, PilotSupportType
from ..utils.ids import article_id as build_article_id
from ..utils.ids import question_id as build_question_id

PILOT_SCOPE = [
    ("i-ii", 1),
    ("i-ii", 6),
    ("i-ii", 22),
    ("i-ii", 55),
    ("i-ii", 71),
    ("i-ii", 90),
    ("i-ii", 109),
    ("ii-ii", 1),
    ("ii-ii", 23),
    ("ii-ii", 47),
    ("ii-ii", 58),
    ("ii-ii", 171),
]
PILOT_SCOPE_SET = set(PILOT_SCOPE)


def question_id(part_id: str, question_number: int) -> str:
    return build_question_id(part_id, question_number)


def article_id(part_id: str, question_number: int, article_number: int) -> str:
    return build_article_id(question_id(part_id, question_number), article_number)


def resp_id(part_id: str, question_number: int, article_number: int) -> str:
    return f"{article_id(part_id, question_number, article_number)}.resp"


def concept(
    concept_id: str,
    canonical_label: str,
    node_type: PilotNodeType,
    aliases: list[str],
    description: str,
    *,
    notes: list[str] | None = None,
    source_scope_seed: list[str] | None = None,
) -> dict[str, object]:
    return {
        "concept_id": concept_id,
        "canonical_label": canonical_label,
        "node_type": node_type,
        "aliases": aliases,
        "description": description,
        "notes": notes or [],
        "source_scope_seed": source_scope_seed or [],
    }


@dataclass(frozen=True)
class StructuralTreatedInSeed:
    source_passage_id: str
    concept_id: str
    support_type: PilotSupportType = "explicit_textual"
    confidence: float = 0.93
    evidence_hints: tuple[str, ...] = ()
    rationale: str = ""


@dataclass(frozen=True)
class DoctrinalSeed:
    source_passage_id: str
    subject_id: str
    relation_type: PilotRelationType
    object_id: str
    support_type: PilotSupportType
    confidence: float
    rationale: str
    evidence_hints: tuple[str, ...]


BASE_PILOT_CONCEPTS = [
    concept(
        "concept.end",
        "End",
        "end",
        ["end", "final cause"],
        "Generic end or final cause as treated in the pilot slice.",
    ),
    concept(
        "concept.ultimate_end",
        "Ultimate End",
        "end",
        ["ultimate end", "last end"],
        "Man's last or ultimate end.",
        notes=[
            "Keep distinct from Beatitude when a passage speaks only of end or final causality.",
        ],
    ),
    concept(
        "concept.beatitude",
        "Beatitude",
        "beatitude",
        ["beatitude", "happiness", "bliss"],
        "Beatitude or happiness as the perfected human end.",
        notes=["In the pilot slice, happiness and beatitude are normalized together."],
    ),
    concept(
        "concept.fruition",
        "Fruition",
        "act_type",
        ["fruition", "enjoyment"],
        "Enjoyment or fruition of the attained good.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.human_act",
        "Human Act",
        "act_type",
        ["human act", "human acts"],
        "Act proper to man as rational and voluntary.",
    ),
    concept(
        "concept.voluntary_act",
        "Voluntary Act",
        "act_type",
        ["voluntary", "voluntary act", "voluntary acts"],
        "Act proceeding from an intrinsic principle with knowledge of the end.",
    ),
    concept(
        "concept.involuntary_act",
        "Involuntary Act",
        "act_type",
        ["involuntary", "involuntariness", "involuntary act"],
        "Act lacking full voluntariness through violence, fear, or ignorance.",
    ),
    concept(
        "concept.will",
        "Will",
        "faculty",
        ["will"],
        "The rational appetite and proximate principle of commanded human action.",
    ),
    concept(
        "concept.choice",
        "Choice",
        "act_type",
        ["choice", "to choose"],
        "Elective act of the will.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.command",
        "Command",
        "act_type",
        ["command", "to command"],
        "Practical act applying counsel and judgment to action.",
    ),
    concept(
        "concept.intention",
        "Intention",
        "act_type",
        ["intention"],
        "Act by which the will tends toward an end.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.use_act",
        "Use",
        "act_type",
        ["use"],
        "Act of applying a thing toward an intended end.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.passion",
        "Passion",
        "passion",
        ["passion", "passions", "soul's passions"],
        "Passion of the soul considered under appetitive motion.",
    ),
    concept(
        "concept.love_passion",
        "Love (Passion)",
        "passion",
        ["love"],
        "Love understood as a passion rather than the infused virtue of charity.",
        notes=["Bare 'love' is ambiguous between passion-language and charity."],
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.hatred",
        "Hatred",
        "passion",
        ["hatred"],
        "Passion opposed to love.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.desire",
        "Desire",
        "passion",
        ["desire"],
        "Passion moving toward an absent good.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.aversion",
        "Aversion",
        "passion",
        ["aversion"],
        "Passion moving away from an apprehended evil.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.hope",
        "Hope (Passion)",
        "passion",
        ["hope"],
        "Passion moving toward a difficult future good.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.despair",
        "Despair",
        "passion",
        ["despair"],
        "Passion recoiling from a difficult good judged unattainable.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.fear",
        "Fear",
        "passion",
        ["fear"],
        "Passion shrinking from impending evil.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.anger",
        "Anger",
        "passion",
        ["anger"],
        "Passion of the irascible appetite concerning injury and vindication.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.sensitive_appetite",
        "Sensitive Appetite",
        "faculty",
        ["sensitive appetite", "appetitive power"],
        "Sensitive appetitive power in which passions are properly found.",
    ),
    concept(
        "concept.intellectual_appetite",
        "Intellectual Appetite",
        "faculty",
        ["intellectual appetite"],
        "Intellectual appetite, that is, the will.",
    ),
    concept(
        "concept.habit",
        "Habit",
        "habit",
        ["habit", "habits"],
        "Stable disposition ordering power toward act.",
    ),
    concept(
        "concept.operative_habit",
        "Operative Habit",
        "habit",
        ["operative habit"],
        "Habit ordered to operation rather than bare being.",
    ),
    concept(
        "concept.virtue",
        "Virtue",
        "virtue",
        ["virtue", "virtues"],
        "Generic virtue as good operative perfection.",
        notes=[
            "Do not collapse generic virtue into a specific virtue without explicit passage support.",
        ],
    ),
    concept(
        "concept.vice",
        "Vice",
        "vice",
        ["vice", "vicious"],
        "Vice considered as privative disorder contrary to virtue.",
    ),
    concept(
        "concept.sin",
        "Sin",
        "sin_type",
        ["sin", "sins"],
        "Bad human act contrary to due rule and measure.",
    ),
    concept(
        "concept.eternal_law",
        "Eternal Law",
        "law_type",
        ["eternal law"],
        "God's reason as the first rule of human willing.",
    ),
    concept(
        "concept.law",
        "Law",
        "law",
        ["law"],
        "Law as ordinance of reason for the common good.",
        notes=["Generic law is kept distinct from named law-types unless the text is explicit."],
    ),
    concept(
        "concept.reason",
        "Reason",
        "faculty",
        ["reason"],
        "Reason as rule and measure of human acts.",
    ),
    concept(
        "concept.practical_reason",
        "Practical Reason",
        "faculty",
        ["practical reason"],
        "Reason as applied to action and counsel.",
    ),
    concept(
        "concept.common_good",
        "Common Good",
        "end",
        ["common good", "universal happiness"],
        "Good of the whole community rather than of a private individual alone.",
    ),
    concept(
        "concept.promulgation",
        "Promulgation",
        "act_type",
        ["promulgation", "promulgated"],
        "Notification applying law to those who must be ruled by it.",
    ),
    concept(
        "concept.natural_law",
        "Natural Law",
        "law_type",
        ["natural law"],
        "Law-type reserved in the pilot registry for later tract expansion.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.human_law",
        "Human Law",
        "law_type",
        ["human law"],
        "Law-type reserved in the pilot registry for later tract expansion.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.divine_law",
        "Divine Law",
        "law_type",
        ["divine law"],
        "Law-type reserved in the pilot registry for later tract expansion.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.grace",
        "Grace",
        "grace",
        ["grace"],
        "Grace as the supernatural help needed beyond fallen nature.",
        notes=[
            "Generic grace remains distinct from operating and cooperating grace unless the text names the subtype.",
        ],
    ),
    concept(
        "concept.operating_grace",
        "Operating Grace",
        "grace_type",
        ["operating grace", "operative grace"],
        "Grace-type reserved in the pilot registry for later grace questions.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.cooperating_grace",
        "Cooperating Grace",
        "grace_type",
        ["cooperating grace", "co-operative grace"],
        "Grace-type reserved in the pilot registry for later grace questions.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.eternal_life",
        "Eternal Life",
        "end",
        ["eternal life", "everlasting life"],
        "Supernatural end exceeding the proportion of human nature.",
    ),
    concept(
        "concept.merit",
        "Merit",
        "act_type",
        ["merit", "meritorious works"],
        "Meritorious human action proportioned to supernatural end only through grace.",
    ),
    concept(
        "concept.commandments",
        "Commandments",
        "precept",
        ["commandments", "commandments of the law"],
        "Precepts whose fulfillment exceeds fallen nature without grace.",
    ),
    concept(
        "concept.perseverance",
        "Perseverance",
        "act_type",
        ["perseverance", "persevere", "persevere in good"],
        "Standing steadfastly in good without falling away.",
    ),
    concept(
        "concept.faith",
        "Faith",
        "virtue",
        ["faith"],
        "Theological virtue assenting to divine truth on God's authority.",
    ),
    concept(
        "concept.first_truth",
        "First Truth",
        "object",
        ["first truth", "divine truth"],
        "Formal object of faith considered under divine revelation.",
    ),
    concept(
        "concept.object_of_faith",
        "Object of Faith",
        "doctrine",
        ["object of faith"],
        "Formal and material object considered in the tract on faith.",
    ),
    concept(
        "concept.article_of_faith",
        "Article of Faith",
        "doctrine",
        ["article of faith", "articles of faith"],
        "Distinct doctrinal articulation within the content of faith.",
    ),
    concept(
        "concept.symbol_of_faith",
        "Symbol of Faith",
        "doctrine",
        ["symbol of faith", "symbol", "creed"],
        "Collected formula by which the truths of faith are proposed.",
    ),
    concept(
        "concept.charity",
        "Charity",
        "virtue",
        ["charity"],
        "Theological virtue of friendship with God.",
        notes=["Do not auto-normalize bare 'love' to charity outside clearly theological context."],
    ),
    concept(
        "concept.friendship_with_god",
        "Friendship with God",
        "doctrine",
        ["friendship of man for God", "friendship with God"],
        "The definitional friendship Aquinas attributes to charity.",
    ),
    concept(
        "concept.form_of_virtues",
        "Form of the Virtues",
        "doctrine",
        ["form of the virtues", "form of virtues"],
        "The ordering role by which charity informs the acts of the virtues.",
    ),
    concept(
        "concept.prudence",
        "Prudence",
        "virtue",
        ["prudence"],
        "Right reason applied to action.",
    ),
    concept(
        "concept.solicitude",
        "Solicitude",
        "act_type",
        ["solicitude", "watchfulness"],
        "Prompt watchfulness and alert execution in matters of action.",
    ),
    concept(
        "concept.false_prudence",
        "False Prudence",
        "vice",
        ["false prudence"],
        "Counterfeit prudence ordered to an apparent rather than true good.",
        notes=["Keep distinct from Prudence of the Flesh when both are named."],
    ),
    concept(
        "concept.prudence_of_flesh",
        "Prudence of the Flesh",
        "vice",
        ["prudence of the flesh"],
        "Prudence-like disposition placing ultimate end in bodily pleasure.",
        notes=["Keep distinct from generic false prudence."],
    ),
    concept(
        "concept.justice",
        "Justice",
        "virtue",
        ["justice"],
        "Moral virtue rendering acts and agents right in relation to another.",
    ),
    concept(
        "concept.general_justice",
        "General Justice",
        "virtue",
        ["general justice", "general virtue", "legal justice"],
        "Justice directing acts of virtue to the common good.",
    ),
    concept(
        "concept.particular_justice",
        "Particular Justice",
        "virtue",
        ["particular justice"],
        "Justice directing a person in relation to other individuals.",
    ),
    concept(
        "concept.rendering_due",
        "Rendering Due",
        "act_type",
        ["render to each one his own", "render to everyone his own", "his due"],
        "Proper act of justice in giving each one what is due.",
    ),
    concept(
        "concept.prophecy",
        "Prophecy",
        "charism",
        ["prophecy", "prophet", "prophets"],
        "Prophetic knowledge and utterance regarding things beyond ordinary human ken.",
        notes=["Prophecy in the pilot slice is kept distinct from the gifts of the Holy Spirit."],
    ),
    concept(
        "concept.knowledge",
        "Knowledge",
        "doctrine",
        ["knowledge", "know"],
        "Cognitive grasp used here for prophecy and other intellectual acts.",
    ),
    concept(
        "concept.future_contingents",
        "Future Contingents",
        "object",
        ["future contingencies", "things to come"],
        "Future contingent events considered as prophetic matter.",
    ),
    concept(
        "concept.gift_holy_spirit",
        "Gift of the Holy Spirit",
        "gift_holy_spirit",
        ["gift of the holy spirit", "gift of the holy ghost"],
        "Generic gift category reserved for later tract expansion.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.beatitude_generic",
        "Beatitude (Generic)",
        "beatitude",
        ["beatitudes"],
        "Generic beatitude registry node reserved for later tract expansion.",
        source_scope_seed=["pilot_registry_seed"],
    ),
    concept(
        "concept.precept",
        "Precept",
        "precept",
        ["precept", "precepts"],
        "Generic precept registry node reserved for later tract expansion.",
        source_scope_seed=["pilot_registry_seed"],
    ),
]


STRUCTURAL_TREATED_IN_SEEDS: list[StructuralTreatedInSeed] = []


def add_treated_in(
    part_id: str,
    question_number: int,
    article_number: int,
    concept_id: str,
    *,
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.93,
    evidence_hints: tuple[str, ...] = (),
    rationale: str = "",
) -> None:
    STRUCTURAL_TREATED_IN_SEEDS.append(
        StructuralTreatedInSeed(
            source_passage_id=resp_id(part_id, question_number, article_number),
            concept_id=concept_id,
            support_type=support_type,
            confidence=confidence,
            evidence_hints=evidence_hints,
            rationale=rationale,
        )
    )


for article_number in range(1, 9):
    add_treated_in("i-ii", 1, article_number, "concept.end")
for article_number in range(4, 8):
    add_treated_in("i-ii", 1, article_number, "concept.ultimate_end")

for article_number in range(1, 9):
    add_treated_in("i-ii", 6, article_number, "concept.voluntary_act")
for article_number in range(5, 9):
    add_treated_in("i-ii", 6, article_number, "concept.involuntary_act")
add_treated_in("i-ii", 6, 4, "concept.will")

for article_number in range(1, 4):
    add_treated_in("i-ii", 22, article_number, "concept.passion")
for article_number in range(2, 4):
    add_treated_in("i-ii", 22, article_number, "concept.sensitive_appetite")
add_treated_in("i-ii", 22, 3, "concept.intellectual_appetite")

for article_number in range(1, 5):
    add_treated_in("i-ii", 55, article_number, "concept.virtue")
for article_number in range(1, 3):
    add_treated_in("i-ii", 55, article_number, "concept.habit")
add_treated_in("i-ii", 55, 2, "concept.operative_habit")

add_treated_in("i-ii", 71, 1, "concept.vice")
add_treated_in("i-ii", 71, 1, "concept.virtue")
add_treated_in("i-ii", 71, 1, "concept.sin")
add_treated_in("i-ii", 71, 2, "concept.vice")
add_treated_in("i-ii", 71, 3, "concept.vice")
add_treated_in("i-ii", 71, 4, "concept.vice")
add_treated_in("i-ii", 71, 4, "concept.virtue")
add_treated_in("i-ii", 71, 5, "concept.sin")
add_treated_in("i-ii", 71, 6, "concept.sin")
add_treated_in("i-ii", 71, 6, "concept.eternal_law")

for article_number in range(1, 5):
    add_treated_in("i-ii", 90, article_number, "concept.law")
add_treated_in("i-ii", 90, 1, "concept.reason")
add_treated_in("i-ii", 90, 2, "concept.common_good")
add_treated_in("i-ii", 90, 2, "concept.beatitude")
add_treated_in("i-ii", 90, 4, "concept.promulgation")

for article_number in range(1, 11):
    add_treated_in("i-ii", 109, article_number, "concept.grace")
add_treated_in("i-ii", 109, 4, "concept.commandments")
add_treated_in("i-ii", 109, 5, "concept.eternal_life")
add_treated_in("i-ii", 109, 5, "concept.merit")
add_treated_in("i-ii", 109, 7, "concept.sin")
add_treated_in("i-ii", 109, 8, "concept.sin")
add_treated_in("i-ii", 109, 9, "concept.perseverance")
add_treated_in("i-ii", 109, 10, "concept.perseverance")

for article_number in range(1, 11):
    add_treated_in("ii-ii", 1, article_number, "concept.faith")
for article_number in range(1, 6):
    add_treated_in("ii-ii", 1, article_number, "concept.object_of_faith")
add_treated_in("ii-ii", 1, 1, "concept.first_truth")
for article_number in range(6, 9):
    add_treated_in("ii-ii", 1, article_number, "concept.article_of_faith")
for article_number in range(9, 11):
    add_treated_in("ii-ii", 1, article_number, "concept.symbol_of_faith")

for article_number in range(1, 9):
    add_treated_in("ii-ii", 23, article_number, "concept.charity")
add_treated_in("ii-ii", 23, 1, "concept.friendship_with_god")
add_treated_in("ii-ii", 23, 3, "concept.virtue")
add_treated_in("ii-ii", 23, 8, "concept.form_of_virtues")
add_treated_in("ii-ii", 23, 8, "concept.virtue")

for article_number in range(1, 17):
    add_treated_in("ii-ii", 47, article_number, "concept.prudence")
add_treated_in("ii-ii", 47, 1, "concept.reason")
add_treated_in("ii-ii", 47, 2, "concept.practical_reason")
add_treated_in("ii-ii", 47, 4, "concept.virtue")
add_treated_in("ii-ii", 47, 5, "concept.virtue")
add_treated_in("ii-ii", 47, 8, "concept.command")
add_treated_in("ii-ii", 47, 9, "concept.solicitude")
add_treated_in("ii-ii", 47, 10, "concept.common_good")
add_treated_in("ii-ii", 47, 11, "concept.common_good")
add_treated_in("ii-ii", 47, 13, "concept.false_prudence")
add_treated_in("ii-ii", 47, 13, "concept.prudence_of_flesh")

for article_number in range(1, 13):
    add_treated_in("ii-ii", 58, article_number, "concept.justice")
add_treated_in("ii-ii", 58, 3, "concept.virtue")
add_treated_in("ii-ii", 58, 4, "concept.will")
add_treated_in("ii-ii", 58, 5, "concept.general_justice")
add_treated_in("ii-ii", 58, 6, "concept.general_justice")
add_treated_in("ii-ii", 58, 7, "concept.particular_justice")
add_treated_in("ii-ii", 58, 11, "concept.rendering_due")

for article_number in range(1, 7):
    add_treated_in("ii-ii", 171, article_number, "concept.prophecy")
add_treated_in("ii-ii", 171, 1, "concept.knowledge")
add_treated_in("ii-ii", 171, 3, "concept.future_contingents")


DOCTRINAL_RELATION_SEEDS = [
    DoctrinalSeed(
        resp_id("i-ii", 22, 3),
        "concept.passion",
        "resides_in",
        "concept.sensitive_appetite",
        "explicit_textual",
        0.98,
        "The passage explicitly places passion properly in the sensitive appetite.",
        ("sensitive appetite", "passion is properly to be found"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 55, 1),
        "concept.virtue",
        "species_of",
        "concept.habit",
        "explicit_textual",
        0.99,
        "The respondeo explicitly concludes that human virtues are habits.",
        ("human virtues are habits", "habit"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 55, 2),
        "concept.virtue",
        "species_of",
        "concept.operative_habit",
        "explicit_textual",
        0.98,
        "The respondeo explicitly concludes that human virtue is an operative habit.",
        ("operative habit", "human virtue"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 71, 1),
        "concept.vice",
        "contrary_to",
        "concept.virtue",
        "explicit_textual",
        0.95,
        "The passage lists vice among the things found contrary to virtue.",
        ("contrary to virtue", "vice"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 71, 6),
        "concept.sin",
        "contrary_to",
        "concept.eternal_law",
        "explicit_textual",
        0.98,
        "The Augustinian definition explicitly says sin is contrary to the eternal law.",
        ("contrary to the eternal law", "sin"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 90, 1),
        "concept.law",
        "regulated_by",
        "concept.reason",
        "explicit_textual",
        0.98,
        "The passage explicitly says law is something pertaining to reason.",
        ("law is something pertaining to reason", "reason"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 90, 2),
        "concept.law",
        "directed_to",
        "concept.common_good",
        "explicit_textual",
        0.98,
        "The passage explicitly concludes that every law is ordained to the common good.",
        ("every law is ordained to the common good", "common good"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 90, 4),
        "concept.law",
        "requires",
        "concept.promulgation",
        "explicit_textual",
        0.97,
        "The passage explicitly states that promulgation is necessary for law to obtain its force.",
        ("promulgation is necessary", "law obtain its force"),
    ),
    DoctrinalSeed(
        resp_id("i-ii", 109, 5),
        "concept.eternal_life",
        "requires",
        "concept.grace",
        "explicit_textual",
        0.96,
        "The passage explicitly says that without grace man cannot merit everlasting life.",
        ("without grace man cannot merit everlasting life", "grace"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 1, 1),
        "concept.faith",
        "has_object",
        "concept.first_truth",
        "explicit_textual",
        0.98,
        "The formal aspect of faith's object is explicitly said to be the First Truth.",
        ("it is nothing else than the First Truth", "object of faith"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 1, 6),
        "concept.article_of_faith",
        "part_of",
        "concept.faith",
        "explicit_textual",
        0.94,
        "The passage says the matters of faith contain distinct articles fitting together as parts.",
        ("matters of Christian faith", "distinct articles"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 1, 9),
        "concept.symbol_of_faith",
        "directed_to",
        "concept.faith",
        "explicit_textual",
        0.94,
        "The symbol is defined as a collection of maxims of faith so that truth may be proposed for belief.",
        ("maxims of faith", "that he may believe it"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 23, 1),
        "concept.charity",
        "defined_as",
        "concept.friendship_with_god",
        "explicit_textual",
        0.98,
        "The passage explicitly concludes that charity is the friendship of man for God.",
        ("charity is the friendship of man for God", "friendship"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 23, 3),
        "concept.charity",
        "species_of",
        "concept.virtue",
        "explicit_textual",
        0.97,
        "The respondeo explicitly concludes that charity is a virtue.",
        ("charity is a virtue", "virtue"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 23, 8),
        "concept.virtue",
        "perfected_by",
        "concept.charity",
        "explicit_textual",
        0.94,
        "The passage says charity gives form to the acts of the virtues by directing them to the last end.",
        ("charity is called the form of the virtues", "gives the form"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 1),
        "concept.prudence",
        "resides_in",
        "concept.reason",
        "strong_textual_inference",
        0.92,
        "The passage argues that prudence belongs to the cognitive faculty rather than the appetitive power.",
        ("cognitive faculty", "prudence"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 2),
        "concept.prudence",
        "resides_in",
        "concept.practical_reason",
        "explicit_textual",
        0.98,
        "The passage explicitly limits prudence to the practical reason.",
        ("prudence resides only in the practical reason", "practical reason"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 4),
        "concept.prudence",
        "species_of",
        "concept.virtue",
        "explicit_textual",
        0.97,
        "The passage explicitly concludes that prudence has the nature of virtue.",
        ("prudence has the nature of virtue", "virtue"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 8),
        "concept.prudence",
        "has_act",
        "concept.command",
        "explicit_textual",
        0.98,
        "The passage explicitly says command is the chief act of prudence.",
        ("chief act of prudence", "command"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 9),
        "concept.prudence",
        "has_act",
        "concept.solicitude",
        "explicit_textual",
        0.97,
        "The passage explicitly says solicitude belongs properly to prudence.",
        ("solicitude belongs properly to prudence", "solicitude"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 10),
        "concept.prudence",
        "directed_to",
        "concept.common_good",
        "explicit_textual",
        0.96,
        "The passage explicitly says prudence regards not only private good but also the common good.",
        ("prudence regards", "common good"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 13),
        "concept.false_prudence",
        "opposed_by",
        "concept.prudence",
        "strong_textual_inference",
        0.9,
        "False prudence is presented as a likeness set against prudence simply so called.",
        ("false prudence", "prudence simply so-called"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 47, 13),
        "concept.prudence_of_flesh",
        "opposed_by",
        "concept.prudence",
        "strong_textual_inference",
        0.88,
        "Prudence of the flesh is named as the prudence placing ultimate end in bodily pleasure.",
        ("prudence of the flesh", "true prudence"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 58, 3),
        "concept.justice",
        "species_of",
        "concept.virtue",
        "explicit_textual",
        0.97,
        "The passage treats justice as a human virtue rendering act and agent good.",
        ("human virtue", "justice"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 58, 4),
        "concept.justice",
        "resides_in",
        "concept.will",
        "explicit_textual",
        0.98,
        "The passage explicitly concludes that justice is in the will as its subject.",
        ("justice must needs be in", "will"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 58, 5),
        "concept.general_justice",
        "species_of",
        "concept.justice",
        "explicit_textual",
        0.95,
        "The passage explicitly says justice is called a general virtue insofar as it directs to the common good.",
        ("justice is called a general virtue", "general virtue"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 58, 7),
        "concept.particular_justice",
        "species_of",
        "concept.justice",
        "explicit_textual",
        0.95,
        "The passage explicitly says there is need for particular justice besides legal justice.",
        ("there is need for particular justice", "particular justice"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 58, 11),
        "concept.justice",
        "has_act",
        "concept.rendering_due",
        "explicit_textual",
        0.97,
        "The passage explicitly defines the proper act of justice as rendering to each one his own.",
        ("proper act of justice", "render to each one his own"),
    ),
    DoctrinalSeed(
        resp_id("ii-ii", 171, 1),
        "concept.prophecy",
        "species_of",
        "concept.knowledge",
        "explicit_textual",
        0.97,
        "The passage explicitly says prophecy first and chiefly consists in knowledge.",
        ("prophecy first and chiefly consists in knowledge", "knowledge"),
    ),
]
