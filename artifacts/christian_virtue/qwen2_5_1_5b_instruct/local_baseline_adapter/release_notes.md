# Christian Virtue Qwen2.5 1.5B Local Baseline

This release mirrors the canonical local `local-baseline` adapter publication for the `summa-moral-graph` Christian virtue SFT pipeline.

## Included here

- Hugging Face adapter: https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b
- Curated experiment report: https://github.com/hanzhenzhujene/summa-virtue-alignment/blob/45759fc32305204b24705674b6295bdfaf707a17/docs/reports/christian_virtue_qwen2_5_1_5b_local_baseline_report.md
- Dataset card: https://github.com/hanzhenzhujene/summa-virtue-alignment/blob/45759fc32305204b24705674b6295bdfaf707a17/docs/christian_virtue_dataset_card.md
- Training export: `data/processed/sft/exports/christian_virtue_v1`

## Purpose

Train an Aquinas-grounded Christian virtue assistant that answers within reviewed evidence, uses Aquinas's moral categories, and preserves source traceability.

## Artifact Status

- The public GitHub release keeps the earlier distribution tag `christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038` for continuity, but the authoritative benchmark numbers in this package and curated report come from the corrected run `20260419_154300`.
- Treat the curated report and local package manifest as the canonical evaluation surface for the current repo numbers.

## Executive Readout

- Clearest public win: `Virtue concept explanation` at `40.6%` exact over `32` prompts.
- Strongest tract slice: `Theological virtues` at `21.1%` exact over `19` prompts.
- This published run uses a deliberately small local demo model, so the result should be read as proof-of-pipeline rather than the final quality target.
- This release foregrounds the strongest virtue-aligned slices; the full held-out matrix remains in the curated report.
- Full task/tract breakdowns and the qualitative goal-demo panel live in the curated report.

## Headline public highlights

- Strongest task slice: `Virtue concept explanation` at `40.6%`
- Strongest tract slice: `Theological virtues` at `21.1%`
- Run id: `20260419_154300`
- Git commit: `662c9d309fefd80d22f2caf7f65622afdee7ef10`

## Canonical command path

```bash
make build-christian-virtue-sft
make train-christian-virtue-qwen2-5-1-5b-local-smoke
make train-christian-virtue-qwen2-5-1-5b-local-baseline
make eval-christian-virtue-qwen2-5-1-5b-local-base-test
make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test
make compare-christian-virtue-qwen2-5-1-5b-local-test
make report-christian-virtue-qwen2-5-1-5b-local-baseline
make verify-christian-virtue-qwen2-5-1-5b-local-publishable
```
