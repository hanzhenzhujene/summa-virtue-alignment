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
    REPO_ROOT / "scripts" / "smoke_test_christian_virtue_chat.py",
]

PUBLIC_WORKFLOW_PATHS = [
    REPO_ROOT / ".github" / "workflows" / "public-release-check.yml",
]

DOCSTRING_PATHS = [
    REPO_ROOT / "streamlit_app.py",
    REPO_ROOT / "scripts" / "smoke_test_christian_virtue_chat.py",
    REPO_ROOT / "scripts" / "deploy_christian_virtue_chat_space.py",
    REPO_ROOT / "scripts" / "gradio_christian_virtue_chat.py",
    REPO_ROOT / "app" / "Home.py",
    REPO_ROOT / "app" / "pages" / "1_Corpus_Browser.py",
    REPO_ROOT / "app" / "pages" / "2_Passage_Explorer.py",
    REPO_ROOT / "app" / "pages" / "3_Concept_Explorer.py",
    REPO_ROOT / "app" / "pages" / "4_Graph_View.py",
    REPO_ROOT / "app" / "pages" / "5_Stats.py",
    REPO_ROOT / "app" / "pages" / "6_Chat.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "app" / "chat.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "app" / "gradio_chat.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "app" / "dashboard.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "app" / "tracts.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "cli.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "ingest" / "corpus.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "viewer" / "shell.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "viewer" / "load.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "comparison.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "chat.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "chat_smoke.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "filters.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "loaders.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "preflight.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "runtime.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "serialization.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "splitters.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "templates.py",
    REPO_ROOT / "src" / "summa_moral_graph" / "sft" / "utils.py",
]

SHELL_COMMENT_PATHS = [
    REPO_ROOT / "scripts" / "setup_christian_virtue_local.sh",
    REPO_ROOT / "scripts" / "reproduce_christian_virtue_qwen2_5_1_5b_local.sh",
    REPO_ROOT / "scripts" / "launch_christian_virtue_qwen2_5_1_5b_full_corpus_loop.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_qwen2_5_1_5b_local_adapter_eval.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_qwen2_5_1_5b_local_base_eval.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_qwen2_5_1_5b_local_compare.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_qwen2_5_1_5b_local_loop.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_qwen2_5_1_5b_local_train.sh",
    REPO_ROOT / "scripts" / "christian_virtue_small_common.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_small_train.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_small_base_eval.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_small_adapter_eval.sh",
    REPO_ROOT / "scripts" / "run_christian_virtue_small_loop.sh",
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


def test_public_shell_entrypoints_have_header_comments() -> None:
    for path in SHELL_COMMENT_PATHS:
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines, f"Expected shell script to be non-empty: {path}"
        assert lines[0] == "#!/usr/bin/env bash", f"Expected standard bash shebang in {path}"
        assert len(lines) > 1 and lines[1].startswith("# "), (
            f"Expected a short header comment after the shebang in {path}"
        )


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


def test_readme_states_thomist_goal_and_full_corpus_result() -> None:
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "# summa virtue alignment" in readme_text
    assert "evidence-first christian virtue dataset" in readme_text
    assert "audit surface" in readme_text
    assert "audit surface" in readme_text
    assert "built on the corpus and evidence model of summa moral graph" in readme_text
    assert "## dataset merit" in readme_text
    assert "## at a glance" in readme_text
    assert "## latest result" in readme_text
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
    assert "generic theology chatbot" in readme_text
    assert "strongest repo-local result" in readme_text
    assert "expected outputs from a successful canonical run" in readme_text
    assert "docs/repository_map.md" in readme_text
    assert "artifacts/christian_virtue/" in readme_text
    assert "full-corpus training run" in readme_text
    assert "christian_virtue_qwen2_5_1_5b_full_corpus_progress.svg" in readme_text
    assert "christian_virtue_qwen2_5_1_5b_full_corpus_tract_profile.svg" in readme_text
    assert "christian_virtue_qwen2_5_1_5b_full_corpus_report.md" in readme_text
    assert "gradio-chat-christian-virtue-qwen2-5-1-5b-full-corpus" in readme_text
    assert "summa-virtue-chat.hf.space" in readme_text
    assert "deploy-christian-virtue-chat-space" in readme_text
    assert "chat-christian-virtue-qwen2-5-1-5b-full-corpus" in readme_text
    assert "smoke-test-christian-virtue-chat" in readme_text
    assert "full_corpus_chat" in readme_text
    assert "full_corpus_chat_smoke" in readme_text
    assert "run-christian-virtue-qwen2-5-1-5b-full-corpus-loop" in readme_text
    assert "71.2%" in readme_text
    assert "36.5%" in readme_text
    assert "0.0%" in readme_text
    assert "100.0%" in readme_text
    assert "small published release artifact" in readme_text
    assert "reproduce-christian-virtue-qwen2-5-1-5b-local" in readme_text
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
    assert "strongest repo-local result" in scripts_guide
    assert "smallest published package" in scripts_guide
    assert "setup_christian_virtue_local.sh" in scripts_guide
    assert "reproduce_christian_virtue_qwen2_5_1_5b_local.sh" in scripts_guide
    assert "gradio_christian_virtue_chat.py" in scripts_guide
    assert "deploy_christian_virtue_chat_space.py" in scripts_guide
    assert "chat_christian_virtue_model.py" in scripts_guide
    assert "smoke_test_christian_virtue_chat.py" in scripts_guide
    assert "build_christian_virtue_sft_dataset.py" in scripts_guide
    assert "audit_christian_virtue_frontier.py" in scripts_guide
    assert "build_christian_virtue_full_corpus_report.py" in scripts_guide
    assert "build_christian_virtue_citation_frontier_report.py" in scripts_guide
    assert "build_christian_virtue_justice_guarded_report.py" in scripts_guide
    assert "launch_christian_virtue_qwen2_5_1_5b_full_corpus_loop.sh" in scripts_guide
    assert "run_christian_virtue_qwen2_5_1_5b_citation_frontier_audit.sh" in scripts_guide
    assert "make audit-christian-virtue-qwen2-5-1-5b-local-frontier" in scripts_guide
    assert "make gradio-chat-christian-virtue-qwen2-5-1-5b-full-corpus" in scripts_guide
    assert "make deploy-christian-virtue-chat-space" in scripts_guide
    assert "make chat-christian-virtue-qwen2-5-1-5b-full-corpus" in scripts_guide
    assert "make smoke-test-christian-virtue-chat" in scripts_guide
    assert "make launch-christian-virtue-qwen2-5-1-5b-full-corpus-loop" in scripts_guide
    assert "make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop" in scripts_guide
    assert "make report-christian-virtue-qwen2-5-1-5b-full-corpus" in scripts_guide
    assert "make run-christian-virtue-qwen2-5-1-5b-citation-frontier-loop" in scripts_guide
    assert "make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop" in scripts_guide
    assert "make run-christian-virtue-qwen2-5-1-5b-justice-guarded-loop" in scripts_guide
    assert "MPS safety env overrides" in scripts_guide
    assert "prints the key output paths" in scripts_guide


def test_repository_map_names_canonical_public_bundle() -> None:
    repository_map = (REPO_ROOT / "docs" / "repository_map.md").read_text(encoding="utf-8")
    assert "## Canonical Public Bundle" in repository_map
    assert "strongest repo-local result" in repository_map.lower()
    assert "smallest published package" in repository_map.lower()
    assert "christian_virtue_v1" in repository_map
    assert "christian_virtue_citation_frontier_audit.md" in repository_map
    assert "christian_virtue_qwen2_5_1_5b_full_corpus_report.md" in repository_map
    assert "christian_virtue_qwen2_5_1_5b_citation_frontier_report.md" in repository_map
    assert (
        "christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md"
        in repository_map
    )
    assert "qwen2_5_1_5b_instruct_lora_mps_full_corpus.yaml" in repository_map
    assert "qwen2_5_1_5b_instruct_full_corpus_adapter_test.yaml" in repository_map
    assert "scripts/gradio_christian_virtue_chat.py" in repository_map
    assert "scripts/deploy_christian_virtue_chat_space.py" in repository_map
    assert "scripts/smoke_test_christian_virtue_chat.py" in repository_map
    assert "src/summa_moral_graph/app/gradio_chat.py" in repository_map
    assert "app/pages/6_Chat.py" in repository_map
    assert "src/summa_moral_graph/app/chat.py" in repository_map
    assert "src/summa_moral_graph/sft/chat_smoke.py" in repository_map
    assert "build_christian_virtue_full_corpus_report.py" in repository_map
    assert "make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop" in repository_map
    assert "christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md" in repository_map
    assert "qwen2_5_1_5b_instruct_lora_mps_accuracy_first_hybrid.yaml" in repository_map
    assert "qwen2_5_1_5b_instruct_accuracy_first_adapter_test.yaml" in repository_map
    assert "make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop" in repository_map
    assert "make run-christian-virtue-qwen2-5-1-5b-justice-guarded-loop" in repository_map
    assert "local_baseline_adapter/README.md" in repository_map


def test_public_claim_map_mentions_online_chat_surface() -> None:
    claim_map = (REPO_ROOT / "docs" / "public_claim_map.md").read_text(encoding="utf-8")
    assert "jennyzhu0822-summa-virtue-chat.hf.space" in claim_map
    assert "make deploy-christian-virtue-chat-space" in claim_map
    assert "public online chat surface" in claim_map.lower()


def test_secondary_public_docs_name_online_chat_surface() -> None:
    dataset_card = (REPO_ROOT / "docs" / "christian_virtue_dataset_card.md").read_text(
        encoding="utf-8"
    )
    sft_guide = (REPO_ROOT / "docs" / "christian_virtue_sft.md").read_text(encoding="utf-8")
    fine_tune_guide = (
        REPO_ROOT / "docs" / "fine_tune_with_summa_moral_graph.md"
    ).read_text(encoding="utf-8")
    experiments = (
        REPO_ROOT / "docs" / "reports" / "christian_virtue_experiments.md"
    ).read_text(encoding="utf-8")

    for text in (dataset_card, sft_guide, fine_tune_guide, experiments):
        assert "jennyzhu0822-summa-virtue-chat.hf.space" in text
        assert "summa-moral-graph.streamlit.app" in text

    assert "small-model `qwen/qwen2.5-1.5b-instruct`" in dataset_card.lower()
    assert "public interaction" in sft_guide.lower()


def test_fine_tune_guide_names_completed_justice_guarded_follow_up() -> None:
    guide_text = (
        REPO_ROOT / "docs" / "fine_tune_with_summa_moral_graph.md"
    ).read_text(encoding="utf-8")
    assert "## Justice-Guarded Citation-Repair Follow-Up" in guide_text
    assert "make run-christian-virtue-qwen2-5-1-5b-justice-guarded-loop" in guide_text
    assert (
        "christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md"
        in guide_text
    )
    assert "## Accuracy-First Hybrid Follow-Up" in guide_text
    assert "make run-christian-virtue-qwen2-5-1-5b-accuracy-first-loop" in guide_text
    assert "christian_virtue_qwen2_5_1_5b_accuracy_first_hybrid_report.md" in guide_text
    assert "MPS safety env overrides" in guide_text
    assert "41.2%" in guide_text


def test_public_claim_map_mentions_full_corpus_result() -> None:
    claim_map_text = (REPO_ROOT / "docs" / "public_claim_map.md").read_text(encoding="utf-8")
    assert "71.2%" in claim_map_text
    assert "make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop" in claim_map_text
    assert "christian_virtue_qwen2_5_1_5b_full_corpus_report.md" in claim_map_text
    assert "published small-model adapter" in claim_map_text
    assert "run-christian-virtue-qwen2-5-1-5b-full-corpus-loop" in claim_map_text
