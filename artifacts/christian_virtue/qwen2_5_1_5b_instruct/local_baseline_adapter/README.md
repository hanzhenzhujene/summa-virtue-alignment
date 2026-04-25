---
base_model: Qwen/Qwen2.5-1.5B-Instruct
base_model_relation: adapter
license: mit
library_name: peft
pipeline_tag: text-generation
language:
- en
tags:
- lora
- text-generation
- christian-virtue
- aquinas
- summa-moral-graph
- evidence-grounded
- citation-aware
---

# Summa Moral Graph Christian Virtue LoRA Adapter

This is the canonical reproducible LoRA adapter for the `summa-moral-graph` Christian virtue SFT baseline. It fine-tunes `Qwen/Qwen2.5-1.5B-Instruct` toward Aquinas-grounded Christian virtue reasoning while preserving explicit passage-level traceability to reviewed evidence.

## Abstract

The purpose of this model is not to produce generic theological chat or to memorize citation strings. The goal is to show, in a compact and reproducible public baseline, that reviewed Summa Moral Graph supervision can measurably move a general model toward Aquinas's virtue categories, evidence-bounded answers, and citation-aware outputs.

## Snapshot

| Item | Value |
| --- | --- |
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Training mode | LoRA on Apple Silicon `mps`, `float16`, no quantization |
| Reviewed source annotations | `555` |
| Total SFT examples | `1883` |
| Train / val / test | `1475 / 175 / 233` |
| Canonical run id | `20260421_134712` |
| Git commit | `40c724d0aaab5cdedc25110a1b4545157e9dcea3` |
| Held-out exact citation | `36.5%` |
| Strongest task slice | `Virtue concept explanation` at `65.6%` |
| Strongest tract slice | `Justice core` at `50.0%` |

## Artifact Status

- The public GitHub release keeps the earlier distribution tag `christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038` for continuity, but the authoritative benchmark numbers in this package and curated report come from the corrected run `20260421_134712`.
- Treat the curated report and local package manifest as the canonical evaluation surface for the current repo numbers.
- `subset_summary.json` records the exact balanced `(task_type, tract)` composition of the local training and eval subsets used for this run.

## Why This Adapter Exists

- Train an Aquinas-grounded Christian virtue assistant rather than a generic theology bot.
- Keep the supervision evidence-first: reviewed doctrinal annotations only, joined back to stable passage ids.
- Demonstrate a small public baseline that others can inspect, reproduce, and adapt to their own models before scaling up to larger runs.

## Public Benchmark Highlights

| Highlight | Base | Adapter | Delta |
| --- | ---: | ---: | ---: |
| Held-out benchmark exact citation | `0.0%` | `36.5%` | `36.5%` |
| Virtue concept explanation | `0.0%` | `65.6%` | `65.6%` |
| Reviewed relation explanation | `0.0%` | `62.7%` | `62.7%` |
| Justice core tract | `0.0%` | `50.0%` | `50.0%` |

## Executive Readout

- Held-out benchmark exact citation reaches `36.5%` over `233` prompts.
- The clearest public win is `Virtue concept explanation`: `65.6%` exact over `32` held-out prompts.
- Second strongest task slice: `Reviewed relation explanation` at `62.7%` exact over `67` prompts.
- Strongest tract slice: `Justice core` at `50.0%` exact over `42` prompts.
- This published run uses a deliberately small 1.5B local demo model, so the result should be read as proof that the pipeline works rather than as the ceiling for final quality.
- This package intentionally foregrounds the strongest virtue-aligned slices; the full held-out matrix remains in the published report.
- Full task/tract breakdowns and the qualitative goal-demo panel live in the published report.

![Held-out benchmark comparison](./assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg)

*Figure. Held-out base-vs-adapter comparison from the canonical local `local-baseline` run. The key claim is straightforward: even a small reproducible demo baseline moves model behavior in the right direction, which makes this a credible public SFT template rather than only a code release.*

## Dataset And Evidence Policy

- Training export: `data/processed/sft/exports/christian_virtue_v1`
- Dataset manifest: `data/processed/sft/exports/christian_virtue_v1/manifest.json`
- Dataset card: [GitHub link](https://github.com/hanzhenzhujene/summa-virtue-alignment/blob/29921f1a625c73c5a221bcb170c666efb6cba923/docs/christian_virtue_dataset_card.md)
- Full report: [GitHub link](https://github.com/hanzhenzhujene/summa-virtue-alignment/blob/29921f1a625c73c5a221bcb170c666efb6cba923/docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- GitHub release: https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038
- Hugging Face adapter: https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b
- Online chat: https://jennyzhu0822-summa-virtue-chat.hf.space
- Graph viewer: https://summa-moral-graph.streamlit.app/
- Supervision source: approved reviewed doctrinal annotations only
- Excluded from default training truth: structural-editorial review, candidate material, and processed edge exports
- Leakage-safe grouping key: `question_id`

Task families in this export:

- Passage-grounded doctrinal QA: `555`
- Reviewed relation explanation: `555`
- Citation-grounded moral answer: `555`
- Virtue concept explanation: `218`

## How To Use This Adapter

```python
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_model_id = "Qwen/Qwen2.5-1.5B-Instruct"
adapter_id = "JennyZhu0822/summa-virtue-qwen2.5-1.5b"

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16,
    device_map="auto",
)
model = PeftModel.from_pretrained(base_model, adapter_id)
```

Recommended use pattern:

- Ask for Aquinas-grounded explanations of virtues, vices, acts, or relations.
- Ask the model to stay within cited support and to preserve stable passage ids when possible.
- Keep the tokenizer/chat template aligned with the listed base model so the canonical prompt format is preserved.
- Use exactly the listed base model; this adapter is not meant to be merged into a different backbone without retesting.

## Reproduce This Exact Artifact

- Hugging Face adapter: https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b
- Online chat: https://jennyzhu0822-summa-virtue-chat.hf.space
- Graph viewer: https://summa-moral-graph.streamlit.app/
- GitHub repo: https://github.com/hanzhenzhujene/summa-virtue-alignment
- Matching GitHub release: https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038
- Curated experiment report: [GitHub link](https://github.com/hanzhenzhujene/summa-virtue-alignment/blob/29921f1a625c73c5a221bcb170c666efb6cba923/docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- Dataset card: [GitHub link](https://github.com/hanzhenzhujene/summa-virtue-alignment/blob/29921f1a625c73c5a221bcb170c666efb6cba923/docs/christian_virtue_dataset_card.md)

The shortest canonical reproduction path is:

```bash
make setup-christian-virtue-local
make reproduce-christian-virtue-qwen2-5-1-5b-local
make verify-christian-virtue-qwen2-5-1-5b-local-publishable
```

The repo also keeps the stepwise train/eval/report commands and the full report if you need a more granular audit trail.

## What This Demonstrates

- The dataset can move even a small general instruction model toward better Aquinas-grounded virtue reasoning.
- A fully local Apple-Silicon run can produce a meaningful, inspectable held-out improvement that proves the pipeline works.
- The repo is usable as a public fine-tuning template for other researchers who want to swap in their own base model or scale up.

## Next Step For Stronger Results

- This published checkpoint is the easy-to-reproduce demo baseline, not the intended final ceiling for model quality.
- The same dataset and workflow are designed to support larger models and longer GPU-backed experiments when stronger results become the priority.
