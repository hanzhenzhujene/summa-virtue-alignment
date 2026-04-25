# Christian Virtue Experiments

## Purpose

This index tracks the public experiment story that the repo currently foregrounds.

Raw `runs/` artifacts stay out of the committed repo by default. The entries here are the
reader-facing checkpoints that explain the current dataset, method, strongest result, and release
surface without forcing a reviewer to reconstruct the story from terminal logs.

Public first-use links:

- online chat:
  [jennyzhu0822-summa-virtue-chat.hf.space](https://jennyzhu0822-summa-virtue-chat.hf.space)
- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- companion graph viewer:
  [summa-moral-graph.streamlit.app](https://summa-moral-graph.streamlit.app/)

## Current Flagship Result

### Qwen2.5 1.5B Full-Corpus LoRA

This is the strongest repo-local Christian virtue result currently documented in the project.

- Report:
  [christian_virtue_qwen2_5_1_5b_full_corpus_report.md](./christian_virtue_qwen2_5_1_5b_full_corpus_report.md)
- Benchmark packet summary:
  [christian_virtue_benchmark_packet_summary.md](./christian_virtue_benchmark_packet_summary.md)
- Positive benchmark readout:
  [christian_virtue_positive_benchmark_readout.md](./christian_virtue_positive_benchmark_readout.md)
- Positive benchmark examples:
  [christian_virtue_positive_benchmark_examples.md](./christian_virtue_positive_benchmark_examples.md)
- Latest positive-only benchmark packet:
  `runs/christian_virtue/qwen2_5_1_5b_instruct/benchmark_packet/latest/report.md`
- Dataset card:
  [../christian_virtue_dataset_card.md](../christian_virtue_dataset_card.md)
- Public fine-tune guide:
  [../fine_tune_with_summa_moral_graph.md](../fine_tune_with_summa_moral_graph.md)

Completed repo-local run ids:

- untuned-model eval: `20260420_162346`
- full-corpus train: `20260422_223349`
- full-corpus adapter test: `20260423_011453`
- supplementary VirtueBench V2 base eval: `20260425_004101`
- supplementary VirtueBench V2 full-corpus eval: `20260425_010109`
- supplementary VirtueBench V2 paired base eval: `20260425_014109`
- supplementary VirtueBench V2 paired full-corpus eval: `20260425_015430`
- supplementary VirtueBench V2 positive-only diagnostic report: `20260425_083752`
- supplementary Aquinas grounding probe base eval: `20260425_024231`
- supplementary Aquinas grounding probe full-corpus eval: `20260425_034345`
- supplementary external candidate base eval: `20260425_090412`
- supplementary external candidate full-corpus eval: `20260425_090920`
- supplementary external positive-only comparison: `20260425_091658`
- consolidated positive-only benchmark packet: `20260425_091751`

What it demonstrates:

- overall held-out exact citation rises from `0.0%` to `71.2%`
- `passage_grounded_doctrinal_qa` reaches `100.0%`
- `reviewed_relation_explanation` reaches `100.0%`
- `virtue_concept_explanation` reaches `100.0%`
- `justice_core` reaches `71.4%`
- the in-domain Aquinas grounding probe confirms the behavior shift more directly: exact segment
  citation rises from `0.0%` base to `71.2%` LoRA, segment-id citation presence rises from `0.0%`
  to `100.0%`, and the transparent grounding score rises from `37.7%` to `74.2%`
- the better-matched VirtueBench V2 diagnostic improves from `29.7%` base to `58.0%`
  full-corpus LoRA on the capped 300-row run, but it also reveals strong LoRA A-position bias
  (`294` A answers out of `300`), so it should not be overclaimed as clean virtue discernment yet
- the counterbalanced paired VirtueBench V2 run is the safer read: it improves from `34.0%` base
  to `49.5%` LoRA on the capped 200-row run, but the LoRA still answers `A` on `197/200`
  prompts, so this remains a diagnostic for future calibration rather than a public benchmark win
- an expanded external candidate slate screened `15` short multiple-choice slices and promotes
  only the `5` LoRA-positive rows: MMLU world religions `+5.0` pp, MMMLU-ZH business ethics
  `+3.3` pp, MMMLU-ZH moral scenarios `+3.3` pp, MMMLU-ZH philosophy `+1.7` pp, and MMLU moral
  scenarios `+1.7` pp, all at `100.0%` parse rate

This is the clearest repo-local demonstration that the reviewed Christian virtue dataset can teach
strong Aquinas-grounded doctrinal and explanatory behavior on held-out evaluation once the model
sees the full reviewed training surface.

### Quick Read

![Held-out tract profile after full-corpus LoRA](assets/christian_virtue_qwen2_5_1_5b_full_corpus_tract_profile.svg)

The tract profile comes first because it is the fastest way to see that the result is broad rather
than concentrated in one tract. All eight tracked virtue tracts now sit in a narrow, strong band
on the held-out test split.

![From untuned model to earlier small-data LoRA to full-corpus LoRA](assets/christian_virtue_qwen2_5_1_5b_full_corpus_progress.svg)

The second public figure shows the full improvement ladder: untouched model, earlier small-data
LoRA rung (`train 128 / val 32`), and the completed full-corpus LoRA run (`train 1475 / val 175`).

| Held-out virtue slice | Untuned model | Earlier small-data LoRA | Full-corpus LoRA | Gain over earlier LoRA |
| --- | ---: | ---: | ---: | ---: |
| Overall exact citation | `0.0%` | `36.5%` | `71.2%` | `+34.8 pts` |
| Passage-grounded doctrinal QA | `0.0%` | `32.8%` | `100.0%` | `+67.2 pts` |
| Reviewed relation explanation | `0.0%` | `62.7%` | `100.0%` | `+37.3 pts` |
| Virtue concept explanation | `0.0%` | `65.6%` | `100.0%` | `+34.4 pts` |
| Justice core tract | `0.0%` | `50.0%` | `71.4%` | `+21.4 pts` |

Canonical rerun command:

```bash
make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop
```

Curated report rebuild:

```bash
make report-christian-virtue-qwen2-5-1-5b-full-corpus
```

## Public Release Artifact

The repo also ships a smaller public adapter package for readers who want the lightest release
surface:

- Hugging Face adapter:
  [JennyZhu0822/summa-virtue-qwen2.5-1.5b](https://huggingface.co/JennyZhu0822/summa-virtue-qwen2.5-1.5b)
- Matching GitHub release:
  [christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038](https://github.com/hanzhenzhujene/summa-virtue-alignment/releases/tag/christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038)
- Local adapter package mirror:
  [../../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md](../../artifacts/christian_virtue/qwen2_5_1_5b_instruct/local_baseline_adapter/README.md)

That public package is intentionally smaller than the full-corpus repo-local result. It exists as
the lightest reproducible release artifact, while the full-corpus report above is the strongest
current local result.
