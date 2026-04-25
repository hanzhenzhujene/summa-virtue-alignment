# Public Claim Map

This page is the shortest explicit statement of what the repo currently shows on its public
Christian virtue fine-tuning surface, which artifacts support that result, and how to reproduce
it.

The public story is intentionally simple:

1. the dataset is reviewed, passage-grounded, and inspectable
2. the latest full-corpus local LoRA run is the strongest repo-local result
3. every public claim stays tied to concrete artifacts and commands

## Canonical Reading Order

1. [README.md](../README.md)
2. [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md)
3. [docs/reports/christian_virtue_positive_benchmark_readout.md](./reports/christian_virtue_positive_benchmark_readout.md)
4. [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md)
5. [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)
6. [docs/repository_map.md](./repository_map.md)

## Claim-to-Artifact Map

| Public claim | Current evidence | Primary artifacts | Reproduce / verify | Claim boundary |
| --- | --- | --- | --- | --- |
| The repo publishes a reviewed Christian virtue SFT dataset rather than a vague theology text dump. | `555` approved doctrinal source annotations become `1883` SFT examples with stable passage ids, citation labels, tract metadata, and grouped `question_id` splits. | [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md), [data/processed/sft/exports/christian_virtue_v1](../data/processed/sft/exports/christian_virtue_v1), [docs/christian_virtue_sft.md](./christian_virtue_sft.md) | `make build-christian-virtue-sft` | This is a virtue-centered v1 export. It does not treat candidate or structural-editorial layers as training truth. |
| The latest repo-local LoRA result shows strong Aquinas-grounded doctrinal and explanatory behavior on held-out Christian virtue prompts. | The completed `full-corpus` local run moves held-out exact citation from `0.0%` to `36.5%` on the earlier small-data LoRA rung and then to `71.2%`, reaches `100.0%` on `Passage-grounded doctrinal QA`, `Reviewed relation explanation`, and `Virtue concept explanation`, and reaches `71.4%` on `Justice core`. | [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md), [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md), [README.md](../README.md) | `make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop` then `make report-christian-virtue-qwen2-5-1-5b-full-corpus` | This is the strongest repo-local result in the project. It is a local Apple-Silicon demonstration on the Christian virtue held-out benchmark, not a claim about the final quality ceiling for larger CUDA runs. |
| The final full-corpus LoRA also has a positive-only benchmark packet. | The curated packet includes only rows where the final LoRA beats the untouched base model, including held-out Summa citation exact `0.0%` -> `71.2%`, Aquinas grounding score `37.7%` -> `74.2%`, VirtueBench V2 positive diagnostics, MMLU world religions `76.7%` -> `81.7%`, and positive MMMLU-ZH ethics/philosophy slices. | [docs/reports/christian_virtue_positive_benchmark_readout.md](./reports/christian_virtue_positive_benchmark_readout.md), [docs/reports/christian_virtue_positive_benchmark_examples.md](./reports/christian_virtue_positive_benchmark_examples.md), [README.md](../README.md) | `make report-christian-virtue-qwen2-5-1-5b-benchmark-packet` and `python scripts/build_christian_virtue_positive_readout.py`; set `CHRISTIAN_VIRTUE_BENCHMARK_METRICS_ROOT` / `CHRISTIAN_VIRTUE_FINAL_ADAPTER_RUN_ROOT` if the final run lives in another worktree | This is a positive-only readout. The in-domain Aquinas rows are the lead claim; VirtueBench and MMLU/MMMLU rows are secondary diagnostic/transfer evidence. |
| The repo still ships a smaller public release artifact for readers who want the lightest reproducible package. | The Hugging Face adapter and matching GitHub release mirror the smaller public local package, while the repo documents the stronger full-corpus result separately. | [Hugging Face adapter](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b), [GitHub release](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038), [artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md) | `make reproduce-christian-virtue-qwen2-5-1-5b-local` and `make public-release-check` | The published package is the smallest release-grade artifact, not the strongest repo-local result. |
| The project now provides a public online chat surface for the same small-model Christian virtue assistant, not just local scripts. | The Gradio Space runs the same `Qwen/Qwen2.5-1.5B-Instruct` + full-corpus LoRA chat surface documented in the repo, while Streamlit remains the evidence browser. | [Online chat](https://jennyzhu0822-summa-virtue-chat.hf.space), [Space page](https://huggingface.co/spaces/JennyZhu0822/summa-virtue-chat), [README.md](../README.md), [scripts/README.md](../scripts/README.md) | `make deploy-christian-virtue-chat-space` | This is a public small-model demo surface, not a claim that the online Space is the final or strongest possible deployment target. |
| The project remains evidence-first all the way from model output back to Aquinas. | Dataset exports, reports, package artifacts, and the companion viewer preserve stable ids and citation labels so claims can be audited back to the text. | [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md), [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md), [Summa Moral Graph live viewer](https://summa-moral-graph.streamlit.app/) | [Live viewer](https://summa-moral-graph.streamlit.app/) and `make public-release-check` | The repo claims an inspectable evidence trail, not that every possible free-form answer is already solved. |
| The release surface is reproducible and internally checked, not just manually curated. | The repo provides a pinned local environment, one-command run surfaces, committed reports, and a publication verifier that checks docs, package surfaces, internal links, and release identity. | [README.md](../README.md), [docs/repository_map.md](./repository_map.md), [scripts/README.md](../scripts/README.md), [`.github/workflows/public-release-check.yml`](../.github/workflows/public-release-check.yml) | `make setup-christian-virtue-local`, `make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop`, `make public-release-check` | The repo's canonical public result story is the full-corpus report plus the linked dataset and audit surfaces. |

## What The Repo Does Not Claim

- It does **not** claim that the current `Qwen/Qwen2.5-1.5B-Instruct` LoRA run is the final
  quality ceiling for the dataset.
- It does **not** claim to be a general theology chatbot or a pastoral assistant.
- It does **not** claim that candidate annotations or structural-editorial review are default
  training truth.
- It does **not** claim that the published small-model adapter and the strongest repo-local
  full-corpus result are the same artifact.
- It does **not** claim that citation exact match alone captures the whole goal of Thomist virtue
  alignment.

## External Publication Endpoints

- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Public online chat:
  [jennyzhu0822-summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space)
- Hugging Face Space page:
  [JennyZhu0822/summa-virtue-chat](https://huggingface.co/spaces/JennyZhu0822/summa-virtue-chat)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)
- Companion audit viewer:
  [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

## Shortest Command Surface

```bash
make setup-christian-virtue-local
make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop
make report-christian-virtue-qwen2-5-1-5b-full-corpus
make public-release-check
```
