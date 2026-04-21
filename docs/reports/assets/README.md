# Report Figures

These figures are the committed publication assets for the Christian virtue local baseline and its
citation-focused follow-up.

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
- `christian_virtue_citation_frontier_modes.svg`
  - supports the claim that the completed citation-frontier follow-up improves citation-seeking
    behavior on the user-style moral QA frontier while leaving stable-id recovery unfinished
  - used in the baseline citation frontier audit report
- `christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg`
  - supports the claim that the completed citation-frontier follow-up materially raises citation
    signal and achieves the first non-zero exact stable-id recovery on held-out moral QA
  - used in the citation-frontier follow-up report

The canonical narrative for these assets lives in:

- [Flagship report](../christian_virtue_qwen2_5_1_5b_local_baseline_report.md)
- [Citation-frontier follow-up report](../christian_virtue_qwen2_5_1_5b_citation_frontier_report.md)
- [Citation frontier audit](../christian_virtue_citation_frontier_audit.md)
- [Experiment index](../christian_virtue_experiments.md)
