# Report Figures

These figures are the committed publication assets for the Christian virtue local baseline.

- `christian_virtue_qwen2_5_1_5b_pilot_lite_training_curves.svg`
  - supports the claim that the canonical `pilot-lite` run is a real, stable optimization trace
  - used in the flagship local report as Figure 1
- `christian_virtue_qwen2_5_1_5b_pilot_timing_comparison.svg`
  - supports the claim that `pilot-lite` is the correct public local rung on a 16 GB Apple-Silicon
    laptop, even though a heavier `pilot` config remains available
  - used in the flagship local report as Figure 2
- `christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg`
  - supports the claim that the adapter improves held-out benchmark behavior over the untouched
    base model
  - used in the flagship local report as Figure 3

The canonical narrative for these assets lives in:

- [Flagship report](../christian_virtue_qwen2_5_1_5b_pilot_lite_report.md)
- [Experiment index](../christian_virtue_experiments.md)
