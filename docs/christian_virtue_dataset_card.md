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
- Maintainer workflow:
  [docs/christian_virtue_sft.md](./christian_virtue_sft.md)
- Flagship local report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md](./reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md)
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
- local Apple-Silicon LoRA pilot runs with `Qwen/Qwen2.5-1.5B-Instruct`
- remote CUDA QLoRA baselines for larger models

## Canonical Published Baseline Using This Dataset

- Hugging Face adapter:
  [JennyZhu0822/summa-moral-graph-qwen2.5-1.5b-pilot-lite](https://huggingface.co/JennyZhu0822/summa-moral-graph-qwen2.5-1.5b-pilot-lite)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-pilot-lite-20260418_193038](https://github.com/hanzhenzhujene/summa-moral-graph-fork/releases/tag/christian-virtue-qwen2.5-1.5b-pilot-lite-20260418_193038)
- Curated report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md](./reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md)
- Public quickstart and command path:
  [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)

## Out of Scope

- ungrounded theology chat
- automated promotion of candidate annotations into training truth
- collapsing doctrinal supervision with structural-editorial review material

## Risks

- the outputs are templated from reviewed annotations, so stylistic diversity is bounded
- strong textual inference examples still require careful downstream evaluation for overreach
- citation accuracy is measurable, but doctrinal adequacy still needs human review
