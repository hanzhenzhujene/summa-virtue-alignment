# Accuracy-First Hybrid Report

This completed follow-up keeps the same tiny local `Qwen/Qwen2.5-1.5B-Instruct` budget as the
canonical baseline, `citation-frontier`, and `justice-guarded`, but optimizes explicitly for the
highest held-out exact citation result. It combines justice/STI protected buckets with additional
hard-slice `citation_grounded_moral_answer` reservations.

## Executive Readout

- strongest same-budget overall result in the local 1.5B series: `41.2%`
- strongest `passage_grounded_doctrinal_qa` result so far: `50.7%`
- strongest `reviewed_relation_explanation` result so far: `64.2%`
- best read of this run: a small-model proof that the dataset can push overall held-out virtue
  accuracy materially higher under the same local budget

## Setup

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Train run | `20260421_164616` |
| Adapter eval run | `20260421_165359` |
| Compare run | `20260421_171851` |
| Train duration | `7.6` minutes |
| Train quotas | `citation_grounded_moral_answer=56`, `reviewed_relation_explanation=26`, `virtue_concept_explanation=22`, `passage_grounded_doctrinal_qa=24` |
| Protected buckets | `4` justice/STI reservations and `2` moral-QA reservations |
| Config snapshot | `runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid/20260421_164616/config_snapshot.yaml` |
| Train metadata | `runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid/20260421_164616/train_metadata.json` |
| Adapter metrics | `runs/christian_virtue/qwen2_5_1_5b_instruct/accuracy_first_hybrid_adapter_test/20260421_165359/metrics.json` |

## Result Table

| Slice | Baseline | Citation-frontier | Justice-guarded | Accuracy-first |
| --- | ---: | ---: | ---: | ---: |
| Overall held-out exact citation | `36.5%` | `38.6%` | `39.1%` | `41.2%` |
| Citation-grounded moral answer | `0.0%` | `3.0%` | `0.0%` | `0.0%` |
| Passage-grounded doctrinal QA | `32.8%` | `37.3%` | `46.3%` | `50.7%` |
| Reviewed relation explanation | `62.7%` | `61.2%` | `55.2%` | `64.2%` |
| Virtue concept explanation | `65.6%` | `68.8%` | `71.9%` | `59.4%` |
| Justice core | `50.0%` | `19.0%` | `42.9%` | `31.0%` |
| Strong textual inference | `48.6%` | `20.0%` | `42.9%` | `25.7%` |

## What Improved

- This is now the strongest same-budget overall result in the local 1.5B series at `41.2%`.
- `passage_grounded_doctrinal_qa` reached `50.7%`, the best result so far on that slice.
- `reviewed_relation_explanation` reached `64.2%`, slightly above the canonical baseline and well
  above `justice-guarded`.
- Relative to the canonical baseline, the net held-out exact citation gain is `+4.7` points.

## Open Question

- `citation_grounded_moral_answer` stayed at `0.0%` exact stable-id recovery, so the hybrid did
  not recover the frontier's small hard-slice win.
- `justice_core` fell to `31.0%`, which is better than `citation-frontier` but still clearly worse
  than both the canonical baseline and `justice-guarded`.
- `strong_textual_inference` also fell to `25.7%`, again above `citation-frontier` but below the
  stronger doctrinal runs.
- `virtue_concept_explanation` dropped to `59.4%`, which means the new overall win comes mostly
  from passage and relation slices rather than from the strongest virtue-concept behavior.

## Interpretation

If the optimization target is pure held-out exact citation, this is now the repo's best same-budget
local recipe. But it is not yet the clean all-around successor to `local-baseline` or
`justice-guarded`, because the hardest user-style moral-QA slice remains flat and the doctrinal
justice/STI recovery is only partial.

So the project now has three different same-budget strengths:

- `citation-frontier`: best hard-slice moral-QA exact-id recovery
- `justice-guarded`: best doctrinal protection on justice/STI among the follow-ups
- `accuracy-first`: best overall held-out exact citation

## Reproduce

```bash
make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop
```
