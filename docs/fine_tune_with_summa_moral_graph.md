# Fine-Tune With Summa Moral Graph

## What This Repo Gives You

This repo is the canonical public guide, demo, and proof-of-work for fine-tuning on an
evidence-first Christian virtue dataset grounded in Thomas Aquinas's moral corpus.

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
- official rung: `local-baseline`
- goal: stable reproducibility and a convincing proof-of-pipeline demo, not the strongest final
  quality run

This local 1.5B setup is intentionally small. It exists so users can verify the full SFT loop on a
laptop and then carry the same dataset/method over to larger runs when they want stronger results.

Current repo note:

- the live `smoke` and `local-baseline` configs now use `32` train-time eval examples so the
  round-robin validation slice covers all four task families
- the already-published baseline report still reflects the earlier `16`-example monitoring slice,
  which affected train-time diagnostics rather than the held-out base-vs-adapter benchmark itself

One-command setup:

```bash
make setup-christian-virtue-local
```

That command uses the pinned lockfile at
`requirements/local-mps-py312.lock.txt` and then installs the repo in editable mode without
re-resolving the environment.

One-command canonical reproduction:

```bash
make reproduce-christian-virtue-qwen2-5-1-5b-local
```

If you want the explicit stepwise path, run:

```bash
make build-christian-virtue-sft
```

Smoke train:

```bash
make train-christian-virtue-qwen2-5-1-5b-local-smoke
```

Mac-safe local-baseline train:

```bash
make train-christian-virtue-qwen2-5-1-5b-local-baseline
```

That rung now keeps the same `128` train examples and `20` steps, but uses a `32`-example
train-time eval slice so loss monitoring is less biased toward only the first two task families.

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
make report-christian-virtue-qwen2-5-1-5b-local-baseline
```

Final publishable QA gate:

```bash
make verify-christian-virtue-qwen2-5-1-5b-local-publishable
```

That command rebuilds the committed dataset export if needed, regenerates the curated report,
refreshes the local adapter package, and verifies that the public README/docs/report surfaces still
match the canonical published bundle.

Shorter public-release command:

```bash
make public-release-check
```

This alias adds `ruff` and `mypy` ahead of the publication-surface verification pass, so it is the
best final command before sharing the repo publicly.

The adapter eval wrapper prefers `local_baseline/latest`, then `extended/latest`, then `smoke/latest`.

One-command local loop:

```bash
make run-christian-virtue-qwen2-5-1-5b-local-loop
```

That loop is the experiment loop only. The canonical publishable path for a fresh machine is still:

1. `make setup-christian-virtue-local`
2. `make reproduce-christian-virtue-qwen2-5-1-5b-local`
3. `make public-release-check`

## Citation-Frontier Follow-Up

Once the canonical `local-baseline` run exists, the highest-leverage follow-up is not broader
dataset scope. It is a same-budget mixture change aimed at the remaining
`citation_grounded_moral_answer` bottleneck.

That follow-up has now been run successfully in this repo:

```bash
make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop
```

Completed result:

- overall held-out exact citation improved from `0.365` to `0.386`
- `citation_grounded_moral_answer` exact stable-id recovery improved from `0.000` to `0.030`
- any citation signal on that hard slice improved from `0.403` to `0.836`
- the run also introduced real tradeoffs, especially on `justice_core` and
  `strong_textual_inference`

Read the finished follow-up analysis here:

- [docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)
- [docs/reports/christian_virtue_citation_frontier_audit.md](./reports/christian_virtue_citation_frontier_audit.md)

The first link is the completed same-budget follow-up result. The second is the original hard-slice
audit that motivated the experiment.

Stepwise path:

```bash
make train-christian-virtue-qwen2-5-1-5b-citation-frontier
make eval-christian-virtue-qwen2-5-1-5b-citation-frontier-test
make compare-christian-virtue-qwen2-5-1-5b-citation-frontier
make audit-christian-virtue-qwen2-5-1-5b-citation-frontier
make report-christian-virtue-qwen2-5-1-5b-citation-frontier
```

What changes relative to `local-baseline`:

- same backbone: `Qwen/Qwen2.5-1.5B-Instruct`
- same local runtime target: Apple Silicon `mps`
- same small public budget: `128` train examples, `20` steps
- different subset policy: `task_tract_quota_round_robin`
- different train mix:
  - `citation_grounded_moral_answer=64`
  - `reviewed_relation_explanation=24`
  - `virtue_concept_explanation=24`
  - `passage_grounded_doctrinal_qa=16`

What this experiment is for:

- keep the Christian virtue dataset fixed
- keep the public `local-baseline` demo unchanged
- test whether a more citation-heavy small-run mixture improves stable-id recovery on held-out
  user-style moral prompts

Current conclusion:

- yes, the same-budget citation-heavy recipe does improve the hard user-style citation task
- no, it is not yet the new public baseline, because it trades away too much on some doctrinal
  slices
- the next step after this follow-up is a justice-guarded citation-repair recipe rather than more
  dataset scope

Expected output roots:

- `runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier/latest/`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_adapter_test/latest/`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_compare_test/latest/`
- `runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_audit/latest/`

## Current Artifact Status

The repo now keeps one corrected canonical local package and two stable public distribution
endpoints:

- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)
- Local adapter package:
  [../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md)
- Curated report:
  [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)

Canonical repo-local run ids:

- train: `20260421_134712`
- base test: `20260420_162346`
- adapter test: `20260421_141053`
- compare test: `20260421_145439`

Current canonical headline held-out `test` result:

- base citation exact match: `0.000`
- adapter citation exact match: `0.365`
- net gain: `+0.365`
- strongest task slice: `Virtue concept explanation` at `65.6%`
- second strongest task slice: `Reviewed relation explanation` at `62.7%`
- strongest tract slice: `Justice core` at `50.0%`

Interpret this published result as a small-model demonstration baseline. It is the public example
showing that the Summa Moral Graph dataset can move model behavior in the right direction. The same
pipeline is meant to scale to larger models and longer GPU runs afterward.

The Hugging Face repo and GitHub release remain the public distribution endpoints. The GitHub
release keeps its original tag slug `20260418_193038` for continuity, while the curated report and
local adapter package are the authoritative evaluation surfaces for the canonical `0.365` result.

## What The Local Run Writes

Runs are timestamped under:

```text
runs/christian_virtue/qwen2_5_1_5b_instruct/
```

Examples:

- `smoke/20260417_141530/`
- `local_baseline/20260417_142245/`
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
- `subset_summary.json` for training runs
- `predictions.jsonl` for inference runs

Recommended local order on a 16 GB Apple-Silicon laptop:

1. `smoke`
2. `local-baseline`
3. `base_test`
4. `adapter_test`
5. `compare_test`
6. curated report generation

The full `extended` config is still available, but it is intentionally heavier and may be too slow for
routine local use on this hardware. It is an experimental stretch path, not the public default.

The local training configs now expose two deterministic subset policies for small capped runs:

- `task_tract_round_robin`
  - the canonical `local-baseline` policy
  - balances across task families and virtue tracts
- `task_tract_quota_round_robin`
  - the citation-frontier policy
  - keeps tract balancing inside each task family while letting a small run emphasize one task type

That means local runs no longer depend on the accidental order of the first rows in `train.jsonl`.

The local `16`-example eval subset is intentionally tiny and currently covers only the first two
task families under that deterministic round-robin ordering. Treat it as a training-time stability
signal, not as the main public benchmark. The authoritative public claim comes from the full
held-out `233`-example `test` split.

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
- `subset_summary.json` for the exact train/eval subset strategy and selected task/tract mix
- the curated report in
  [docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
  for the publishable research summary

Key evaluation fields:

- `citation_exact_match`
- `citation_partial_match`
- `citation_overlap`
- `relation_type_accuracy`
- `by_tract`
- `by_support_type`

## Packaging And Publication

Once the canonical `local-baseline`, `base_test`, and `adapter_test` runs exist, package the adapter:

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
