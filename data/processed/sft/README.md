# SFT Artifacts

- `samples/` contains small committed inspection artifacts.
- `exports/` is the default build destination for full dataset exports and manifests.
- `exports/<dataset>/benchmarks/` contains prompt-only non-train benchmark inputs for inference.
- most regenerated exports remain gitignored by default.
- the committed public Christian virtue releases now live under:
  - `exports/christian_virtue_v1/`
  - `exports/christian_virtue_v1_ood/`
- those committed exports are part of the public fine-tuning entry surface for this repo.
- raw run logs and checkpoints still belong in `runs/` and remain gitignored.
