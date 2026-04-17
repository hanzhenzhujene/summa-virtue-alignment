# SFT Artifacts

- `samples/` contains small committed inspection artifacts.
- `exports/` is the default build destination for full dataset exports and manifests.
- `exports/<dataset>/benchmarks/` contains prompt-only non-train benchmark inputs for inference.
- `exports/` is gitignored so large regenerated datasets do not clutter the repo history.
- training checkpoints default to `outputs/`, which is also gitignored.
