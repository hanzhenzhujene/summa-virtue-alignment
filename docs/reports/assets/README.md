# Report Figures

These figures are the committed publication assets for the Christian virtue local baseline, the
completed full-corpus local run, and the citation-focused follow-up series.

- `christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg`
  - supports the claim that the canonical `local-baseline` run is a real, stable optimization trace
  - used in the flagship local report as Figure 1
- `christian_virtue_qwen2_5_1_5b_local_recipe_timing_comparison.svg`
  - supports the claim that `local-baseline` is the correct public local rung on a 16 GB Apple-Silicon
    laptop, even though a heavier `extended` config remains available
  - used in the flagship local report as Figure 2
- `christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg`
  - supports the claim that the adapter improves held-out benchmark behavior over the untouched
    base model
  - used in the flagship local report as Figure 3
- `christian_virtue_qwen2_5_1_5b_full_corpus_vs_baseline.svg`
  - supports the claim that the completed full-corpus local run more than doubles the canonical
    held-out exact-citation result while saturating the repo's strongest doctrinal and explanatory
    task families
  - used in the full-corpus local report as Figure 1
- `christian_virtue_qwen2_5_1_5b_full_corpus_tract_profile.svg`
  - supports the claim that every virtue tract improves under the completed full-corpus local
    recipe, with the strongest tract scores clustering around the low 70s
  - used in the full-corpus local report as Figure 2
- `christian_virtue_qwen2_5_1_5b_full_corpus_training_curves.svg`
  - supports the claim that the longer full-corpus Apple-Silicon local run stays stable through
    the larger two-epoch training budget
  - used in the full-corpus local report as Figure 3
- `christian_virtue_citation_frontier_modes.svg`
  - supports the claim that the completed citation-frontier follow-up improves citation-seeking
    behavior on the user-style moral QA frontier while leaving stable-id recovery unfinished
  - used in the baseline citation frontier audit report
- `christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg`
  - supports the claim that the completed citation-frontier follow-up materially raises citation
    signal and achieves the first non-zero exact stable-id recovery on held-out moral QA
  - used in the citation-frontier follow-up report
- `christian_virtue_qwen2_5_1_5b_justice_guarded_tradeoffs.svg`
  - supports the claim that the justice-guarded same-budget follow-up is the strongest overall
    exact-citation local result so far while recovering most of the `justice_core` /
    `strong_textual_inference` drop from citation-frontier
  - used in the justice-guarded follow-up report

The canonical narrative for these assets lives in:

- [Flagship report](../christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- [Full-corpus local report](../christian_virtue_qwen2_5_1_5b_full_corpus_report.md)
- [Citation-frontier follow-up report](../christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)
- [Justice-guarded follow-up report](../christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md)
- [Citation frontier audit](../christian_virtue_citation_frontier_audit.md)
- [Experiment index](../christian_virtue_experiments.md)
