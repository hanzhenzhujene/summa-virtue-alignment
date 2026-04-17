# Christian Virtue Experiments

## Purpose

This file is a short human-readable index of noteworthy Christian virtue SFT runs. Full raw logs
stay under `runs/` and are not part of the committed repo history by default. This report tracks
the curated, repo-level experiment story instead.

## Current Recorded Snapshots

### Qwen3 0.6B Base Test Baseline

Recorded from the local benchmark artifacts under
`runs/christian_virtue/qwen3_0_6b/base_test/`. Those raw run files are not part of the committed
repo surface.

Observed on the held-out `test` split:

- count: `233`
- citation exact match: `0.172`
- citation partial match: `0.172`
- citation overlap: `0.172`

Interpretation:

- the base model can produce Thomistic-sounding prose
- it often fails the repo's citation-grounding requirement
- this is the benchmark floor the adapter path is meant to beat

### Qwen2.5 1.5B Local MPS Pilot Path

Target path:

- `Qwen/Qwen2.5-1.5B-Instruct`
- LoRA on Apple Silicon MPS
- timestamped outputs under `runs/christian_virtue/qwen2_5_1_5b_instruct/`

Validated smoke checkpoint:

- smoke run id: `20260417_135222`
- train examples: `64`
- eval examples: `16`
- global steps: `8`
- train runtime: about `85s`
- final eval loss: `2.524`
- final device: `mps`
- final dtype: `float16`

What is now confirmed:

- the local MPS LoRA training path genuinely starts and finishes
- the run writes `config_snapshot.yaml`, `environment.json`, `run_manifest.json`,
  `train_metadata.json`, `train_log_history.jsonl`, and shell logs
- the adapter artifacts are reusable for the next evaluation step

Still pending for this model path:

- a real local `pilot` run
- held-out `base_test` generation and evaluation
- held-out `adapter_test` generation and evaluation

## How To Add A New Curated Entry

For a new experiment, record:

- model and runtime
- exact config file
- split evaluated
- headline citation metrics
- one short interpretation
- links to the run's `report.md`, `metrics.json`, and config snapshot
