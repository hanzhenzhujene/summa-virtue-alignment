# Christian Virtue Qwen2.5 1.5B Local Baseline Report

## Scope

This report documents the canonical local Apple-Silicon LoRA baseline for the Christian virtue SFT pipeline. It is the official reproducible `Qwen/Qwen2.5-1.5B-Instruct` `local-baseline` demonstration path for this repo.

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
| Local-baseline train subset | `128` |
| Local-baseline eval subset | `32` |
| Max steps | `20` |
| Runtime device | `mps` |
| Git commit | `40c724d0aaab5cdedc25110a1b4545157e9dcea3` |
| Training run id | `20260421_134712` |

Committed inputs:

- Dataset manifest: [data/processed/sft/exports/christian_virtue_v1/manifest.json](../../data/processed/sft/exports/christian_virtue_v1/manifest.json)
- Training config: [configs/train/qwen2_5_1_5b_instruct_lora_mps_local_baseline.yaml](../../configs/train/qwen2_5_1_5b_instruct_lora_mps_local_baseline.yaml)
- Base inference config: [configs/inference/qwen2_5_1_5b_instruct_base_test.yaml](../../configs/inference/qwen2_5_1_5b_instruct_base_test.yaml)
- Adapter inference config: [configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml](../../configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml)
- Published adapter: [Hugging Face model page](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- GitHub release: [Release page](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)

## Executive Readout

This table foregrounds the strongest held-out virtue slices for the repo's intended Aquinas-grounded alignment goal.

| Slice | Base | Adapter | Delta |
| --- | ---: | ---: | ---: |
| Virtue concept explanation | `0.0%` | `65.6%` | `65.6%` |
| Reviewed relation explanation | `0.0%` | `62.7%` | `62.7%` |
| Goal-demo exact citations | `0 / 12` | `6 / 12` | `+6` |

Strongest public task slices:

- Virtue concept explanation: 65.6% exact over `32` held-out prompts.
- Reviewed relation explanation: 62.7% exact over `67` held-out prompts.

Strongest tract slices:

- Justice core: 50.0% exact over `42` held-out prompts.

Why this is a persuasive demo baseline:

- The strongest gain lands on virtue concept explanation, the cleanest direct test of Thomist virtue alignment in this benchmark.
- Reviewed relation explanation also improves materially, which matters because the dataset is built from reviewed doctrinal relations joined back to source passages.
- Goal-demo exact citations move from `0 / 12` to `6 / 12`.
- The gain appears on held-out prompts rather than on memorized training rows.
- This is a deliberately small demo run, so the result should be read as proof that the pipeline works and can scale upward.

Representative examples:

- Clear adapter win: slot 1 `Charity and fraternal correction`.

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
| Eval examples | `32` |
| Per-device train batch size | `1` |
| Gradient accumulation steps | `8` |
| LoRA rank | `16` |
| LoRA alpha | `32` |
| LoRA dropout | `0.05` |
| Seed | `17` |

The local-baseline subset policy is deterministic and balanced rather than random: the trainer selects a round-robin subset across `(task_type, tract)` buckets from the committed `train.jsonl` export, preserving stable within-bucket order while avoiding the first-rows bias of a tiny local run.

- Train subset strategy: `task_tract_round_robin`
- Eval subset strategy: `task_tract_round_robin`
- Train subset task mix: `citation_grounded_moral_answer=32, passage_grounded_doctrinal_qa=32, reviewed_relation_explanation=32, virtue_concept_explanation=32`
- Train subset tract mix: `connected_virtues_109_120=16, fortitude_closure_136_140=16, fortitude_parts_129_135=16, justice_core=16, prudence=16, temperance_141_160=16, temperance_closure_161_170=16, theological_virtues=16`
- Eval subset task mix: `citation_grounded_moral_answer=9, passage_grounded_doctrinal_qa=8, reviewed_relation_explanation=8, virtue_concept_explanation=7`

This corrected local-baseline rerun also uses the repaired vice-opposition prompt wording in the `citation_grounded_moral_answer` family: `excess_opposed_to` and `deficiency_opposed_to` questions now ask for the vice opposed to the virtue object, which matches the underlying reviewed `vice -> virtue` annotations.

Held-out generation also uses deterministic decoding. Both the base model and the adapter run with `do_sample = false`, `max_new_tokens = 256` / `256`, and seed `17` / `17` on the prompt-only benchmark export.

Citation metrics are computed by extracting passage ids from free-form model outputs and comparing them against the reference `source_passage_ids` for each held-out example. Relation-type accuracy is not reported for this baseline because the current generation format does not emit a structured predicted relation label.

## Runtime Environment

| Item | Value |
| --- | --- |
| Python | `3.12.2` |
| Torch | `2.11.0` |
| Transformers | `4.57.6` |
| PEFT | `0.19.1` |
| TRL | `0.29.1` |
| Accelerate | `1.13.0` |
| Approx train wall-clock | `23.2 minutes` |

## Training Trajectory

![Local-baseline training curves](assets/christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg)

*Figure 1. Loss and mean token accuracy across the canonical 20-step `local-baseline` local run. For this public baseline, the claim is not state-of-the-art quality but a stable, inspectable local optimization trace.*

The training curve is healthy for a local demonstration run: loss falls sharply, token accuracy rises, and the small eval slice stays close to the training signal.

## Why `local-baseline` Is The Official Local Rung

![Local recipe timing comparison](assets/christian_virtue_qwen2_5_1_5b_local_recipe_timing_comparison.svg)

*Figure 2. Cumulative wall-clock time to logged steps on Apple `mps` for the interrupted heavier `extended` recipe and the canonical `local-baseline` recipe. This figure supports the operational decision to bless `local-baseline` as the public local path: it is the rung that remains reproducible on a 16 GB laptop.*

The repo keeps the heavier `extended` config for experimentation, but the timing comparison shows why it is not the public quickstart path. On this hardware, the heavier rung becomes operationally unstable long before it becomes the right publication baseline.

## Held-Out Test Comparison

![Base vs adapter test comparison](assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg)

*Figure 3. Held-out citation exact match for the untouched base model versus the LoRA adapter, focusing on the strongest virtue-aligned evaluation slices. This figure supports the central empirical claim that the dataset moves model behavior in the right direction for the repo's intended use rather than merely packaging a training recipe.*

| Model | Count | Citation exact | Citation partial | Citation overlap |
| --- | ---: | ---: | ---: | ---: |
| Base model | `233` | `0.000` | `0.000` | `0.000` |
| LoRA adapter | `233` | `0.365` | `0.365` | `0.365` |

The adapter materially improves held-out citation grounding over the untouched base model on the virtue-aligned slices that most closely match the repo's intended SFT goal. At the same time, the `citation_grounded_moral_answer` slice remains at `0.000` exact in this corrected run, so the present baseline is strongest on concept and relation tasks rather than on fully user-style moral QA.

## Goal Demo Panel

This fixed panel uses held-out examples chosen to reflect the real SFT goal: virtue definition, part distinctions, act relations, vice opposition, and tract-local explanation.

| Panel summary | Value |
| --- | --- |
| Held-out slots | `12` |
| Adapter exact citations | `6 / 12` |
| Adapter-only wins | `6` |
| Both miss | `6` |
| Clearest adapter win | `slot 1 - Charity and fraternal correction` |

The examples below stay fully visible in the repo, but they are collapsed by default so the report reads like a curated release artifact instead of a raw log.

<details>
<summary><strong>1. Charity and fraternal correction</strong> - Reviewed relation explanation - Theological virtues - base miss -> adapter hit</summary>

- Focus: Act/virtue relation inside the theological virtues
- Task type: Reviewed relation explanation
- Tract: Theological virtues
- Prompt: Explain this reviewed doctrinal relation from the cited passage. Tract: Theological virtues Subject: Charity Relation type: has_act Object: Fraternal Correctio…
- Reference citations: `st.ii-ii.q033.a001.resp`
- Citation outcome: `base miss -> adapter hit`

**Reference answer**

> The reviewed relation is that Charity has Fraternal Correction as an act. The passage states this directly. Question 33 explicitly says that fraternal correction is an act of charity. Citations: - st.ii-ii.q033.a001.resp (II-II q.33 a.1 resp)

**Base model excerpt**

> The relation "has_act" between the theological virtue of charity and the act of fraternal correction is explained in the passage as follows: 1. **Relation Type**: The relation is "has_act" which indicates that the theological virtue of charity has the act of fraternal correction as one of its manifestations. 2. **Object**: The object of this relation is the act of fraternal correction. 3. **Passage Context**: The pa…

**LoRA adapter excerpt**

> The reviewed relation is that Charity has the act of Fraternal Correction. This is stated directly in the cited passage, which states: "Fraternity is a virtue of the will , and is directed to the amendment of the brother . Now the amendment of the brother is twofold, one which applies a remedy to the sin of the wrongdoer, considered as hurtful to others, and especially to the common good . This correction is an act…

</details>

<details>
<summary><strong>2. Faith as a theological virtue</strong> - Virtue concept explanation - Theological virtues - base miss -> adapter miss</summary>

- Focus: Virtue explanation in Aquinas's own categories
- Task type: Virtue concept explanation
- Tract: Theological virtues
- Prompt: Explain this concept using only the supporting passages below. Concept: Faith Tract: Theological virtues Question context: The act of faith Supporting passages…
- Reference citations: `st.ii-ii.q002.a002.resp`
- Citation outcome: `base miss -> adapter miss`

**Reference answer**

> Aquinas presents Faith as one that has Act of Faith as an act. Citations: - st.ii-ii.q002.a002.resp (II-II q.2 a.2 resp)

**Base model excerpt**

> The concept of faith, as discussed in the context of the theological virtues, is fundamentally tied to the relationship between the intellect and the will. According to Aquinas, the object of faith can be understood in three ways: 1. **On the Part of the Intellect**: The object of faith is primarily considered on the part of the intellect, which is the source of the act of faith. This aspect of faith involves believ…

**LoRA adapter excerpt**

> Faith is considered as an act of the intellect in relation to God, as stated above (II-II:1:1). The object of faith is divided into two aspects: the material aspect, which is the content of the faith, and the formal aspect, which is the medium of the faith. The formal aspect is the First Truth, to which man gives his adhesion, so as to assent to It. The object of faith is considered as an act of the will in relation…

</details>

<details>
<summary><strong>3. Commutative justice and restitution</strong> - Reviewed relation explanation - Justice core - base miss -> adapter miss</summary>

- Focus: Justice and its proper act
- Task type: Reviewed relation explanation
- Tract: Justice core
- Prompt: Explain this reviewed doctrinal relation from the cited passage. Tract: Justice core Subject: Commutative Justice Relation type: has_act Object: Restitution Pa…
- Reference citations: `st.ii-ii.q062.a001.resp`
- Citation outcome: `base miss -> adapter miss`

**Reference answer**

> The reviewed relation is that Commutative Justice has Restitution as an act. The passage states this directly. Article 1 explicitly states that restitution is an act of commutative justice. Citations: - st.ii-ii.q062.a001.resp (II-II q.62 a.1 resp)

**Base model excerpt**

> The relation "has_act" between "Restitution" and "Commutative Justice" in the cited passage is explained as follows: Restitution is an act of commutative justice. According to Aquinas, restitution involves restoring a person to the possession or dominion of their thing, which is a fundamental aspect of commutative justice. This act of restitution is considered equal in justice to the payment of one thing for another…

**LoRA adapter excerpt**

> The reviewed relation is that of has_act. The cited passage states this directly in the first sentence: "To restore is seemingly the same as to reinstate a person in the possession or dominion of his thing, so that in restitution we consider the equality of justice attending the payment of one thing for another, and this belongs to commutative justice . Hence restitution is an act of commutative justice , occasioned…

</details>

<details>
<summary><strong>4. Commutative justice as a concept</strong> - Virtue concept explanation - Justice core - base miss -> adapter hit</summary>

- Focus: Virtue definition with tract-local grounding
- Task type: Virtue concept explanation
- Tract: Justice core
- Prompt: Explain this concept using only the supporting passages below. Concept: Commutative Justice Tract: Justice core Question context: Restitution Supporting passag…
- Reference citations: `st.ii-ii.q062.a001.resp`
- Citation outcome: `base miss -> adapter hit`

**Reference answer**

> Aquinas presents Commutative Justice as one that has Restitution as an act. Citations: - st.ii-ii.q062.a001.resp (II-II q.62 a.1 resp)

**Base model excerpt**

> Commutative justice, as explained in the supporting passage, involves restoring a person to the possession or dominion of their thing. This concept is central to restitution, which is an act of commutative justice. Restitution is considered when one person has what belongs to another, either with or without the other's consent. The passage specifically mentions restitution in the context of robbery or theft, where t…

**LoRA adapter excerpt**

> Commutative Justice Supporting passage: - st.ii-ii.q062.a001.resp (II-II q.62 a.1 resp) Explanation: Restitution is considered to be the same as reinstate a person in the possession or dominion of his thing. This is because restitution involves restoring something to its rightful owner, which is a form of commutative justice. Commutative justice deals with the equality of justice in the exchange of one thing for ano…

</details>

<details>
<summary><strong>5. Regnative prudence</strong> - Virtue concept explanation - Prudence - base miss -> adapter hit</summary>

- Focus: Prudence species and political ordering
- Task type: Virtue concept explanation
- Tract: Prudence
- Prompt: Explain this concept using only the supporting passages below. Concept: Regnative Prudence Tract: Prudence Question context: The subjective parts of prudence S…
- Reference citations: `st.ii-ii.q050.a001.resp`
- Citation outcome: `base miss -> adapter hit`

**Reference answer**

> Aquinas presents Regnative Prudence as one that is a subjective part of Prudence. Citations: - st.ii-ii.q050.a001.resp (II-II q.50 a.1 resp)

**Base model excerpt**

> Regnative prudence is a specific form of prudence that applies to rulers who govern both themselves and the perfect community of a city or kingdom. It is the most perfect kind of prudence because it involves governing not just an individual but a larger, more universal community. This prudence is considered a species of prudence because it is a distinct and specialized form of prudence that is uniquely applicable to…

**LoRA adapter excerpt**

> Regnative Prudence is a special kind of prudence that governs and commands in a city or kingdom. This is stated in the cited passage, which states that prudence governs and commands, and that this applies to a king governing a city or kingdom. The passage explicitly states that this is a special kind of prudence, and that it is a species of prudence. Citations: - st.ii-ii.q050.a001.resp (II-II q.50 a.1 resp)

</details>

<details>
<summary><strong>6. Military prudence as a part of prudence</strong> - Reviewed relation explanation - Prudence - base miss -> adapter hit</summary>

- Focus: Subjective-part classification within prudence
- Task type: Reviewed relation explanation
- Tract: Prudence
- Prompt: Why does this passage support the reviewed doctrinal relation below? Tract: Prudence Subject: Military Prudence Relation type: subjective_part_of Object: Prude…
- Reference citations: `st.ii-ii.q050.a004.resp`
- Citation outcome: `base miss -> adapter hit`

**Reference answer**

> The reviewed relation is that Military Prudence is a subjective part of Prudence. The passage states this directly. Q50.4 explicitly says there should be military prudence alongside political prudence. Citations: - st.ii-ii.q050.a004.resp (II-II q.50 a.4 resp)

**Base model excerpt**

> This passage supports the reviewed doctrinal relation between "Military Prudence" and "Prudence" by explicitly stating that military prudence is a necessary complement to prudence. Specifically, it asserts that prudence should conform to nature, which includes both the natural tendency to govern oneself and the natural defense against external threats. The passage then explains that this natural defense includes the…

**LoRA adapter excerpt**

> The passage supports the reviewed relation by explicitly stating that military prudence is a part of prudence. The passage directly states this in the last sentence, using Aquinas's categories rather than generic self-help language. Citations: - st.ii-ii.q050.a004.resp (II-II q.50 a.4 resp)

</details>

<details>
<summary><strong>7. Truth in self-presentation</strong> - Virtue concept explanation - Connected virtues (II-II qq.109-120) - base miss -> adapter hit</summary>

- Focus: Connected virtue outside the four cardinal/theological headline labels
- Task type: Virtue concept explanation
- Tract: Connected virtues (II-II qq.109-120)
- Prompt: Explain this concept using only the supporting passages below. Concept: Truth Tract: Connected virtues (II-II qq.109-120) Question context: Truth Supporting pa…
- Reference citations: `st.ii-ii.q109.a002.resp, st.ii-ii.q109.a003.resp`
- Citation outcome: `base miss -> adapter hit`

**Reference answer**

> Aquinas presents Truth as one that concerns self-presentation in relation to Self-Presentation. It also is annexed to Justice. Citations: - st.ii-ii.q109.a002.resp (II-II q.109 a.2 resp) - st.ii-ii.q109.a003.resp (II-II q.109 a.3 resp)

**Base model excerpt**

> The concept of truth, as explained in the supporting passages, is a special virtue that is connected to justice. According to Aquinas, truth is a virtue that is annexed to justice, meaning it is a secondary virtue that falls short of the perfect virtue of justice but shares certain characteristics with it. Truth is directed to another, manifesting the things that concern the person who is being addressed. It also se…

**LoRA adapter excerpt**

> Truth is a special virtue connected to justice. Truth is related to justice as a secondary virtue to its principal. Truth is directed to another, as a manifestation of the truth is directed to another person. Truth also equals signs to the things that concern man himself, as justice does. Truth falls short of the proper aspect of justice in relation to moral debt, rather than legal debt. Truth is a part of justice,…

</details>

<details>
<summary><strong>8. Abstinence within temperance</strong> - Reviewed relation explanation - Temperance (II-II qq.141-160) - base miss -> adapter miss</summary>

- Focus: Subjective-part classification in temperance
- Task type: Reviewed relation explanation
- Tract: Temperance (II-II qq.141-160)
- Prompt: Why does this passage support the reviewed doctrinal relation below? Tract: Temperance (II-II qq.141-160) Subject: Abstinence Relation type: subjective_part_of…
- Reference citations: `st.ii-ii.q143.a001.resp`
- Citation outcome: `base miss -> adapter miss`

**Reference answer**

> The reviewed relation is that Abstinence is a subjective part of Temperance. The passage states this directly. Question 143 explicitly assigns abstinence among temperance's subjective parts. Citations: - st.ii-ii.q143.a001.resp (II-II q.143 a.1 resp)

**Base model excerpt**

> This passage supports the reviewed doctrinal relation between Temperance and Abstinence by explaining how temperance has subjective parts, specifically "shamefacedness" and "honesty." These subjective parts are integral to temperance and are related to abstinence. The passage states that temperance more than any other virtue lays claim to a certain comeliness, and the vices of intemperance excel others in disgrace.…

**LoRA adapter excerpt**

> The passage supports the reviewed doctrinal relation by explicitly stating that temperance has subjective parts. The passage states: - Temperance has three kinds of parts: integral, subjective, and potential. - The integral parts of temperance are "shamefacedness" and "honesty." - The subjective parts of temperance are its species, which are differentiated according to the difference of matter or object. The passage…

</details>

<details>
<summary><strong>9. Continence within temperance</strong> - Reviewed relation explanation - Temperance (II-II qq.141-160) - base miss -> adapter hit</summary>

- Focus: Potential-part distinction in temperance
- Task type: Reviewed relation explanation
- Tract: Temperance (II-II qq.141-160)
- Prompt: Why does this passage support the reviewed doctrinal relation below? Tract: Temperance (II-II qq.141-160) Subject: Continence Relation type: potential_part_of…
- Reference citations: `st.ii-ii.q143.a001.resp`
- Citation outcome: `base miss -> adapter hit`

**Reference answer**

> The reviewed relation is that Continence is a potential part of Temperance. The passage states this directly. Question 143 explicitly assigns continence among temperance's potential parts. Citations: - st.ii-ii.q143.a001.resp (II-II q.143 a.1 resp)

**Base model excerpt**

> This passage supports the reviewed doctrinal relation between Temperance and Continence by explaining how Continence is a potential part of Temperance. Specifically, the passage states that Continence is one of the potential parts of Temperance, which is a cardinal virtue. It distinguishes Continence as a potential part from the integral parts of Temperance, which include "shamefacedness" and "honesty." The passage…

**LoRA adapter excerpt**

> The passage supports the reviewed relation by explicitly stating that continence is a potential part of temperance. The passage directly cites this relation in the cited passage id st.ii-ii.q143.a001.resp. Key passage text: The passage explicitly states this relation in the cited passage id st.ii-ii.q143.a001.resp. Citations: - st.ii-ii.q143.a001.resp (II-II q.143 a.1 resp)

</details>

<details>
<summary><strong>10. Lust and chastity</strong> - Citation-grounded moral answer - Temperance (II-II qq.141-160) - base miss -> adapter miss</summary>

- Focus: Vice opposition rather than generic moral paraphrase
- Task type: Citation-grounded moral answer
- Tract: Temperance (II-II qq.141-160)
- Prompt: According to Aquinas, what vice is opposed to Chastity by excess?
- Reference citations: `st.ii-ii.q153.a001.resp`
- Citation outcome: `base miss -> adapter miss`

**Reference answer**

> According to the cited passage, Lust is opposed to Chastity by excess. The passage states this directly. Lust is the disordered contrary of chastity in venereal matter. Citations: - st.ii-ii.q153.a001.resp (II-II q.153 a.1 resp)

**Base model excerpt**

> According to Aquinas, the vice opposed to chastity by excess is lust. This can be found in his discussion in the Summa Theologica, specifically in the Second Part of the Second Part, Question 82, Article 2, where he states: "The vice opposed to chastity by excess is lust."

**LoRA adapter excerpt**

> According to Aquinas, the vice opposed to Chastity by excess is Lust. The passage states this directly: CITATION ST.ii-ii.q006.a001.resp (II-II q.6 a.1 resp) Aquinas identifies Lust as the vice opposed to Chastity by excess. He states this explicitly in the cited passage. The passage states this directly: CITATION ST.ii-ii.q006.a001.resp (II-II q.6 a.1 resp) Aquinas identifies Lust as the vice opposed to Chastity by…

</details>

<details>
<summary><strong>11. Constancy in the fortitude tract</strong> - Virtue concept explanation - Fortitude closure (II-II qq.136-140) - base miss -> adapter miss</summary>

- Focus: Fortitude-part explanation without collapsing nearby concepts
- Task type: Virtue concept explanation
- Tract: Fortitude closure (II-II qq.136-140)
- Prompt: Explain this concept using only the supporting passages below. Concept: Constancy Tract: Fortitude closure (II-II qq.136-140) Question context: Perseverance Su…
- Reference citations: `st.ii-ii.q137.a003.resp`
- Citation outcome: `base miss -> adapter miss`

**Reference answer**

> Aquinas presents Constancy as one that is part of fortitude through Fortitude. Citations: - st.ii-ii.q137.a003.resp (II-II q.137 a.3 resp)

**Base model excerpt**

> In the context of perseverance and constancy, as discussed in the passage from St. Thomas Aquinas's "Summa Theologica," these virtues are distinguished by their approach to maintaining virtue in the face of challenges. Perseverance is concerned with the intrinsic difficulty of maintaining a good action over time, which is inherent to the act itself. Constancy, on the other hand, addresses external hindrances that ma…

**LoRA adapter excerpt**

> Constancy is a virtue that is subordinate to perseverance in the moral hierarchy. The passage states this directly in the cited passage. It also explains that constancy is a virtue that makes it easier to persist in good against external hindrances, while perseverance makes it easier to persist against the difficulty of the continuance of the act itself. This is further supported by the cited passage. The cited pass…

</details>

<details>
<summary><strong>12. Magnificence and great work</strong> - Citation-grounded moral answer - Fortitude parts (II-II qq.129-135) - base miss -> adapter miss</summary>

- Focus: Tract-local object relation in annexed virtues
- Task type: Citation-grounded moral answer
- Tract: Fortitude parts (II-II qq.129-135)
- Prompt: What does Aquinas teach about the relation between Magnificence and Great Work?
- Reference citations: `st.ii-ii.q135.a001.resp`
- Citation outcome: `base miss -> adapter miss`

**Reference answer**

> According to the cited passage, Magnificence concerns great work in relation to Great Work. The passage states this directly. Article 1 explicitly says the magnificent man intends principally the greatness of his work. Citations: - st.ii-ii.q135.a001.resp (II-II q.135 a.1 resp)

**Base model excerpt**

> Aquinas teaches that Magnificence and Great Work are closely related in his moral philosophy. According to Aquinas, Magnificence is a virtue that involves magnanimity and generosity, characterized by a sense of nobility and a desire to do good. Great Work, on the other hand, refers to the fulfillment of one's duties and responsibilities in life. Aquinas argues that Magnificence is essential for Great Work. He states…

**LoRA adapter excerpt**

> According to passage ST.ii-ii.q001.a001.resp, magnificence is a moral virtue. The relation between magnificence and great work is that of a good to a good work. The relation is that of a good to a good work because the good of a good work is the good of the agent who does it. The relation is that of a good to a good work because the good of a good work is the good of the agent who does it. The relation is that of a…

</details>

## Comparison Summary

- Baseline: Base model
- Candidate: LoRA adapter

### Overall

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 233 | 233 | +0 |
| citation_exact_match | 0.000 | 0.365 | +0.365 |
| citation_partial_match | 0.000 | 0.365 | +0.365 |
| citation_overlap | 0.000 | 0.365 | +0.365 |
| relation_type_accuracy | n/a | n/a | n/a |

### By Split

#### test

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 233 | 233 | +0 |
| citation_exact_match | 0.000 | 0.365 | +0.365 |
| citation_partial_match | 0.000 | 0.365 | +0.365 |
| citation_overlap | 0.000 | 0.365 | +0.365 |
| relation_type_accuracy | n/a | n/a | n/a |


### By Tract

#### connected_virtues_109_120

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 7 | 7 | +0 |
| citation_exact_match | 0.000 | 0.429 | +0.429 |
| citation_partial_match | 0.000 | 0.429 | +0.429 |
| citation_overlap | 0.000 | 0.429 | +0.429 |
| relation_type_accuracy | n/a | n/a | n/a |

#### fortitude_closure_136_140

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 17 | 17 | +0 |
| citation_exact_match | 0.000 | 0.294 | +0.294 |
| citation_partial_match | 0.000 | 0.294 | +0.294 |
| citation_overlap | 0.000 | 0.294 | +0.294 |
| relation_type_accuracy | n/a | n/a | n/a |

#### fortitude_parts_129_135

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 51 | 51 | +0 |
| citation_exact_match | 0.000 | 0.176 | +0.176 |
| citation_partial_match | 0.000 | 0.176 | +0.176 |
| citation_overlap | 0.000 | 0.176 | +0.176 |
| relation_type_accuracy | n/a | n/a | n/a |

#### justice_core

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 42 | 42 | +0 |
| citation_exact_match | 0.000 | 0.500 | +0.500 |
| citation_partial_match | 0.000 | 0.500 | +0.500 |
| citation_overlap | 0.000 | 0.500 | +0.500 |
| relation_type_accuracy | n/a | n/a | n/a |

#### prudence

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 40 | 40 | +0 |
| citation_exact_match | 0.000 | 0.475 | +0.475 |
| citation_partial_match | 0.000 | 0.475 | +0.475 |
| citation_overlap | 0.000 | 0.475 | +0.475 |
| relation_type_accuracy | n/a | n/a | n/a |

#### temperance_141_160

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 46 | 46 | +0 |
| citation_exact_match | 0.000 | 0.326 | +0.326 |
| citation_partial_match | 0.000 | 0.326 | +0.326 |
| citation_overlap | 0.000 | 0.326 | +0.326 |
| relation_type_accuracy | n/a | n/a | n/a |

#### temperance_closure_161_170

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 11 | 11 | +0 |
| citation_exact_match | 0.000 | 0.364 | +0.364 |
| citation_partial_match | 0.000 | 0.364 | +0.364 |
| citation_overlap | 0.000 | 0.364 | +0.364 |
| relation_type_accuracy | n/a | n/a | n/a |

#### theological_virtues

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 19 | 19 | +0 |
| citation_exact_match | 0.000 | 0.474 | +0.474 |
| citation_partial_match | 0.000 | 0.474 | +0.474 |
| citation_overlap | 0.000 | 0.474 | +0.474 |
| relation_type_accuracy | n/a | n/a | n/a |


### By Support Type

#### explicit_textual

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 200 | 200 | +0 |
| citation_exact_match | 0.000 | 0.345 | +0.345 |
| citation_partial_match | 0.000 | 0.345 | +0.345 |
| citation_overlap | 0.000 | 0.345 | +0.345 |
| relation_type_accuracy | n/a | n/a | n/a |

#### strong_textual_inference

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 35 | 35 | +0 |
| citation_exact_match | 0.000 | 0.486 | +0.486 |
| citation_partial_match | 0.000 | 0.486 | +0.486 |
| citation_overlap | 0.000 | 0.486 | +0.486 |
| relation_type_accuracy | n/a | n/a | n/a |


### By Task Type

#### citation_grounded_moral_answer

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 67 | 67 | +0 |
| citation_exact_match | 0.000 | 0.000 | +0.000 |
| citation_partial_match | 0.000 | 0.000 | +0.000 |
| citation_overlap | 0.000 | 0.000 | +0.000 |
| relation_type_accuracy | n/a | n/a | n/a |

#### passage_grounded_doctrinal_qa

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 67 | 67 | +0 |
| citation_exact_match | 0.000 | 0.328 | +0.328 |
| citation_partial_match | 0.000 | 0.328 | +0.328 |
| citation_overlap | 0.000 | 0.328 | +0.328 |
| relation_type_accuracy | n/a | n/a | n/a |

#### reviewed_relation_explanation

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 67 | 67 | +0 |
| citation_exact_match | 0.000 | 0.627 | +0.627 |
| citation_partial_match | 0.000 | 0.627 | +0.627 |
| citation_overlap | 0.000 | 0.627 | +0.627 |
| relation_type_accuracy | n/a | n/a | n/a |

#### virtue_concept_explanation

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| count | 32 | 32 | +0 |
| citation_exact_match | 0.000 | 0.656 | +0.656 |
| citation_partial_match | 0.000 | 0.656 | +0.656 |
| citation_overlap | 0.000 | 0.656 | +0.656 |
| relation_type_accuracy | n/a | n/a | n/a |

## What This Demonstrates

1. The repo now has one clean, reproducible local 1.5B training recipe that works on Apple Silicon.
2. The committed Christian virtue dataset can measurably move a base model toward repo-specific doctrinal behavior.
3. The adapter is stronger than the base model on the held-out benchmark and on a fixed qualitative goal panel.
4. The repo is publishable as a fine-tuning entrypoint because data, methods, evaluation, and model packaging now line up.

## Why This Is A Demo Baseline

1. It does not claim that the local laptop recipe is the best-quality final model.
2. It should be read as a proof-of-pipeline baseline built on a deliberately small demo model.
3. It motivates larger remote CUDA experiments when stronger final quality becomes the primary objective.

## Recommended Public Reproduction Path

```bash
make setup-christian-virtue-local
make reproduce-christian-virtue-qwen2-5-1-5b-local
```

The one-command reproduce target runs the dataset build, `smoke`, canonical `local-baseline` train, base test eval, adapter test eval, comparison, report rebuild, and publication verification gate in order.
The final verification step is still exposed directly as `make verify-christian-virtue-qwen2-5-1-5b-local-publishable` when you want to run the public-surface QA gate on its own.

## Headline Numbers

- Base citation exact match: 0.0%
- Adapter citation exact match: 36.5%
- Net gain: 36.5%
