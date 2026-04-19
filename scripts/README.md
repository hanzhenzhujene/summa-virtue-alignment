# Scripts Guide

This directory contains both public reproduction entrypoints and maintainer-oriented corpus
workflow helpers. If you are new to the repo, start from `Makefile` and this page rather than
calling random scripts directly.

## Public Quickstart Surface

These are the scripts behind the canonical Christian virtue local baseline:

- `setup_christian_virtue_local.sh`
  - creates the pinned Apple-Silicon virtual environment from
    `requirements/local-mps-py312.lock.txt`
- `reproduce_christian_virtue_qwen2_5_1_5b_local.sh`
  - runs the full canonical local loop from dataset build through verification
  - prints the key output paths for the curated report, local adapter package, and latest run dirs
- `run_christian_virtue_qwen2_5_1_5b_local_train.sh`
  - launches `smoke`, `local-baseline`, or the heavier experimental `extended` local training
- `run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh`
  - generates and evaluates held-out base-model predictions
- `run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh`
  - generates and evaluates held-out adapter predictions
- `run_christian_virtue_qwen2_5_1_5b_local_compare.sh`
  - compares the canonical local base and adapter runs

The preferred public commands remain:

```bash
make setup-christian-virtue-local
make reproduce-christian-virtue-qwen2-5-1-5b-local
make public-release-check
```

After the reproduction command completes, the most important outputs are:

- `docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md`
- `artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline/latest`

## Dataset, Eval, Report, And Publication

These scripts define the public SFT workflow and are the main ones to read if you want to swap in
your own model or adapt the method:

- `build_christian_virtue_sft_dataset.py`
- `train_christian_virtue_qlora.py`
- `generate_christian_virtue_predictions.py`
- `eval_christian_virtue_sft.py`
- `compare_christian_virtue_runs.py`
- `build_christian_virtue_local_report.py`
- `publish_christian_virtue_adapter.py`
- `verify_christian_virtue_publication.py`
- `smoke_test_christian_virtue_sft.py`

## Remote Small-Model CUDA Loop

These wrapper scripts support the smaller remote-GPU research loop:

- `preflight_christian_virtue_gpu.py`
- `run_christian_virtue_small_train.sh`
- `run_christian_virtue_small_base_eval.sh`
- `run_christian_virtue_small_adapter_eval.sh`
- `run_christian_virtue_small_loop.sh`
- `christian_virtue_small_common.sh`

This path is useful for cheaper CUDA experiments, but it is not the public default baseline for
the repo.

## Corpus And Review Workflow Helpers

The remaining `build_*_block.py` and `build_*_review_queue.py` scripts are tract-maintenance
utilities for the evidence and review workflow. They are important to the repo, but they are not
the first scripts an outsider should start with when evaluating the SFT deliverable.

If you need orientation for those surfaces, read:

- [docs/repository_map.md](../docs/repository_map.md)
- [docs/full_corpus_workflow.md](../docs/full_corpus_workflow.md)
- [docs/review_queue_guide.md](../docs/review_queue_guide.md)
