# Scripts Guide

This directory contains both public reproduction entrypoints and maintainer-oriented corpus
workflow helpers. If you are new to the repo, start from `Makefile` and this page rather than
calling random scripts directly.

## Public Quickstart Surface

This repo exposes two public script surfaces:

- the strongest repo-local result: the completed `full-corpus` Christian virtue run
- the smallest published package: the lighter `local-baseline` release artifact

These are the scripts behind those public entrypoints:

- `setup_christian_virtue_local.sh`
  - creates the pinned Apple-Silicon virtual environment from
    `requirements/local-mps-py312.lock.txt`
- `reproduce_christian_virtue_qwen2_5_1_5b_local.sh`
  - runs the full canonical local loop from dataset build through verification
  - prints the key output paths for the curated report, local adapter package, and latest run dirs
- `run_christian_virtue_qwen2_5_1_5b_local_train.sh`
  - launches `smoke`, `local-baseline`, `full-corpus`, `citation-frontier`, `accuracy-first`,
    `justice-guarded`, or the heavier experimental `extended` local training
  - the `full-corpus`, `accuracy-first`, and `justice-guarded` modes automatically export the MPS safety env overrides that were
    required for the successful rerun
- `run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh`
  - generates and evaluates held-out base-model predictions
- `run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh`
  - generates and evaluates held-out adapter predictions for the canonical baseline, the long-running full-corpus experiment, the citation-frontier experiment, the accuracy-first hybrid, or the justice-guarded follow-up
  - the `full-corpus`, `accuracy-first`, and `justice-guarded` modes also reuse those MPS safety env overrides during generation and
    evaluation
- `run_christian_virtue_qwen2_5_1_5b_local_compare.sh`
  - compares the canonical local base and adapter runs, or compares local-baseline against the full-corpus, citation-frontier, accuracy-first, or justice-guarded adapters
- `launch_christian_virtue_qwen2_5_1_5b_full_corpus_loop.sh`
  - launches the full-corpus train → held-out adapter eval → comparison loop in the background
  - records a launch log, PID file, and the active run-family root so long MPS runs can continue outside the terminal session
- `run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh`
  - audits the hardest `citation_grounded_moral_answer` slice for the latest citation-frontier adapter
- `audit_christian_virtue_frontier.py`
  - runs a fast frontier audit on the remaining hard slice, `citation_grounded_moral_answer`
  - writes a compact markdown report and SVG figure that explain the next logical research step
- `build_christian_virtue_citation_frontier_report.py`
  - assembles the curated markdown report for the completed citation-frontier follow-up
  - summarizes both the real gain and the remaining doctrinal tradeoffs from that run
- `build_christian_virtue_full_corpus_report.py`
  - assembles the curated markdown report for the completed full-corpus local run
  - summarizes the strongest held-out doctrinal and explanatory gains from the full reviewed split
- `build_christian_virtue_justice_guarded_report.py`
  - assembles the curated markdown report for the justice-guarded follow-up
  - captures the recovery in `justice_core` / `strong_textual_inference` together with the remaining moral-QA gap

The preferred public commands are:

```bash
make setup-christian-virtue-local
make launch-christian-virtue-qwen2-5-1-5b-full-corpus-loop
make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop
make report-christian-virtue-qwen2-5-1-5b-full-corpus
make reproduce-christian-virtue-qwen2-5-1-5b-local
make public-release-check
make audit-christian-virtue-qwen2-5-1-5b-local-frontier
make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop
make report-christian-virtue-qwen2-5-1-5b-citation-frontier
make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop
make run-christian-virtue-qwen2-5-1-5b-justice-guarded-loop
make report-christian-virtue-qwen2-5-1-5b-justice-guarded
```

After the strongest repo-local run or the smaller published-package path completes, the most
important outputs are:

- `docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md`
- `docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md`
- `docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md`
- `docs/reports/christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md`
- `docs/reports/christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md`
- `artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline/latest`

For the longer full-corpus local experiment, the main monitoring surfaces are:

- `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/launch_latest.log`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/launch_latest.pid`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest/`

For training runs, inspect `subset_summary.json` inside the run directory if you want the exact
deterministic task/tract mix that was selected for a capped local experiment.

## Dataset, Eval, Report, And Publication

These scripts define the public SFT workflow and are the main ones to read if you want to swap in
your own model or adapt the method:

- `build_christian_virtue_sft_dataset.py`
- `train_christian_virtue_qlora.py`
- `generate_christian_virtue_predictions.py`
- `eval_christian_virtue_sft.py`
- `compare_christian_virtue_runs.py`
- `build_christian_virtue_local_report.py`
- `build_christian_virtue_full_corpus_report.py`
- `build_christian_virtue_citation_frontier_report.py`
- `build_christian_virtue_justice_guarded_report.py`
- `publish_christian_virtue_adapter.py`
- `verify_christian_virtue_publication.py`
- `audit_christian_virtue_frontier.py`
- `smoke_test_christian_virtue_sft.py`

## Remote Small-Model CUDA Loop

These wrapper scripts support the smaller remote-GPU research loop:

- `preflight_christian_virtue_gpu.py`
- `run_christian_virtue_small_train.sh`
- `run_christian_virtue_small_base_eval.sh`
- `run_christian_virtue_small_adapter_eval.sh`
- `run_christian_virtue_small_loop.sh`
- `christian_virtue_small_common.sh`

This path is useful for cheaper CUDA experiments, but it is not the main public result surface for
the repo.

## Corpus And Review Workflow Helpers

The remaining `build_*_block.py` and `build_*_review_queue.py` scripts are tract-maintenance
utilities for the evidence and review workflow. They are important to the repo, but they are not
the first scripts an outsider should start with when evaluating the SFT deliverable.

If you need orientation for those surfaces, read:

- [docs/repository_map.md](../docs/repository_map.md)
- [docs/full_corpus_workflow.md](../docs/full_corpus_workflow.md)
- [docs/review_queue_guide.md](../docs/review_queue_guide.md)
