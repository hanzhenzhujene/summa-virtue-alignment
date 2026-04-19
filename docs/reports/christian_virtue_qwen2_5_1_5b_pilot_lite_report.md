# Christian Virtue Qwen2.5 1.5B Local Pilot-Lite Report

## Scope

This report documents the canonical local Apple-Silicon LoRA baseline for the Christian virtue SFT pipeline. It is the official reproducible `Qwen/Qwen2.5-1.5B-Instruct` `pilot-lite` demonstration path for this repo.

It is meant to show more than citation formatting. The real question is whether this dataset can push a general model toward Aquinas-grounded Christian virtue reasoning while keeping answers evidence-bounded and traceable.

## Canonical Purpose

- Primary objective: improve faithful Aquinas-grounded virtue reasoning.
- Secondary objective: preserve citation-grounded traceability.
- Non-goal: treating passage-id emission as the whole purpose of the SFT.

## Experiment Snapshot

| Item | Value |
| --- | --- |
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Training mode | LoRA on `mps`, `float16`, no quantization |
| Dataset export | `christian_virtue_v1` |
| Reviewed source annotations | `555` |
| Total SFT examples | `1883` |
| Train / val / test sizes | `1475 / 175 / 233` |
| Pilot-lite train subset | `128` |
| Pilot-lite eval subset | `16` |
| Max steps | `20` |
| Runtime device | `mps` |
| Git commit | `f9fd58981e8182dbe92ee6ed1c1a389ef2e7f1e9` |
| Training run id | `20260418_193038` |

Committed inputs:

- Dataset manifest: [data/processed/sft/exports/christian_virtue_v1/manifest.json](../../data/processed/sft/exports/christian_virtue_v1/manifest.json)
- Training config: [configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml](../../configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml)
- Base inference config: [configs/inference/qwen2_5_1_5b_instruct_base_test.yaml](../../configs/inference/qwen2_5_1_5b_instruct_base_test.yaml)
- Adapter inference config: [configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml](../../configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml)

## Data And Split Policy

This run uses the committed `christian_virtue_v1` export built from approved reviewed doctrinal annotations only. Structural-editorial review, candidate material, and processed edge exports are not used as training truth.

The dataset remains segment-grounded and grouped by `question_id` for leakage-safe splits.

- Grouping key: `question_id`
- Support types: `explicit_textual, strong_textual_inference`

## Method

| Parameter | Value |
| --- | ---: |
| Learning rate | `0.0002` |
| Max sequence length | `768` |
| Train examples | `128` |
| Eval examples | `16` |
| Per-device train batch size | `1` |
| Gradient accumulation steps | `8` |
| LoRA rank | `16` |
| LoRA alpha | `32` |
| LoRA dropout | `0.05` |
| Seed | `17` |

## Runtime Environment

| Item | Value |
| --- | --- |
| Python | `3.12.2` |
| Torch | `2.11.0` |
| Transformers | `4.57.6` |
| PEFT | `0.19.1` |
| TRL | `0.29.1` |
| Accelerate | `1.13.0` |
| Approx train wall-clock | `4.7 minutes` |

## Training Trajectory

![Pilot-lite training curves](assets/christian_virtue_qwen2_5_1_5b_pilot_lite_training_curves.svg)

The training curve is healthy for a local demonstration run: loss falls sharply, token accuracy rises, and the small eval slice stays close to the training signal.

## Held-Out Test Comparison

![Base vs adapter test comparison](assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg)

| Model | Count | Citation exact | Citation partial | Citation overlap |
| --- | ---: | ---: | ---: | ---: |
| Base model | `233` | `0.000` | `0.000` | `0.000` |
| LoRA adapter | `233` | `0.150` | `0.150` | `0.150` |

The adapter materially improves held-out citation grounding over the untouched base model, but the improvement is uneven across tasks. The open user-style moral-answer task remains the hardest failure mode.

## Goal Demo Panel

This fixed panel uses held-out examples chosen to reflect the real SFT goal: virtue definition, part distinctions, act relations, vice opposition, and tract-local explanation.

### 1. Charity and fraternal correction

- Focus: Act/virtue relation inside the theological virtues
- Task type: Reviewed relation explanation
- Tract: Theological virtues
- Prompt: Explain this reviewed doctrinal relation from the cited passage. Tract: Theological virtues Subject: Charity Relation type: has_act Object: Fraternal Correction Passage id: st.ii-ii.q033.a001.resp Passage text: The corr…
- Reference citations: `st.ii-ii.q033.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> The reviewed relation is that Charity has Fraternal Correction as an act. The passage states this directly. Question 33 explicitly says that fraternal correction is an act of charity. Citations: - st.ii-ii.q033.a001.resp (II-II q.33 a.1 resp)

Base model:

> The relation "has_act" between the theological virtue of charity and the act of fraternal correction is explained in the passage as follows: 1. **Relation Type**: The relation is "has_act" which indicates that the theological virtue of charity has the act of fraternal correction as one of its manifestations. 2. **Object**: The object of this relation is the act of fraternal correction. 3. **Passage Context**: The pa…

LoRA adapter:

> According to the cited passage, fraternal correction is an act of charity rather than a healing of a bodily infirmity or relieving of an external bodily need. The passage states this directly. The relation type is "has_act", and the object is "Fraternal Correction". The passage cites Aquinas's own words to support this claim. Article 1 explicitly states that fraternal correction is an act of charity. Article 2 expla…

### 2. Faith as a theological virtue

- Focus: Virtue explanation in Aquinas's own categories
- Task type: Virtue concept explanation
- Tract: Theological virtues
- Prompt: Explain this concept using only the supporting passages below. Concept: Faith Tract: Theological virtues Question context: The act of faith Supporting passages: - st.ii-ii.q002.a002.resp (II-II q.2 a.2 resp) The act of…
- Reference citations: `st.ii-ii.q002.a002.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> Aquinas presents Faith as one that has Act of Faith as an act. Citations: - st.ii-ii.q002.a002.resp (II-II q.2 a.2 resp)

Base model:

> The concept of faith, as discussed in the context of the theological virtues, is fundamentally tied to the relationship between the intellect and the will. According to Aquinas, the object of faith can be understood in three ways: 1. **On the Part of the Intellect**: The object of faith is primarily considered on the part of the intellect, which is the source of the act of faith. This aspect of faith involves believ…

LoRA adapter:

> According to the cited passage, faith is an act of the intellect on the part of the will. The object of faith is considered on three aspects: material, formal, and formal on account of the will. The formal aspect is the First Truth referred to the will as an end. Answering this question requires citing passage II-II.q002.a002.resp.

### 3. Commutative justice and restitution

- Focus: Justice and its proper act
- Task type: Reviewed relation explanation
- Tract: Justice core
- Prompt: Explain this reviewed doctrinal relation from the cited passage. Tract: Justice core Subject: Commutative Justice Relation type: has_act Object: Restitution Passage id: st.ii-ii.q062.a001.resp Passage text: To restore i…
- Reference citations: `st.ii-ii.q062.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `True`

Reference:

> The reviewed relation is that Commutative Justice has Restitution as an act. The passage states this directly. Article 1 explicitly states that restitution is an act of commutative justice. Citations: - st.ii-ii.q062.a001.resp (II-II q.62 a.1 resp)

Base model:

> The relation "has_act" between "Restitution" and "Commutative Justice" in the cited passage is explained as follows: Restitution is an act of commutative justice. According to Aquinas, restitution involves restoring a person to the possession or dominion of their thing, which is a fundamental aspect of commutative justice. This act of restitution is considered equal in justice to the payment of one thing for another…

LoRA adapter:

> According to the cited passage, restitution is an act of commutative justice. The passage states this directly. Restitution is considered the same as reinstate a person in possession or dominion of his thing, which is part of commutative justice. The passage explicitly links restitution to commutative justice. Citations: - st.ii-ii.q062.a001.resp

### 4. Commutative justice as a concept

- Focus: Virtue definition with tract-local grounding
- Task type: Virtue concept explanation
- Tract: Justice core
- Prompt: Explain this concept using only the supporting passages below. Concept: Commutative Justice Tract: Justice core Question context: Restitution Supporting passages: - st.ii-ii.q062.a001.resp (II-II q.62 a.1 resp) To resto…
- Reference citations: `st.ii-ii.q062.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `True`

Reference:

> Aquinas presents Commutative Justice as one that has Restitution as an act. Citations: - st.ii-ii.q062.a001.resp (II-II q.62 a.1 resp)

Base model:

> Commutative justice, as explained in the supporting passage, involves restoring a person to the possession or dominion of their thing. This concept is central to restitution, which is an act of commutative justice. Restitution is considered when one person has what belongs to another, either with or without the other's consent. The passage specifically mentions restitution in the context of robbery or theft, where t…

LoRA adapter:

> According to the cited passage, restitution is considered the same as reinstate a person in possession of their thing, which is a key aspect of commutative justice. The passage states that restitution involves equality of justice in payment of one thing for another, which is part of commutative justice. It mentions restitution as occasioned by one person having what belongs to another, either with consent or against…

### 5. Regnative prudence

- Focus: Prudence species and political ordering
- Task type: Virtue concept explanation
- Tract: Prudence
- Prompt: Explain this concept using only the supporting passages below. Concept: Regnative Prudence Tract: Prudence Question context: The subjective parts of prudence Supporting passages: - st.ii-ii.q050.a001.resp (II-II q.50 a.…
- Reference citations: `st.ii-ii.q050.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `True`

Reference:

> Aquinas presents Regnative Prudence as one that is a subjective part of Prudence. Citations: - st.ii-ii.q050.a001.resp (II-II q.50 a.1 resp)

Base model:

> Regnative prudence is a specific form of prudence that applies to rulers who govern both themselves and the perfect community of a city or kingdom. It is the most perfect kind of prudence because it involves governing not just an individual but a larger, more universal community. This prudence is considered a species of prudence because it is a distinct and specialized form of prudence that is uniquely applicable to…

LoRA adapter:

> According to the cited passage, regnative prudence is a special kind of prudence that governs and commands in a king's governance of a city or kingdom. The passage states this directly and provides evidence from II-II:47:10 that prudence governs and commands in governance, and that this is a special kind of prudence. The passage also explains why regnative prudence is a special kind of prudence, citing the universal…

### 6. Military prudence as a part of prudence

- Focus: Subjective-part classification within prudence
- Task type: Reviewed relation explanation
- Tract: Prudence
- Prompt: Why does this passage support the reviewed doctrinal relation below? Tract: Prudence Subject: Military Prudence Relation type: subjective_part_of Object: Prudence Passage id: st.ii-ii.q050.a004.resp Passage text: Whatev…
- Reference citations: `st.ii-ii.q050.a004.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> The reviewed relation is that Military Prudence is a subjective part of Prudence. The passage states this directly. Q50.4 explicitly says there should be military prudence alongside political prudence. Citations: - st.ii-ii.q050.a004.resp (II-II q.50 a.4 resp)

Base model:

> This passage supports the reviewed doctrinal relation between "Military Prudence" and "Prudence" by explicitly stating that military prudence is a necessary complement to prudence. Specifically, it asserts that prudence should conform to nature, which includes both the natural tendency to govern oneself and the natural defense against external threats. The passage then explains that this natural defense includes the…

LoRA adapter:

> This passage supports the reviewed doctrinal relation by explicitly stating that military prudence is a subjective part of prudence. The passage directly compares military prudence to political prudence and explicitly includes military prudence as a part of prudence. The cited passage explicitly states that military prudence is a part of prudence, making this passage directly support the doctrinal relation between m…

### 7. Truth in self-presentation

- Focus: Connected virtue outside the four cardinal/theological headline labels
- Task type: Virtue concept explanation
- Tract: Connected virtues (II-II qq.109-120)
- Prompt: Explain this concept using only the supporting passages below. Concept: Truth Tract: Connected virtues (II-II qq.109-120) Question context: Truth Supporting passages: - st.ii-ii.q109.a002.resp (II-II q.109 a.2 resp) The…
- Reference citations: `st.ii-ii.q109.a002.resp, st.ii-ii.q109.a003.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> Aquinas presents Truth as one that concerns self-presentation in relation to Self-Presentation. It also is annexed to Justice. Citations: - st.ii-ii.q109.a002.resp (II-II q.109 a.2 resp) - st.ii-ii.q109.a003.resp (II-II q.109 a.3 resp)

Base model:

> The concept of truth, as explained in the supporting passages, is a special virtue that is connected to justice. According to Aquinas, truth is a virtue that is annexed to justice, meaning it is a secondary virtue that falls short of the perfect virtue of justice but shares certain characteristics with it. Truth is directed to another, manifesting the things that concern the person who is being addressed. It also se…

LoRA adapter:

> According to the cited passages, truth is a special virtue connected to justice. The passage states that truth has two aspects in common with justice: it is directed to another and sets up equality between things. However, it falls short of justice in the notion of debt. Truth is thus considered a part of justice, annexed as a secondary virtue. The passage cites Augustine's statement that good consists in order to s…

### 8. Abstinence within temperance

- Focus: Subjective-part classification in temperance
- Task type: Reviewed relation explanation
- Tract: Temperance (II-II qq.141-160)
- Prompt: Why does this passage support the reviewed doctrinal relation below? Tract: Temperance (II-II qq.141-160) Subject: Abstinence Relation type: subjective_part_of Object: Temperance Passage id: st.ii-ii.q143.a001.resp Pass…
- Reference citations: `st.ii-ii.q143.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> The reviewed relation is that Abstinence is a subjective part of Temperance. The passage states this directly. Question 143 explicitly assigns abstinence among temperance's subjective parts. Citations: - st.ii-ii.q143.a001.resp (II-II q.143 a.1 resp)

Base model:

> This passage supports the reviewed doctrinal relation between Temperance and Abstinence by explaining how temperance has subjective parts, specifically "shamefacedness" and "honesty." These subjective parts are integral to temperance and are related to abstinence. The passage states that temperance more than any other virtue lays claim to a certain comeliness, and the vices of intemperance excel others in disgrace.…

LoRA adapter:

> This passage supports the reviewed doctrinal relation by explicitly stating that temperance has subjective parts. The passage directly compares temperance to shamefacedness and honesty, which are explicitly called subjective parts of temperance. The review correctly identifies this as subjective_part_of relation type.

### 9. Continence within temperance

- Focus: Potential-part distinction in temperance
- Task type: Reviewed relation explanation
- Tract: Temperance (II-II qq.141-160)
- Prompt: Why does this passage support the reviewed doctrinal relation below? Tract: Temperance (II-II qq.141-160) Subject: Continence Relation type: potential_part_of Object: Temperance Passage id: st.ii-ii.q143.a001.resp Passa…
- Reference citations: `st.ii-ii.q143.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> The reviewed relation is that Continence is a potential part of Temperance. The passage states this directly. Question 143 explicitly assigns continence among temperance's potential parts. Citations: - st.ii-ii.q143.a001.resp (II-II q.143 a.1 resp)

Base model:

> This passage supports the reviewed doctrinal relation between Temperance and Continence by explaining how Continence is a potential part of Temperance. Specifically, the passage states that Continence is one of the potential parts of Temperance, which is a cardinal virtue. It distinguishes Continence as a potential part from the integral parts of Temperance, which include "shamefacedness" and "honesty." The passage…

LoRA adapter:

> This passage supports the reviewed doctrinal relation by explicitly stating that temperance has potential parts that are secondary virtues. The passage directly cites this as part of Aquinas's explanation of temperance's potential parts. Article 1 explicitly states that temperance has potential parts, and then goes on to list these potential parts as secondary virtues. Article 2 further elaborates on this by explain…

### 10. Lust and chastity

- Focus: Vice opposition rather than generic moral paraphrase
- Task type: Citation-grounded moral answer
- Tract: Temperance (II-II qq.141-160)
- Prompt: According to Aquinas, what is the excessive vice opposed to Lust?
- Reference citations: `st.ii-ii.q153.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> According to the cited passage, Lust is opposed by the excessive vice Chastity. The passage states this directly. Lust is the disordered contrary of chastity in venereal matter. Citations: - st.ii-ii.q153.a001.resp (II-II q.153 a.1 resp)

Base model:

> According to Aquinas, the excessive vice opposed to Lust is Gluttony. Aquinas identifies Gluttony as the vice that is "excessive" in relation to Lust. He explains that while Lust involves excessive desire for sensual pleasures, Gluttony involves excessive desire for food and drink. Aquinas argues that while Lust is a vice that involves excessive desire for sensual pleasures, Gluttony is a vice that involves excessiv…

LoRA adapter:

> According to the cited passage, Excessive Lust is opposed by Diligence. The passage states this directly. Article 1 explicitly states this opposition. Citations: - st.ii-ii.q125.a001.resp (II-II q.125 a.1 resp)

### 11. Constancy in the fortitude tract

- Focus: Fortitude-part explanation without collapsing nearby concepts
- Task type: Virtue concept explanation
- Tract: Fortitude closure (II-II qq.136-140)
- Prompt: Explain this concept using only the supporting passages below. Concept: Constancy Tract: Fortitude closure (II-II qq.136-140) Question context: Perseverance Supporting passages: - st.ii-ii.q137.a003.resp (II-II q.137 a.…
- Reference citations: `st.ii-ii.q137.a003.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> Aquinas presents Constancy as one that is part of fortitude through Fortitude. Citations: - st.ii-ii.q137.a003.resp (II-II q.137 a.3 resp)

Base model:

> In the context of perseverance and constancy, as discussed in the passage from St. Thomas Aquinas's "Summa Theologica," these virtues are distinguished by their approach to maintaining virtue in the face of challenges. Perseverance is concerned with the intrinsic difficulty of maintaining a good action over time, which is inherent to the act itself. Constancy, on the other hand, addresses external hindrances that ma…

LoRA adapter:

> According to the cited passage, constancy differs from perseverance in Aquinas's view. Perseverance is about persisting in good against intrinsic difficulties, while constancy is about persisting against external hindrances. Perseverance is seen as a more intrinsic virtue related to the act itself, whereas constancy deals with external obstacles. The passage states that perseverance takes precedence over constancy i…

### 12. Magnificence and great work

- Focus: Tract-local object relation in annexed virtues
- Task type: Citation-grounded moral answer
- Tract: Fortitude parts (II-II qq.129-135)
- Prompt: What does Aquinas teach about the relation between Magnificence and Great Work?
- Reference citations: `st.ii-ii.q135.a001.resp`
- Base exact citation match: `False`
- Adapter exact citation match: `False`

Reference:

> According to the cited passage, Magnificence concerns great work in relation to Great Work. The passage states this directly. Article 1 explicitly says the magnificent man intends principally the greatness of his work. Citations: - st.ii-ii.q135.a001.resp (II-II q.135 a.1 resp)

Base model:

> Aquinas teaches that Magnificence and Great Work are closely related in his moral philosophy. According to Aquinas, Magnificence is a virtue that involves magnanimity and generosity, characterized by a sense of nobility and a desire to do good. Great Work, on the other hand, refers to the fulfillment of one's duties and responsibilities in life. Aquinas argues that Magnificence is essential for Great Work. He states…

LoRA adapter:

> According to the cited passage, Magnificence is the perfection of Great Work. The passage states this directly. Article 1 explicitly states this relation. Citations: - st.ii-ii.q125.a001.resp (II-II q.125 a.1 resp)

## Comparison Summary

# Christian Virtue Run Comparison

- Baseline: Base model
- Candidate: LoRA adapter

## Overall

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 233 | 233 | +0 |
| citation_exact_match | 0.000 | 0.150 | +0.150 |
| citation_partial_match | 0.000 | 0.150 | +0.150 |
| citation_overlap | 0.000 | 0.150 | +0.150 |
| relation_type_accuracy | n/a | n/a | n/a |

## By Split

### test

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 233 | 233 | +0 |
| citation_exact_match | 0.000 | 0.150 | +0.150 |
| citation_partial_match | 0.000 | 0.150 | +0.150 |
| citation_overlap | 0.000 | 0.150 | +0.150 |
| relation_type_accuracy | n/a | n/a | n/a |


## By Tract

### connected_virtues_109_120

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 7 | 7 | +0 |
| citation_exact_match | 0.000 | 0.000 | +0.000 |
| citation_partial_match | 0.000 | 0.000 | +0.000 |
| citation_overlap | 0.000 | 0.000 | +0.000 |
| relation_type_accuracy | n/a | n/a | n/a |

### fortitude_closure_136_140

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 17 | 17 | +0 |
| citation_exact_match | 0.000 | 0.118 | +0.118 |
| citation_partial_match | 0.000 | 0.118 | +0.118 |
| citation_overlap | 0.000 | 0.118 | +0.118 |
| relation_type_accuracy | n/a | n/a | n/a |

### fortitude_parts_129_135

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 51 | 51 | +0 |
| citation_exact_match | 0.000 | 0.098 | +0.098 |
| citation_partial_match | 0.000 | 0.098 | +0.098 |
| citation_overlap | 0.000 | 0.098 | +0.098 |
| relation_type_accuracy | n/a | n/a | n/a |

### justice_core

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 42 | 42 | +0 |
| citation_exact_match | 0.000 | 0.238 | +0.238 |
| citation_partial_match | 0.000 | 0.238 | +0.238 |
| citation_overlap | 0.000 | 0.238 | +0.238 |
| relation_type_accuracy | n/a | n/a | n/a |

### prudence

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 40 | 40 | +0 |
| citation_exact_match | 0.000 | 0.225 | +0.225 |
| citation_partial_match | 0.000 | 0.225 | +0.225 |
| citation_overlap | 0.000 | 0.225 | +0.225 |
| relation_type_accuracy | n/a | n/a | n/a |

### temperance_141_160

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 46 | 46 | +0 |
| citation_exact_match | 0.000 | 0.130 | +0.130 |
| citation_partial_match | 0.000 | 0.130 | +0.130 |
| citation_overlap | 0.000 | 0.130 | +0.130 |
| relation_type_accuracy | n/a | n/a | n/a |

### temperance_closure_161_170

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 11 | 11 | +0 |
| citation_exact_match | 0.000 | 0.000 | +0.000 |
| citation_partial_match | 0.000 | 0.000 | +0.000 |
| citation_overlap | 0.000 | 0.000 | +0.000 |
| relation_type_accuracy | n/a | n/a | n/a |

### theological_virtues

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 19 | 19 | +0 |
| citation_exact_match | 0.000 | 0.158 | +0.158 |
| citation_partial_match | 0.000 | 0.158 | +0.158 |
| citation_overlap | 0.000 | 0.158 | +0.158 |
| relation_type_accuracy | n/a | n/a | n/a |


## By Support Type

### explicit_textual

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 200 | 200 | +0 |
| citation_exact_match | 0.000 | 0.145 | +0.145 |
| citation_partial_match | 0.000 | 0.145 | +0.145 |
| citation_overlap | 0.000 | 0.145 | +0.145 |
| relation_type_accuracy | n/a | n/a | n/a |

### strong_textual_inference

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 35 | 35 | +0 |
| citation_exact_match | 0.000 | 0.171 | +0.171 |
| citation_partial_match | 0.000 | 0.171 | +0.171 |
| citation_overlap | 0.000 | 0.171 | +0.171 |
| relation_type_accuracy | n/a | n/a | n/a |


## By Task Type

### citation_grounded_moral_answer

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 67 | 67 | +0 |
| citation_exact_match | 0.000 | 0.000 | +0.000 |
| citation_partial_match | 0.000 | 0.000 | +0.000 |
| citation_overlap | 0.000 | 0.000 | +0.000 |
| relation_type_accuracy | n/a | n/a | n/a |

### passage_grounded_doctrinal_qa

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 67 | 67 | +0 |
| citation_exact_match | 0.000 | 0.090 | +0.090 |
| citation_partial_match | 0.000 | 0.090 | +0.090 |
| citation_overlap | 0.000 | 0.090 | +0.090 |
| relation_type_accuracy | n/a | n/a | n/a |

### reviewed_relation_explanation

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 67 | 67 | +0 |
| citation_exact_match | 0.000 | 0.194 | +0.194 |
| citation_partial_match | 0.000 | 0.194 | +0.194 |
| citation_overlap | 0.000 | 0.194 | +0.194 |
| relation_type_accuracy | n/a | n/a | n/a |

### virtue_concept_explanation

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 32 | 32 | +0 |
| citation_exact_match | 0.000 | 0.500 | +0.500 |
| citation_partial_match | 0.000 | 0.500 | +0.500 |
| citation_overlap | 0.000 | 0.500 | +0.500 |
| relation_type_accuracy | n/a | n/a | n/a |

## What This Demonstrates

1. The repo now has one clean, reproducible local 1.5B training recipe that works on Apple Silicon.
2. The committed Christian virtue dataset can measurably move a base model toward repo-specific doctrinal behavior.
3. The adapter is stronger than the base model on the held-out benchmark and on a fixed qualitative goal panel.
4. The repo is publishable as a fine-tuning entrypoint because data, methods, evaluation, and model packaging now line up.

## What This Does Not Demonstrate

1. It does not prove that the local laptop recipe is the best-quality final model.
2. It does not solve the hardest citation-grounded moral-answer cases.
3. It does not replace the need for larger remote CUDA experiments when quality improvement becomes the primary objective.

## Recommended Public Reproduction Path

```bash
make build-christian-virtue-sft
make train-christian-virtue-qwen2-5-1-5b-local-smoke
make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite
make eval-christian-virtue-qwen2-5-1-5b-local-base-test
make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test
make compare-christian-virtue-qwen2-5-1-5b-local-test
make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite
```

## Headline Numbers

- Base citation exact match: 0.0%
- Adapter citation exact match: 15.0%
- Net gain: 15.0%
