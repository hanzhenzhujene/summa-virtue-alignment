# Repository Map

This document is the shortest reliable orientation guide for a new collaborator, reviewer, or
model trainer.

## Public Entry Surfaces

- [CITATION.cff](../CITATION.cff): citation metadata for the public software and dataset release
- [README.md](../README.md): first-stop overview, headline results, and canonical reproduction path
- [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md): external
  user guide for training or swapping in another model
- [docs/christian_virtue_sft.md](./christian_virtue_sft.md): maintainer and research workflow
- [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md): dataset scope,
  intended use, and limits
- [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md):
  flagship local experiment report

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
the public local baseline from tract-maintenance helpers and remote-model utilities.

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

### Reporting And Publication

- `scripts/build_christian_virtue_local_report.py`
- `scripts/publish_christian_virtue_adapter.py`
- `scripts/verify_christian_virtue_publication.py`

## Reproducibility Contract

The official public local path is:

1. `make setup-christian-virtue-local`
2. `make reproduce-christian-virtue-qwen2-5-1-5b-local`
3. `make public-release-check`

The setup command uses the pinned lockfile
[requirements/local-mps-py312.lock.txt](../requirements/local-mps-py312.lock.txt).

The reproduce command rebuilds the dataset if needed, runs the local `smoke` and `local-baseline`
training rungs, generates base and adapter held-out predictions, writes the comparison report, and
runs the publication verification gate.

The public-release check then runs `ruff`, `mypy`, and the publication-surface verification bundle
so the repo can be shared with one final sanity pass.

## Recommended Reading Order

1. [README.md](../README.md)
2. [docs/fine_tune_with_summa_moral_graph.md](./fine_tune_with_summa_moral_graph.md)
3. [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md)
4. [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md)
5. [docs/christian_virtue_sft.md](./christian_virtue_sft.md)
