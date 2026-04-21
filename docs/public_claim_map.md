# Public Claim Map

This page is the shortest explicit statement of what this repo currently proves, which artifacts
support each claim, how to reproduce them, and where the claim boundaries are.

It is intentionally narrower than a project vision page. The goal here is not aspiration. The
goal is a release-grade map from public claim to public evidence.

## Canonical Reading Order

1. [README.md](../README.md)
2. [docs/public_claim_map.md](./public_claim_map.md)
3. [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
4. [docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)
5. [docs/reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md](./reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md)
6. [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)

## Claim-to-Artifact Map

| Public claim | Current evidence | Primary artifacts | Reproduce / verify | Claim boundary |
| --- | --- | --- | --- | --- |
| The repo publishes a reviewed Christian virtue SFT dataset rather than a vague theology text dump. | `555` approved doctrinal source annotations become `1883` SFT examples with stable passage ids, citation labels, tract metadata, and grouped `question_id` splits. | [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md), [data/processed/sft/exports/christian_virtue_v1](../data/processed/sft/exports/christian_virtue_v1), [docs/christian_virtue_sft.md](./christian_virtue_sft.md) | `make build-christian-virtue-sft` | This is a virtue-centered v1 export. It does not claim that all moral-corpus supervision is in scope, and it does not treat candidate or structural-editorial layers as training truth. |
| Reviewed Christian virtue supervision can move a small general model toward better Thomist virtue behavior on held-out prompts. | The canonical local `Qwen/Qwen2.5-1.5B-Instruct` LoRA baseline improves held-out exact citation from `0.0%` to `36.5%`, `Virtue concept explanation` from `0.0%` to `65.6%`, `Reviewed relation explanation` from `0.0%` to `62.7%`, and `Justice core` from `0.0%` to `50.0%`. | [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md), [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md), [artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md) | `make reproduce-christian-virtue-qwen2-5-1-5b-local` then `make public-release-check` | This is a minimal Apple-Silicon demonstration, not a claim about the strongest achievable final model. Citation exact match is one evaluation surface, not the whole theological goal. |
| The repo can diagnose and improve the hardest citation bottleneck without changing dataset scope. | The completed same-budget `citation-frontier` follow-up moves held-out exact citation from `36.5%` to `38.6%` and lifts `citation_grounded_moral_answer` exact stable-id recovery from `0.0%` to `3.0%`. | [docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md), [docs/reports/christian_virtue_citation_frontier_audit.md](./reports/christian_virtue_citation_frontier_audit.md) | `make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop` and `make report-christian-virtue-qwen2-5-1-5b-citation-frontier` | The follow-up is a real result, but not a replacement public baseline: it improves the citation frontier while regressing `justice_core` and `strong_textual_inference`. |
| The repo now exposes one highest-accuracy same-budget recipe instead of leaving follow-up tuning vague. | The completed `accuracy-first` hybrid reaches `41.2%` overall held-out exact citation, with `passage_grounded_doctrinal_qa` at `50.7%` and `reviewed_relation_explanation` at `64.2%`, making it the strongest same-budget local result so far. | [docs/reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md](./reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md), [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md), [README.md](../README.md) | `make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop` | This is the current best same-budget accuracy result, not yet the clean public baseline replacement: `citation_grounded_moral_answer` exact stable-id recovery remains `0.0%`, and `justice_core` / `strong_textual_inference` only partially recover. |
| The public release is reproducible and internally checked, not just manually curated. | The repo provides a pinned local setup, a one-command canonical reproduction path, and a publication verifier that checks docs, package surfaces, internal links, and release identity. | [README.md](../README.md), [docs/repository_map.md](./repository_map.md), [scripts/README.md](../scripts/README.md), [`.github/workflows/public-release-check.yml`](../.github/workflows/public-release-check.yml) | `make setup-christian-virtue-local`, `make reproduce-christian-virtue-qwen2-5-1-5b-local`, `make public-release-check` | The local path is the canonical public baseline. Larger CUDA runs remain important future work, but they are not the current public contract for this repo. |
| The project remains evidence-first all the way from model output back to Aquinas. | The dataset, reports, package surfaces, and companion viewer all preserve stable ids and citation labels so claims can be audited back to Aquinas's text. | [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md), [docs/reports/christian_virtue_citation_frontier_audit.md](./reports/christian_virtue_citation_frontier_audit.md), [Summa Moral Graph live viewer](https://summa-moral-graph.streamlit.app/) | `make audit-christian-virtue-qwen2-5-1-5b-local-frontier` plus the viewer links in the README | This does not claim that every free-form model answer is already citation-perfect. It claims that the repo keeps the evidence trail explicit and inspectable. |

## What The Repo Does Not Claim

- It does **not** claim that the current `Qwen/Qwen2.5-1.5B-Instruct` adapter is the intended
  final deployment size or the strongest possible SFT result.
- It does **not** claim that this is a general theology chatbot or a pastoral assistant.
  The repo's target is Thomist moral virtue alignment, not a general theology chatbot.
- It does **not** claim that the citation-frontier follow-up should replace the canonical public
  baseline in its current form.
  In other words, this is not a replacement public baseline yet.
- It does **not** claim that the current `accuracy-first` hybrid has solved the hardest
  user-style moral-QA slice.
  The repo's best same-budget accuracy result still leaves `citation_grounded_moral_answer`
  exact stable-id recovery at `0.0%`.
- It does **not** claim that candidate annotations or structural-editorial review are default
  training truth.
- It does **not** claim that citation exact match alone captures the whole goal of Thomist virtue
  alignment.

## External Publication Endpoints

- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)
- Companion audit viewer:
  [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

## Shortest Command Surface

```bash
make setup-christian-virtue-local
make reproduce-christian-virtue-qwen2-5-1-5b-local
make public-release-check
```

If you want the completed citation-focused follow-up as well:

```bash
make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop
make report-christian-virtue-qwen2-5-1-5b-citation-frontier
```

If you want the current best same-budget accuracy result:

```bash
make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop
```
