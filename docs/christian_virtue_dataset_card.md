# Christian Virtue Dataset Card

## Summary

`christian_virtue_v1` is a chat-style SFT dataset built from reviewed doctrinal annotations in the
Summa Moral Graph repository. It is designed for a Christian virtue assistant grounded in Aquinas's
virtue corpus rather than a generic theology model.

The goal of this dataset is not merely to teach a model to emit citation strings. The goal is to
support Aquinas-grounded Christian virtue reasoning that stays inside reviewed doctrinal evidence
and remains traceable to stable passage ids.

The committed public dataset exports live in:

- [data/processed/sft/exports/christian_virtue_v1](../data/processed/sft/exports/christian_virtue_v1)
- [data/processed/sft/exports/christian_virtue_v1_ood](../data/processed/sft/exports/christian_virtue_v1_ood)

## Public Entry Points

- Fine-tuning guide:
  [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)
- Public claim map:
  [docs/public_claim_map.md](./public_claim_map.md)
- Maintainer workflow:
  [docs/christian_virtue_sft.md](./christian_virtue_sft.md)
- Flagship local report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- Experiment index:
  [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md)
- Repository map:
  [docs/repository_map.md](./repository_map.md)

## Source Data

- Canonical text: `data/interim/summa_moral_segments.jsonl`
- Metadata enrichment: `data/interim/summa_moral_questions.jsonl`,
  `data/interim/summa_moral_articles.jsonl`
- Supervision: eight selected `data/gold/*_reviewed_doctrinal_annotations.jsonl` files

Excluded by default:

- structural-editorial reviewed files
- candidate files
- processed edge exports as primary supervision
- religion / owed-relation / pilot doctrinal blocks

## Scale

Default build statistics:

- `555` reviewed source annotations
- `1883` SFT examples
- `445` explicit-textual source annotations
- `110` strong-textual-inference source annotations

Task families:

- `555` passage-grounded doctrinal QA
- `555` reviewed relation explanation
- `555` citation-grounded moral answer
- `218` concept explanation

Public split surface:

- `1475` train examples
- `175` val examples
- `233` test examples
- prompt-only held-out benchmarks under
  [data/processed/sft/exports/christian_virtue_v1/benchmarks](../data/processed/sft/exports/christian_virtue_v1/benchmarks)

## Schema

Each row contains:

- `example_id`
- `task_type`
- `messages`
- `metadata`

Metadata retains tract, source passage ids, citation labels, subject/object ids, relation type,
support type, and split grouping keys.

Prompt-only benchmark exports are also produced for non-train splits so models can be evaluated on
held-out prompts without shipping the gold assistant answer in the generation input.

## Split Policy

- grouping key: `question_id`
- doctrinal support types:
  - `explicit_textual`
  - `strong_textual_inference`
- optional OOD release:
  [data/processed/sft/exports/christian_virtue_v1_ood](../data/processed/sft/exports/christian_virtue_v1_ood)

## Intended Use

- supervised fine-tuning for Aquinas-grounded Christian virtue assistance
- qualitative evaluation of doctrinal faithfulness and citation behavior
- tract-aware doctrinal QA prototypes grounded in Aquinas
- local Apple-Silicon LoRA baseline runs with `Qwen/Qwen2.5-1.5B-Instruct`
- remote CUDA QLoRA baselines for larger models

## Canonical Published Baseline Using This Dataset

- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Public online chat:
  [jennyzhu0822-summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space)
- Hugging Face Space page:
  [JennyZhu0822/summa-virtue-chat](https://huggingface.co/spaces/JennyZhu0822/summa-virtue-chat)
- Companion graph viewer:
  [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)
- Curated report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- Public quickstart and command path:
  [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)

The current report reflects the canonical local rerun (`20260421_134712` train,
`20260421_141053` adapter eval). The local adapter package in
`artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/` is the authoritative
packaged evaluation surface for that result, while the public GitHub release keeps its original tag
slug for continuity. The current canonical held-out benchmark reaches `0.365` exact citation
overall, with strongest gains on `Virtue concept explanation` and `Reviewed relation explanation`.
The online chat uses the same small-model `Qwen/Qwen2.5-1.5B-Instruct` Christian virtue assistant,
while the Streamlit viewer remains the evidence browser and graph surface.

## Out of Scope

- ungrounded theology chat
- automated promotion of candidate annotations into training truth
- collapsing doctrinal supervision with structural-editorial review material

## Risks

- the outputs are templated from reviewed annotations, so stylistic diversity is bounded
- strong textual inference examples still require careful downstream evaluation for overreach
- citation accuracy is measurable, but doctrinal adequacy still needs human review
