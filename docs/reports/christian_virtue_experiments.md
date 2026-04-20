# Christian Virtue Experiments

## Purpose

This index tracks the curated experiment story for the Christian virtue SFT path.

Raw `runs/` artifacts stay out of the committed repo by default. The entries here are the
publishable, reader-facing checkpoints that matter for reproducing the dataset, method, and model
behavior.

If you are new to the repo, use this page as the shortest bridge between the top-level README and
the full flagship report: it tells you which run matters, what it proves, and where to click next.

## Flagship Local Baseline

### Qwen2.5 1.5B Local Baseline

This is the canonical Apple-Silicon local demonstration run for the repo.

- Report:
  [christian_virtue_qwen2_5_1_5b_local_baseline_report.md](./christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- Dataset card:
  [../christian_virtue_dataset_card.md](../christian_virtue_dataset_card.md)
- Public fine-tune guide:
  [../fine_tune_with_summa_moral_graph.md](../fine_tune_with_summa_moral_graph.md)

What it demonstrates:

- the committed Christian virtue dataset can drive a real SFT loop end-to-end
- the official local `local-baseline` recipe is reproducible on a 16 GB Apple-Silicon laptop
- a deliberately small 1.5B demo model is already enough to show the pipeline works
- the LoRA adapter beats the untouched base model on the held-out benchmark
- the repo can serve as a public fine-tuning entrypoint rather than only a private research log

Published artifacts:

- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)
- Local adapter package:
  [../../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](../../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md)

Current corrected repo-local run ids:

- train: `20260419_154300`
- base test: `20260418_143349`
- adapter test: `20260419_154757`
- compare test: `20260419_160910`

Public headline on the corrected held-out `test` split:

- strongest task slice: `Virtue concept explanation` moves from `0.0%` to `40.6%`
- second strongest task slice: `Reviewed relation explanation` moves from `0.0%` to `20.9%`
- strongest tract slice: `Theological virtues` moves from `0.0%` to `21.1%`
- goal-demo exact citations: `0 / 12` on base -> `5 / 12` on adapter

Publication note:

- the Hugging Face repo and GitHub release remain the public distribution endpoints
- the GitHub release keeps its original tag slug `20260418_193038` for continuity
- the local adapter package, flagship report, and figures in this repo are the authoritative
  evaluation surfaces for the corrected held-out result

### Quick Read: Why This Shows The SFT Works

Strongest held-out virtue slices:

| Held-out virtue slice | Base | Adapter | Delta |
| --- | ---: | ---: | ---: |
| Virtue concept explanation | `0.0%` | `40.6%` | `+40.6%` |
| Reviewed relation explanation | `0.0%` | `20.9%` | `+20.9%` |

#### Training Trace

![Local-baseline training curves](assets/christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg)

A clean local optimization trace on Apple `mps`: loss falls sharply and token accuracy rises over
the 20-step run.

#### Held-Out Improvement

![Base vs adapter held-out comparison](assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg)

The adapter materially outperforms base on the strongest held-out virtue slices, especially on
virtue-concept and reviewed-relation tasks. The strongest tract-level gain also lands in
`Theological virtues`, which is exactly the part of the corpus where a Thomist virtue assistant
should become most visibly sharper.

This is the public demo result, not the intended ceiling. The point of this run is to show that a
small easy-to-reproduce model already exhibits the right movement, which makes the case for larger
follow-on SFT runs even stronger.

## Canonical Command Surface

```bash
make setup-christian-virtue-local
make reproduce-christian-virtue-qwen2-5-1-5b-local
```

The one-command reproduction target runs the full local publication loop end to end. The longer
stepwise command path remains documented in the fine-tuning guide for readers who want to inspect
each stage separately.

## Policy

- `local-baseline` is the only official local rung for public docs and quickstart paths.
- Heavier local `extended` runs remain experimental.
- Larger CUDA experiments remain important, but they are not the public baseline for this repo.
