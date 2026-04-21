from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

PUBLIC_DOC_PATHS = [
    REPO_ROOT / "CITATION.cff",
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "public_claim_map.md",
    REPO_ROOT / "docs" / "fine_tune_with_summa_moral_graph.md",
    REPO_ROOT / "docs" / "repository_map.md",
    REPO_ROOT / "scripts" / "README.md",
]

PUBLIC_WORKFLOW_PATHS = [
    REPO_ROOT / ".github" / "workflows" / "public-release-check.yml",
]

DOCSTRING_PATHS = [
    REPO_ROOT / "streamlit_app.py",
    REPO_ROOT / "app" / "Home.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "app" / "dashboard.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "app" / "tracts.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "cli.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "ingest" / "corpus.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "viewer" / "shell.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "viewer" / "load.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "comparison.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "filters.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "loaders.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "preflight.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "runtime.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "serialization.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "splitters.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "templates.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "utils.py",
]


def _module_docstring(path: Path) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return ast.get_docstring(tree)


def test_public_docs_exist() -> None:
    for path in PUBLIC_DOC_PATHS:
        assert path.exists(), f"Expected public doc surface to exist: {path}"


def test_public_release_workflow_exists() -> None:
    for path in PUBLIC_WORKFLOW_PATHS:
        assert path.exists(), f"Expected public workflow surface to exist: {path}"


def test_major_public_python_files_have_module_docstrings() -> None:
    for path in DOCSTRING_PATHS:
        docstring = _module_docstring(path)
        assert docstring, f"Expected a top-level docstring in {path}"


def test_public_release_check_is_documented() -> None:
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    guide_text = (REPO_ROOT / "docs" / "fine_tune_with_summa_moral_graph.md").read_text(
        encoding="utf-8"
    )
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    workflow_text = (
        REPO_ROOT / ".github" / "workflows" / "public-release-check.yml"
    ).read_text(encoding="utf-8")

    assert "make public-release-check" in readme_text
    assert "make public-release-check" in guide_text
    assert "public-release-check:" in makefile_text
    assert "make public-release-check" in workflow_text
    assert "actions/checkout@v6" in workflow_text
    assert "actions/setup-python@v6" in workflow_text


def test_makefile_pins_canonical_local_publication_identity() -> None:
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "LOCAL_15B_HF_REPO_ID := JennyZhu0822/summa-virtue-qwen2.5-1.5b" in makefile_text
    assert (
        "LOCAL_15B_RELEASE_TAG := christian-virtue-qwen2.5-1.5b-local-baseline-20260418_193038"
        in makefile_text
    )
    assert "--published-model-url $(LOCAL_15B_HF_URL)" in makefile_text
    assert "--release-url $(LOCAL_15B_RELEASE_URL)" in makefile_text
    assert "--hf-repo-id $(LOCAL_15B_HF_REPO_ID)" in makefile_text
    assert "--release-tag $(LOCAL_15B_RELEASE_TAG)" in makefile_text
    assert (
        "LOCAL_15B_TRAIN_METADATA := "
        "$(LOCAL_15B_ROOT)/local_baseline/latest/train_metadata.json"
    ) in makefile_text
    assert (
        "LOCAL_15B_BASE_METRICS := $(LOCAL_15B_ROOT)/base_test/latest/metrics.json"
    ) in makefile_text
    assert (
        "LOCAL_15B_ADAPTER_METRICS := $(LOCAL_15B_ROOT)/adapter_test/latest/metrics.json"
        in makefile_text
    )
    assert (
        "Canonical local run artifacts not present; "
        "verifying committed public surfaces only."
    ) in makefile_text


def test_readme_states_thomist_goal_and_minimal_example_framing() -> None:
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "# summa virtue alignment" in readme_text
    assert "evidence-first christian virtue dataset" in readme_text
    assert "minimal sft demonstration" in readme_text
    assert "audit surface" in readme_text
    assert "built on the corpus and evidence model of summa moral graph" in readme_text
    assert "## dataset merit" in readme_text
    assert "## training demo" in readme_text
    assert "## method overview" in readme_text
    assert "## repository structure" in readme_text
    assert "## reproducibility contract" in readme_text
    assert "docs/public_claim_map.md" in readme_text
    assert "## why this dataset is unusual" in readme_text
    assert "## theological grounding" in readme_text
    assert (
        "the dataset exists to train models toward aquinas-grounded christian virtue reasoning"
        in readme_text
    )
    assert "reviewed, passage-grounded" in readme_text
    assert "relational, and auditable" in readme_text
    assert "teaches structure, not just vocabulary" in readme_text
    assert "keeps the training truth unusually clean" in readme_text
    assert "thomist moral virtue" in readme_text
    assert "minimal example" in readme_text
    assert "generic theology chatbot" in readme_text
    assert "not the strongest achievable final model" in readme_text
    assert "expected outputs from a successful canonical run" in readme_text
    assert "docs/repository_map.md" in readme_text
    assert "artifacts/christian_virtue/" in readme_text
    assert "latest local training run" in readme_text
    assert "christian_virtue_qwen2_5_1_5b_local_baseline_training_curves.svg" in readme_text
    assert "christian_virtue_qwen2_5_1_5b_base_vs_adapter_test.svg" in readme_text
    assert "christian_virtue_qwen2_5_1_5b_citation_frontier_report.md" in readme_text
    assert "newadvent.org/summa/3023.htm#article1" in readme_text
    assert "newadvent.org/summa/3058.htm#article1" in readme_text
    assert "actions/workflows/public-release-check.yml/badge.svg" in readme_text


def test_citation_file_states_public_release_identity() -> None:
    citation_text = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8").lower()
    assert 'title: "summa virtue alignment"' in citation_text
    assert "thomas aquinas" in citation_text
    assert "christian virtue" in citation_text


def test_scripts_guide_names_canonical_local_entrypoints() -> None:
    scripts_guide = (REPO_ROOT / "scripts" / "README.md").read_text(encoding="utf-8")
    assert "setup_christian_virtue_local.sh" in scripts_guide
    assert "reproduce_christian_virtue_qwen2_5_1_5b_local.sh" in scripts_guide
    assert "build_christian_virtue_sft_dataset.py" in scripts_guide
    assert "audit_christian_virtue_frontier.py" in scripts_guide
    assert "build_christian_virtue_citation_frontier_report.py" in scripts_guide
    assert "run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh" in scripts_guide
    assert "make audit-christian-virtue-qwen2-5-1-5b-local-frontier" in scripts_guide
    assert "make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop" in scripts_guide
    assert "prints the key output paths" in scripts_guide


def test_repository_map_names_canonical_public_bundle() -> None:
    repository_map = (REPO_ROOT / "docs" / "repository_map.md").read_text(encoding="utf-8")
    assert "## Canonical Public Bundle" in repository_map
    assert "christian_virtue_v1" in repository_map
    assert "christian_virtue_citation_frontier_audit.md" in repository_map
    assert "christian_virtue_qwen2_5_1_5b_citation_frontier_report.md" in repository_map
    assert "local_baseline_adapter/README.md" in repository_map
