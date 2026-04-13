from __future__ import annotations

import importlib.util
from pathlib import Path

from summa_moral_graph.viewer.load import load_viewer_data
from summa_moral_graph.viewer.navigation import (
    ACTIVE_VIEW_KEY,
    STATS_TAB_KEY,
    ensure_session_state,
)
from summa_moral_graph.viewer.registry import (
    adapter_for_preset,
    preset_family,
    preset_label,
    preset_range,
    sorted_preset_names,
)
from summa_moral_graph.viewer.state import (
    active_scope_summary,
    concept_payload_for_selection,
    graph_edges_for_view,
    graph_payload_for_export,
    passage_results,
)


def _load_root_streamlit_module():
    repo_root = Path(__file__).resolve().parent.parent
    module_path = repo_root / "streamlit_app.py"
    spec = importlib.util.spec_from_file_location(
        "summa_moral_graph_root_app",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_streamlit_root_entry_points_at_repo_shell() -> None:
    streamlit_app = _load_root_streamlit_module()

    assert Path(streamlit_app.REPO_ROOT).name == "aquinas"
    assert streamlit_app.SRC_DIR == Path(streamlit_app.REPO_ROOT) / "src"


def test_viewer_load_curates_home_routes() -> None:
    data = load_viewer_data()

    assert data.home_start_concepts
    assert data.home_start_passages
    assert "concept.prudence" in data.home_start_concepts
    assert all(concept_id in data.bundle.registry for concept_id in data.home_start_concepts)
    assert all(passage_id in data.bundle.passages for passage_id in data.home_start_passages)


def test_viewer_preset_registry_exposes_family_range_and_adapter() -> None:
    preset_name = "prudence:overview"

    assert preset_name in sorted_preset_names()
    assert preset_label(preset_name) == "Prudence overview (QQ. 47–56)"
    assert preset_family(preset_name) == "prudence"
    assert preset_range(preset_name) == (47, 56)
    assert adapter_for_preset(preset_name) is not None


def test_active_scope_summary_uses_preset_metadata() -> None:
    scope = active_scope_summary({"smg_active_preset": "prudence:overview"})

    assert scope.label == "Prudence overview (QQ. 47–56)"
    assert scope.family == "prudence"
    assert scope.start_question == 47
    assert scope.end_question == 56


def test_entrypoint_defaults_only_apply_when_entrypoint_changes() -> None:
    data = load_viewer_data()
    session_state: dict[str, object] = {}

    ensure_session_state(
        session_state,
        data,
        default_view="Concept Explorer",
        default_stats_tab="Corpus coverage",
        entrypoint_id="page-concept",
    )
    assert session_state[ACTIVE_VIEW_KEY] == "Concept Explorer"
    assert session_state[STATS_TAB_KEY] == "Corpus coverage"

    session_state[ACTIVE_VIEW_KEY] = "Passage Explorer"
    session_state[STATS_TAB_KEY] = "Validation & review"
    ensure_session_state(
        session_state,
        data,
        default_view="Concept Explorer",
        default_stats_tab="Corpus coverage",
        entrypoint_id="page-concept",
    )
    assert session_state[ACTIVE_VIEW_KEY] == "Passage Explorer"
    assert session_state[STATS_TAB_KEY] == "Validation & review"

    ensure_session_state(
        session_state,
        data,
        default_view="Stats / Audit",
        default_stats_tab="Reader stats",
        entrypoint_id="page-stats",
    )
    assert session_state[ACTIVE_VIEW_KEY] == "Stats / Audit"
    assert session_state[STATS_TAB_KEY] == "Reader stats"


def test_viewer_local_map_requires_center_concept() -> None:
    data = load_viewer_data()

    edges, reason = graph_edges_for_view(
        data,
        preset_name="prudence:overview",
        map_range=(47, 56),
        include_structural=False,
        include_editorial=False,
        include_candidate=False,
        relation_types=None,
        relation_groups=None,
        node_types=None,
        focus_tags=None,
        question_id=None,
        center_concept=None,
        segment_types=None,
        local_only=True,
    )

    assert edges == []
    assert reason == "Pick a center concept to build a local map."


def test_viewer_prudence_slice_supports_concept_passage_and_graph_flow(
    prudence_artifacts: dict[str, object],
) -> None:
    _ = prudence_artifacts
    data = load_viewer_data()

    payload = concept_payload_for_selection(
        data,
        "concept.prudence",
        preset_name="prudence:overview",
    )
    assert payload["reviewed_doctrinal_edges"]
    assert "reviewed_structural_edges" in payload
    assert "candidate_mentions" in payload

    passages = passage_results(
        data,
        query="prudence",
        part_id=None,
        question_id=None,
        article_id=None,
        segment_type=None,
        preset_name="prudence:overview",
    )
    assert passages
    assert all(
        passage.part_id == "ii-ii" and 47 <= passage.question_number <= 56
        for passage in passages[:10]
    )

    edges, reason = graph_edges_for_view(
        data,
        preset_name="prudence:overview",
        map_range=(47, 56),
        include_structural=False,
        include_editorial=False,
        include_candidate=False,
        relation_types=None,
        relation_groups=None,
        node_types=None,
        focus_tags=None,
        question_id=None,
        center_concept="concept.prudence",
        segment_types=None,
        local_only=True,
    )
    assert reason is None
    assert edges
    assert all(edge["layer"] == "reviewed_doctrinal" for edge in edges)

    export_payload = graph_payload_for_export(
        edges,
        scope_label="Prudence overview",
        preset_name="prudence:overview",
        map_range=(47, 56),
        question_id=None,
        center_concept="concept.prudence",
    )
    assert export_payload["counts"]["nodes"] >= 2
    assert export_payload["counts"]["edges"] == len(edges)


def test_viewer_registry_wraps_tract_filters_with_extra_shared_kwargs() -> None:
    data = load_viewer_data()

    edges, reason = graph_edges_for_view(
        data,
        preset_name="theological:faith",
        map_range=(1, 16),
        include_structural=False,
        include_editorial=False,
        include_candidate=False,
        relation_types=None,
        relation_groups=None,
        node_types=None,
        focus_tags={"justice_species"},
        question_id=None,
        center_concept="concept.faith",
        segment_types=None,
        local_only=True,
    )

    assert reason is None
    assert edges
