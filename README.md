# Summa Virtue Alignment

Evidence-first dataset, minimal SFT demonstration, and audit surface for Thomist moral virtue
alignment, built on the evidence model and corpus work of Summa Moral Graph.

This repo packages one public research release: a reviewed Christian virtue dataset, a reproducible
local fine-tuning path, and an inspectable theological trail back to Aquinas's text.

[![Read the SFT guide](https://img.shields.io/badge/Start%20here-SFT%20guide-1f4d3b?style=for-the-badge)](./docs/fine_tune_with_summa_moral_graph.md)
[![View the published adapter](https://img.shields.io/badge/Hugging%20Face-published%20adapter-c97d20?style=for-the-badge&logo=huggingface&logoColor=white)](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
[![Open the live viewer](https://img.shields.io/badge/Open%20the%20live%20viewer-summa--moral--graph.streamlit.app-183b56?style=for-the-badge&logo=streamlit&logoColor=white)](https://summa-moral-graph.streamlit.app/)

![Python](https://img.shields.io/badge/Python-3.11%2B-2f5d8a?style=flat-square)
![Research Release](https://img.shields.io/badge/Release-publication--ready-1f4d3b?style=flat-square)
![Evidence](https://img.shields.io/badge/Evidence-segment--grounded-596b4f?style=flat-square)
![Layers](https://img.shields.io/badge/Layers-reviewed%20%7C%20editorial%20%7C%20structural%20%7C%20candidate-6d5a7a?style=flat-square)
[![Public Release Check](https://github.com/hanzhenzhujene/summa-virtue-alignment/actions/workflows/public-release-check.yml/badge.svg)](https://github.com/hanzhenzhujene/summa-virtue-alignment/actions/workflows/public-release-check.yml)

> **BUILT FROM THE MAIN GRAPH**  
> [**Summa Moral Graph**](https://github.com/hanzhenzhujene/summa-moral-graph) · Jenny Zhu's interactive Aquinas dashboard and evidence-first knowledge graph. [Live viewer](https://summa-moral-graph.streamlit.app/)

> Minimal example, not ceiling: the released `Qwen/Qwen2.5-1.5B-Instruct` LoRA adapter is a
> deliberately small Apple-Silicon run. Its job is to prove that the dataset, training loop, and
> evaluation surface work end to end on reviewed evidence. It is not the strongest achievable final model.

## Public Result

The public claim is narrow and testable: reviewed Christian virtue supervision can move a small
general model toward better Thomist moral virtue behavior on held-out prompts.

| Public highlight | Base | Adapter | Delta |
| --- | ---: | ---: | ---: |
| Virtue concept explanation | `0.0%` | `40.6%` | `+40.6%` |
| Reviewed relation explanation | `0.0%` | `20.9%` | `+20.9%` |
| Theological virtues tract | `0.0%` | `21.1%` | `+21.1%` |
| Goal-demo exact citations | `0 / 12` | `5 / 12` | `+5` |

![Local-baseline training curves](docs/reports/assets/christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg)

*Figure 1. Training trace for the canonical `local-baseline` run on Apple Silicon `mps`. The point
is not scale; it is a stable, inspectable local optimization path.*

![Base vs adapter held-out comparison](docs/reports/assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg)

*Figure 2. Held-out exact citation match on the strongest virtue-aligned slices. This is the
central empirical claim of the repo.*

The full breakdown, qualitative panel, and method details live in the
[flagship report](./docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md).

## Three Purposes

This repo has three public purposes.

| Purpose | What is public here | Why it matters |
| --- | --- | --- |
| Curate reviewed Thomist virtue supervision | `555` approved doctrinal annotations turned into `1883` training examples, joined back to stable passage ids | The training signal is inspectable moral-theological evidence, not vague religion text |
| Demonstrate a real minimal SFT path | A reproducible `Qwen/Qwen2.5-1.5B-Instruct` LoRA run on Apple Silicon `mps` | A new reader can rerun the full loop without renting a large GPU |
| Preserve an audit trail | Held-out benchmarks, curated report, released adapter, and live evidence browser | A reviewer can inspect what was trained, what improved, and what remains limited |

## Start Here

| I want to... | Start here |
| --- | --- |
| Reproduce the minimal public baseline | `make setup-christian-virtue-local` then `make reproduce-christian-virtue-qwen2-5-1-5b-local` |
| Inspect the strongest evidence | [Flagship report](./docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md) |
| Fine-tune my own model on the same dataset | [docs/fine_tune_with_summa_moral_graph.md](./docs/fine_tune_with_summa_moral_graph.md) |
| Inspect the released model artifact | [Hugging Face adapter](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b) · [GitHub release](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038) |
| Audit the passages and graph directly | [Live viewer](https://summa-moral-graph.streamlit.app/) |

Canonical local path:

```bash
make setup-christian-virtue-local
make reproduce-christian-virtue-qwen2-5-1-5b-local
make public-release-check
```

The pinned local environment lives at
[requirements/local-mps-py312.lock.txt](./requirements/local-mps-py312.lock.txt).

## Fine-Tune Your Model With Summa Moral Graph

This repo is the public entrypoint for reusing the same evidence-first Christian virtue dataset and
evaluation loop with another backbone.

Start with:

- [docs/fine_tune_with_summa_moral_graph.md](./docs/fine_tune_with_summa_moral_graph.md)
- [docs/christian_virtue_dataset_card.md](./docs/christian_virtue_dataset_card.md)
- [data/processed/sft/exports/christian_virtue_v1](./data/processed/sft/exports/christian_virtue_v1)
- [data/processed/sft/exports/christian_virtue_v1_ood](./data/processed/sft/exports/christian_virtue_v1_ood)
- [artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](./artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md)

Smallest model-swap contract:

- `model_name_or_path`
- `lora_target_modules`
- `runtime_backend`
- `torch_dtype`
- `max_seq_length`

## Thomist Target

The target is not a generic theology chatbot. The target is Thomist moral virtue alignment: a
model that answers within Aquinas's moral categories, stays inside reviewed evidence, and preserves
source traceability.

In scope:

- Aquinas-grounded explanations of virtues, vices, acts, parts, and oppositions
- evidence-bounded doctrinal QA
- citation traceability back to stable passage ids

Out of scope:

- generic religion chat
- pastoral counseling or spiritual direction
- candidate material or structural-editorial review treated as training truth
- objections and `sed contra` used as default doctrinal supervision

## Theological Grounding

This dataset is built for Aquinas's treatment of the virtues in the moral corpus of the *Summa
Theologiae*, not for broad religious paraphrase.

| Theme | Aquinas locus | Why it matters here |
| --- | --- | --- |
| Charity considered in itself | [II-II q.23 a.1](https://www.newadvent.org/summa/3023.htm#article1) | Grounds the theological-virtue tract in Aquinas's own account of charity |
| Fraternal correction as an act of charity | [II-II q.33 a.1](https://www.newadvent.org/summa/3033.htm#article1) | Grounds a representative act-of-charity relation in the dataset and goal-demo panel |
| Prudence considered in itself | [II-II q.47 a.1](https://www.newadvent.org/summa/3047.htm#article1) | Grounds the prudence tract in Aquinas's account of practical reason |
| Justice | [II-II q.58 a.1](https://www.newadvent.org/summa/3058.htm#article1) | Grounds the justice tract in Aquinas's formal account of justice |

## Dataset Snapshot

### Corpus surface

- `296` questions
- `1482` articles
- `6032` doctrinally usable `resp`/`ad` segments

The textual spine covers `I-II, qq. 1–114` and `II-II, qq. 1–182`, excluding `II-II, qq. 183–189`,
`Part I`, `Part III`, and the `Supplement`.

### Christian virtue export

- dataset: [data/processed/sft/exports/christian_virtue_v1](./data/processed/sft/exports/christian_virtue_v1)
- optional OOD companion:
  [data/processed/sft/exports/christian_virtue_v1_ood](./data/processed/sft/exports/christian_virtue_v1_ood)
- `555` approved doctrinal source annotations
- `1883` SFT examples
- split sizes: `1475` train, `175` val, `233` test
- grouping key: `question_id`

The v1 doctrinal scope is virtue-centered: theological virtues, prudence, justice core, connected
virtues, fortitude parts and closure, and temperance parts and closure.

### Task families

| Task family | Count | What it teaches |
| --- | ---: | --- |
| Passage-grounded doctrinal QA | `555` | Answer from a cited passage without leaving the evidence |
| Reviewed relation explanation | `555` | Explain subject-relation-object claims in natural language |
| Citation-grounded moral answer | `555` | Answer user-style moral questions with explicit passage traceability |
| Virtue concept explanation | `218` | Explain a virtue, vice, act, or part relation from supporting passages |

### Evidence discipline

| Design choice | Why it matters |
| --- | --- |
| Segment id is the evidence unit | Supervision stays attached to precise textual support |
| Only approved reviewed doctrinal annotations are used | Candidate material is not silently promoted to truth |
| `resp` and `ad` are the default doctrinal units | Training centers on Aquinas's own answer |
| Stable ids survive end to end | Reports, predictions, and model outputs stay auditable |
| Grouped `question_id` splits | Held-out evaluation is less prone to leakage |

## Minimal Local Example

| Property | Value |
| --- | --- |
| Base model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Training method | LoRA on Apple Silicon `mps`, `float16`, no quantization |
| Public rung | `local-baseline` |
| Train subset | `128` examples |
| Eval subset | `16` examples |
| Max steps | `20` |
| Runtime goal | Honest end-to-end reproducibility on a 16 GB laptop |

This minimal example proves three things:

- the reviewed dataset can move model behavior in the right Thomist direction
- the train / infer / eval / report / package loop is real
- the repo is usable as a public fine-tuning template

It does not prove:

- that `1.5B` is the intended final deployment size
- that local Apple-Silicon training is the strongest path for final model quality
- that citation exact match is the whole theological evaluation story

## Evidence Browser

**Live app:** [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

The Streamlit viewer is the companion audit surface for the SFT work: it lets a reader move from
concept to relation to passage to graph while keeping the underlying reviewed evidence visible.

Run it locally with:

```bash
make app
```

The entrypoint is [streamlit_app.py](./streamlit_app.py).

## Repository Structure

| Path | Role |
| --- | --- |
| `data/interim/` | Canonical question, article, and segment spine |
| `data/gold/` | Reviewed doctrinal and structural-editorial annotations |
| `data/processed/sft/exports/` | Committed Christian virtue dataset exports |
| `src/summa_moral_graph/sft/` | Dataset builder, runtime, evaluation, reporting, publication |
| `src/summa_moral_graph/viewer/` | Streamlit viewer shell |
| `scripts/` | Reproducible build, train, eval, report, and packaging entrypoints |
| `docs/` | Public guide, dataset card, report, and repository map |

For a fuller tour, see [docs/repository_map.md](./docs/repository_map.md) and
[scripts/README.md](./scripts/README.md).

## More Docs

- dataset card: [docs/christian_virtue_dataset_card.md](./docs/christian_virtue_dataset_card.md)
- fine-tuning guide: [docs/fine_tune_with_summa_moral_graph.md](./docs/fine_tune_with_summa_moral_graph.md)
- maintainer workflow: [docs/christian_virtue_sft.md](./docs/christian_virtue_sft.md)
- flagship report: [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- repository map: [docs/repository_map.md](./docs/repository_map.md)
