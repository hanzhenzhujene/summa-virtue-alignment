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

Current canonical repo-local run ids:

- train: `20260421_134712`
- base test: `20260420_162346`
- adapter test: `20260421_141053`
- compare test: `20260421_145439`

Public headline on the canonical held-out `test` split:

- overall held-out exact citation moves from `0.0%` to `36.5%`
- strongest task slice: `Virtue concept explanation` moves from `0.0%` to `65.6%`
- second strongest task slice: `Reviewed relation explanation` moves from `0.0%` to `62.7%`
- strongest tract slice: `Justice core` moves from `0.0%` to `50.0%`

Publication note:

- the Hugging Face repo and GitHub release remain the public distribution endpoints
- the GitHub release keeps its original tag slug `20260418_193038` for continuity
- the local adapter package, flagship report, and figures in this repo are the authoritative
  evaluation surfaces for the corrected held-out result

### Quick Read: Why This Shows The SFT Works

Strongest held-out virtue slices:

| Held-out virtue slice | Base | Adapter | Delta |
| --- | ---: | ---: | ---: |
| Held-out benchmark exact citation | `0.0%` | `36.5%` | `+36.5%` |
| Virtue concept explanation | `0.0%` | `65.6%` | `+65.6%` |
| Reviewed relation explanation | `0.0%` | `62.7%` | `+62.7%` |

#### Training Trace

![Local-baseline training curves](assets/christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg)

A clean local optimization trace on Apple `mps`: loss falls sharply and token accuracy rises over
the 20-step run.

#### Held-Out Improvement

![Base vs adapter held-out comparison](assets/christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg)

The adapter materially outperforms base on the strongest held-out virtue slices, especially on
virtue-concept and reviewed-relation tasks. The strongest tract-level gain now lands in
`Justice core`, while the overall held-out benchmark also moves sharply upward.

This is the public demo result, not the intended ceiling. The point of this run is to show that a
small easy-to-reproduce model already exhibits the right movement, which makes the case for larger
follow-on SFT runs even stronger.

## Completed Follow-Up: Citation Frontier

The citation-frontier follow-up is now complete. It keeps the same small local 1.5B budget as the
canonical `local-baseline`, but shifts half of the tiny train subset toward
`citation_grounded_moral_answer` while preserving relation, concept, and passage-grounded anchors.

- Follow-up report:
  [christian_virtue_qwen2_5_1_5b_citation_frontier_report.md](./christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)
- Original hard-slice audit:
  [christian_virtue_citation_frontier_audit.md](./christian_virtue_citation_frontier_audit.md)

Completed repo-local run ids:

- frontier train: `20260421_005543`
- frontier adapter test: `20260421_010240`
- frontier audit: `20260421_012610`

What changed relative to `local-baseline`:

- overall held-out exact citation improved from `36.5%` to `38.6%`
- the hardest user-style slice `citation_grounded_moral_answer` moved from `0.0%` to `3.0%`
  exact stable-id recovery
- any citation signal on that hard slice rose from `47.8%` to `83.6%`
- the run also exposed a real tradeoff: `justice_core` fell from `50.0%` to `19.0%`, and
  `strong_textual_inference` fell from `48.6%` to `20.0%`

This means the citation-heavy mixture is a genuine research result, but not yet a replacement for
the public baseline. The next experiment should keep the new citation-seeking behavior while
protecting the regressed doctrinal slices.

Canonical rerun command:

```bash
make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop
```

Curated follow-up report rebuild:

```bash
make report-christian-virtue-qwen2-5-1-5b-citation-frontier
```

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
