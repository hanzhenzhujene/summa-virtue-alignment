# Report Figures

These figures are the committed public assets for the current Christian virtue release surface.

- `christian_virtue_qwen2_5_1_5b_full_corpus_tract_profile.svg`
  - supports the claim that the completed full-corpus run is strong across the full virtue tract
    surface rather than on one narrow tract only
  - used in the README, the full-corpus report, and the curated experiment index
- `christian_virtue_qwen2_5_1_5b_full_corpus_progress.svg`
  - supports the repo's main public result by showing the full progression from the untouched
    `Qwen/Qwen2.5-1.5B-Instruct` model to the earlier small-data LoRA rung and then to the
    completed full-corpus LoRA result
  - used in the README, the full-corpus report, and the curated experiment index
- `christian_virtue_qwen2_5_1_5b_full_corpus_training_curves.svg`
  - supports the claim that the longer Apple-Silicon full-corpus run stays stable across the
    larger two-epoch training budget
  - used in the full-corpus report
- `christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg`
  - preserves the smaller public release artifact's optimization trace
  - used in the published small-model report surface
- `christian_virtue_qwen2_5_1_5b_local_recipe_timing_comparison.svg`
  - preserves the timing comparison that justifies the smaller public release package on a 16 GB
    Apple-Silicon laptop
  - used in the smaller public release report
- `christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg`
  - preserves the held-out comparison for the smaller public release package
  - used in the smaller public release report
- `christian_virtue_citation_frontier_modes.svg`
  - preserves the original hard-slice citation-frontier audit figure
  - used in the citation frontier audit report
- `christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg`
  - preserves the completed citation-frontier follow-up figure as a card-framed failure-mode
    breakdown from the untuned model to the citation-frontier adapter
  - used in the citation-frontier follow-up report
- `christian_virtue_qwen2_5_1_5b_justice_guarded_tradeoffs.svg`
  - preserves the justice-guarded follow-up figure
  - used in the justice-guarded follow-up report
- `christian_virtue_positive_benchmark_deltas.svg`
  - shows the positive-only base-to-LoRA deltas across in-domain, VirtueBench, and external
    transfer rows
  - used in the README and the positive benchmark readout
- `christian_virtue_positive_benchmark_levels.svg`
  - shows absolute base and LoRA levels for the same positive-only benchmark rows
  - used in the README and the positive benchmark readout

The canonical narrative for these assets lives in:

- [README.md](../../../README.md)
- [Full-corpus report](../christian_virtue_qwen2_5_1_5b_full_corpus_report.md)
- [Positive benchmark readout](../christian_virtue_positive_benchmark_readout.md)
- [Experiment index](../christian_virtue_experiments.md)
- [Public claim map](../../public_claim_map.md)
