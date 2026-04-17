# Christian Virtue SFT

## Objective

This pipeline builds a v1 instruction-tuning dataset for a Christian virtue assistant grounded in
Thomas Aquinas's moral corpus as structured in this repository. The goal is not a generic theology
chatbot and not a whole-repo text dump. The goal is a virtue-centered SFT dataset that preserves:

- stable passage ids from `data/interim/`
- reviewed doctrinal supervision from selected `data/gold/` files
- citation traceability back to segment-level evidence
- separation between doctrinal, structural-editorial, and candidate layers

The canonical evidence unit remains the interim segment id. Every generated example keeps source
passage ids and citation labels in metadata, and the assistant outputs include citation blocks.

## Why V1 Is Virtue-Centered

The repo's full moral corpus contains several distinct supervision layers and tract families. V1
focuses on Christian virtue formation and virtue-adjacent doctrinal relations because that is the
highest-signal path to an assistant that can explain virtues, vices, acts, and tract-local
distinctions in Aquinas's own moral corpus without flattening the repo into generic prose.

The selected reviewed doctrinal files are:

- `data/gold/theological_virtues_reviewed_doctrinal_annotations.jsonl`
- `data/gold/prudence_reviewed_doctrinal_annotations.jsonl`
- `data/gold/justice_core_reviewed_doctrinal_annotations.jsonl`
- `data/gold/connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl`
- `data/gold/fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl`
- `data/gold/fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl`
- `data/gold/temperance_141_160_reviewed_doctrinal_annotations.jsonl`
- `data/gold/temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl`

The default builder keeps only rows with:

- `review_status == "approved"`
- `support_type in {"explicit_textual", "strong_textual_inference"}`
- `edge_layer == "doctrinal"` when present

The current v1 build uses `555` reviewed source annotations across those files.

## Why Structural-Editorial And Candidate Layers Stay Out

V1 explicitly excludes:

- all `*_reviewed_structural_editorial_annotations.jsonl`
- all `data/candidate/*`
- all `data/processed/*edges*` as primary supervision
- `religion_tract_reviewed_doctrinal_annotations.jsonl`
- `owed_relation_tract_reviewed_doctrinal_annotations.jsonl`
- `pilot_reviewed_doctrinal_annotations.jsonl`

That exclusion is deliberate. Structural-editorial files are valuable for graph navigation and
scholarly review, but they are not the same thing as doctrinal supervision. Candidate files are
review queues, not approved truth. Derived processed edges are exports, not the canonical source of
evidence. Keeping those layers separate prevents the training set from silently learning reviewer
workflow shortcuts as though they were doctrinal claims.

## How Examples Are Built

The builder lives under
[src/summa_moral_graph/sft](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/src/summa_moral_graph/sft).
It:

1. loads the canonical interim segments, questions, and articles
2. loads the selected doctrinal annotation files
3. validates required fields
4. defaults missing doctrinal `edge_layer` fields to `"doctrinal"` when the source file itself is a
   reviewed doctrinal file
5. filters by approved review status and allowed support types
6. deduplicates by `annotation_id`
7. joins each annotation back to its source segment text and citation label
8. emits chat-style SFT examples plus a manifest

The serialized example schema is:

```json
{
  "example_id": "christian_virtue_v1.reviewed_relation_explanation.ann.charity-has-act-beneficence",
  "task_type": "reviewed_relation_explanation",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {
    "annotation_id": "ann.charity-has-act-beneficence",
    "source_passage_id": "st.ii-ii.q023.a001.resp",
    "citation_label": "II-II q.23 a.1 resp",
    "tract": "theological_virtues",
    "subject_id": "concept.charity",
    "relation_type": "has_act",
    "object_id": "concept.beneficence",
    "support_type": "explicit_textual",
    "group_keys": {"question_id": "st.ii-ii.q023"}
  }
}
```

V1 generates four template families:

- `passage_grounded_doctrinal_qa`
- `reviewed_relation_explanation`
- `virtue_concept_explanation`
- `citation_grounded_moral_answer`

The default full build currently yields:

- `555` passage-grounded doctrinal QA examples
- `555` reviewed relation explanation examples
- `555` citation-grounded moral answer examples
- `218` concept explanation examples
- `1883` total examples

The builder also emits prompt-only benchmark files under
`data/processed/sft/exports/<dataset>/benchmarks/` for every non-train split. Those benchmark
files keep the exact `system` and `user` messages plus metadata, but strip the gold assistant
answer so evaluation runs do not accidentally leak the reference response into generation inputs.

## How Splits Are Built

The default split policy is deterministic grouped splitting by `question_id`, stratified
tract-by-tract.

Why `question_id`:

- many examples are generated from the same source passage or from multiple annotations within one
  question
- grouping by question prevents the same doctrinal locus from appearing in both train and
  evaluation splits
- question grouping is still fine-grained enough to preserve tract balance better than tract-level
  splitting alone

How it works:

- within each tract, question groups are ordered by a stable hash of `(seed, tract, question_id)`
- groups are then assigned to `train`, `val`, and `test` according to the configured ratios
- every example inherits the split of its question group

The default `christian_virtue_v1` build currently produces:

- `train`: `1475` examples across `98` question groups
- `val`: `175` examples across `13` question groups
- `test`: `233` examples across `13` question groups

The harder OOD config in
[configs/sft/christian_virtue_v1_ood.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/sft/christian_virtue_v1_ood.yaml)
holds out the whole `temperance_closure_161_170` tract as `ood_test`. That build currently yields:

- `train`: `1360`
- `val`: `162`
- `test`: `222`
- `ood_test`: `139`

Because prompt-only benchmark exports are written for non-train splits, the default evaluation
surfaces are now:

- `data/processed/sft/exports/christian_virtue_v1/benchmarks/test.jsonl`
- `data/processed/sft/exports/christian_virtue_v1/benchmarks/val.jsonl`
- `data/processed/sft/exports/christian_virtue_v1_ood/benchmarks/{test, val, ood_test}.jsonl`

## Commands

Build the default dataset:

```bash
make build-christian-virtue-sft
```

Run the smoke test:

```bash
make smoke-test-christian-virtue-sft
```

Run the builder directly with a different config:

```bash
.venv/bin/python scripts/build_christian_virtue_sft_dataset.py \
  --config configs/sft/christian_virtue_v1_ood.yaml
```

Prototype QLoRA training on the default 4B target:

```bash
.venv/bin/pip install -e ".[dev,sft]"
make train-christian-virtue-proto
```

Smaller same-family prototype training on `Qwen/Qwen3-0.6B`:

```bash
.venv/bin/pip install -e ".[dev,sft]"
make train-christian-virtue-small
```

Dry-run the training plan without launching training:

```bash
.venv/bin/python scripts/train_christian_virtue_qlora.py \
  --config configs/train/qwen3_4b_qlora.yaml \
  --dry-run
```

Dry-run a held-out inference run:

```bash
.venv/bin/python scripts/generate_christian_virtue_predictions.py \
  --config configs/inference/qwen3_4b_base_test.yaml \
  --dry-run
```

Generate test predictions from a base or adapter-backed model:

```bash
.venv/bin/python scripts/generate_christian_virtue_predictions.py \
  --config configs/inference/qwen3_4b_base_test.yaml
```

Smaller same-family baseline benchmark:

```bash
.venv/bin/python scripts/generate_christian_virtue_predictions.py \
  --config configs/inference/qwen3_0_6b_base_test.yaml
```

On CUDA machines, the default inference configs keep 4-bit loading enabled. On non-CUDA machines,
the runner now records an explicit fallback in `run_manifest.json` and uses standard weights on the
resolved device (`mps` on Apple Silicon when available, otherwise CPU) instead of pretending that
CUDA-only quantization is still active.

Evaluate only the intended held-out split:

```bash
.venv/bin/python scripts/eval_christian_virtue_sft.py \
  --dataset-dir data/processed/sft/exports/christian_virtue_v1 \
  --predictions data/processed/sft/eval/christian_virtue_qwen3_4b_base_test/predictions.jsonl \
  --splits test
```

Evaluate a prediction file:

```bash
.venv/bin/python scripts/eval_christian_virtue_sft.py \
  --dataset-dir data/processed/sft/exports/christian_virtue_v1 \
  --predictions path/to/predictions.jsonl
```

If `--predictions` is omitted, the evaluation script self-evaluates against the reference dataset.
That is useful for smoke checks, not for model comparison.

## Training Scaffolding

The training scaffolding uses:

- `transformers`
- `trl`
- `peft`
- `bitsandbytes`
- `accelerate`

The default train configs are:

- [configs/train/qwen3_0_6b_qlora.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/train/qwen3_0_6b_qlora.yaml)
- [configs/train/qwen3_4b_qlora.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/train/qwen3_4b_qlora.yaml)
- [configs/train/qwen3_8b_qlora.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/train/qwen3_8b_qlora.yaml)

Recommended order for this repo:

- start with `Qwen/Qwen3-0.6B` to validate the end-to-end training/eval loop cheaply
- move to `Qwen/Qwen3-4B` once the small-model run shows real citation gains
- treat `Qwen/Qwen3-8B` as the later, quality-first run rather than the first paid experiment

The training code lazy-imports those dependencies so the dataset builder, tests, and smoke checks do
not require heavy GPU packages.

Default QLoRA choices:

- 4-bit loading
- NF4 quantization
- bfloat16 compute when CUDA bf16 is available, otherwise float16
- LoRA target modules for standard attention/MLP projections
- gradient checkpointing
- config-driven sequence length, batch size, accumulation, and save/eval cadence

## Evaluation Scaffolding

The evaluation script computes:

- citation exact match
- citation partial match
- citation overlap ratio
- relation-type accuracy when predictions expose `predicted_relation_type`
- tract-wise breakdowns
- support-type breakdowns
- a markdown qualitative review report

The repo now also includes config-driven inference generation so evaluation can be run against
prompt-only benchmark exports rather than ad hoc hand-built prediction files. The default inference
configs live in:

- [configs/inference/qwen3_0_6b_base_test.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/inference/qwen3_0_6b_base_test.yaml)
- [configs/inference/qwen3_4b_base_test.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/inference/qwen3_4b_base_test.yaml)
- [configs/inference/qwen3_4b_base_ood.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/inference/qwen3_4b_base_ood.yaml)
- [configs/inference/qwen3_4b_adapter_test.yaml](/Users/hanzhenzhu/Desktop/summa-moral-graph-fork/configs/inference/qwen3_4b_adapter_test.yaml)

The generation runner writes `predictions.jsonl` plus a `run_manifest.json` under the configured
evaluation output directory. Each prediction row preserves `example_id`, `split`, and metadata so
the evaluator can score only the intended held-out split.

`run_manifest.json` now also records the resolved runtime device, the effective dtype, and whether
4-bit loading remained active. That makes Apple-Silicon or CPU benchmark runs inspectable instead
of hiding a hardware-specific fallback.

The inference runner now also:

- disables Qwen3 reasoning mode at prompt-render time so benchmark outputs do not include
  `<think> ... </think>` traces by default
- strips any stray `<think> ... </think>` block from decoded assistant text before serialization
- writes `predictions.partial.jsonl` incrementally during long runs so interrupted benchmarks can
  resume instead of restarting from scratch

Prediction rows may expose either:

- `assistant_text`
- `prediction`
- a `messages` array with an assistant message

If relation-type accuracy is desired for non-reference predictions, include
`predicted_relation_type` in each prediction row. The evaluator no longer infers a predicted
relation type from copied reference metadata inside prediction files, because that would turn a
traceability field into a false perfect score.

## Known Limitations

- Template generation is deterministic and evidence-first, but still synthetic. It is not a
  substitute for human-authored doctrinal QA at scale.
- The evaluation scaffold focuses on citation behavior and relation labels. It does not yet score
  doctrinal adequacy or stylistic faithfulness beyond those measurable surfaces.
- The current inference runner generates sequentially and is designed for clean reproducibility, not
  maximum throughput.
- On a 16 GB Apple-Silicon laptop, the full `Qwen/Qwen3-4B` held-out benchmark is still slow
  enough that full test and OOD sweeps should be treated as remote-GPU work rather than assumed
  local workflows.
- The builder currently trusts the selected doctrinal file list rather than auto-discovering tract
  inclusion from review manifests.
- Some reviewed doctrinal files omit an `edge_layer` field. The builder treats those rows as
  doctrinal because the file boundary itself is already doctrinally scoped.

## Recommended V2 Next Steps

- add reviewer-authored free-response supervision for especially central virtues
- enrich evaluation with doctrinal entailment and unsupported-claim checks
- add harder cross-tract question synthesis tasks once more reviewed doctrinal coverage is in place
- explore DPO or preference optimization after a stable citation-faithful SFT baseline exists
