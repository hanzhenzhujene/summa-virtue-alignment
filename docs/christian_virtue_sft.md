# Christian Virtue SFT

## Research Objective

This repo now supports a clean Christian virtue SFT workflow built from the reviewed moral corpus of
Thomas Aquinas in the *Summa Theologiae*. The v1 target is not a general theology chatbot. The
target is a citation-aware virtue assistant that:

- stays grounded in segment-level evidence
- inherits stable passage ids from `data/interim/`
- uses only approved reviewed doctrinal supervision in the default build
- keeps doctrinal, structural-editorial, and candidate layers separate
- can be trained and evaluated through reproducible local and remote loops

The canonical evidence unit remains the segment id, not the whole article.

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

The first local baseline is:

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
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,sft]"
make build-christian-virtue-sft
```

Smoke train:

```bash
bash scripts/run_christian_virtue_qwen2_5_1_5b_local_train.sh smoke
```

Pilot train:

```bash
bash scripts/run_christian_virtue_qwen2_5_1_5b_local_train.sh pilot
```

Base-model held-out test:

```bash
bash scripts/run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh
```

Adapter held-out test:

```bash
bash scripts/run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh
```

One-command local pilot loop:

```bash
bash scripts/run_christian_virtue_qwen2_5_1_5b_local_loop.sh
```

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
- Adapter evaluation expects `runs/christian_virtue/qwen2_5_1_5b_instruct/pilot/latest` to exist.
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
