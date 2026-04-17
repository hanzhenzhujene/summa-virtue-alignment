from __future__ import annotations

from pathlib import Path


def test_public_fine_tune_docs_and_exports_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    expected_paths = [
        repo_root / "docs/fine_tune_with_summa_moral_graph.md",
        repo_root / "docs/christian_virtue_sft.md",
        repo_root / "docs/christian_virtue_dataset_card.md",
        repo_root / "docs/reports/christian_virtue_experiments.md",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/manifest.json",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/train.jsonl",
        repo_root / "data/processed/sft/exports/christian_virtue_v1/benchmarks/test.jsonl",
        repo_root / "data/processed/sft/exports/christian_virtue_v1_ood/manifest.json",
        repo_root / "data/processed/sft/exports/christian_virtue_v1_ood/benchmarks/ood_test.jsonl",
        repo_root / "data/processed/sft/samples/christian_virtue_v1_sample.jsonl",
    ]

    for path in expected_paths:
        assert path.exists(), path


def test_readme_and_gitignore_expose_public_fine_tune_surface() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme_text = (repo_root / "README.md").read_text(encoding="utf-8")
    gitignore_text = (repo_root / ".gitignore").read_text(encoding="utf-8")

    assert "Fine-Tune Your Model With Summa Moral Graph" in readme_text
    assert "docs/fine_tune_with_summa_moral_graph.md" in readme_text
    assert "!data/processed/sft/exports/christian_virtue_v1/**" in gitignore_text
    assert "!data/processed/sft/exports/christian_virtue_v1_ood/**" in gitignore_text
