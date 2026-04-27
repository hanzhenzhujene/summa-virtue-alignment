# Schema

## Repo Layers

The repo currently has twelve important data layers:

1. interim textual corpus
2. pilot reviewed ontology and graph layer
3. prudence tract reviewed block
4. full-corpus candidate workflow
5. theological virtues reviewed block
6. justice core reviewed block
7. religion tract reviewed block
8. owed-relation tract reviewed block
9. connected virtues `II-II, qq. 109–120` reviewed block
10. fortitude-parts `II-II, qq. 129–135` reviewed block
11. fortitude-closure `II-II, qq. 136–140` reviewed block
12. temperance-closure `II-II, qq. 161–170` reviewed block

The interim corpus remains the canonical textual foundation. The pilot and prudence layers are overlays on top of stable passage ids, not replacements for the textual spine.

## Stable Textual IDs

Canonical passage ids come from the interim corpus and remain stable:

- question: `st.i-ii.q001`
- article: `st.i-ii.q001.a001`
- segment: `st.i-ii.q001.a001.resp`
- segment: `st.i-ii.q001.a001.ad1`

The parser still recognizes the full article structure, including objections and
the sed contra, but exported passage ids are doctrinal-content ids only:

- `resp` = `I answer that`
- `ad` = `Reply to Objection ...`

Standalone objections and sed-contra text are excluded from interim segments,
candidate artifacts, graph exports, and Streamlit passage displays.

All reviewed annotations must cite those retained doctrinal segment ids.

## Pilot Concept Registry

Pilot concept records live in `data/gold/pilot_concept_registry.jsonl`.

Fields:

- `concept_id`: stable canonical id such as `concept.prudence`
- `canonical_label`: display label for the concept
- `node_type`: one of the pilot node types
- `aliases`: conservative alternate labels
- `description`: short doctrinal description
- `notes`: disambiguation or review notes
- `source_scope`: question ids where the concept currently has reviewed support in the pilot layer

Current pilot node types include:

- `end`
- `beatitude`
- `act_type`
- `passion`
- `habit`
- `virtue`
- `vice`
- `sin_type`
- `wrong_act`
- `law`
- `law_type`
- `grace`
- `grace_type`
- `gift_holy_spirit`
- `charism`
- `precept`
- `faculty`
- `object`
- `domain`
- `role`
- `process`
- `doctrine`
- `question`
- `article`

## Pilot Annotation Schema

Pilot reviewed annotations live in:

- `data/gold/pilot_reviewed_structural_annotations.jsonl`
- `data/gold/pilot_reviewed_doctrinal_annotations.jsonl`

Fields:

- `annotation_id`
- `source_passage_id`
- `subject_id`
- `subject_label`
- `subject_type`
- `relation_type`
- `object_id`
- `object_label`
- `object_type`
- `evidence_text`
- `evidence_rationale`
- `confidence`
- `edge_layer`
- `support_type`
- `review_status`

Important enum fields:

- `edge_layer`: `structural` or `doctrinal`
- `support_type`:
  - `explicit_textual`
  - `strong_textual_inference`
  - `structural_editorial`
- `due_mode`:
  - optional on older reviewed layers
  - mandatory for the owed-relation tract doctrinal layer
  - current values:
    - `origin`
    - `excellence`
    - `authority`
    - `benefaction`
    - `rectificatory`
- `connected_virtues_cluster`:
  - optional on older reviewed layers
  - mandatory for the connected-virtues `II-II, qq. 109–120` doctrinal layer
  - current values:
    - `self_presentation`
    - `social_interaction`
    - `external_goods`
    - `legal_equity`
- `review_status`: currently `approved` for reviewed pilot records

## Structural vs Doctrinal Edges

Structural edges represent repo organization and article treatment:

- `contains_article`
- `treated_in`

Doctrinal edges represent relation claims supported by reviewed annotations:

- `contrary_to`
- `opposed_by`
- `corresponds_to`
- `perfected_by`
- `regulated_by`
- `directed_to`
- `species_of`
- `part_of`
- `caused_by`
- `requires`
- `defined_as`
- `resides_in`
- `has_act`
- `has_object`
- `requires_restitution`
- `harms_domain`
- `corrupts_process`
- `abuses_role`
- `annexed_to`
- `excess_opposed_to`
- `deficiency_opposed_to`
- `concerns_sacred_object`
- `misuses_sacred_object`
- `corrupts_spiritual_exchange`
- `concerns_due_to`
- `owed_to_role`
- `responds_to_benefaction`
- `responds_to_command`
- `rectifies_wrong`
- `concerns_self_presentation`
- `concerns_social_interaction`
- `concerns_external_goods`
- `corrects_legal_letter`
- `preserves_intent_of_law`
- `related_to_fortitude`
- `concerns_honor`
- `concerns_worthiness`
- `concerns_great_expenditure`
- `concerns_great_work`
- `part_of_fortitude`
- `corresponding_gift_of`
- `precept_of`
- `commands_act_of`
- `forbids_opposed_vice_of`
- `case_of`
- `results_in_punishment`
- `tempted_by`
- `concerns_ordered_inquiry`
- `concerns_external_behavior`
- `concerns_outward_attire`

These two layers are exported separately and filtered separately in the app.

## Pilot Edge Schema

Aggregated pilot edge bundles live in:

- `data/processed/pilot_structural_edges.jsonl`
- `data/processed/pilot_doctrinal_edges.jsonl`

Fields:

- `edge_id`
- `subject_id`
- `subject_label`
- `subject_type`
- `relation_type`
- `object_id`
- `object_label`
- `object_type`
- `edge_layer`
- `support_annotation_ids`
- `source_passage_ids`
- `support_types`
- `evidence_snippets`
- `due_mode`
- `connected_virtues_cluster`

Rules:

- doctrinal edges must have supporting annotation ids
- doctrinal edges must have supporting passage ids
- structural edges may exist without reviewed annotation ids when they are direct containment exports

## Validation Outputs

Pilot validation currently writes:

- `data/processed/validation_report.json`
- `docs/validation_summary.md`

The validation layer checks:

- every annotation references an existing passage
- every concept id in annotations exists in the pilot registry
- every doctrinal edge has annotation support
- exported nodes are either structural or registry-backed
- duplicate annotations are flagged
- missing evidence snippets are flagged
- suspicious alias collisions are flagged

## Prudence Tract Extension

The prudence tract remains a stricter reviewed block on top of the same textual ids.

Prudence-specific part taxonomy is intentionally more precise than the broader pilot layer. It uses first-class typed relations:

- `integral_part_of`
- `subjective_part_of`
- `potential_part_of`

Those remain documented in the prudence artifacts and are not collapsed back into generic `part_of`.

## Theological Virtues Tract Extension

The first larger reviewed doctrinal block now covers:

- `II-II, qq. 1–16` faith and opposing sins
- `II-II, qq. 17–22` hope and opposing sins
- `II-II, qq. 23–46` charity and major contrary sins or acts

The tract exports are split so that they cannot be confused:

- `data/gold/theological_virtues_reviewed_doctrinal_annotations.jsonl`
- `data/gold/theological_virtues_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/theological_virtues_reviewed_doctrinal_edges.jsonl`
- `data/processed/theological_virtues_reviewed_structural_editorial_edges.jsonl`
- `data/processed/theological_virtues_structural_edges.jsonl`

Interpretation rules:

- reviewed doctrinal edges are built only from `explicit_textual` and `strong_textual_inference` annotations
- reviewed structural-editorial correspondences remain separate even when the source passage is explicit, because they are navigational or tract-organizing rather than doctrinal graph claims
- automatic structural edges remain only question/article containment exports
- candidate mentions and candidate relation proposals remain outside all reviewed exports

The tract also inherits earlier pilot review where the pilot slice overlaps this range, especially:

- `II-II q.1`
- `II-II q.23`

Those inherited annotations retain their stable ids and are combined only at tract-graph/report time.

## Justice Core Tract Extension

The next reviewed block now covers:

- `II-II, qq. 57–79`

This justice-core overlay is exported in a way that keeps doctrinal, structural-editorial, and candidate layers materially distinct:

- `data/gold/justice_core_reviewed_concepts.jsonl`
- `data/gold/justice_core_reviewed_doctrinal_annotations.jsonl`
- `data/gold/justice_core_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/justice_core_reviewed_doctrinal_edges.jsonl`
- `data/processed/justice_core_reviewed_structural_editorial_edges.jsonl`
- `data/processed/justice_core_structural_edges.jsonl`
- `data/processed/justice_core_coverage.json`
- `data/processed/justice_core_validation_report.json`

Justice-core concept handling now distinguishes:

- justice species:
  - `general_justice`
  - `particular_justice`
  - `distributive_justice`
  - `commutative_justice`
- wrong acts:
  - `theft`
  - `robbery`
  - `false_accusation`
  - `false_witness`
  - `reviling`
  - `usury`
  - and other tract-specific injustices
- harmed domains:
  - `life`
  - `bodily_integrity`
  - `property`
  - `honor`
  - `reputation`
  - `truth_in_legal_proceedings`

## Religion Tract Extension

The next reviewed block now covers:

- `II-II, qq. 80–100`

This overlay keeps doctrinal, structural-editorial, structural, and candidate layers materially separate:

- `data/gold/religion_tract_reviewed_concepts.jsonl`
- `data/gold/religion_tract_reviewed_doctrinal_annotations.jsonl`
- `data/gold/religion_tract_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/religion_tract_reviewed_doctrinal_edges.jsonl`
- `data/processed/religion_tract_reviewed_structural_editorial_edges.jsonl`
- `data/processed/religion_tract_structural_edges.jsonl`
- `data/processed/religion_tract_coverage.json`
- `data/processed/religion_tract_validation_report.json`

Religion-tract reviewed concept handling currently distinguishes:

- structural bridge concepts:
  - `justice`
  - `religion`
- positive acts of religion:
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
  - `praise_of_god`
- excess / superstition concepts:
  - `superstition`
  - `undue_worship_of_true_god`
  - `idolatry`
  - `divination`
  - `superstitious_observance`
- deficiency / irreligion concepts:
  - `temptation_of_god`
  - `perjury`
  - `sacrilege`
  - `simony`
- sacred-object or sacred-domain concepts:
  - `divine_worship`
  - `divine_name`
  - `promise_to_god`
  - `sworn_assertion`
  - `sacred_thing`
  - `sacred_person`
  - `sacred_place`
  - `spiritual_thing`
  - `sacrament`
  - `spiritual_action`
  - `spiritual_office`

Religion-tract relation semantics are intentionally explicit:

- `annexed_to`:
  - use only for tract-level virtue placement, such as religion under justice
- `has_act`:
  - use when the passage supports a real act-of-religion relation, not merely a nearby topic
- `excess_opposed_to`:
  - use for superstition or related excesses opposed to religion or right worship
- `deficiency_opposed_to`:
  - use for irreligion or related defects opposed to religion or its proper acts
- `concerns_sacred_object`:
  - use when a positive act is ordered toward a stable sacred object or domain
- `misuses_sacred_object`:
  - use when a vice or sinful practice profanes, misuses, or wrongfully handles a sacred object or domain
- `corrupts_spiritual_exchange`:
  - use narrowly for simony or similarly specific spiritual-buying/selling corruption; do not broaden it into generic market exchange language

Interpretation rules:

- reviewed doctrinal edges are built only from `explicit_textual` and `strong_textual_inference` annotations
- reviewed structural-editorial correspondences remain separate even when a question title plainly names the concept
- automatic structural edges remain only question/article containment exports
- candidate mentions and candidate relation proposals remain outside all reviewed exports

Current tract summary from generated reports:

- `21` questions
- `939` passages
- `42` registered concepts used
- `231` reviewed annotations
- `63` reviewed doctrinal edges
- `157` reviewed structural-editorial correspondences
- `2077` candidate mentions
- `659` candidate relation proposals

## Owed-Relation Tract Extension

The next reviewed block now covers:

- `II-II, qq. 101–108`

This overlay keeps doctrinal, structural-editorial, structural, and candidate layers materially separate:

- `data/gold/owed_relation_tract_reviewed_concepts.jsonl`
- `data/gold/owed_relation_tract_reviewed_doctrinal_annotations.jsonl`
- `data/gold/owed_relation_tract_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/owed_relation_tract_reviewed_doctrinal_edges.jsonl`
- `data/processed/owed_relation_tract_reviewed_structural_editorial_edges.jsonl`
- `data/processed/owed_relation_tract_structural_edges.jsonl`
- `data/processed/owed_relation_tract_coverage.json`
- `data/processed/owed_relation_tract_validation_report.json`

The tract adds a first-class `due_mode` field to its reviewed doctrinal annotations and edges. This keeps distinct owed relations inspectable without collapsing them into a generic respect bucket.

Current due modes:

- `origin`
- `excellence`
- `authority`
- `benefaction`
- `rectificatory`

The tract uses those modes across semantically narrower relation families:

- `concerns_due_to`
- `owed_to_role`
- `responds_to_benefaction`
- `responds_to_command`
- `rectifies_wrong`

Interpretation rules for this tract:

- `due_mode` is required on doctrinal annotations and doctrinal edges
- `owed_to_role` must target a role node, not a person instance
- `country` remains an object-level or domain-level target, not a person-like role
- benefaction-related, authority-related, origin-related, excellence-related, and rectificatory debt remain distinct even when the English surface language uses broad talk of what is “due”
- reviewed structural-editorial correspondences remain separate from default doctrinal graph exports

Current tract summary from generated reports:

- `8` questions
- `282` passages
- `27` registered concepts used
- `169` reviewed annotations
- `38` reviewed doctrinal edges
- `110` reviewed structural-editorial correspondences
- `732` candidate mentions
- `226` candidate relation proposals

## Connected Virtues 109-120 Extension

The next reviewed block now covers:

- `II-II, qq. 109–120`

This overlay keeps doctrinal, structural-editorial, structural, and candidate layers materially separate:

- `data/gold/connected_virtues_109_120_reviewed_concepts.jsonl`
- `data/gold/connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl`
- `data/gold/connected_virtues_109_120_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/connected_virtues_109_120_reviewed_doctrinal_edges.jsonl`
- `data/processed/connected_virtues_109_120_reviewed_structural_editorial_edges.jsonl`
- `data/processed/connected_virtues_109_120_structural_edges.jsonl`
- `data/processed/connected_virtues_109_120_coverage.json`
- `data/processed/connected_virtues_109_120_validation_report.json`

The tract adds a first-class `connected_virtues_cluster` field to its reviewed doctrinal annotations and edges. This keeps the four local sub-clusters inspectable instead of flattening them into one vague social-virtue bucket.

Current tract clusters:

- `self_presentation`
- `social_interaction`
- `external_goods`
- `legal_equity`

The tract also adds a small cluster-specific relation family:

- `concerns_self_presentation`
- `concerns_social_interaction`
- `concerns_external_goods`
- `corrects_legal_letter`
- `preserves_intent_of_law`

Connected-virtues reviewed concept handling currently distinguishes:

- self-presentation / truthfulness:
  - `truth_self_presentation`
  - `lying`
  - `dissimulation`
  - `hypocrisy`
  - `boasting`
  - `irony`
  - `self_presentation`
- ordinary social interaction:
  - `friendliness_affability`
  - `flattery`
  - `quarreling`
  - `social_interaction`
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
  - `justice`

Interpretation rules for this tract:

- `truth_self_presentation` is not the same node as faith-tract truth or `first_truth`
- `friendliness_affability` is not silently merged into `charity`
- `liberality` is not silently merged into `almsgiving`, `mercy`, or broader money-language elsewhere in the corpus
- `epikeia` is not reduced to generic fairness; its reviewed relations stay tied to legal letter, intent of law, justice, and common good
- `structural_editorial` treatment correspondences remain separate from default doctrinal graph exports even when question headings are explicit

Current tract summary from generated reports:

- `12` questions
- `340` passages
- `23` registered concepts used
- `182` reviewed annotations
- `44` reviewed doctrinal edges
- `138` reviewed structural-editorial correspondences
- `763` candidate mentions
- `238` candidate relation proposals
- doctrinal cluster counts:
  - `21` self-presentation relations
  - `8` social-interaction relations
  - `11` external-goods relations
  - `4` epikeia / legal-equity relations

## Fortitude Parts 129-135 Extension

The next reviewed block now covers:

- `II-II, qq. 129–135`

This overlay keeps doctrinal, structural-editorial, structural, and candidate layers materially separate:

- `data/gold/fortitude_parts_129_135_reviewed_concepts.jsonl`
- `data/gold/fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl`
- `data/gold/fortitude_parts_129_135_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl`
- `data/processed/fortitude_parts_129_135_reviewed_structural_editorial_edges.jsonl`
- `data/processed/fortitude_parts_129_135_structural_edges.jsonl`
- `data/processed/fortitude_parts_129_135_coverage.json`
- `data/processed/fortitude_parts_129_135_validation_report.json`

The tract adds a first-class `fortitude_parts_cluster` field to its reviewed doctrinal edges. This keeps honor-related magnanimity structure distinct from expenditure-related magnificence structure.

Current tract clusters:

- `honor_worthiness`
- `expenditure_work`

The tract also uses a small cluster-specific relation family:

- `related_to_fortitude`
- `concerns_honor`
- `concerns_worthiness`
- `concerns_great_expenditure`
- `concerns_great_work`

Fortitude-parts reviewed concept handling currently distinguishes:

- magnanimity cluster:
  - `magnanimity`
  - `honor_recognition`
  - `worthiness`
  - `presumption_magnanimity`
  - `ambition`
  - `glory`
  - `vainglory`
  - `pusillanimity`
  - `confidence`
  - `security_assurance`
  - `goods_of_fortune`
- magnificence cluster:
  - `magnificence`
  - `great_expenditure`
  - `great_work`
  - `meanness_magnificence`
  - `waste_magnificence`

Interpretation rules for this tract:

- `magnanimity` and `magnificence` remain distinct concept ids and distinct reviewed graph neighborhoods
- `presumption_magnanimity` remains distinct from the hope-tract `presumption`
- `excess_opposed_to` and `deficiency_opposed_to` remain explicit rather than being flattened into one vague opposition relation
- `honor_recognition` remains distinct from expenditure/work structure so that magnanimity is not silently merged into magnificence
- `structural_editorial` treatment correspondences remain separate from default doctrinal graph exports

Current tract summary from generated reports:

- `7` questions
- `212` passages
- `20` registered concepts used
- `150` reviewed annotations
- `33` reviewed doctrinal edges
- `97` reviewed structural-editorial correspondences
- `532` candidate mentions
- `158` candidate relation proposals
- doctrinal tract counts:
  - `4` excess-opposition relations
  - `2` deficiency-opposition relations
  - `20` honor-related relations
  - `13` expenditure-related relations
  - `fairness_in_distribution`
  - `fairness_in_exchange`
- judicial roles and process:
  - `judge_role`
  - `accuser_role`
  - `defendant_role`
  - `witness_role`
  - `advocate_role`
  - `judicial_process`

Justice-core relation semantics:

- `requires_restitution`: a wrong act or abusive role-use is textually tied to the obligation of restitution
- `harms_domain`: the wrong act injures a stable moral or juridical domain such as property, honor, or judicial truth
- `corrupts_process`: the wrong act deforms the judicial or public process rather than merely harming a private good
- `abuses_role`: the wrong act misuses a stable office-role such as judge, accuser, witness, or advocate

Interpretation rules for this tract:

- reviewed doctrinal exports remain limited to `explicit_textual` and `strong_textual_inference`
- reviewed structural-editorial correspondences remain separate even when the passage explicitly names the concept, because `treated_in` is navigational rather than doctrinal
- candidate mentions and candidate relation proposals remain outside all reviewed exports
- role nodes are role-level abstractions only, never person instances
- harmed-domain nodes are distinct from virtues, vices, and wrong acts; they exist to keep the injury structure inspectable

## Full-Corpus Structural Workflow

The full moral corpus is now structurally indexed across:

- `I-II, qq. 1–114`
- `II-II, qq. 1–182`

Explicit exclusions remain manifest-visible rather than silently omitted:

- `II-II, qq. 183–189`

Processed structural workflow files:

- `data/processed/corpus_manifest.json`
- `data/processed/question_index.csv`
- `data/processed/article_index.csv`
- `data/processed/ingestion_log.jsonl`
- `data/processed/coverage_report.json`

`question_index.csv` includes both included questions and explicit excluded rows. Excluded rows must carry `parse_status = excluded`.

## Corpus Concept Registry

The broader corpus registry lives in `data/gold/corpus_concept_registry.jsonl`.

Fields:

- `concept_id`
- `canonical_label`
- `node_type`
- `aliases`
- `description`
- `notes`
- `source_scope`
- `parent_concept_id`
- `registry_status`
- `disambiguation_notes`
- `related_concepts`
- `introduced_in_questions`

`registry_status` distinguishes reviewed pilot seeds from broader corpus seed concepts. The registry is intentionally scalable, but still conservative.

## Candidate Mention Schema

Full-corpus candidate mentions live in `data/candidate/corpus_candidate_mentions.jsonl`.

Fields:

- `candidate_id`
- `passage_id`
- `matched_text`
- `normalized_text`
- `proposed_concept_id`
- `proposed_concept_ids`
- `proposed_node_type`
- `match_method`
- `confidence`
- `ambiguity_flag`
- `context_snippet`
- `char_start`
- `char_end`
- `review_status`

Rules:

- candidate mentions are workflow aids, not approved concept assignments
- `review_status` defaults to `unreviewed`
- ambiguous matches must remain ambiguous unless a reviewer resolves them elsewhere

## Candidate Relation Proposal Schema

Full-corpus candidate relations live in `data/candidate/corpus_candidate_relation_proposals.jsonl`.

Fields:

- `proposal_id`
- `source_passage_id`
- `subject_id`
- `subject_label`
- `subject_type`
- `relation_type`
- `object_id`
- `object_label`
- `object_type`
- `proposal_method`
- `evidence_text`
- `confidence`
- `ambiguity_flag`
- `support_candidate_ids`
- `review_status`

Rules:

- proposals remain `unreviewed` until promoted by explicit human review
- reviewed exports must never depend on these proposal files
- `treated_in` proposals are allowed as review aids, but they are still candidate material unless separately reviewed

## Coverage And Review Queue Outputs

Coverage and review support files:

- `data/processed/candidate_validation_report.json`
- `data/processed/corpus_review_queue.json`
- `data/processed/review_packets/`

These files are designed to help a human reviewer prioritize work by:

- question
- candidate density
- ambiguity burden
- reviewed coverage gap
- parse uncertainty

## Fortitude Closure Tract Extension

The fortitude-closure reviewed block now covers:

- `II-II, qq. 136–140`
  - `q.136` patience
  - `q.137` perseverance
  - `q.138` the vices opposed to perseverance
  - `q.139` the gift of fortitude
  - `q.140` the precepts of fortitude

Closure-specific reviewed exports live in:

- `data/gold/fortitude_closure_136_140_reviewed_concepts.jsonl`
- `data/gold/fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl`
- `data/gold/fortitude_closure_136_140_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl`
- `data/processed/fortitude_closure_136_140_reviewed_structural_editorial_edges.jsonl`
- `data/processed/fortitude_closure_136_140_structural_edges.jsonl`

Fortitude-closure relation additions:

- `part_of_fortitude`
  - use when the passage explicitly places patience or perseverance among fortitude's parts
  - do not use this as a generic synonym for `part_of`
- `corresponding_gift_of`
  - use when the tract explicitly distinguishes the gift of fortitude from the virtue while still relating them
- `precept_of`
  - use for stable precept-to-virtue or precept-to-fortitude-part linkage in `q.140`
- `commands_act_of`
  - use only when the text genuinely supports a positive precept relation to patience or perseverance
- `forbids_opposed_vice_of`
  - use only when the tract genuinely supports a prohibitive precept structure around fortitude's opposed matter

Identity rules for this tract:

- `concept.patience` and `concept.perseverance_virtue` must remain distinct concept ids
- `concept.fortitude` and `concept.fortitude_gift` must remain distinct concept ids
- `concept.perseverance_virtue` must remain distinct from earlier act-level `concept.perseverance`
- if `longanimity` and `constancy` are represented, they must not be silently merged with patience or perseverance without tract-specific warrant

The fortitude synthesis layer is intentionally controlled:

- default doctrinal synthesis includes only reviewed doctrinal edges
- reviewed structural-editorial correspondences are available separately
- candidate mentions and candidate relation proposals are excluded from default synthesis exports
- the current repo has reviewed fortitude doctrine for `qq. 129–140`
- `qq. 123–128` remain structurally available but do not yet have their own dedicated reviewed doctrinal block

## Temperance Phase-1 Tract Extension

The temperance phase-1 reviewed block now covers:

- `II-II, qq. 141–160`
  - `qq.141–142` temperance itself and the vices opposed to temperance
  - `q.143` parts of temperance in general
  - `qq.144–145` integral parts
  - `qq.146–154` subjective parts centered on food, drink, and sex
  - `qq.155–160` potential parts through modesty in general

Temperance phase-1 reviewed exports live in:

- `data/gold/temperance_141_160_reviewed_concepts.jsonl`
- `data/gold/temperance_141_160_reviewed_doctrinal_annotations.jsonl`
- `data/gold/temperance_141_160_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/temperance_141_160_reviewed_doctrinal_edges.jsonl`
- `data/processed/temperance_141_160_reviewed_structural_editorial_edges.jsonl`
- `data/processed/temperance_141_160_structural_edges.jsonl`
- `data/processed/temperance_phase1_synthesis_nodes.csv`
- `data/processed/temperance_phase1_synthesis_edges.csv`
- `data/processed/temperance_phase1_synthesis.graphml`

Temperance-specific relation additions:

- `integral_part_of`
  - use when the tract explicitly places a concept among temperance's integral parts
  - current reviewed use is driven by `q.143` and the integral-part questions `qq. 144–145`
- `subjective_part_of`
  - use when the tract explicitly places a concept among temperance's subjective parts
  - do not use this as a shortcut for every closely related practice or state
- `potential_part_of`
  - use when the tract explicitly places a concept among temperance's potential parts
  - keep it distinct from both integral and subjective placement
- `act_of`
  - use when the tract treats a practice as an act or exercise of a virtue without collapsing the practice into the virtue itself
  - the current tract uses this conservatively for `fasting -> abstinence`
- `concerns_food`
  - use for stable food-related matter in abstinence, fasting, and gluttony material
- `concerns_drink`
  - use for stable drink-related matter in sobriety and drunkenness material
- `concerns_sexual_pleasure`
  - use for stable venereal or sexual-pleasure matter in chastity, virginity, lust, and parts-of-lust material
- `concerns_anger`
  - use where the tract explicitly treats meekness, incontinence, or anger around the anger-domain itself
- `concerns_outward_moderation`
  - use for `q.160` when the tract is about modesty in general and outward moderation rather than later humility-specific or exterior-behavior subquestions

Temperance part-taxonomy rules:

- `q.143` is the controlling tract-level taxonomy source
- the current reviewed taxonomy keeps these levels distinct:
  - integral:
    - `shamefacedness`
    - `honesty_temperance`
  - subjective:
    - `abstinence`
    - `sobriety`
    - `chastity`
    - `purity_temperance`
  - potential:
    - `continence`
    - `meekness`
    - `modesty_general`
- do not flatten these three levels into generic `part_of`
- do not auto-promote nearby concepts into the wrong level merely because they are treated in neighboring questions

Identity and separation rules for this tract:

- `concept.abstinence` and `concept.fasting` must remain distinct concept ids
- `concept.chastity` and `concept.virginity` must remain distinct concept ids
- `concept.continence` and `concept.temperance` must remain distinct concept ids
- `concept.meekness` and `concept.clemency` must remain distinct concept ids
- `concept.modesty_general` must remain distinct from later humility / studiousness / exterior-modesty material
- `concept.anger` and `concept.anger_vice` must not be silently merged when the tract needs the passion-level / vice-level distinction preserved
- `concept.lust` and the tract-local parts of lust must not be collapsed into a generic sexual-sin bucket

Temperance synthesis is intentionally controlled:

- default temperance synthesis includes only reviewed doctrinal edges
- reviewed structural-editorial correspondences are available separately
- candidate mentions and candidate relation proposals are excluded from default temperance synthesis exports
- synthesis outputs preserve `temperance_cluster` and `temperance_focus` metadata so part-taxonomy and matter-domain filters remain inspectable in the app and exported tables

## Temperance Closure 161-170 Tract Extension

The temperance closure reviewed block now covers:

- `II-II, qq. 161–170`
  - `qq.161–162` humility and pride
  - `qq.163–165` Adam's first sin, its punishments, and the temptation
  - `qq.166–167` studiousness and curiosity
  - `qq.168–169` external modesty in words, deeds, and attire
  - `q.170` the precepts of temperance

Temperance closure reviewed exports live in:

- `data/gold/temperance_closure_161_170_reviewed_concepts.jsonl`
- `data/gold/temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl`
- `data/gold/temperance_closure_161_170_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/temperance_closure_161_170_reviewed_doctrinal_edges.jsonl`
- `data/processed/temperance_closure_161_170_reviewed_structural_editorial_edges.jsonl`
- `data/processed/temperance_closure_161_170_structural_edges.jsonl`
- `data/processed/temperance_full_synthesis_nodes.csv`
- `data/processed/temperance_full_synthesis_edges.csv`
- `data/processed/temperance_full_synthesis.graphml`

Temperance-closure-specific relation additions:

- `case_of`
  - use for `Adam's first sin case_of pride`
  - keep the case node distinct from the generic vice node
- `results_in_punishment`
  - use for punishments explicitly attached to Adam's first sin in `q.164`
  - do not widen it into every downstream consequence note
- `tempted_by`
  - use for the tract-local temptation structure in `q.165`
  - keep it distinct from generic desire or curiosity language
- `concerns_ordered_inquiry`
  - use for `studiousness -> ordered_inquiry` and `curiosity -> disordered_inquiry`
  - do not flatten it into neutral modern curiosity language
- `concerns_external_behavior`
  - use for `q.168` outward-movement / play / eutrapelia structure
- `concerns_outward_attire`
  - use for `q.169` attire and adornment structure

Identity and separation rules for this tract:

- `concept.humility` and `concept.pride` must remain distinct concept ids
- `concept.pride` and `concept.adams_first_sin` must remain distinct concept ids
- `concept.studiousness` and `concept.curiosity` must remain distinct concept ids
- `concept.modesty_general` must remain distinct from:
  - `concept.external_behavior_modesty`
  - `concept.outward_attire_modesty`
- precept focus tags must attach to:
  - `q.170`
  - the temperance precept nodes
  - actual precept relations
  and not to every concept that later appears as a precept target

Full temperance synthesis is intentionally controlled:

- default synthesis includes only reviewed doctrinal edges across `qq. 141–170`
- reviewed structural-editorial correspondences are available separately in the editorial GraphML export
- candidate mentions and candidate relation proposals are excluded from default full-temperance synthesis exports
- synthesis outputs preserve both:
  - phase-1 metadata:
    - `temperance_cluster`
    - `temperance_focus`
  - closure metadata:
    - `temperance_closure_cluster`
    - `temperance_closure_focus`
