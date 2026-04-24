# Repository Map

This document is the shortest reliable orientation guide for a new collaborator, reviewer, or
model trainer.

## Public Entry Surfaces

- [CITATION.cff](../CITATION.cff): citation metadata for the public software and dataset release
- [README.md](../README.md): first-stop overview, headline results, and canonical reproduction path
- [docs/public_claim_map.md](./public_claim_map.md): explicit map from public claim to artifact,
  command, and claim boundary
- [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md): external
  user guide for training or swapping in another model
- [docs/christian_virtue_sft.md](./christian_virtue_sft.md): maintainer and research workflow
- [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md): dataset scope,
  intended use, and limits
- [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md):
  flagship repo-local report for the full reviewed Christian virtue split
- [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md):
  smaller published local package report mirrored to the release artifact
- [docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md):
  completed same-budget citation-focused follow-up report
- [docs/reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md](./reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md):
  completed same-budget justice-guarded follow-up report
- [docs/reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md](./reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md):
  completed same-budget accuracy-first follow-up report

## Canonical Public Bundle

If you want the smallest set of files that define the public release, start here:

- dataset export: `data/processed/sft/exports/christian_virtue_v1/`
- full-corpus report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md)
- public claim map:
  [docs/public_claim_map.md](./public_claim_map.md)
- smaller published package report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- frontier audit:
  [docs/reports/christian_virtue_citation_frontier_audit.md](./reports/christian_virtue_citation_frontier_audit.md)
- follow-up citation-frontier report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)
- justice-guarded follow-up report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md](./reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md)
- local adapter package:
  [../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md)
- external model page:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)

## Top-Level Layout

```text
artifacts/   publication-ready adapter packages and release surfaces
configs/     dataset, training, and inference configs
data/        canonical text spine, reviewed annotations, candidates, and SFT exports
docs/        public guides, schema notes, and reports
scripts/     reproducible dataset, training, eval, reporting, and publication entrypoints
src/         Python package for ingest, annotations, viewer, and SFT logic
tests/       regression coverage for corpus, viewer, and SFT/publication surfaces
```

## Archival Planning Context

- [docs/archive/aquinas_summa_moral_graph_implementation_plan.md](./archive/aquinas_summa_moral_graph_implementation_plan.md):
  early project scoping memo retained as historical context
- [docs/execplans/summa-moral-graph.md](./execplans/summa-moral-graph.md): live execution log
  and decision history for the current workflow

## Data Layout

### Canonical Text

- `data/interim/summa_moral_segments.jsonl`
- `data/interim/summa_moral_articles.jsonl`
- `data/interim/summa_moral_questions.jsonl`

These files are the canonical parsed textual spine. Stable segment ids begin here and remain the
anchor for downstream datasets, graph views, and model outputs.

### Reviewed Supervision

- `data/gold/*_reviewed_doctrinal_annotations.jsonl`
- `data/gold/*_reviewed_structural_editorial_annotations.jsonl`

Doctrinal and structural-editorial review remain separate. The default Christian virtue SFT path
uses only selected doctrinal files.

### Candidate Layer

- `data/candidate/*`

Candidate material is review support, not approved truth. It is intentionally excluded from the
default training surface.

### Public SFT Exports

- `data/processed/sft/exports/christian_virtue_v1/`
- `data/processed/sft/exports/christian_virtue_v1_ood/`
- `data/processed/sft/samples/`

These committed exports are the public dataset entrypoint for model training and evaluation.

## Code Layout

### Viewer And Graph

- `streamlit_app.py`: unified Streamlit entrypoint
- `scripts/gradio_christian_virtue_chat.py`: recommended local Gradio chat entrypoint for the
  full-corpus adapter
- `src/summa_moral_graph/app/gradio_chat.py`: Gradio chat surface and session logging controls
- `app/pages/6_Chat.py`: user-friendly chat page for the full-corpus Christian virtue adapter
- `src/summa_moral_graph/app/chat.py`: Streamlit chat surface, session logging, and controls
- `src/summa_moral_graph/viewer/`: shared viewer shell, routing, and render helpers
- `src/summa_moral_graph/graph/`: graph exports and tract synthesis helpers

### Annotation And Corpus Workflow

- `src/summa_moral_graph/annotations/`: tract registries, reviewed overlays, and build helpers
- `src/summa_moral_graph/ingest/`: parsing and normalization utilities
- `src/summa_moral_graph/utils/`: shared repo-level helpers

### SFT Package

- `src/summa_moral_graph/sft/config.py`: typed config loading
- `src/summa_moral_graph/sft/loaders.py`: dataset input loading
- `src/summa_moral_graph/sft/filters.py`: doctrinal row filtering and deduplication
- `src/summa_moral_graph/sft/builders.py`: example assembly and manifest stats
- `src/summa_moral_graph/sft/templates.py`: prompt/response template families
- `src/summa_moral_graph/sft/splitters.py`: grouped split construction
- `src/summa_moral_graph/sft/training.py`: LoRA and QLoRA runtime resolution
- `src/summa_moral_graph/sft/inference.py`: held-out generation loop
- `src/summa_moral_graph/sft/evaluation.py`: citation and breakdown metrics
- `src/summa_moral_graph/sft/reporting.py`: plots, goal-demo panel, and curated reports
- `src/summa_moral_graph/sft/publication.py`: adapter packaging and release metadata

## Script Entry Points

See also [scripts/README.md](../scripts/README.md) for a grouped entrypoint guide that separates
the strongest repo-local path from the smaller published package path, tract-maintenance helpers,
and remote-model utilities.

### Dataset

- `scripts/build_christian_virtue_sft_dataset.py`
- `scripts/smoke_test_christian_virtue_sft.py`

### Canonical Local Baseline

- `scripts/setup_christian_virtue_local.sh`
- `scripts/reproduce_christian_virtue_qwen2_5_1_5b_local.sh`
- `scripts/run_christian_virtue_qwen2_5_1_5b_local_train.sh`
- `scripts/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh`
- `scripts/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh`
- `scripts/run_christian_virtue_qwen2_5_1_5b_local_compare.sh`

### Follow-Up And Scale-Up Experiments

- `configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml`
- `configs/train/qwen2_5_1_5b_instruct_lora_mps_full_corpus.yaml`
- `configs/train/qwen2_5_1_5b_instruct_lora_mps_accuracy_first_hybrid.yaml`
- `configs/train/qwen2_5_1_5b_instruct_lora_mps_justice_guarded_citation_repair.yaml`
- `configs/inference/qwen2_5_1_5b_instruct_citation_frontier_adapter_test.yaml`
- `configs/inference/qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml`
- `configs/inference/qwen2_5_1_5b_instruct_accuracy_first_adapter_test.yaml`
- `configs/inference/qwen2_5_1_5b_instruct_justice_guarded_adapter_test.yaml`
- `scripts/chat_christian_virtue_model.py`
- `scripts/run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh`
- `scripts/build_christian_virtue_full_corpus_report.py`
- `scripts/build_christian_virtue_citation_frontier_report.py`
- `scripts/build_christian_virtue_justice_guarded_report.py`

These are the main post-baseline experiment surfaces:

- `full-corpus` is the strongest full-data local scale-up on the same 1.5B backbone
- `citation-frontier`, `justice-guarded`, and `accuracy-first` are the same-budget follow-up
  family for probing citation recovery and doctrinal tradeoffs under tiny local budgets

### Reporting And Publication

- `scripts/build_christian_virtue_local_report.py`
- `scripts/audit_christian_virtue_frontier.py`
- `scripts/publish_christian_virtue_adapter.py`
- `scripts/verify_christian_virtue_publication.py`

## Reproducibility Contract

There are two public reproduction surfaces, and they serve different purposes:

### Strongest repo-local result

1. `make setup-christian-virtue-local`
2. `make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop`
3. `make report-christian-virtue-qwen2-5-1-5b-full-corpus`
4. `make public-release-check`

This is the path for reproducing the strongest repo-local Christian virtue result.

### Smallest published package

1. `make setup-christian-virtue-local`
2. `make reproduce-christian-virtue-qwen2-5-1-5b-local`
3. `make public-release-check`

This is the lightest release-grade path mirrored to the published Hugging Face adapter and GitHub
release.

Both paths use the pinned lockfile
[requirements/local-mps-py312.lock.txt](../requirements/local-mps-py312.lock.txt).

The public-release check then runs `ruff`, `mypy`, and the publication-surface verification bundle
so the repo can be shared with one final sanity pass.

For the fastest post-baseline audit, run:

4. `make audit-christian-virtue-qwen2-5-1-5b-local-frontier`

That audit reuses the canonical held-out predictions and writes a focused report on the remaining
user-style citation frontier, so the next experiment can be chosen without another long local run.

The completed citation-frontier follow-up is:

5. `make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop`

That loop keeps the same `Qwen/Qwen2.5-1.5B-Instruct` local envelope but changes the tiny subset
mixture so half of the train budget goes to `citation_grounded_moral_answer`.

The finished follow-up report now lives at:

6. [docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)

The completed strongest full-data local run is:

7. `make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop`

Its curated report now lives at:

8. [docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md)

The next completed same-budget doctrinal-guard follow-up is:

9. `make run-christian-virtue-qwen2-5-1-5b-justice-guarded-loop`

Its curated report now lives at:

10. [docs/reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md](./reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md)

The official justice-guarded wrappers now export the required MPS safety env overrides
automatically for training and adapter evaluation.

The completed highest-accuracy same-budget follow-up is:

11. `make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop`

It keeps the same budget, keeps the justice/STI guards, and restores a little more
`citation_grounded_moral_answer` pressure, yielding the repo's strongest same-budget overall exact
citation result so far (`41.2%`).

The completed result now lives at:

12. [docs/reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md](./reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md)

## Recommended Reading Order

1. [README.md](../README.md)
2. [docs/public_claim_map.md](./public_claim_map.md)
3. [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)
4. [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md)
5. [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md)
6. [docs/christian_virtue_sft.md](./christian_virtue_sft.md)
