# Christian Virtue Dataset Card

## Summary

`christian_virtue_v1` is a chat-style SFT dataset built from reviewed doctrinal annotations in the
Summa Moral Graph repository. It is designed for a Christian virtue assistant grounded in Aquinas's
virtue corpus rather than a generic theology model.

The committed public dataset exports live in:

- [data/processed/sft/exports/christian_virtue_v1](../data/processed/sft/exports/christian_virtue_v1)
- [data/processed/sft/exports/christian_virtue_v1_ood](../data/processed/sft/exports/christian_virtue_v1_ood)

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

## Intended Use

- supervised fine-tuning for citation-aware virtue assistance
- qualitative evaluation of citation behavior
- tract-aware doctrinal QA prototypes grounded in Aquinas
- local Apple-Silicon LoRA pilot runs with `Qwen/Qwen2.5-1.5B-Instruct`
- remote CUDA QLoRA baselines for larger models

## Out of Scope

- ungrounded theology chat
- automated promotion of candidate annotations into training truth
- collapsing doctrinal supervision with structural-editorial review material

## Risks

- the outputs are templated from reviewed annotations, so stylistic diversity is bounded
- strong textual inference examples still require careful downstream evaluation for overreach
- citation accuracy is measurable, but doctrinal adequacy still needs human review
