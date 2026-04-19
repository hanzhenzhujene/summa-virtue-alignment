# SFT Artifacts

- `samples/` contains small committed inspection artifacts.
- `exports/` is the default build destination for full dataset exports and manifests.
- `exports/<dataset>/benchmarks/` contains prompt-only non-train benchmark inputs for inference.
- most regenerated exports remain gitignored by default.
- the committed public Christian virtue releases now live under:
  - `exports/christian_virtue_v1/`
  - `exports/christian_virtue_v1_ood/`
- those committed exports are part of the public fine-tuning entry surface for this repo.
- public docs for using those exports live at:
  - [Dataset card](../../../docs/christian_virtue_dataset_card.md)
  - [Fine-tuning guide](../../../docs/fine_tune_with_summa_moral_graph.md)
  - [Repository map](../../../docs/repository_map.md)
  - [Flagship local report](../../../docs/reports/christian_virtue_qwen2_5_1_5b_pilot_lite_report.md)
- the canonical local environment is pinned in:
  - `../../../requirements/local-mps-py312.lock.txt`
- raw run logs and checkpoints still belong in `runs/` and remain gitignored.
