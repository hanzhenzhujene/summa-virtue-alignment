# Christian Virtue SFT

## Research Objective

This repo now supports a clean Christian virtue SFT workflow built from the reviewed moral corpus of
Thomas Aquinas in the *Summa Theologiae*. The v1 target is not a general theology chatbot. The
target is an Aquinas-grounded Christian virtue assistant that:

- learns Aquinas's moral structure rather than generic moral advice
- explains virtues, vices, acts, parts, and doctrinal relations in Aquinas's categories
- stays grounded in segment-level evidence
- inherits stable passage ids from `data/interim/`
- uses only approved reviewed doctrinal supervision in the default build
- keeps doctrinal, structural-editorial, and candidate layers separate
- can be trained and evaluated through reproducible local and remote loops

The canonical evidence unit remains the segment id, not the whole article.

### North Star

The purpose of this SFT is not merely to align citation formatting.

The real goal is to turn a general model into a Christian virtue model that can:

- reason faithfully within Aquinas's virtue framework
- distinguish virtue, vice, act, object, part, and opposition correctly
- answer in clear modern English without collapsing into generic self-help language
- remain bounded by reviewed doctrinal evidence
- provide citations as accountability and traceability, not as the whole end of the project

The working priority is:

1. faithful virtue reasoning
2. evidence-bounded doctrinal answers
3. citation-grounded traceability

That means a run should not be judged as successful simply because it emits passage ids. A strong
run should also show that the model has actually internalized Aquinas's moral distinctions.

## Why V1 Is Virtue-Centered

The repo contains more than one review layer and more than one tract family. V1 stays tightly
scoped to the Christian virtue path so the fine-tuning target is doctrinally coherent and
operationally reproducible.

Included doctrinal sources:

- `data/gold/theological_virtues_reviewed_doctrinal_annotations.jsonl`
- `data/gold/prudence_reviewed_doctrinal_annotations.jsonl`
- `data/gold/justice_core_reviewed_doctrinal_annotations.jsonl`
- `data/gold/connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl`
- `data/gold/fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl`
- `data/gold/fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl`
- `data/gold/temperance_141_160_reviewed_doctrinal_annotations.jsonl`
- `data/gold/temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl`

Included rows must satisfy:

- `review_status == "approved"`
- `support_type in {"explicit_textual", "strong_textual_inference"}`
- doctrinal layer only

Default exclusions:

- all `*_reviewed_structural_editorial_annotations.jsonl`
- all `data/candidate/*`
- all `data/processed/*edges*` as primary supervision
- `religion_tract_reviewed_doctrinal_annotations.jsonl`
- `owed_relation_tract_reviewed_doctrinal_annotations.jsonl`
- `pilot_reviewed_doctrinal_annotations.jsonl`

## Why Structural-Editorial And Candidate Layers Stay Out

This repo is evidence-first and layer-aware. Structural-editorial review is useful, but it is not
the same thing as doctrinal supervision. Candidate files are review material, not approved truth.
Keeping those layers out of default SFT prevents reviewer workflow artifacts from being learned as
if they were direct doctrinal claims.

## How Examples Are Built

The builder lives under [src/summa_moral_graph/sft](../src/summa_moral_graph/sft).
It:

1. loads `data/interim/summa_moral_segments.jsonl` plus question and article metadata
2. loads the selected reviewed doctrinal files
3. validates required fields
4. filters by approved review status and allowed support type
5. deduplicates by `annotation_id`
6. joins each annotation back to `source_passage_id`
7. emits chat-style SFT examples with stable ids, citation labels, and tract metadata
8. emits manifests and prompt-only benchmark splits for held-out inference

Current default dataset scale:

- `555` reviewed source annotations
- `1883` total SFT examples
- `1475` train examples
- `175` val examples
- `233` test examples

Current OOD dataset scale:

- `1360` train examples
- `162` val examples
- `222` test examples
- `139` `ood_test` examples

Template families:

- `passage_grounded_doctrinal_qa`
- `reviewed_relation_explanation`
- `virtue_concept_explanation`
- `citation_grounded_moral_answer`

## Split Policy

Splits are grouped by `question_id`, not by row-level random shuffle.

Why:

- many examples share the same passage or doctrinal locus
- question-level grouping avoids leakage across train and evaluation splits
- it preserves tract structure better than naive global random splitting

The OOD config holds out a coherent tract block:

- `temperance_closure_161_170` becomes `ood_test`

## Public Dataset Surface

The public committed dataset release is now part of this repo:

- [data/processed/sft/exports/christian_virtue_v1](../data/processed/sft/exports/christian_virtue_v1)
- [data/processed/sft/exports/christian_virtue_v1_ood](../data/processed/sft/exports/christian_virtue_v1_ood)
- [data/processed/sft/samples/christian_virtue_v1_sample.jsonl](../data/processed/sft/samples/christian_virtue_v1_sample.jsonl)

Important files inside each export:

- `all.jsonl`
- `train.jsonl`
- `val.jsonl`
- `test.jsonl`
- `manifest.json`
- `benchmark_manifest.json`
- `benchmarks/*.jsonl`

## Build Commands

Build the default dataset:

```bash
make build-christian-virtue-sft
```

Build the OOD dataset:

```bash
make build-christian-virtue-sft-ood
```

Run the smoke test:

```bash
make smoke-test-christian-virtue-sft
```

Builder direct invocation:

```bash
.venv/bin/python scripts/build_christian_virtue_sft_dataset.py \
  --config configs/sft/christian_virtue_v1.yaml
```

## Local Mac MPS Path

The canonical local baseline is:

- `Qwen/Qwen2.5-1.5B-Instruct`

This is a LoRA path for Apple Silicon MPS, not a CUDA QLoRA path.

Runtime behavior on MPS:

- `load_in_4bit=false`
- no `bitsandbytes` requirement
- no `BitsAndBytesConfig`
- no `prepare_model_for_kbit_training`
- model weights load in `float16`
- runtime resolves to `mps`

Recommended local environment:

```bash
make setup-christian-virtue-local
make build-christian-virtue-sft
```

The setup target uses the pinned local lockfile at
`requirements/local-mps-py312.lock.txt`.

One-command canonical reproduction:

```bash
make reproduce-christian-virtue-qwen2-5-1-5b-local
```

Smoke train:

```bash
make train-christian-virtue-qwen2-5-1-5b-local-smoke
```

Mac-safe pilot-lite train:

```bash
make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite
```

Base-model held-out test:

```bash
make eval-christian-virtue-qwen2-5-1-5b-local-base-test
```

Adapter held-out test:

```bash
make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test
```

Base-vs-adapter comparison:

```bash
make compare-christian-virtue-qwen2-5-1-5b-local-test
```

Curated local report:

```bash
make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite
```

Final publishable QA gate:

```bash
make verify-christian-virtue-qwen2-5-1-5b-local-publishable
```

This is the maintainer-facing release check: it rebuilds the canonical local report, refreshes the
local adapter package, and verifies that the package manifest, run artifacts, README, guide docs,
experiment index, and curated report still agree about the published baseline.

Shorter public-release command:

```bash
make public-release-check
```

This alias adds `ruff` and `mypy` ahead of the publication-surface verification pass, so it is the
best one-line release audit before sharing the repo externally.

One-command local pilot loop:

```bash
make run-christian-virtue-qwen2-5-1-5b-local-loop
```

The local adapter eval wrapper now looks for `pilot_lite/latest` first and falls back to
`pilot/latest` if you have a heavier full pilot run.

The heavier full `pilot` config remains in the repo as an experimental path, but it is no longer
the public default because `pilot-lite` is the reliable rung on the current 16 GB Mac.

## Publication Workflow

Package the canonical adapter locally:

```bash
make package-christian-virtue-qwen2-5-1-5b-local-adapter
```

Publish the adapter to Hugging Face Hub and create the matching GitHub release:

```bash
make publish-christian-virtue-qwen2-5-1-5b-local-adapter
```

The packaging step copies the adapter weights and tokenizer-side metadata into an isolated
`artifacts/` directory, writes a model card, and writes release notes tied to the exact run id and
git commit.

Current published canonical artifacts:

- Hugging Face adapter:
  [JennyZhu0822/summa-moral-graph-qwen2.5-1.5b-pilot-lite](https://huggingface.co/JennyZhu0822/summa-moral-graph-qwen2.5-1.5b-pilot-lite)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-pilot-lite-20260418_193038](https://github.com/hanzhenzhujene/summa-moral-graph-fork/releases/tag/christian-virtue-qwen2.5-1.5b-pilot-lite-20260418_193038)
- Canonical train run id: `20260418_193038`
- Canonical adapter eval run id: `20260418_203546`
- Current held-out `test` citation exact: `0.150`

## Remote CUDA Path

The remote CUDA path remains the right place for larger QLoRA experiments such as:

- `Qwen/Qwen3-0.6B`
- `Qwen/Qwen3-4B`
- `Qwen/Qwen3-8B`

Environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,sft]"
```

Preflight:

```bash
make preflight-christian-virtue-gpu
```

Small remote baseline loop:

```bash
make train-christian-virtue-small-smoke
make train-christian-virtue-small
make generate-christian-virtue-small-base-test
make eval-christian-virtue-small-base-test
make generate-christian-virtue-small-adapter-test
make eval-christian-virtue-small-adapter-test
make compare-christian-virtue-small-test
```

## Standard Run Outputs

The local 1.5B run root is:

```text
runs/christian_virtue/qwen2_5_1_5b_instruct/
```

Expected step roots:

- `smoke/<run_id>/`
- `pilot/<run_id>/`
- `base_test/<run_id>/`
- `adapter_test/<run_id>/`

The remote 0.6B baseline remains under:

```text
runs/christian_virtue/qwen3_0_6b/
```

Every timestamped local run directory is designed to hold:

- `config_snapshot.yaml`
- `command.log`
- `stdout.log`
- `stderr.log`
- `run_manifest.json`
- `environment.json`
- `metrics.json`
- `report.md`
- `predictions.jsonl` for inference runs
- `predictions.partial.jsonl` during in-progress generation
- `train_metadata.json` for training runs
- `train_log_history.jsonl` for training runs

`run_manifest.json` records:

- `run_id`
- `start_time`
- `end_time`
- `git_commit`
- `resolved_device`
- `torch_dtype`
- `model_name_or_path`
- `dataset_dir`
- `dataset_manifest_path`
- `config_snapshot_path`
- package versions for `python`, `torch`, `transformers`, `peft`, `trl`, and `accelerate`

## Config Surface

Shared runtime fields:

- `runtime_backend`: `auto | cuda | mps | cpu`
- `torch_dtype`: `auto | float16 | float32 | bfloat16`

Useful training config fields to swap when using your own model:

- `model_name_or_path`
- `lora_target_modules`
- `max_seq_length`
- `runtime_backend`
- `torch_dtype`
- `load_in_4bit`

New local MPS configs:

- [configs/train/qwen2_5_1_5b_instruct_lora_mps_smoke.yaml](../configs/train/qwen2_5_1_5b_instruct_lora_mps_smoke.yaml)
- [configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml](../configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml)
- [configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot.yaml](../configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot.yaml)
- [configs/inference/qwen2_5_1_5b_instruct_base_test.yaml](../configs/inference/qwen2_5_1_5b_instruct_base_test.yaml)
- [configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml](../configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml)

## Evaluation

The evaluator reports:

- citation exact match
- citation partial match
- citation overlap
- relation-type accuracy when prediction rows expose `predicted_relation_type`
- tract-wise breakdowns
- support-type breakdowns
- qualitative examples in `report.md`

Direct evaluation command:

```bash
.venv/bin/python scripts/eval_christian_virtue_sft.py \
  --dataset-dir data/processed/sft/exports/christian_virtue_v1 \
  --predictions runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/predictions.jsonl \
  --splits test \
  --report-path runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/report.md \
  --metrics-path runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest/metrics.json
```

## Common Failure Points

- `bitsandbytes` is only required for the CUDA 4-bit path, not for the local MPS 1.5B path.
- If `runtime_backend: mps` is set on a non-Apple-Silicon machine, runtime resolution should fail
  loudly instead of silently falling back.
- Adapter evaluation now prefers
  `runs/christian_virtue/qwen2_5_1_5b_instruct/pilot_lite/latest` and falls back to
  `runs/christian_virtue/qwen2_5_1_5b_instruct/pilot/latest`, then to
  `runs/christian_virtue/qwen2_5_1_5b_instruct/smoke/latest`.
- A successful smoke train proves wiring, not model quality.
- A 16 GB MacBook can run the local pilot path, but it is not the right target for long,
  full-scale experiments.

## Known Limitations

- The current evaluation scaffold still measures traceability better than doctrinal adequacy.
- The local 1.5B path is meant to be a stable pilot baseline, not the final quality ceiling.
- The dataset is templated from reviewed doctrine, so stylistic diversity is intentionally bounded.
- Sequential generation is slower than high-throughput inference backends, but easier to audit.

## Recommended V2 Next Steps

- add human-authored doctrinal response targets for central virtue questions
- score unsupported claims and doctrinal entailment explicitly
- add stronger cross-tract held-out evaluations
- compare multiple small instruct backbones after the 1.5B local baseline is stable
