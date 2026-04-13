# Annotation Guide

## Core Rule

A reviewed edge is acceptable only when it can be traced to a real passage id and defended from the cited text.

The canonical evidence unit is the interim segment id, not a whole question or tract.

## Structural vs Doctrinal vs Candidate

Use `structural` when the repo is recording organizational facts such as:

- a question containing an article
- an article clearly treating a concept

Use `doctrinal` when the cited passage supports a real relation claim such as:

- `virtue contrary_to vice`
- `law directed_to common_good`
- `faith has_object first_truth`
- `charity defined_as friendship_with_god`
- `prudence has_act command`
- `theft harms_domain property`
- `false_witness corrupts_process judicial_process`
- `dishonest_advocacy requires_restitution restitution`

Keep an item in `candidate` when:

- the wording is ambiguous
- the concept mapping is not stable yet
- the relation depends mostly on editorial synthesis
- confidence would drop below the current review threshold

Do not promote candidate material automatically.

## Full-Corpus Candidate Workflow

The full-corpus workflow now produces:

- candidate concept mentions
- candidate relation proposals
- review queue summaries
- question-specific markdown packets

These are review aids only. They are not reviewed doctrine and must not be shown as reviewed graph facts unless a human explicitly promotes them into a reviewed annotation file.

## Support Types

- `explicit_textual`: the passage directly states or clearly names the relation
- `strong_textual_inference`: the passage strongly supports the relation, but not in a clean formula
- `structural_editorial`: the relation is mainly organizational or editorial and should stay out of default doctrinal exports

Default doctrinal graph views should foreground only doctrinal annotations with textual support.

## When To Approve A Doctrinal Edge

Approve a doctrinal edge when the passage supports a claim about:

- opposition
- correspondence
- perfection
- causation
- regulation
- direction to an end
- hierarchy or species
- act, object, or faculty location

Reject or defer a doctrinal edge when the passage only:

- names a topic without relating it
- offers a gloss better handled in a note
- uses a generic label that could name several concepts
- requires outside theological knowledge to make the link look stronger than the text itself does

## Concept Collapse Rules

Do not collapse two labels into one concept unless the registry and the passage justify it.

Be especially careful with:

- `ultimate end` vs `beatitude`
- `charity` vs `love` when `love` may mean a passion
- `charity` vs `love (act)` when the text is speaking about charity's principal act rather than the virtue as habit
- `despair` as passion vs `despair` as sin
- `hatred` as passion vs `hatred` as sin
- generic `law` vs a named law type
- generic `grace` vs operating or cooperating grace
- generic `virtue` vs a specific virtue
- `false prudence` vs `prudence of the flesh`

If ambiguity remains, record it in registry notes, alias overrides, or candidate review files instead of forcing equivalence.

## When To Reuse A Concept Id

Reuse an existing concept id when:

- the passage wording fits the canonical concept without strain
- aliases or normalization notes already cover the wording safely
- the concept would remain doctrinally stable across questions

Create or defer a new concept id when:

- the phrase names a real distinction that would be flattened by reuse
- the English wording is homonymous across passions, virtues, laws, or graces
- the registry needs a narrower or broader concept than any current node

If unsure, keep the item in candidate and record the ambiguity in the review packet or registry notes.

## Confidence Guidance

Suggested ranges:

- `0.95–0.99`: direct textual definition, enumeration, or explicit opposition
- `0.90–0.94`: strong doctrinal support with small interpretive compression
- `0.85–0.89`: borderline reviewed material that should stay visible for human re-check
- below `0.85`: usually better kept in candidate review

Confidence should reflect the passage support, not how plausible the claim feels from outside knowledge.

## Ambiguity Handling

When a label is ambiguous:

- keep the registry canonical label narrow
- store safe aliases only
- declare known ambiguous labels in `data/gold/pilot_alias_overrides.yml`
- prefer notes over forced merges

The normalization layer is conservative by design. It does not do fuzzy theology.

## Structural Treatment Annotations

`treated_in` should be used conservatively.

It is appropriate when the article's respondeo genuinely treats the concept as a topic of discussion. It is not appropriate merely because the concept could be inferred from broader tract context.

In the theological virtues block, question-level `treated_in` is also acceptable when:

- the question title and opening respondeo are plainly centered on that concept, and
- the annotation is being used as a reviewed structural-editorial correspondence rather than a doctrinal edge.

Do not use `treated_in` to smuggle doctrinal relations into the structural layer.

## Candidate Review Practice

When reviewing a packet:

1. verify the concept match against the passage text itself
2. reject ambiguous matches that depend on broad thematic guessing
3. approve only the smallest defensible relation claim
4. preserve evidence text and rationale in the reviewed annotation
5. leave unresolved items in candidate rather than forcing closure

Doctrinal review should stay slower than candidate generation. That asymmetry is intentional.

## Prudence-Specific Rule

The prudence tract keeps its own higher-precision part taxonomy:

- `integral_part_of`
- `subjective_part_of`
- `potential_part_of`

Do not collapse those typed prudence-part relations into generic notes or generic `part_of`.

## Justice Core Rule

For `II-II, qq. 57–79`, keep these distinctions explicit:

- justice species vs generic justice:
  - `general_justice`
  - `particular_justice`
  - `distributive_justice`
  - `commutative_justice`
- wrong act vs harmed domain:
  - `theft` is not `property`
  - `backbiting` is not `reputation`
  - `false_witness` is not `truth_in_legal_proceedings`
- role/process vs person:
  - `judge_role`
  - `accuser_role`
  - `defendant_role`
  - `witness_role`
  - `advocate_role`
  - `judicial_process`

Justice-specific review rules:

- use `harms_domain` only when the passage supports a stable domain of injury:
  - `property`
  - `honor`
  - `reputation`
  - `friendship`
  - `truth_in_legal_proceedings`
  - `fairness_in_distribution`
  - `fairness_in_exchange`
- use `requires_restitution` only when the text supports an actual restorative obligation, not merely because the act feels reparable
- use `corrupts_process` when the passage concerns deformation of judicial order, accusation, testimony, judgment, or legal defense
- use `abuses_role` when the passage is about misuse of an office-role rather than generic wrongdoing

Do not collapse a tract-specific wrong act into a generic vice label when Aquinas is making a narrower juridical distinction:

- `robbery` is not just `injustice` in the abstract
- `false_accusation` is not just `lying`
- `extortionate_advocacy` is not just `avarice`
- `respect_of_persons` is not just a loose note about favoritism

Doctrinal relation vs descriptive gloss:

- approve a doctrinal justice edge when the passage supports a stable claim like:
  - `distributive_justice species_of particular_justice`
  - `respect_of_persons opposed_by distributive_justice`
  - `false_witness harms_domain truth_in_legal_proceedings`
- keep a descriptive gloss out of the graph when the passage only offers:
  - a comparison
  - a rhetorical illustration
  - a wider moral backdrop without a stable tract-specific relation

## Theological Virtues Rule

For `II-II, qq. 1–46`, keep these distinctions explicit:

- virtue vs act:
  - `charity`
  - `love (act)`
  - `confession of faith`
  - `beneficence`
  - `almsgiving`
  - `fraternal correction`
- virtue vs opposing sin:
  - `faith` vs `unbelief`
  - `hope` vs `despair (sin)` / `presumption`
  - `charity` vs `hatred (sin)` / `sloth` / `envy`
- doctrinal relation vs editorial tract framing:
  - `faith perfected_by understanding_gift`
  - `hope perfected_by fear_of_lord_gift`
  - `charity perfected_by wisdom_gift`

Use `structural_editorial` when a correspondence depends mainly on tract organization or conservative synthesis rather than the passage's direct wording.

## Religion Tract Rule

For `II-II, qq. 80–100`, keep these distinctions explicit:

- virtue vs act:
  - `religion`
  - `devotion`
  - `prayer`
  - `adoration`
  - `sacrifice`
  - `oblation`
  - `first_fruits`
  - `tithes`
  - `vow`
  - `oath`
  - `adjuration`
- positive act vs opposed vice:
  - `oath` is not `perjury`
  - `religion` is not `superstition`
  - `religion` is not `sacrilege`
  - `religion` is not `simony`
- sacred object or domain vs vice:
  - `divine_name` is not `perjury`
  - `sacred_thing` is not `sacrilege`
  - `spiritual_thing` is not `simony`

Religion-specific review rules:

- use `annexed_to` only for the tract-bridge claim that religion is annexed to justice; if that claim is supported mainly by tract framing rather than article argument, keep it `structural_editorial`
- use `has_act` when a passage supports a real act-of-religion relation:
  - `religion has_act prayer`
  - `religion has_act sacrifice`
  - `religion has_act vow`
- use `excess_opposed_to` for superstition-side excesses, not for every generic contrary:
  - `idolatry excess_opposed_to religion`
  - `divination excess_opposed_to religion`
- use `deficiency_opposed_to` for irreligion-side defects:
  - `perjury deficiency_opposed_to oath`
  - `sacrilege deficiency_opposed_to religion`
- use `concerns_sacred_object` for positive ordering toward stable sacred domains:
  - `oath concerns_sacred_object divine_name`
  - `vow concerns_sacred_object promise_to_god`
- use `misuses_sacred_object` when the wrong consists in profaning or abusing a sacred object:
  - `sacrilege misuses_sacred_object sacred_place`
  - `perjury misuses_sacred_object divine_name`
- use `corrupts_spiritual_exchange` only for simony-style sacred commerce distortion, not for ordinary unjust exchange

Do not collapse distinct divine-name or promise acts:

- `oath`
- `vow`
- `adjuration`

These remain separate even when they share reverential language.

Do not collapse superstition-side material into one generic bucket:

- `undue_worship_of_true_god`
- `idolatry`
- `divination`
- `superstitious_observance`

Doctrinal relation vs descriptive gloss:

- approve a doctrinal religion-tract edge when the passage supports a stable claim like:
  - `religion has_act prayer`
  - `idolatry excess_opposed_to religion`
  - `sacrilege misuses_sacred_object sacred_thing`
- keep the item out of the doctrinal graph when the passage only offers:
  - a broad comparison between worship practices
  - a rhetorical explanation of reverence without a stable relation
  - an example that would force `oath`, `vow`, and `adjuration` into one flattened speech-act node

## Owed-Relation Tract Rule

For `II-II, qq. 101–108`, keep these distinctions explicit:

- due mode vs generic respect:
  - `origin`
  - `excellence`
  - `authority`
  - `benefaction`
  - `rectificatory`
- virtue vs role:
  - `piety` is not `parent_role`
  - `observance` is not `person_in_dignity_role`
  - `obedience` is not `superior_role`
  - `gratitude` is not `benefactor_role`
- rectificatory response vs generic opposition:
  - `vengeance` is not generic `anger`
  - `prior_wrong` is not the same thing as the virtue that rectifies it

Owed-relation review rules:

- use `due_mode` on every doctrinal annotation and doctrinal edge in this tract
- use `concerns_due_to` when the passage identifies the distinct kind of debt:
  - `piety concerns_due_to origin_related_due`
  - `gratitude concerns_due_to benefaction_related_due`
- use `owed_to_role` only for stable role-level targets, never person instances:
  - `piety owed_to_role parent_role`
  - `obedience owed_to_role superior_role`
- use `responds_to_command` for the authority-command structure:
  - `obedience responds_to_command command`
- use `responds_to_benefaction` for benefit-repayment structure:
  - `gratitude responds_to_benefaction benefaction`
- use `rectifies_wrong` when the passage is about punitive or corrective response to prior wrong:
  - `vengeance rectifies_wrong prior_wrong`

Do not collapse these distinct debts into one general justice note:

- origin-related duty to parents and country
- excellence-related duty to persons in dignity
- authority-related duty under command
- benefaction-related duty to a benefactor
- rectificatory due after prior wrong

Doctrinal relation vs descriptive gloss:

- approve a doctrinal owed-relation edge when the passage supports a stable claim like:
  - `piety owed_to_role parent_role`
  - `obedience responds_to_command command`
  - `ingratitude contrary_to gratitude`
  - `vengeance rectifies_wrong prior_wrong`
- keep it out of the doctrinal graph when the passage only:
  - uses broad reverential language without fixing the due mode
  - compares several superiors without identifying the relevant owed relation
  - would force benefaction, authority, and excellence into one undifferentiated schema

## Connected Virtues 109-120 Rule

For `II-II, qq. 109–120`, keep the four sub-clusters explicit:

- self-presentation:
  - `truth_self_presentation`
  - `lying`
  - `dissimulation`
  - `hypocrisy`
  - `boasting`
  - `irony`
- ordinary social interaction:
  - `friendliness_affability`
  - `flattery`
  - `quarreling`
- external goods:
  - `liberality`
  - `covetousness`
  - `prodigality`
  - `external_goods`
  - `giving`
  - `retaining`
- epikeia / equity:
  - `epikeia`
  - `legal_letter`
  - `intent_of_law`
  - `common_good`
  - `law`

Connected-virtues review rules:

- use `connected_virtues_cluster` on every doctrinal annotation and doctrinal edge in this tract:
  - `self_presentation`
  - `social_interaction`
  - `external_goods`
  - `legal_equity`
- use `concerns_self_presentation` for the tract-local self-manifestation domain, not for theological truth:
  - `truth_self_presentation concerns_self_presentation self_presentation`
  - `boasting concerns_self_presentation self_presentation`
- distinguish dissimulation, hypocrisy, boasting, and irony rather than collapsing them into generic falsehood:
  - `hypocrisy species_of dissimulation`
  - `boasting species_of lying`
  - `irony contrary_to truth_self_presentation`
- use `concerns_social_interaction` for affability material:
  - `friendliness_affability concerns_social_interaction social_interaction`
  - `flattery concerns_social_interaction social_interaction`
- keep affability distinct from charity:
  - approve `friendliness_affability opposed_by flattery`
  - do not rewrite affability passages as generic charity notes unless the text itself makes that move
- use `concerns_external_goods` and related act/object structure for liberality material:
  - `liberality concerns_external_goods external_goods`
  - `liberality has_act giving`
  - `covetousness has_act retaining`
- keep liberality distinct from mercy, almsgiving, and wider justice/exchange material unless the passage itself warrants a narrower overlap
- use `corrects_legal_letter` and `preserves_intent_of_law` for epikeia where the passage is explicitly about law’s literal wording and the lawgiver’s intention:
  - `epikeia corrects_legal_letter legal_letter`
  - `epikeia preserves_intent_of_law intent_of_law`

Do not collapse these tract-local distinctions:

- `truth_self_presentation` is not `first_truth`
- `hypocrisy` is not every form of `dissimulation` unless the passage warrants the narrower relation
- `flattery` and `quarreling` are not generic bad-speech labels
- `liberality` is not generic generosity everywhere in the corpus
- `epikeia` is not generic fairness or justice simpliciter

Doctrinal relation vs descriptive gloss:

- approve a doctrinal connected-virtues edge when the passage supports a stable claim like:
  - `truth_self_presentation opposed_by lying`
  - `friendliness_affability opposed_by quarreling`
  - `liberality opposed_by prodigality`
  - `epikeia preserves_intent_of_law intent_of_law`
- keep it out of the doctrinal graph when the passage only:
  - uses the English word `truth` in a faith-related or generic sense
  - uses broad social language without fixing the tract-specific virtue or vice
  - mentions money or goods without grounding the local liberality / covetousness / prodigality distinction
  - praises fairness without clearly treating epikeia’s correction of rigid legal literalism

## Fortitude Parts 129-135 Rule

For `II-II, qq. 129–135`, keep the two sub-clusters explicit:

- honor / worthiness:
  - `magnanimity`
  - `honor_recognition`
  - `worthiness`
  - `presumption_magnanimity`
  - `ambition`
  - `glory`
  - `vainglory`
  - `pusillanimity`
- expenditure / great work:
  - `magnificence`
  - `great_expenditure`
  - `great_work`
  - `meanness_magnificence`
  - `waste_magnificence`

Fortitude-parts review rules:

- keep `magnanimity` and `magnificence` as distinct concept ids and distinct tract neighborhoods
- keep `presumption_magnanimity` distinct from the hope-tract `presumption`
- use `related_to_fortitude` for the annexed-to-fortitude placement of magnanimity and magnificence when the tract explicitly makes that comparison
- use `concerns_honor` and `concerns_worthiness` for the magnanimity cluster:
  - `magnanimity concerns_honor honor_recognition`
  - `pusillanimity concerns_worthiness worthiness`
- use `concerns_great_expenditure` and `concerns_great_work` for the magnificence cluster:
  - `magnificence concerns_great_expenditure great_expenditure`
  - `magnificence concerns_great_work great_work`
- keep opposition-mode structure explicit:
  - `presumption_magnanimity excess_opposed_to magnanimity`
  - `ambition excess_opposed_to magnanimity`
  - `vainglory excess_opposed_to magnanimity`
  - `pusillanimity deficiency_opposed_to magnanimity`
  - `meanness_magnificence deficiency_opposed_to magnificence`
  - `waste_magnificence excess_opposed_to magnificence`
- use `contrary_to` only when the tract explicitly states that one vice stands opposed to another vice, as in `waste_magnificence contrary_to meanness_magnificence`

Do not collapse these tract-local distinctions:

- `magnanimity` is not `magnificence`
- `vainglory` is not generic pride
- `pusillanimity` is not humility
- `great_expenditure` is not `honor_recognition`
- the vice of `waste_magnificence` is not generic prodigality unless a later tract justifies that link

Doctrinal relation vs descriptive gloss:

- approve a doctrinal fortitude-parts edge when the passage supports a stable claim like:
  - `magnanimity related_to_fortitude fortitude`
  - `ambition directed_to honor_recognition`
  - `vainglory directed_to glory`
  - `magnificence concerns_great_work great_work`
- keep it out of the doctrinal graph when the passage only:
  - uses broad greatness language without fixing honor-related or expenditure-related structure
  - invites a modern psychological gloss on magnanimity, vainglory, or pusillanimity
  - would flatten magnanimity and magnificence into one vague greatness node
  - would overstate later fortitude-part structure beyond what `qq. 129–135` actually support

## Fortitude Closure Rule

For `II-II, qq. 136–140`, keep these distinction layers explicit:

- virtue-level fortitude parts:
  - `patience`
  - `perseverance_virtue`
- vice-level opposed terms:
  - `effeminacy_perseverance`
  - `pertinacity_perseverance`
- gift-level node:
  - `fortitude_gift`
- precept-level nodes:
  - `precepts_of_fortitude`
  - `precepts_of_fortitude_parts`
- nearby descriptive or comparison terms only when tract support justifies them:
  - `longanimity_fortitude`
  - `constancy_fortitude`

Fortitude-closure review rules:

- do not collapse `patience` into `perseverance_virtue`
- do not collapse either virtue into generic endurance language
- do not collapse `fortitude_gift` into virtue-level `fortitude`
- do not silently merge `longanimity` with patience or `constancy` with perseverance unless the cited passage warrants it
- use `part_of_fortitude` when `q.136` or `q.137` explicitly places the virtue under fortitude
- use `corresponding_gift_of` conservatively for the relation between `fortitude_gift` and virtue-level `fortitude`
- use `precept_of`, `commands_act_of`, and `forbids_opposed_vice_of` conservatively in `q.140`

Precept-linkage guidance:

- approve a precept-linkage edge only when `q.140` genuinely supports that specific linkage
- do not auto-link every fortitude-adjacent concept to the precepts of fortitude
- keep `magnanimity` and `magnificence` out of precept edges unless `q.140` itself warrants the relation

Gift-linkage guidance:

- approve a doctrinal gift edge when the tract clearly distinguishes the gift from the virtue while relating them
- keep tract-level correspondences editorial if the relation depends mainly on synthesis rather than local wording

Doctrinal relation vs descriptive gloss:

- approve a doctrinal fortitude-closure edge when the passage supports a stable claim like:
  - `patience part_of_fortitude fortitude`
  - `perseverance_virtue part_of_fortitude fortitude`
  - `fortitude_gift corresponding_gift_of fortitude`
  - `precepts_of_fortitude_parts commands_act_of patience`
- keep it out of the doctrinal graph when the passage only:
  - uses broad endurance language without fixing patience or perseverance
  - suggests a thematic similarity between gift and virtue without tract-specific support
  - invites a summary connection to all fortitude material rather than the specific linkage stated in `q.139` or `q.140`

## Temperance 141-160 Rule

For `II-II, qq. 141–160`, keep five sub-clusters explicit:

- temperance proper:
  - `temperance`
  - `intemperance`
  - `insensibility_temperance`
  - `pleasures_of_touch`
  - `food`
  - `drink`
  - `sexual_pleasure`
- general and integral parts:
  - `parts_of_temperance_general`
  - `shamefacedness`
  - `honesty_temperance`
  - `beauty_of_virtue`
- subjective parts, food and drink:
  - `abstinence`
  - `fasting`
  - `gluttony`
  - `sobriety`
  - `drunkenness`
- subjective parts, sex:
  - `chastity`
  - `purity_temperance`
  - `virginity`
  - `lust`
  - tract-local parts of lust only where the passage support is explicit enough
- potential parts:
  - `continence`
  - `incontinence`
  - `clemency`
  - `meekness`
  - `anger`
  - `anger_vice`
  - `cruelty`
  - `modesty_general`

Temperance review rules:

- let `q.143` control tract-level part taxonomy
- keep the three part levels explicit:
  - integral:
    - `shamefacedness integral_part_of temperance`
    - `honesty_temperance integral_part_of temperance`
  - subjective:
    - `abstinence subjective_part_of temperance`
    - `sobriety subjective_part_of temperance`
    - `chastity subjective_part_of temperance`
    - `purity_temperance subjective_part_of temperance`
  - potential:
    - `continence potential_part_of temperance`
    - `meekness potential_part_of temperance`
    - `modesty_general potential_part_of temperance`
- do not use a vague `part_of` edge when the tract support is really integral, subjective, or potential
- do not infer a part placement only from neighboring question order

Food and drink guidance:

- keep `abstinence` distinct from `fasting`
- use `act_of` when the tract treats fasting as a practice or exercise of abstinence rather than the same virtue:
  - `fasting act_of abstinence`
- keep `sobriety` distinct from `abstinence`
- keep `gluttony` distinct from `drunkenness`
- use matter-domain relations when the tract is explicitly about the domain itself:
  - `abstinence concerns_food food`
  - `sobriety concerns_drink drink`
  - `gluttony concerns_food food`
  - `drunkenness concerns_drink drink`

Sexual-matter guidance:

- keep `chastity` distinct from `virginity`
- do not auto-upgrade `virginity` into a subjective part merely because `chastity` is a subjective part
- keep `lust` distinct from its tract-local parts
- use the reviewed parts-of-lust nodes only when `q.154` itself supports the narrower species relation
- do not flatten the tract into a generic sexual-sin graph

Potential-part guidance:

- keep `continence` distinct from `temperance`
- keep `meekness` distinct from `clemency`
- keep `anger` and `anger_vice` distinct when the passage support turns on a passion / vice distinction
- keep `modesty_general` distinct from later humility, studiousness, and external-modesty questions
- approve `potential_part_of` for `clemency` only if the specific passage actually states that placement; do not infer it merely because `q.157` treats clemency beside meekness

Doctrinal relation vs descriptive gloss:

- approve a doctrinal temperance edge when the passage supports a stable claim like:
  - `temperance concerns_food food`
  - `abstinence subjective_part_of temperance`
  - `fasting act_of abstinence`
  - `chastity concerns_sexual_pleasure sexual_pleasure`
  - `meekness opposed_by anger_vice`
  - `modesty_general potential_part_of temperance`
- keep it out of the doctrinal graph when the passage only:
  - uses broad self-control language without fixing temperance’s matter
  - mentions fasting, virginity, or modesty in a merely devotional or descriptive way
  - invites a summary of the whole lust taxonomy beyond what the reviewed `q.154` text warrants
  - would flatten food, drink, sex, anger, clemency, and outward moderation into one generic moderation bucket

## Temperance Closure 161-170 Rule

For `II-II, qq. 161–170`, keep five sub-clusters explicit:

- humility and pride:
  - `humility`
  - `pride`
  - `truth_about_self`
  - `own_excellence`
- Adam's first sin as doctrinal case:
  - `adams_first_sin`
  - `divine_likeness`
  - `knowledge_good_and_evil`
  - tract-local punishment and temptation concepts only where the reviewed passage warrants them
- studiousness and curiosity:
  - `studiousness`
  - `curiosity`
  - `ordered_inquiry`
  - `disordered_inquiry`
- external modesty:
  - `external_behavior_modesty`
  - `eutrapelia`
  - `playful_actions`
  - `outward_attire_modesty`
  - `outward_apparel`
- precepts:
  - `precepts_of_temperance`
  - `precepts_of_temperance_parts`

Temperance-closure review rules:

- keep `humility` distinct from `modesty_general`
- keep `pride` distinct from `Adam's first sin`
- keep `studiousness` distinct from `curiosity`
- keep `external_behavior_modesty` and `outward_attire_modesty` distinct from each other and from `modesty_general`
- keep precept nodes and precept-target concepts distinct

Humility and pride guidance:

- do not collapse humility into self-deprecation or generic lowliness
- do not collapse pride into generic confidence or every form of self-assertion
- approve doctrinal edges such as:
  - `pride contrary_to humility`
  - `humility directed_to God`
  - `humility regulated_by truth_about_self`
- keep broader rhetorical language about greatness, honor, or self-estimation out of the doctrinal graph unless the passage itself stabilizes the relation

Adam's-first-sin guidance:

- model `Adam's first sin` as a doctrinal case node, not as a synonym for pride
- use `case_of` when the tract explicitly treats the first sin under pride
- use `results_in_punishment` only for punishments explicitly tied to the case in `q.164`
- use `tempted_by` only for the tract-local temptation structure in `q.165`
- do not create person-instance graphs for Adam, Eve, or the serpent unless the tract absolutely requires them; this repo currently stays at the case-level instead

Studiousness and curiosity guidance:

- keep `studiousness` as a virtue or ordered practice of inquiry
- keep `curiosity` as disordered inquiry, not neutral modern curiosity
- approve doctrinal edges such as:
  - `studiousness concerns_ordered_inquiry ordered_inquiry`
  - `curiosity concerns_ordered_inquiry disordered_inquiry`
  - `curiosity contrary_to studiousness`
- do not collapse this tract into generic knowledge-language without moral ordering

External modesty guidance:

- keep `modesty_general` from `q.160` separate from the outward-expression species treated in `qq.168–169`
- use `concerns_external_behavior` for outward movement, play, and eutrapelia structure in `q.168`
- use `concerns_outward_attire` for `q.169`
- do not collapse modesty in words/deeds with modesty in attire
- do not reduce `qq.168–169` to a generic social-convention note when the tract is making a virtue/vice distinction

Temperance precept guidance:

- annotate precept-linkage conservatively
- approve `precept_of`, `commands_act_of`, or `forbids_opposed_vice_of` only when `q.170` itself supports the linkage
- do not auto-link every temperance-adjacent virtue or vice to the precepts of temperance
- do not use precept-target concepts as a shortcut for graph focus tags; keep actual precept nodes and relations explicit

Doctrinal relation vs tract-level editorial summary:

- approve a doctrinal temperance-closure edge when the passage supports a stable claim like:
  - `adams_first_sin case_of pride`
  - `studiousness concerns_ordered_inquiry ordered_inquiry`
  - `outward_attire_modesty concerns_outward_attire outward_apparel`
  - `precepts_of_temperance precept_of temperance`
- keep an item `structural_editorial` when it mainly depends on tract organization or conservative synthesis, such as:
  - article or question treatment correspondences
  - cautious bridge edges from `q.170` to earlier temperance material when the wording is indirect
