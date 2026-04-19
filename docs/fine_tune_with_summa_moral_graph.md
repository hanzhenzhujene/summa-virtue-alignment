# Fine-Tune With Summa Moral Graph

## What This Repo Gives You

This repo is a ready-to-use fine-tuning entrypoint for an evidence-first Christian virtue dataset
grounded in Thomas Aquinas's moral corpus.

The purpose of this SFT is not only to make a model emit aligned citations. The purpose is to help
the model internalize Aquinas's virtue structure well enough to answer faithfully in Aquinas's
categories, while using citations as a verification layer.

You do not need to rebuild the dataset before you start. The committed dataset exports already live
in the repo:

- [data/processed/sft/exports/christian_virtue_v1](../data/processed/sft/exports/christian_virtue_v1)
- [data/processed/sft/exports/christian_virtue_v1_ood](../data/processed/sft/exports/christian_virtue_v1_ood)

Those exports include:

- train/val/test JSONL files
- prompt-only benchmark files for held-out inference
- dataset manifests
- stable passage ids and citation labels in metadata

## What You Are Training For

The north-star behavior is:

- faithful Christian virtue reasoning in Aquinas's framework
- clear distinctions between virtue, vice, act, object, part, and opposition
- evidence-bounded answers rather than generic moralizing
- citation-grounded traceability as a guardrail

In short:

- first, teach the model to think and answer like an Aquinas-grounded Christian virtue assistant
- then, make that behavior inspectable through stable passage-id citations

## Why This Dataset Is Evidence-First

The canonical evidence unit is the segment id, not a vague article blob.

Every example is built from:

- `data/interim/summa_moral_segments.jsonl`
- stable question/article metadata
- approved reviewed doctrinal annotations from selected virtue tracts

The default pipeline excludes:

- structural-editorial review as training truth
- candidate files as training truth
- processed edges as primary supervision

That means the fine-tuning data stays inspectable and traceable.

## Which Files Are The Training Data

The main default dataset release is:

- [data/processed/sft/exports/christian_virtue_v1/train.jsonl](../data/processed/sft/exports/christian_virtue_v1/train.jsonl)
- [data/processed/sft/exports/christian_virtue_v1/val.jsonl](../data/processed/sft/exports/christian_virtue_v1/val.jsonl)
- [data/processed/sft/exports/christian_virtue_v1/test.jsonl](../data/processed/sft/exports/christian_virtue_v1/test.jsonl)

Held-out prompt inputs for generation live in:

- [data/processed/sft/exports/christian_virtue_v1/benchmarks/test.jsonl](../data/processed/sft/exports/christian_virtue_v1/benchmarks/test.jsonl)
- [data/processed/sft/exports/christian_virtue_v1/benchmarks/val.jsonl](../data/processed/sft/exports/christian_virtue_v1/benchmarks/val.jsonl)

Optional OOD data lives under `christian_virtue_v1_ood/`.

## Quickstart: Local Mac MPS With Qwen2.5 1.5B

This is the official local demonstration path:

- model: `Qwen/Qwen2.5-1.5B-Instruct`
- method: LoRA on Apple Silicon MPS
- official rung: `pilot-lite`
- goal: stable reproducibility and publishable demonstration, not giant local training

Setup:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,sft]"
make build-christian-virtue-sft
```

Smoke train:

```bash
make train-christian-virtue-qwen2-5-1-5b-local-smoke
```

Mac-safe pilot-lite train:

```bash
make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite
```

Base-model test predictions and evaluation:

```bash
make eval-christian-virtue-qwen2-5-1-5b-local-base-test
```

Adapter test predictions and evaluation:

```bash
make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test
```

Base-vs-adapter comparison:

```bash
make compare-christian-virtue-qwen2-5-1-5b-local-test
```

Curated publishable report:

```bash
make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite
```

The adapter eval wrapper prefers `pilot_lite/latest`, then `pilot/latest`, then `smoke/latest`.

One-command local loop:

```bash
make run-christian-virtue-qwen2-5-1-5b-local-loop
```

That loop now defaults to `pilot-lite`, which is the practical local rung on a 16 GB Apple-Silicon
machine.

## Current Canonical Published Artifacts

The current official local publication bundle is:

- Hugging Face adapter:
  [JennyZhu0822/summa-moral-graph-qwen2.5-1.5b-pilot-lite](https://huggingface.co/JennyZhu0822/summa-moral-graph-qwen2.5-1.5b-pilot-lite)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-pilot-lite-20260418_193038](https://github.com/hanzhenzhujene/summa-moral-graph-fork/releases/tag/christian-virtue-qwen2.5-1.5b-pilot-lite-20260418_193038)
- Curated report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md](./reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md)

Canonical published run ids:

- train: `20260418_193038`
- base test: `20260418_143349`
- adapter test: `20260418_203546`
- compare test: `20260418_225541`

Current headline held-out `test` result:

- base citation exact match: `0.000`
- adapter citation exact match: `0.150`
- net gain: `+0.150`

## What The Local Run Writes

Runs are timestamped under:

```text
runs/christian_virtue/qwen2_5_1_5b_instruct/
```

Examples:

- `smoke/20260417_141530/`
- `pilot_lite/20260417_142245/`
- `base_test/20260417_143012/`
- `adapter_test/20260417_144108/`

Each run directory is designed to contain:

- `config_snapshot.yaml`
- `command.log`
- `stdout.log`
- `stderr.log`
- `environment.json`
- `run_manifest.json`
- `metrics.json`
- `report.md`
- `train_metadata.json` for training runs
- `train_log_history.jsonl` for training runs
- `predictions.jsonl` for inference runs

Recommended local order on a 16 GB Apple-Silicon laptop:

1. `smoke`
2. `pilot-lite`
3. `base_test`
4. `adapter_test`
5. `compare_test`
6. curated report generation

The full `pilot` config is still available, but it is intentionally heavier and may be too slow for
routine local use on this hardware. It is an experimental stretch path, not the public default.

## Remote CUDA Path

If you want a bigger or faster experiment, use the existing CUDA path instead of forcing your local
laptop to do it.

Recommended remote order:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,sft]"
make preflight-christian-virtue-gpu
make train-christian-virtue-small-smoke
make train-christian-virtue-small
make generate-christian-virtue-small-base-test
make eval-christian-virtue-small-base-test
make generate-christian-virtue-small-adapter-test
make eval-christian-virtue-small-adapter-test
make compare-christian-virtue-small-test
```

## How To Swap In Your Own Model

The smallest change surface is the config file.

Edit:

- `model_name_or_path`
- `lora_target_modules`
- `max_seq_length`
- `runtime_backend`
- `torch_dtype`

Practical guidance:

- if you stay on Apple Silicon, keep `runtime_backend: mps`
- if you move to a Linux CUDA box and want QLoRA, use `runtime_backend: cuda` and
  `load_in_4bit: true`
- if your model uses different projection module names, update `lora_target_modules`
- if memory gets tight, lower `max_seq_length`, `max_train_examples`, or accumulation-sensitive
  settings first

## How To Generate Base And Adapter Predictions

Base model:

```bash
PYTHONPATH=src python scripts/generate_christian_virtue_predictions.py \
  --config configs/inference/qwen2_5_1_5b_instruct_base_test.yaml \
  --output-dir runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/manual_run
```

Adapter model:

```bash
PYTHONPATH=src python scripts/generate_christian_virtue_predictions.py \
  --config configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml \
  --output-dir runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/manual_run
```

Evaluate either prediction file:

```bash
PYTHONPATH=src python scripts/eval_christian_virtue_sft.py \
  --dataset-dir data/processed/sft/exports/christian_virtue_v1 \
  --predictions runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/manual_run/predictions.jsonl \
  --splits test \
  --report-path runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/manual_run/report.md \
  --metrics-path runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/manual_run/metrics.json
```

## How To Read The Outputs

Look at:

- `metrics.json` for machine-readable scores
- `report.md` for a readable summary plus qualitative samples
- `run_manifest.json` for device, dtype, model, git commit, and dataset linkage
- `environment.json` for package versions and execution context
- the curated report in
  [docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md](./reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md)
  for the publishable research summary

Key evaluation fields:

- `citation_exact_match`
- `citation_partial_match`
- `citation_overlap`
- `relation_type_accuracy`
- `by_tract`
- `by_support_type`

## Packaging And Publication

Once the canonical `pilot-lite`, `base_test`, and `adapter_test` runs exist, package the adapter:

```bash
make package-christian-virtue-qwen2-5-1-5b-local-adapter
```

Publish the adapter to Hugging Face Hub and cut the matching GitHub release:

```bash
make publish-christian-virtue-qwen2-5-1-5b-local-adapter
```

The package metadata records:

- base model name
- dataset export path
- canonical run id
- git commit
- held-out base vs adapter headline metrics
- links to the curated report and dataset card

## What To Read Next

- Maintainer workflow:
  [docs/christian_virtue_sft.md](./christian_virtue_sft.md)
- Dataset card:
  [docs/christian_virtue_dataset_card.md](./christian_virtue_dataset_card.md)
- Experiment index:
  [docs/reports/christian_virtue_experiments.md](./reports/christian_virtue_experiments.md)
