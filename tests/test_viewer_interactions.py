from __future__ import annotations

from types import SimpleNamespace

from streamlit.testing.v1 import AppTest

from summa_moral_graph.app.corpus import build_graph_for_edges, graph_html
from summa_moral_graph.viewer.graph_component import render_clickable_graph
from summa_moral_graph.viewer.load import load_viewer_data
from summa_moral_graph.viewer.navigation import (
    ACTIVE_PRESET_KEY,
    ACTIVE_VIEW_KEY,
    CONCEPT_VIEW,
    CONCEPT_ID_KEY,
    MAP_MODE_KEY,
    MAP_PENDING_ACTION_KEY,
    MAP_RANGE_KEY,
    MAP_SELECTED_NODE_KEY,
    MAP_VIEW,
    PASSAGE_ID_KEY,
    STATS_TAB_KEY,
    consume_pending_map_action,
    consume_widget_updates,
    ensure_session_state,
    open_concept,
    open_map,
    open_passage,
    open_stats,
    queue_map_action,
    queue_widget_updates,
    reset_map_filters,
    select_map_node,
    set_active_view,
)
from summa_moral_graph.viewer.shell import _open_overall_map_route, _resolve_download_scope
from summa_moral_graph.viewer.state import (
    available_focus_tags_for_scope,
    concept_payload_for_selection,
    generate_structural_edges_for_range,
    graph_edges_for_view,
    normalize_passage_filter_state,
    passage_results,
    selected_passage_for_results,
)


def test_open_overall_map_route_forces_overall_mode() -> None:
    session_state: dict[str, object] = {
        ACTIVE_VIEW_KEY: "Concept Explorer",
        MAP_MODE_KEY: "Local map",
        ACTIVE_PRESET_KEY: "",
    }

    _open_overall_map_route(
        session_state,
        concept_id="concept.prudence",
        preset_name="prudence:overview",
    )

    assert session_state[ACTIVE_VIEW_KEY] == "Overall Map"
    assert session_state[MAP_MODE_KEY] == "Overall map"
    assert session_state[ACTIVE_PRESET_KEY] == "prudence:overview"
    assert session_state[CONCEPT_ID_KEY] == "concept.prudence"


def test_download_scope_defaults_to_active_preset_but_stays_local() -> None:
    session_state: dict[str, object] = {
        ACTIVE_PRESET_KEY: "prudence:overview",
    }

    resolved = _resolve_download_scope(
        session_state,
        key="smg_home_download_scope",
        fallback_preset_name=str(session_state[ACTIVE_PRESET_KEY]),
    )

    assert resolved == "prudence:overview"
    assert session_state["smg_home_download_scope"] == "prudence:overview"
    assert session_state[ACTIVE_PRESET_KEY] == "prudence:overview"


def test_open_concept_queues_concept_selectbox_widget_sync() -> None:
    session_state: dict[str, object] = {}

    open_concept(session_state, "concept.justice", preset_name="justice:overview")

    assert session_state["smg_pending_concept_selectbox"] == "concept.justice"
    assert session_state["smg_concept_show_relation_labels"] is True


def test_navigation_helpers_keep_cross_view_state_consistent() -> None:
    session_state: dict[str, object] = {}

    open_concept(session_state, "concept.justice", preset_name="justice:overview")
    assert session_state[ACTIVE_VIEW_KEY] == "Concept Explorer"
    assert session_state[CONCEPT_ID_KEY] == "concept.justice"
    assert session_state[ACTIVE_PRESET_KEY] == "justice:overview"
    assert session_state["smg_concept_show_relation_labels"] is True

    open_passage(session_state, "st.ii-ii.q057.a001.resp", preset_name="justice:overview")
    assert session_state[ACTIVE_VIEW_KEY] == "Passage Explorer"
    assert session_state[PASSAGE_ID_KEY] == "st.ii-ii.q057.a001.resp"

    open_stats(session_state, tab_name="Corpus coverage")
    assert session_state[ACTIVE_VIEW_KEY] == "Stats / Audit"
    assert session_state[STATS_TAB_KEY] == "Corpus coverage"


def test_ensure_session_state_normalizes_map_range_values() -> None:
    data = load_viewer_data()
    session_state: dict[str, object] = {
        MAP_RANGE_KEY: [80, 57],
    }

    ensure_session_state(session_state, data)

    assert session_state[MAP_RANGE_KEY] == (57, 80)


def test_ensure_session_state_defaults_relation_labels_to_on() -> None:
    data = load_viewer_data()
    session_state: dict[str, object] = {}

    ensure_session_state(session_state, data)

    assert session_state["smg_map_show_relation_labels"] is True
    assert session_state["smg_concept_show_relation_labels"] is True


def test_set_active_view_resets_concept_relation_labels_to_on() -> None:
    session_state: dict[str, object] = {
        ACTIVE_VIEW_KEY: "Overall Map",
        "smg_concept_show_relation_labels": False,
    }

    set_active_view(session_state, CONCEPT_VIEW)

    assert session_state[ACTIVE_VIEW_KEY] == CONCEPT_VIEW
    assert session_state["smg_concept_show_relation_labels"] is True


def test_open_map_forces_relation_labels_on() -> None:
    session_state: dict[str, object] = {
        ACTIVE_VIEW_KEY: "Concept Explorer",
        MAP_MODE_KEY: "Local map",
        "smg_map_show_relation_labels": False,
    }

    open_map(session_state, concept_id="concept.justice", mode="Overall map")

    assert session_state[ACTIVE_VIEW_KEY] == MAP_VIEW
    assert session_state[MAP_MODE_KEY] == "Overall map"
    assert session_state["smg_map_show_relation_labels"] is True


def test_reset_map_filters_clears_focus_tags_without_losing_mode_or_center() -> None:
    session_state: dict[str, object] = {
        MAP_MODE_KEY: "Overall map",
        "smg_map_center_concept": "concept.justice",
        "smg_map_focus_tags": ["justice_species"],
        "smg_map_relation_groups": ["Opposition"],
        "smg_map_include_candidate": True,
        MAP_RANGE_KEY: (57, 79),
    }

    reset_map_filters(session_state)

    assert session_state[MAP_MODE_KEY] == "Overall map"
    assert session_state["smg_map_center_concept"] == "concept.justice"
    assert session_state["smg_map_focus_tags"] == []
    assert session_state["smg_map_relation_groups"] == []
    assert session_state["smg_map_include_candidate"] is False
    assert session_state[MAP_RANGE_KEY] == (1, 46)


def test_queue_and_consume_pending_map_reset_action() -> None:
    session_state: dict[str, object] = {
        MAP_MODE_KEY: "Overall map",
        "smg_map_center_concept": "concept.justice",
        "smg_map_focus_tags": ["justice_species"],
        "smg_map_relation_groups": ["Opposition"],
        MAP_RANGE_KEY: (57, 79),
    }

    queue_map_action(session_state, "reset_filters")

    assert session_state[MAP_PENDING_ACTION_KEY] == "reset_filters"

    consumed = consume_pending_map_action(session_state)

    assert consumed == "reset_filters"
    assert session_state["smg_map_focus_tags"] == []
    assert session_state[MAP_RANGE_KEY] == (1, 46)
    assert session_state["smg_map_center_concept"] == "concept.justice"


def test_select_map_node_keeps_user_in_map_view() -> None:
    session_state: dict[str, object] = {
        ACTIVE_VIEW_KEY: "Overall Map",
    }

    select_map_node(session_state, "st.ii-ii.q057")

    assert session_state[ACTIVE_VIEW_KEY] == MAP_VIEW
    assert session_state[MAP_SELECTED_NODE_KEY] == "st.ii-ii.q057"


def test_queue_widget_updates_stores_pending_preset_change() -> None:
    session_state: dict[str, object] = {}

    queue_widget_updates(session_state, **{ACTIVE_PRESET_KEY: "prudence:overview"})

    pending = session_state["smg_pending_widget_updates"]
    assert isinstance(pending, dict)
    assert pending[ACTIVE_PRESET_KEY] == "prudence:overview"


def test_consume_widget_updates_keeps_pending_container_available() -> None:
    session_state: dict[str, object] = {}

    queue_widget_updates(session_state, **{ACTIVE_PRESET_KEY: "prudence:overview"})
    consume_widget_updates(session_state)

    assert session_state[ACTIVE_PRESET_KEY] == "prudence:overview"
    assert session_state["smg_pending_widget_updates"] == {}


def test_selected_passage_for_results_resets_to_first_visible_result() -> None:
    data = load_viewer_data()
    results = passage_results(
        data,
        query="prudence",
        part_id=None,
        question_id=None,
        article_id=None,
        segment_type=None,
        preset_name="prudence:overview",
    )
    visible_results = results[:6]
    session_state = {PASSAGE_ID_KEY: "st.ii-ii.q080.a001.resp"}

    selected = selected_passage_for_results(session_state, visible_results, data.bundle)

    assert selected is not None
    assert selected.segment_id == visible_results[0].segment_id


def test_selected_passage_for_results_returns_none_when_result_set_is_empty() -> None:
    data = load_viewer_data()
    session_state = {PASSAGE_ID_KEY: "st.ii-ii.q080.a001.resp"}

    selected = selected_passage_for_results(session_state, [], data.bundle)

    assert selected is None


def test_normalize_passage_filter_state_clears_stale_question_and_article_for_part() -> None:
    data = load_viewer_data()

    filters = normalize_passage_filter_state(
        data,
        part_id="i-ii",
        question_id="st.ii-ii.q057",
        article_id="st.ii-ii.q057.a001",
        preset_name=None,
    )

    assert filters.selected_part == "i-ii"
    assert filters.selected_question == ""
    assert filters.selected_article == ""

    results = passage_results(
        data,
        query="",
        part_id=filters.selected_part or None,
        question_id=filters.selected_question or None,
        article_id=filters.selected_article or None,
        segment_type=None,
        preset_name=None,
    )

    assert results
    assert all(passage.part_id == "i-ii" for passage in results[:25])


def test_normalize_passage_filter_state_respects_tract_scope() -> None:
    data = load_viewer_data()

    filters = normalize_passage_filter_state(
        data,
        part_id="i-ii",
        question_id="st.i-ii.q001",
        article_id="st.i-ii.q001.a001",
        preset_name="prudence:overview",
    )

    assert filters.part_locked is True
    assert filters.selected_part == "ii-ii"
    assert filters.selected_question == ""
    assert filters.selected_article == ""
    assert filters.part_options == ("ii-ii",)
    assert filters.question_options
    assert all(question_id.startswith("st.ii-ii.q0") for question_id in filters.question_options)


def test_passage_explorer_clears_stale_advanced_filters_in_live_shell() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Passage Explorer" in radio.options:
            radio.set_value("Passage Explorer")
            break
    app.run(timeout=30)

    def selectbox(label: str):
        return next(widget for widget in app.selectbox if widget.label == label)

    selectbox("Part").set_value("ii-ii")
    app.run(timeout=30)
    selectbox("Question").set_value("st.ii-ii.q057")
    app.run(timeout=30)
    selectbox("Article").set_value("st.ii-ii.q057.a001")
    app.run(timeout=30)
    selectbox("Part").set_value("i-ii")
    app.run(timeout=30)

    assert not app.exception
    assert selectbox("Question").value == ""
    assert selectbox("Article").value == ""
    assert any(
        button.label.startswith("Open I-II q.")
        for button in app.button
    )


def test_concept_payload_for_selection_preserves_tract_scope_when_empty() -> None:
    data = load_viewer_data()

    payload = concept_payload_for_selection(
        data,
        "concept.justice",
        preset_name="prudence:overview",
    )

    assert payload["scope_mode"] == "tract"
    assert payload["scope_label"] == "Prudence overview (QQ. 47–56)"
    assert payload["broader_corpus_fallback"] is False
    assert payload["reviewed_doctrinal_edges"] == []


def test_concept_payload_for_selection_normalizes_justice_tract_edge_keys() -> None:
    data = load_viewer_data()

    payload = concept_payload_for_selection(
        data,
        "concept.justice",
        preset_name="justice:justice_overview",
    )

    assert payload["scope_mode"] == "tract"
    assert payload["reviewed_incident_edges"]
    assert payload["reviewed_doctrinal_edges"] == payload["reviewed_incident_edges"]
    assert payload["reviewed_structural_edges"] == payload["editorial_correspondences"]


def test_concept_payload_for_selection_normalizes_supporting_passages_and_notes() -> None:
    data = load_viewer_data()

    payload = concept_payload_for_selection(
        data,
        "concept.justice",
        preset_name="justice:justice_overview",
    )

    assert payload["supporting_passages"] == payload["top_supporting_passages"]
    assert (
        payload["ambiguity_notes"] == payload["unresolved_disambiguation_notes"]
    )


def test_generate_structural_edges_for_range_includes_i_ii_and_ii_ii_questions() -> None:
    data = load_viewer_data()

    rows = generate_structural_edges_for_range(
        data.bundle,
        question_id=None,
        map_range=(1, 10),
        center_concept=None,
    )
    subject_ids = {str(row["subject_id"]) for row in rows}

    assert any(subject_id.startswith("st.i-ii.q") for subject_id in subject_ids)
    assert any(subject_id.startswith("st.ii-ii.q") for subject_id in subject_ids)


def test_render_clickable_graph_returns_clicked_concept_when_component_is_available(
    monkeypatch,
) -> None:
    def fake_component(**_: object) -> SimpleNamespace:
        return SimpleNamespace(clicked={"conceptId": "concept.justice"})

    monkeypatch.setattr(
        "summa_moral_graph.viewer.graph_component._graph_component",
        lambda: fake_component,
    )

    result = render_clickable_graph(
        graph_html="<html><body>graph</body></html>",
        height="600px",
        key="test-interactive-graph",
    )

    assert result.interactive is True
    assert result.warning is None
    assert result.clicked_concept_id == "concept.justice"


def test_render_clickable_graph_warns_when_static_fallback_is_used(monkeypatch) -> None:
    calls: list[tuple[int, bool]] = []

    monkeypatch.setattr(
        "summa_moral_graph.viewer.graph_component._graph_component",
        lambda: None,
    )
    monkeypatch.setattr(
        "summa_moral_graph.viewer.graph_component.legacy_components.html",
        lambda graph_html, height, scrolling: calls.append((height, scrolling)),
    )

    result = render_clickable_graph(
        graph_html="<html><body>graph</body></html>",
        height="640px",
        key="test-static-graph",
    )

    assert result.interactive is False
    assert result.clicked_concept_id is None
    assert "static fallback" in str(result.warning).casefold()
    assert calls == [(684, True)]


def test_render_clickable_graph_warns_when_component_raises(monkeypatch) -> None:
    calls: list[tuple[int, bool]] = []

    def fake_component(**_: object) -> SimpleNamespace:
        raise RuntimeError("component blew up")

    monkeypatch.setattr(
        "summa_moral_graph.viewer.graph_component._graph_component",
        lambda: fake_component,
    )
    monkeypatch.setattr(
        "summa_moral_graph.viewer.graph_component.legacy_components.html",
        lambda graph_html, height, scrolling: calls.append((height, scrolling)),
    )

    result = render_clickable_graph(
        graph_html="<html><body>graph</body></html>",
        height="620px",
        key="test-broken-graph",
    )

    assert result.interactive is False
    assert result.clicked_concept_id is None
    assert "static" in str(result.warning).casefold()
    assert calls == [(664, True)]


def test_graph_html_relation_labels_can_be_shown_and_hidden() -> None:
    data = load_viewer_data()
    graph = build_graph_for_edges(data.bundle.reviewed_doctrinal_edges[:1])

    html_without_labels = graph_html(graph, height=320, show_relation_labels=False)
    html_with_labels = graph_html(graph, height=320, show_relation_labels=True)

    assert "directed to" not in html_without_labels
    assert '"label": "directed to"' in html_with_labels


def test_concept_shortcut_button_updates_concept_selection_in_live_shell() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Concept Explorer" in radio.options:
            radio.set_value("Concept Explorer")
            break
    app.run(timeout=30)

    labels = [button.label for button in app.button]
    shortcut_index = labels.index("Abstinence · virtue")
    app.button[shortcut_index].click()
    app.run(timeout=30)

    assert app.selectbox[0].value == "concept.abstinence"


def test_overall_map_view_renders_without_streamlit_exception() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Overall Map" in radio.options:
            radio.set_value("Overall Map")
            break
    app.run(timeout=30)

    assert not app.exception


def test_graph_edges_for_view_combines_cross_family_ranges() -> None:
    data = load_viewer_data()

    edges, reason = graph_edges_for_view(
        data,
        preset_name=None,
        map_range=(57, 122),
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
        local_only=False,
    )

    question_numbers = {
        data.bundle.passages[str(passage_id)].question_number
        for edge in edges
        for passage_id in edge.get("source_passage_ids", [])
        if str(passage_id) in data.bundle.passages
        and data.bundle.passages[str(passage_id)].part_id == "ii-ii"
    }

    assert reason is None
    assert edges
    assert any(57 <= question <= 79 for question in question_numbers)
    assert any(80 <= question <= 100 for question in question_numbers)
    assert any(101 <= question <= 120 for question in question_numbers)


def test_available_focus_tags_for_scope_returns_cross_tract_tags_for_tagged_ranges() -> None:
    data = load_viewer_data()

    tags = available_focus_tags_for_scope(
        data,
        preset_name=None,
        map_range=(57, 122),
    )

    assert "justice_species" in tags
    assert "positive_act" in tags
    assert "authority_due" in tags


def test_available_focus_tags_for_scope_returns_empty_when_span_has_no_tag_taxonomy() -> None:
    data = load_viewer_data()

    theological_tags = available_focus_tags_for_scope(
        data,
        preset_name=None,
        map_range=(1, 46),
    )
    prudence_tags = available_focus_tags_for_scope(
        data,
        preset_name=None,
        map_range=(47, 56),
    )

    assert theological_tags == []
    assert prudence_tags == []


def test_overall_map_quick_span_button_updates_range_without_exception() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Overall Map" in radio.options:
            radio.set_value("Overall Map")
            break
    app.run(timeout=30)

    for button in app.button:
        if button.label == "57–122":
            button.click()
            break
    app.run(timeout=30)

    question_span_values = [
        slider.value for slider in app.slider if getattr(slider, "label", "") == "Question span"
    ]
    assert not app.exception
    assert question_span_values == [(57, 122)]


def test_overall_map_question_span_slider_handles_cross_family_ranges() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Overall Map" in radio.options:
            radio.set_value("Overall Map")
            break
    app.run(timeout=30)

    for slider in app.slider:
        if getattr(slider, "label", "") == "Question span":
            slider.set_value((141, 170))
            break
    app.run(timeout=30)

    question_span_values = [
        slider.value for slider in app.slider if getattr(slider, "label", "") == "Question span"
    ]
    assert not app.exception
    assert question_span_values == [(141, 170)]


def test_overall_map_reset_all_filters_does_not_raise_streamlit_exception() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Overall Map" in radio.options:
            radio.set_value("Overall Map")
            break
    app.run(timeout=30)

    for multiselect in app.multiselect:
        if getattr(multiselect, "label", "") == "Relation groups":
            multiselect.set_value(["Opposition"])
            break
    app.run(timeout=30)

    for button in app.button:
        if button.label == "Reset all filters":
            button.click()
            break
    app.run(timeout=30)

    assert not app.exception


def test_top_nav_overall_map_button_forces_overall_mode() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)
    for radio in app.radio:
        if getattr(radio, "options", None) and "Overall Map" in radio.options:
            radio.set_value("Overall Map")
            break
    app.run(timeout=30)

    for radio in app.radio:
        if getattr(radio, "label", "") == "Map mode":
            radio.set_value("Local map")
            break
    app.run(timeout=30)

    for button in app.button:
        if button.label == "Map":
            button.click()
            break
    app.run(timeout=30)

    map_mode_values = [
        radio.value for radio in app.radio if getattr(radio, "label", "") == "Map mode"
    ]
    assert map_mode_values == ["Overall map"]


def test_home_open_tract_scope_button_does_not_raise_streamlit_exception() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)

    for button in app.button:
        if button.label == "Open tract":
            button.click()
            break
    app.run(timeout=30)

    assert not app.exception
    navigate_values = [
        radio.value
        for radio in app.radio
        if getattr(radio, "options", None) and "Concept Explorer" in radio.options
    ]
    assert navigate_values == ["Concept Explorer"]


def test_home_open_reviewed_map_button_does_not_raise_streamlit_exception() -> None:
    app = AppTest.from_file("streamlit_app.py")
    app.run(timeout=30)

    for button in app.button:
        if button.label == "Open reviewed map":
            button.click()
            break
    app.run(timeout=30)

    assert not app.exception
