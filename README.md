# Summa Virtue Alignment

Evidence-first Christian virtue dataset, full-corpus LoRA result, and audit surface for Thomist
moral virtue alignment, built on the corpus and evidence model of Summa Moral Graph.

This repo packages one public research release: a reviewed Christian virtue dataset, a reproducible
local fine-tuning path, and an inspectable theological trail back to Aquinas's text.

The dataset exists to train models toward Aquinas-grounded Christian virtue reasoning rather than
generic religion chat, and its main merit is that the supervision stays reviewed, passage-grounded,
relational, and auditable end to end.

| Start | Try | Inspect | Browse | Release gate |
| --- | --- | --- | --- | --- |
| [SFT guide](./docs/fine_tune_with_summa_moral_graph.md) | [Online chat](https://jennyzhu0822-summa-virtue-chat.hf.space) | [Hugging Face adapter](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b) | [Live viewer](https://summa-moral-graph.streamlit.app/) | [![Public Release Check](https://github.com/hanzhenzhujene/summa-virtue-alignment/actions/workflows/public-release-check.yml/badge.svg)](https://github.com/hanzhenzhujene/summa-virtue-alignment/actions/workflows/public-release-check.yml) |

> The published Hugging Face adapter is the smallest public release artifact in the repo. The
> strongest repo-local result is the completed `full-corpus` LoRA run shown below.

## Latest Result

![Held-out tract profile after full-corpus LoRA](docs/reports/assets/christian_virtue_qwen2_5_1_5b_full_corpus_tract_profile.svg)

*Figure 1. The virtue picture comes first: after full-corpus LoRA, all eight tracked virtue tracts
land in a tight high-performance band on untouched test prompts.*

![From untuned model to earlier small-data LoRA to full-corpus LoRA](docs/reports/assets/christian_virtue_qwen2_5_1_5b_full_corpus_progress.svg)

*Figure 2. The same 1.5B model improves from `0.0%` untuned, to `36.5%` after the earlier
small-data LoRA rung (`train 128 / val 32`), to `71.2%` after the full-corpus LoRA run
(`train 1475 / val 175`).*

| Held-out slice | Untuned model | Earlier small-data LoRA | Full-corpus LoRA | Gain over earlier LoRA |
| --- | ---: | ---: | ---: | ---: |
| Overall exact citation | `0.0%` | `36.5%` | `71.2%` | `+34.8 pts` |
| Passage-grounded doctrinal QA | `0.0%` | `32.8%` | `100.0%` | `+67.2 pts` |
| Reviewed relation explanation | `0.0%` | `62.7%` | `100.0%` | `+37.3 pts` |
| Virtue concept explanation | `0.0%` | `65.6%` | `100.0%` | `+34.4 pts` |
| Justice core tract | `0.0%` | `50.0%` | `71.4%` | `+21.4 pts` |

This is the clearest result in the repo so far: once the same 1.5B backbone sees the full reviewed
Christian virtue training split, it becomes a strong doctrinal and explanatory model on held-out
virtue evaluation, and it clearly surpasses the earlier small-data LoRA rung rather than merely
beating an untuned starting point. The full write-up, run metadata, and training trace live in the
[full-corpus report](./docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md).

## Benchmark Improvements

![Base and LoRA benchmark improvements](docs/reports/assets/christian_virtue_benchmark_improvements.svg)

*Figure 3. Base and full-corpus LoRA scores across in-domain Aquinas evaluation, Christian virtue
diagnostics, and English/Chinese external benchmark surfaces. The paired bars make the base-to-LoRA
improvement visible directly on each benchmark surface.*

| Benchmark | Surface | n | Base | LoRA | Delta |
| --- | --- | ---: | ---: | ---: | ---: |
| Held-out Summa citation exact | in-domain held-out | `233` | `0.0%` | `71.2%` | `+71.2 pp` |
| Aquinas grounding probe score | in-domain grounding | `233` | `37.7%` | `74.2%` | `+36.5 pp` |
| Aquinas segment-id citation presence | in-domain grounding | `233` | `0.0%` | `100.0%` | `+100.0 pp` |
| VirtueBench V2 random | Christian virtue diagnostic | `300` | `29.7%` | `58.0%` | `+28.3 pp` |
| VirtueBench V2 paired | Christian virtue diagnostic | `200` | `34.0%` | `49.5%` | `+15.5 pp` |
| MMLU world religions | external English transfer | `60` | `76.7%` | `81.7%` | `+5.0 pp` |
| MMMLU-ZH business ethics | external Chinese transfer | `60` | `58.3%` | `61.7%` | `+3.3 pp` |
| MMMLU-ZH moral scenarios | external Chinese transfer | `60` | `25.0%` | `28.3%` | `+3.3 pp` |
| MMMLU-ZH philosophy | external Chinese transfer | `60` | `53.3%` | `55.0%` | `+1.7 pp` |
| MMLU moral scenarios | external English transfer | `60` | `26.7%` | `28.3%` | `+1.7 pp` |

The benchmark packet is documented in the
[benchmark improvement readout](./docs/reports/christian_virtue_benchmark_improvements.md), with
representative prompt shapes in
[benchmark examples](./docs/reports/christian_virtue_benchmark_examples.md).
If the final adapter or run metrics live in another worktree, rebuild the packet with
`CHRISTIAN_VIRTUE_BENCHMARK_METRICS_ROOT` and `CHRISTIAN_VIRTUE_FINAL_ADAPTER_RUN_ROOT`; the
public builder does not assume a local workstation path.

## At A Glance

| Surface | Current answer |
| --- | --- |
| Goal | Train a model toward Aquinas-grounded Christian virtue reasoning with reviewed, passage-grounded supervision rather than generic religion chat |
| Dataset | `1883` Christian virtue SFT examples built from approved doctrinal annotations with stable passage ids |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` with local Apple-Silicon LoRA |
| Strongest repo-local result | `71.2%` held-out exact citation on the untouched `233`-row test split |
| Strongest held-out slices | `100.0%` on doctrinal QA, `100.0%` on reviewed relation explanation, `100.0%` on virtue concept explanation |
| Online chat | [summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space) |
| Main report | [Full-Corpus Christian Virtue LoRA Report](./docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md) |

## What This Repo Is For

This repo serves three linked purposes:

- **Dataset:** a reviewed Christian virtue SFT export built from approved doctrinal annotations
  joined back to stable Aquinas passage ids.
- **Training demo:** a reproducible local LoRA path that scales from a small release package to
  the strongest full-corpus result now documented in the repo.
- **Audit surface:** reports, figures, package artifacts, and the companion graph viewer so a
  reader can inspect claims back to the text.

## Dataset Merit

This dataset matters because the training truth stays unusually clean and inspectable all the way
through the pipeline:

- stable passage ids survive from the reviewed annotation layer into the final SFT examples
- reviewed doctrinal relations stay separate from candidate material, structural links, and
  editorial cleanup
- Aquinas-specific categories such as virtue, vice, act, part, and opposition remain explicit
  instead of being flattened into generic religion text

## Method Overview

- **Evidence:** joins approved doctrinal annotations back to stable `resp` / `ad` passage ids
  instead of flattening Aquinas into unlabeled text blobs.
  Surface: [dataset export](./data/processed/sft/exports/christian_virtue_v1)
- **Supervision:** builds four instruction families: doctrinal QA, reviewed relation explanation,
  virtue concept explanation, and citation-grounded moral answer.
  Surface: [templates](./src/summa_moral_graph/sft/templates.py)
- **Training:** runs local Apple-Silicon LoRA on `Qwen/Qwen2.5-1.5B-Instruct`, including the
  completed full-corpus rung on all reviewed `train` and `val` rows.
  Surface: [full-corpus config](./configs/train/qwen2_5_1_5b_instruct_lora_mps_full_corpus.yaml)
- **Evaluation:** compares the untouched model to the full-corpus LoRA adapter on held-out prompts
  and reports task-family and tract behavior.
  Surface: [full-corpus report](./docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md)
- **Audit:** preserves stable ids, reports, package metadata, and the companion viewer so claims
  can be checked back against Aquinas's text.
  Surface: [public claim map](./docs/public_claim_map.md)

## Repository Structure

| Path | Role |
| --- | --- |
| [data/](./data/) | Canonical text spine, reviewed annotations, candidates, and committed Christian virtue SFT exports |
| [src/summa_moral_graph/sft/](./src/summa_moral_graph/sft/) | Dataset building, training, inference, evaluation, reporting, and publication logic |
| [scripts/](./scripts/) | Public entrypoints for setup, local training, evaluation, reporting, and publication checks |
| [docs/reports/](./docs/reports/) | Curated experiment reports, audit notes, and publication figures |
| [artifacts/christian_virtue/](./artifacts/christian_virtue/) | Packaged small-model adapter surface mirrored to the public release |
| [docs/public_claim_map.md](./docs/public_claim_map.md) | Explicit map from public claim to artifact, command, and claim boundary |
| [docs/repository_map.md](./docs/repository_map.md) | Shortest full orientation guide for reviewers and collaborators |

## What Makes This Dataset Different

Most theology or religion fine-tuning data is difficult to audit below the document level. This
dataset is built around claim-level traceability: each example keeps the reviewed relation, the
Aquinas passage id, and the doctrinal context that produced it.

| # | Design choice | Why it matters |
| ---: | --- | --- |
| 1 | Structure, not just vocabulary | The model sees reviewed relations such as `species_of`, `opposed_by`, `act_of`, `subjective_part_of`, and `precept_of`, not only words like `charity`, `justice`, or `temperance`. |
| 2 | Aquinas's categories stay distinct | Virtue, vice, act, object, part, gift, precept, and domain are preserved instead of being flattened into generic religious themes. |
| 3 | Passage-grounded supervision | Every training target is tied back to stable `resp` / `ad` passage ids, so the supervision remains anchored in Aquinas's text. |
| 4 | Inspectable alignment data | Each example carries doctrinal metadata, citation labels, source passage ids, relation type, and tract context, making the training signal auditable. |
| 5 | Reviewed truth, not scraped text | Approved doctrinal supervision stays separate from candidate material, structural links, and editorial synthesis, which keeps the release cleaner than a typical scraped religion dataset. |

## Start Here

| I want to... | Start here |
| --- | --- |
| Inspect the strongest repo-local result | [Full-corpus report](./docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md) |
| Inspect the benchmark improvement packet | [Benchmark improvement readout](./docs/reports/christian_virtue_benchmark_improvements.md) |
| Rerun the strongest full-data local result | `make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop` |
| Try the model online | [summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space) |
| Run the smallest release-grade local check | `make setup-christian-virtue-local` then `make reproduce-christian-virtue-qwen2-5-1-5b-local` |
| Audit the exact public claims and boundaries | [docs/public_claim_map.md](./docs/public_claim_map.md) |
| Fine-tune my own model on the same dataset | [docs/fine_tune_with_summa_moral_graph.md](./docs/fine_tune_with_summa_moral_graph.md) |
| Inspect the small published release artifact | [Hugging Face adapter](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b) · [GitHub release](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038) |
| Audit the passages and graph directly | [Live viewer](https://summa-moral-graph.streamlit.app/) |

## Reproducibility Contract

Strongest repo-local path:

```bash
make setup-christian-virtue-local
make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop
make report-christian-virtue-qwen2-5-1-5b-full-corpus
make public-release-check
```

The pinned local environment lives at
[requirements/local-mps-py312.lock.txt](./requirements/local-mps-py312.lock.txt).

Expected outputs from a successful canonical run:

| Output | Path |
| --- | --- |
| Full-corpus report | [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md) |
| Benchmark improvement readout | [docs/reports/christian_virtue_benchmark_improvements.md](./docs/reports/christian_virtue_benchmark_improvements.md) |
| Full-corpus training run | `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest/` |
| Full-corpus adapter test run | `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_adapter_test/latest/` |
| Untuned-model test run | `runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/` |
| Published small-model adapter package | [artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](./artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md) |

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
| Train-time eval subset | `32` examples |
| Max steps | `20` |
| Runtime goal | Honest end-to-end reproducibility on a 16 GB laptop |

This minimal example proves that the reviewed dataset can move model behavior in the right Thomist
direction, that the train / infer / eval / report / package loop is real, and that the repo is
usable as a public fine-tuning template.

It does not claim that `1.5B` is the intended final deployment size, that local Apple-Silicon
training is the strongest path for final model quality, or that citation exact match is the whole
theological evaluation story.

## Chat With The Model

You can talk directly to the completed `full-corpus` adapter in either:

- the online Gradio chat: [summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space)
- the same local Gradio app backed by your own machine

First local use:

```bash
make setup-christian-virtue-local
make smoke-test-christian-virtue-chat
make gradio-chat-christian-virtue-qwen2-5-1-5b-full-corpus
```

Publish or refresh the public online chat from this repo:

```bash
make deploy-christian-virtue-chat-space
```

That sequence:

- builds the pinned local environment
- runs a fast qualitative smoke panel over the current chat layer
- opens a local Gradio chat UI against `Qwen/Qwen2.5-1.5B-Instruct` plus the strongest
  repo-local LoRA adapter

This chat surface is intentionally a small-model demo: it uses
`Qwen/Qwen2.5-1.5B-Instruct` plus the full-corpus Christian virtue LoRA adapter, not a larger
hosted frontier model.

The chat and smoke artifacts are written under:

- `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_chat/`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_chat_smoke/`

The smoke command is a quick qualitative check for the current chat layer. It probes:

- direct definitions
- relation questions from the reviewed moral graph
- practical-moral prompts such as anger, envy, temperance, and fear/courage

Recommended public split:

- **Chat:** [summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space)
- **Graph and evidence browser:** [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

Why this split exists:

- Streamlit Community Cloud's official docs say apps without traffic for 12 hours go to sleep:
  [Manage your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
- Hugging Face's official docs say free `cpu-basic` Spaces sleep after 48 hours of inactivity,
  while upgraded hardware can stay awake indefinitely:
  [Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview),
  [Space runtime sleep time](https://huggingface.co/docs/huggingface_hub/main/package_reference/space_runtime)

So the repo now treats Hugging Face Space as the recommended public chat host, while Streamlit
stays focused on the evidence browser.

If you prefer the terminal, the CLI fallback is still:

```bash
make chat-christian-virtue-qwen2-5-1-5b-full-corpus
```

Inside the chat:

- ask a normal question about virtue, vice, acts, or doctrinal relation
- `/reset` clears conversation history
- `/exit` ends the session

## Evidence Browser

**Live app:** [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

The Streamlit viewer is the companion audit surface for the SFT work: it lets a reader move from
concept to relation to passage to graph while keeping the underlying reviewed evidence visible.

Run it locally with:

```bash
make app
```

The entrypoint is [streamlit_app.py](./streamlit_app.py). For direct model conversation, the
recommended chat surfaces are the Hugging Face Space above and the local Gradio app above.

## Core Paths

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
