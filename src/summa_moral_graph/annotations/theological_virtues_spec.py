from __future__ import annotations

from dataclasses import dataclass, field

from ..models.pilot import PilotRelationType, PilotSupportType

THEOLOGICAL_VIRTUES_MIN_QUESTION = 1
THEOLOGICAL_VIRTUES_MAX_QUESTION = 46


def question_id(question_number: int) -> str:
    return f"st.ii-ii.q{question_number:03d}"


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
    support_type: PilotSupportType = "explicit_textual",
    confidence: float = 0.92,
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


for question_number, concept_id, article_number, rationale in (
    (2, "concept.act_of_faith", 1, "Question 2 explicitly treats the inward act of faith."),
    (2, "concept.faith", 2, "Question 2 treats the act belonging to faith."),
    (3, "concept.confession_of_faith", 1, "Question 3 explicitly treats confession of faith."),
    (3, "concept.faith", 1, "Question 3 treats the outward act flowing from faith."),
    (4, "concept.faith", 1, "Question 4 considers the virtue of faith itself."),
    (5, "concept.faith", 1, "Question 5 treats who may possess faith."),
    (6, "concept.faith", 1, "Question 6 treats the cause of faith."),
    (7, "concept.faith", 1, "Question 7 treats the effects of faith."),
    (8, "concept.understanding_gift", 1, "Question 8 explicitly treats the gift of understanding."),
    (8, "concept.faith", 8, "Question 8 links understanding back to faith and its certitude."),
    (9, "concept.knowledge_gift", 1, "Question 9 explicitly treats the gift of knowledge."),
    (9, "concept.faith", 1, "Question 9 treats the way knowledge serves the truth of faith."),
    (10, "concept.unbelief", 1, "Question 10 explicitly treats unbelief in general."),
    (10, "concept.faith", 1, "Question 10 measures unbelief against faith."),
    (11, "concept.heresy", 1, "Question 11 explicitly treats heresy."),
    (11, "concept.unbelief", 1, "Question 11 treats heresy as a mode of unbelief."),
    (12, "concept.apostasy", 1, "Question 12 explicitly treats apostasy."),
    (12, "concept.unbelief", 1, "Question 12 treats apostasy as pertaining to unbelief."),
    (13, "concept.blasphemy", 1, "Question 13 explicitly treats blasphemy."),
    (13, "concept.confession_of_faith", 1, "Question 13 measures blasphemy against confession of faith."),
    (
        14,
        "concept.blasphemy_against_holy_spirit",
        1,
        "Question 14 explicitly treats the sin against the Holy Spirit.",
    ),
    (14, "concept.holy_spirit", 1, "Question 14 is framed around blasphemy against the Holy Spirit."),
    (15, "concept.blindness_of_mind", 1, "Question 15 explicitly treats blindness of mind."),
    (15, "concept.dullness_of_sense", 2, "Question 15 explicitly treats dullness of sense."),
    (
        15,
        "concept.blasphemy_against_holy_spirit",
        1,
        "Question 15 continues the sin-against-the-Spirit material through its intellectual defects.",
    ),
    (16, "concept.precepts_of_faith_knowledge_and_understanding", 1, "Question 16 treats these precepts."),
    (16, "concept.faith", 1, "Question 16 explicitly treats precepts concerning faith."),
    (17, "concept.hope", 1, "Question 17 explicitly treats hope in itself."),
    (17, "concept.eternal_life", 4, "Question 17 treats the hoped-for final good."),
    (18, "concept.hope", 1, "Question 18 treats the subject of hope."),
    (18, "concept.will", 1, "Question 18 locates hope in the will."),
    (19, "concept.fear_of_lord_gift", 9, "Question 19 treats the gift of fear."),
    (
        19,
        "concept.hope",
        1,
        "The fear tract stands in the hope block and is reviewed with that doctrinal neighborhood in view.",
    ),
    (20, "concept.despair_sin", 1, "Question 20 explicitly treats despair."),
    (20, "concept.hope", 1, "Question 20 treats despair as the contrary movement to hope."),
    (21, "concept.presumption", 1, "Question 21 explicitly treats presumption."),
    (21, "concept.hope", 3, "Question 21 treats presumption as more directly opposed to hope."),
    (22, "concept.precepts_of_hope_and_fear", 1, "Question 22 explicitly treats these precepts."),
    (22, "concept.hope", 1, "Question 22 treats precepts concerning the act of hope."),
    (24, "concept.charity", 1, "Question 24 treats the subject of charity."),
    (24, "concept.will", 1, "Question 24 locates charity in the will."),
    (24, "concept.holy_spirit", 2, "Question 24 treats charity as infused by the Holy Spirit."),
    (25, "concept.charity", 1, "Question 25 treats the object of charity."),
    (25, "concept.god", 1, "Question 25 explicitly treats charity's love of God."),
    (25, "concept.neighbor", 1, "Question 25 explicitly treats charity's love of neighbor."),
    (26, "concept.charity", 1, "Question 26 treats the order of charity."),
    (26, "concept.god", 2, "Question 26 explicitly orders charity first toward God."),
    (26, "concept.neighbor", 2, "Question 26 orders charity's extension to neighbor from God."),
    (27, "concept.love_act", 1, "Question 27 treats the principal act of charity, namely love."),
    (27, "concept.charity", 1, "Question 27 measures love as the proper act of charity."),
    (28, "concept.joy", 1, "Question 28 explicitly treats joy."),
    (28, "concept.charity", 1, "Question 28 treats joy as proceeding from charity."),
    (29, "concept.peace", 3, "Question 29 explicitly treats peace."),
    (29, "concept.charity", 3, "Question 29 treats peace as effected by charity."),
    (30, "concept.mercy", 3, "Question 30 explicitly treats mercy."),
    (30, "concept.charity", 3, "Question 30 treats mercy within the charity tract."),
    (31, "concept.beneficence", 1, "Question 31 explicitly treats beneficence."),
    (31, "concept.charity", 1, "Question 31 treats beneficence as an act of charity."),
    (32, "concept.almsgiving", 1, "Question 32 explicitly treats almsgiving."),
    (32, "concept.mercy", 1, "Question 32 treats almsgiving as an act of mercy."),
    (32, "concept.charity", 1, "Question 32 treats almsgiving as an act of charity through mercy."),
    (33, "concept.fraternal_correction", 1, "Question 33 explicitly treats fraternal correction."),
    (33, "concept.charity", 1, "Question 33 treats fraternal correction as an act of charity."),
    (34, "concept.hatred_sin", 3, "Question 34 explicitly treats hatred."),
    (34, "concept.love_act", 3, "Question 34 measures hatred against due love."),
    (34, "concept.charity", 3, "Question 34 treats hatred within the contrary-to-charity tract."),
    (35, "concept.sloth", 1, "Question 35 explicitly treats sloth."),
    (35, "concept.joy", 3, "Question 35 measures sloth against joy in God."),
    (35, "concept.charity", 3, "Question 35 measures sloth against charity's proper effect."),
    (36, "concept.envy", 1, "Question 36 explicitly treats envy."),
    (36, "concept.charity", 3, "Question 36 explicitly measures envy against charity."),
    (37, "concept.discord", 1, "Question 37 explicitly treats discord."),
    (37, "concept.concord", 1, "Question 37 explicitly treats the concord destroyed by discord."),
    (37, "concept.charity", 1, "Question 37 traces concord back to charity."),
    (38, "concept.contention", 1, "Question 38 explicitly treats contention."),
    (39, "concept.schism", 1, "Question 39 explicitly treats schism."),
    (39, "concept.ecclesial_unity", 1, "Question 39 explicitly treats the unity broken by schism."),
    (39, "concept.charity", 1, "Question 39 traces ecclesial unity back to charity."),
    (40, "concept.war", 1, "Question 40 explicitly treats war."),
    (40, "concept.common_good", 1, "Question 40 measures war by the defense of the common good."),
    (41, "concept.strife", 1, "Question 41 explicitly treats strife."),
    (41, "concept.war", 1, "Question 41 treats strife as private war."),
    (42, "concept.sedition", 1, "Question 42 explicitly treats sedition."),
    (42, "concept.peace", 1, "Question 42 measures sedition against a people's peace."),
    (43, "concept.scandal", 1, "Question 43 explicitly treats scandal."),
    (43, "concept.charity", 2, "Question 43 treats scandal under charity's solicitude for a neighbor."),
    (44, "concept.precepts_of_charity", 1, "Question 44 explicitly treats the precepts of charity."),
    (44, "concept.charity", 1, "Question 44 explicitly makes charity the end of the commandment."),
    (45, "concept.wisdom_gift", 1, "Question 45 explicitly treats the gift of wisdom."),
    (45, "concept.charity", 2, "Question 45 treats wisdom as caused by charity."),
    (45, "concept.beatitude_peacemakers", 6, "Question 45 treats the beatitude corresponding to wisdom."),
    (46, "concept.folly", 1, "Question 46 explicitly treats folly."),
    (46, "concept.wisdom_gift", 1, "Question 46 measures folly against wisdom."),
):
    add_question_treatment(
        question_number,
        concept_id,
        article_number=article_number,
        rationale=rationale,
    )


add_relation(
    2,
    2,
    "concept.faith",
    "has_act",
    "concept.act_of_faith",
    rationale="Question 2 explicitly identifies believing as the act of faith.",
    evidence_hints=("act of faith", "to believe", "an act of faith"),
)
add_relation(
    2,
    9,
    "concept.faith",
    "has_act",
    "concept.act_of_faith",
    rationale="Question 2 again treats the act of believing as the act of faith.",
    evidence_hints=("act of faith", "act of believing"),
)
add_relation(
    3,
    1,
    "concept.faith",
    "has_act",
    "concept.confession_of_faith",
    rationale="Question 3 explicitly treats confession as the outward act of faith.",
    evidence_hints=("outward confession", "act of faith", "outward confession of them"),
)
add_relation(
    6,
    1,
    "concept.faith",
    "caused_by",
    "concept.god",
    rationale="The tract explicitly states that faith must be from God.",
    evidence_hints=("faith must needs be from God", "faith must needs be from God"),
)
add_relation(
    8,
    7,
    "concept.understanding_gift",
    "corresponds_to",
    "concept.beatitude_clean_of_heart",
    rationale="Question 8 explicitly assigns the sixth beatitude to the gift of understanding.",
    evidence_hints=("sixth beatitude", "responds to the gift of understanding"),
)
add_relation(
    9,
    1,
    "concept.faith",
    "perfected_by",
    "concept.understanding_gift",
    rationale="The tract states that sound grasp of what is proposed to faith pertains to the gift of understanding.",
    evidence_hints=("gift of understanding", "things that are proposed to be believed"),
)
add_relation(
    9,
    1,
    "concept.faith",
    "perfected_by",
    "concept.knowledge_gift",
    rationale="The tract states that right judgment about what is to be believed requires the gift of knowledge.",
    evidence_hints=("gift of knowledge", "right judgment"),
)
add_relation(
    9,
    4,
    "concept.knowledge_gift",
    "corresponds_to",
    "concept.beatitude_mourn",
    rationale="Question 9 explicitly states that the beatitude of sorrow corresponds to the gift of knowledge.",
    evidence_hints=("beatitude of sorrow", "correspond to the gift of knowledge"),
)
add_relation(
    10,
    1,
    "concept.unbelief",
    "opposed_by",
    "concept.faith",
    rationale="Question 10 defines unbelief precisely as opposition to the faith.",
    evidence_hints=("opposition to the faith", "unbelief is a sin"),
)
add_relation(
    11,
    1,
    "concept.heresy",
    "species_of",
    "concept.unbelief",
    rationale="Question 11 explicitly treats heresy as a species of unbelief.",
    evidence_hints=("species of unbelief",),
)
add_relation(
    12,
    1,
    "concept.apostasy",
    "species_of",
    "concept.unbelief",
    rationale="Question 12 explicitly states that apostasy simply so called pertains to unbelief.",
    evidence_hints=("pertains to unbelief", "apostasy"),
)
add_relation(
    13,
    1,
    "concept.blasphemy",
    "opposed_by",
    "concept.confession_of_faith",
    rationale="Question 13 explicitly opposes blasphemy to confession of faith.",
    evidence_hints=("opposed to confession of faith",),
)
add_relation(
    14,
    2,
    "concept.despair_sin",
    "species_of",
    "concept.blasphemy_against_holy_spirit",
    rationale="Question 14 enumerates despair among the species assigned to the sin against the Holy Spirit.",
    evidence_hints=('despair', 'sin against the Holy Ghost'),
)
add_relation(
    14,
    2,
    "concept.presumption",
    "species_of",
    "concept.blasphemy_against_holy_spirit",
    rationale="Question 14 enumerates presumption among the species assigned to the sin against the Holy Spirit.",
    evidence_hints=('presumption', 'sin against the Holy Ghost'),
)
add_relation(
    16,
    1,
    "concept.faith",
    "regulated_by",
    "concept.precepts_of_faith_knowledge_and_understanding",
    rationale="Question 16 explicitly allows precepts to be given about the articles of faith.",
    evidence_hints=("precepts of faith", "received many precepts of faith"),
)
add_relation(
    17,
    4,
    "concept.hope",
    "directed_to",
    "concept.eternal_life",
    rationale="Question 17 treats eternal happiness as the last end hoped for from God.",
    evidence_hints=("eternal happiness", "last end"),
)
add_relation(
    17,
    7,
    "concept.hope",
    "requires",
    "concept.faith",
    rationale="Question 17 explicitly states that faith precedes hope.",
    evidence_hints=("faith precedes hope",),
)
add_relation(
    18,
    1,
    "concept.hope",
    "resides_in",
    "concept.will",
    rationale="Question 18 explicitly locates hope in the higher appetite called the will.",
    evidence_hints=("hope resides", "called the will", "higher appetite"),
)
add_relation(
    19,
    12,
    "concept.fear_of_lord_gift",
    "corresponds_to",
    "concept.beatitude_poor_in_spirit",
    rationale="Question 19 explicitly assigns poverty of spirit to the gift of fear.",
    evidence_hints=("Poverty of spirit properly corresponds to fear",),
)
add_relation(
    20,
    1,
    "concept.hope",
    "opposed_by",
    "concept.despair_sin",
    rationale="Question 20 describes despair as the contrary movement to virtuous hope.",
    evidence_hints=("contrary movement of despair", "movement of hope"),
)
add_relation(
    21,
    1,
    "concept.presumption",
    "species_of",
    "concept.blasphemy_against_holy_spirit",
    rationale="Question 21 explicitly says that this presumption is properly the sin against the Holy Ghost.",
    evidence_hints=("sin against the Holy Ghost", "presumption"),
)
add_relation(
    21,
    3,
    "concept.hope",
    "opposed_by",
    "concept.presumption",
    rationale="Question 21 explicitly says presumption is more directly opposed to hope.",
    evidence_hints=("more directly opposed to hope",),
)
add_relation(
    22,
    1,
    "concept.hope",
    "regulated_by",
    "concept.precepts_of_hope_and_fear",
    rationale="Question 22 explicitly treats the precept of hope and its legal role.",
    evidence_hints=("precept of hope", "precepts relating to the act of hope"),
)
add_relation(
    24,
    1,
    "concept.charity",
    "resides_in",
    "concept.will",
    rationale="Question 24 explicitly locates charity in the will.",
    evidence_hints=("subject of charity", "the will"),
)
add_relation(
    24,
    2,
    "concept.charity",
    "caused_by",
    "concept.holy_spirit",
    rationale="Question 24 explicitly states that charity is in us by the infusion of the Holy Ghost.",
    evidence_hints=("infusion of the Holy Ghost", "created charity"),
)
add_relation(
    25,
    1,
    "concept.charity",
    "has_object",
    "concept.god",
    rationale="Question 25 explicitly states that the same act of charity loves God.",
    evidence_hints=("same act whereby we love God", "love God"),
)
add_relation(
    25,
    1,
    "concept.charity",
    "has_object",
    "concept.neighbor",
    rationale="Question 25 explicitly states that the same act of charity loves our neighbor.",
    evidence_hints=("love our neighbor", "same act whereby we love"),
)
add_relation(
    25,
    8,
    "concept.charity",
    "has_object",
    "concept.neighbor",
    rationale="Question 25 explicitly includes enemies under the neighbor-love required by charity in general.",
    evidence_hints=("love given to our neighbor in general", "love of one's enemies"),
)
add_relation(
    26,
    2,
    "concept.charity",
    "has_object",
    "concept.god",
    rationale="Question 26 explicitly says that God ought to be loved chiefly and before all out of charity.",
    evidence_hints=("God ought to be loved chiefly and before all out of charity",),
)
add_relation(
    27,
    1,
    "concept.charity",
    "has_act",
    "concept.love_act",
    rationale="Question 27 explicitly states that to love belongs to charity as charity.",
    evidence_hints=("To love belongs to charity",),
)
add_relation(
    28,
    1,
    "concept.joy",
    "caused_by",
    "concept.charity",
    rationale="Question 28 explicitly says that spiritual joy about God is caused by charity.",
    evidence_hints=("spiritual joy", "caused by charity"),
)
add_relation(
    29,
    3,
    "concept.peace",
    "caused_by",
    "concept.charity",
    rationale="Question 29 explicitly says that the unions implied in peace are effected by charity.",
    evidence_hints=("effected by charity", "Peace implies"),
)
add_relation(
    31,
    1,
    "concept.charity",
    "has_act",
    "concept.beneficence",
    rationale="Question 31 explicitly calls beneficence in general an act of friendship and consequently of charity.",
    evidence_hints=("act of friendship", "consequently, of charity"),
)
add_relation(
    32,
    1,
    "concept.mercy",
    "caused_by",
    "concept.charity",
    rationale="Question 32 explicitly states that mercy is an effect of charity.",
    evidence_hints=("mercy is an effect of charity",),
)
add_relation(
    32,
    1,
    "concept.charity",
    "has_act",
    "concept.almsgiving",
    rationale="Question 32 explicitly says that almsgiving is an act of charity through mercy.",
    evidence_hints=("almsgiving is an act of charity", "through the medium of mercy"),
)
add_relation(
    33,
    1,
    "concept.charity",
    "has_act",
    "concept.fraternal_correction",
    rationale="Question 33 explicitly says that fraternal correction is an act of charity.",
    evidence_hints=("fraternal correction is an act of charity",),
)
add_relation(
    34,
    3,
    "concept.hatred_sin",
    "opposed_by",
    "concept.love_act",
    rationale="Question 34 explicitly states that hatred is opposed to love.",
    evidence_hints=("Hatred is opposed to love",),
)
add_relation(
    35,
    3,
    "concept.sloth",
    "opposed_by",
    "concept.charity",
    rationale="Question 35 explicitly states that sloth is contrary to charity by its genus.",
    evidence_hints=("contrary to charity",),
)
add_relation(
    35,
    3,
    "concept.sloth",
    "opposed_by",
    "concept.joy",
    rationale="Question 35 explicitly opposes sloth to the joy in God that is charity's proper effect.",
    evidence_hints=("proper effect of charity is joy in God",),
)
add_relation(
    36,
    3,
    "concept.envy",
    "opposed_by",
    "concept.charity",
    rationale="Question 36 explicitly states that envy is contrary to charity.",
    evidence_hints=("contrary to charity", "charity rejoices in our neighbor's good"),
)
add_relation(
    37,
    1,
    "concept.concord",
    "caused_by",
    "concept.charity",
    rationale="Question 37 explicitly states that concord results from charity.",
    evidence_hints=("concord results from charity",),
)
add_relation(
    37,
    1,
    "concept.discord",
    "opposed_by",
    "concept.concord",
    rationale="Question 37 explicitly states that discord is opposed to concord.",
    evidence_hints=("Discord is opposed to concord",),
)
add_relation(
    39,
    1,
    "concept.ecclesial_unity",
    "caused_by",
    "concept.charity",
    rationale="Question 39 explicitly states that the unity severed by schism is the effect of charity.",
    evidence_hints=("unity which is the effect of charity",),
)
add_relation(
    39,
    1,
    "concept.schism",
    "opposed_by",
    "concept.ecclesial_unity",
    rationale="Question 39 explicitly states that schism is directly and essentially opposed to unity.",
    evidence_hints=("directly and essentially opposed to unity",),
)
add_relation(
    41,
    1,
    "concept.strife",
    "species_of",
    "concept.war",
    rationale="Question 41 explicitly states that strife is a kind of private war.",
    evidence_hints=("a kind of private war",),
)
add_relation(
    42,
    1,
    "concept.sedition",
    "opposed_by",
    "concept.peace",
    rationale="Question 42 explicitly states that sedition is opposed to the peace of a people.",
    evidence_hints=("opposed to a special kind of good", "peace of a people"),
)
add_relation(
    43,
    2,
    "concept.scandal",
    "opposed_by",
    "concept.charity",
    rationale="Question 43 explicitly says active scandal acts against charity.",
    evidence_hints=("acts against charity",),
)
add_relation(
    44,
    1,
    "concept.charity",
    "regulated_by",
    "concept.precepts_of_charity",
    rationale="Question 44 explicitly says that the end of the commandment is charity.",
    evidence_hints=("The end of the commandment is charity",),
)
add_relation(
    44,
    8,
    "concept.charity",
    "regulated_by",
    "concept.precepts_of_charity",
    rationale="Question 44 explicitly states that the order of charity comes under the precept.",
    evidence_hints=("order of charity must come under the precept",),
)
add_relation(
    45,
    2,
    "concept.wisdom_gift",
    "caused_by",
    "concept.charity",
    rationale="Question 45 explicitly says that the gift of wisdom has charity as its cause.",
    evidence_hints=("wisdom which is a gift", "cause is charity"),
)
add_relation(
    45,
    2,
    "concept.charity",
    "perfected_by",
    "concept.wisdom_gift",
    support_type="strong_textual_inference",
    confidence=0.88,
    rationale="Question 45 grounds the wisdom gift in charity's connaturality with divine things, which strongly supports wisdom as charity's corresponding perfection.",
    evidence_hints=("result of charity", "gift of the Holy Ghost"),
)
add_relation(
    45,
    6,
    "concept.wisdom_gift",
    "corresponds_to",
    "concept.beatitude_peacemakers",
    rationale="Question 45 explicitly ascribes the peacemakers beatitude to the gift of wisdom.",
    evidence_hints=("peacemakers", "gift of wisdom"),
)
add_relation(
    46,
    1,
    "concept.folly",
    "opposed_by",
    "concept.wisdom_gift",
    support_type="strong_textual_inference",
    confidence=0.86,
    rationale="Question 46 explicitly opposes folly to wisdom; within this tract the reviewed alignment is to the gift of wisdom treated immediately before it.",
    evidence_hints=("folly is fittingly opposed to wisdom",),
)


TRACT_CONCEPT_IDS = {
    "concept.act_of_faith",
    "concept.apostasy",
    "concept.article_of_faith",
    "concept.beneficence",
    "concept.beatitude_clean_of_heart",
    "concept.beatitude_mourn",
    "concept.beatitude_peacemakers",
    "concept.beatitude_poor_in_spirit",
    "concept.blasphemy",
    "concept.blasphemy_against_holy_spirit",
    "concept.blindness_of_mind",
    "concept.charity",
    "concept.common_good",
    "concept.confession_of_faith",
    "concept.concord",
    "concept.contention",
    "concept.discord",
    "concept.despair_sin",
    "concept.dullness_of_sense",
    "concept.ecclesial_unity",
    "concept.envy",
    "concept.eternal_life",
    "concept.faith",
    "concept.first_truth",
    "concept.folly",
    "concept.form_of_virtues",
    "concept.fraternal_correction",
    "concept.friendship_with_god",
    "concept.god",
    "concept.hatred_sin",
    "concept.heresy",
    "concept.holy_spirit",
    "concept.hope",
    "concept.joy",
    "concept.knowledge_gift",
    "concept.love_act",
    "concept.mercy",
    "concept.neighbor",
    "concept.object_of_faith",
    "concept.peace",
    "concept.precepts_of_charity",
    "concept.precepts_of_faith_knowledge_and_understanding",
    "concept.precepts_of_hope_and_fear",
    "concept.presumption",
    "concept.scandal",
    "concept.schism",
    "concept.sloth",
    "concept.strife",
    "concept.symbol_of_faith",
    "concept.theological_virtue",
    "concept.understanding_gift",
    "concept.unbelief",
    "concept.virtue",
    "concept.war",
    "concept.will",
    "concept.wisdom_gift",
    "concept.almsgiving",
    "concept.fear_of_lord_gift",
    "concept.sedition",
}
