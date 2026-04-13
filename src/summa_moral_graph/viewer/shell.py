from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, cast

import streamlit as st

from ..app.corpus import (
    build_graph_for_edges,
    candidate_items_for_passage,
    corpus_browser_rows,
    graph_html,
    highlight_passage_text,
    passage_activity_summary,
    reviewed_annotations_for_passage,
    stats_payload,
)
from ..app.ui import (
    MetricCard,
    compact_number,
    dataframe_to_csv_bytes,
    format_edge_option,
    format_question_list,
    payload_to_json_bytes,
    pretty_tag,
    records_frame,
)
from .graph_component import render_clickable_graph, with_graph_click_bridge
from .load import ViewerAppData, load_viewer_data
from .navigation import (
    ACTIVE_PRESET_KEY,
    ACTIVE_VIEW_KEY,
    CONCEPT_ID_KEY,
    CONCEPT_VIEW,
    EDGE_ID_KEY,
    HOME_VIEW,
    MAP_MODE_KEY,
    MAP_VIEW,
    PASSAGE_ID_KEY,
    PASSAGE_VIEW,
    PRIMARY_VIEWS,
    STATS_TAB_KEY,
    STATS_VIEW,
    ensure_session_state,
    open_concept,
    open_map,
    open_passage,
    open_stats,
    set_active_view,
)
from .registry import (
    adapter_for_preset,
    preset_label,
    sorted_preset_names,
)
from .render import (
    card,
    configure_viewer_page,
    empty_state,
    hero,
    info_note,
    key_value_card,
    layer_badges,
    metric_cards,
    pill_row,
    reading_panel,
    section_heading,
    support_card,
    top_nav,
)
from .state import (
    RELATION_GROUPS,
    active_scope_summary,
    concept_matches,
    concept_payload_for_selection,
    graph_edges_for_view,
    graph_focus_counts,
    graph_focus_tag_options,
    graph_payload_for_export,
    graph_relation_type_options,
    graph_rows,
    passage_results,
    relation_groups_for_concept,
    selected_passage_for_results,
    supporting_concepts_for_passage,
)


def _session_state() -> MutableMapping[str, object]:
    return cast(MutableMapping[str, object], st.session_state)


def _route_button(
    *,
    title: str,
    body: str,
    button_label: str,
    key: str,
) -> bool:
    card(title, body)
    return st.button(button_label, key=key, use_container_width=True)


def _scope_pills(data: ViewerAppData) -> list[str]:
    session_state = _session_state()
    scope = active_scope_summary(session_state)
    selected_concept_id = str(session_state.get(CONCEPT_ID_KEY, "") or "")
    selected_passage_id = str(session_state.get(PASSAGE_ID_KEY, "") or "")
    values = [f"Scope: {scope.label}"]
    if selected_concept_id in data.bundle.registry:
        values.append(f"Concept: {data.bundle.registry[selected_concept_id].canonical_label}")
    if selected_passage_id in data.bundle.passages:
        values.append(f"Passage: {data.bundle.passages[selected_passage_id].citation_label}")
    return values


def _relation_counterparty(edge: dict[str, Any], concept_id: str) -> tuple[str, str]:
    if str(edge["subject_id"]) == concept_id:
        return str(edge["object_id"]), str(edge["object_label"])
    return str(edge["subject_id"]), str(edge["subject_label"])


def _graph_html_for_edges(edges: list[dict[str, Any]], *, height: int) -> str:
    graph = build_graph_for_edges(edges)
    return with_graph_click_bridge(graph_html(graph, height=height))


def _support_types_label(edge: dict[str, Any]) -> str:
    support_types = edge.get("support_types", [])
    if isinstance(support_types, list) and support_types:
        return ", ".join(str(value) for value in support_types)
    return "structural"


def render_dashboard(
    *,
    default_view: str | None = None,
    default_stats_tab: str | None = None,
    entrypoint_id: str | None = None,
) -> None:
    configure_viewer_page()
    data = load_viewer_data()
    session_state = _session_state()
    ensure_session_state(
        session_state,
        data,
        default_view=default_view,
        default_stats_tab=default_stats_tab,
        entrypoint_id=entrypoint_id,
    )

    with st.sidebar:
        st.markdown("## Summa Moral Graph")
        st.caption("Aquinas moral corpus")
        current_view = str(session_state[ACTIVE_VIEW_KEY])
        next_view = st.radio(
            "Navigate",
            options=list(PRIMARY_VIEWS),
            index=list(PRIMARY_VIEWS).index(current_view),
            label_visibility="collapsed",
        )
        if next_view != current_view:
            set_active_view(session_state, next_view)
            st.rerun()

        st.selectbox(
            "Tract preset",
            options=["", *sorted_preset_names()],
            format_func=lambda value: "None" if not value else preset_label(value),
            key=ACTIVE_PRESET_KEY,
            help="Shared tract scope used by the concept, passage, and map views.",
        )
        st.caption("Current focus")
        pill_row(_scope_pills(data), tone="accent")
        st.download_button(
            "Download Data",
            data=payload_to_json_bytes(data.dashboard),
            file_name="summa_moral_graph_dashboard_snapshot.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
            key="smg-sidebar-download-data",
        )
        with st.expander("Review and exports", expanded=False):
            st.write(
                "Reviewed tracts: "
                f"{compact_number(int(data.dashboard['summary']['reviewed_tract_blocks']))}"
            )
            st.write(
                "Synthesis exports: "
                f"{compact_number(int(data.dashboard['summary']['synthesis_exports']))}"
            )
            if st.button("Open validation and review", use_container_width=True):
                open_stats(session_state, tab_name="Validation & review")
                st.rerun()

    chosen_view = top_nav(str(session_state[ACTIVE_VIEW_KEY]), PRIMARY_VIEWS)
    if chosen_view != session_state[ACTIVE_VIEW_KEY]:
        set_active_view(session_state, chosen_view)
        st.rerun()

    pill_row(_scope_pills(data), tone="accent")
    info_note(
        "Layers stay separate: doctrine, editorial, structural, candidate."
    )

    active_view = str(session_state[ACTIVE_VIEW_KEY])
    if active_view == HOME_VIEW:
        _render_home(data)
    elif active_view == CONCEPT_VIEW:
        _render_concept_explorer(data)
    elif active_view == PASSAGE_VIEW:
        _render_passage_explorer(data)
    elif active_view == MAP_VIEW:
        _render_map_view(data)
    elif active_view == STATS_VIEW:
        _render_stats_audit(data)


def _render_home(data: ViewerAppData) -> None:
    bundle = data.bundle
    summary = data.dashboard["summary"]
    session_state = _session_state()
    reviewed_concept_count = len(data.reviewed_concept_ids)
    tract_rows = list(data.dashboard["tract_rows"])

    hero_left, hero_right = st.columns((1.3, 0.7), gap="large")
    with hero_left:
        hero(
            "Summa Moral Graph",
            (
                "Browse concepts, passages, tract scopes, and reviewed edges "
                "with evidence traceability."
            ),
            eyebrow="Aquinas moral corpus",
        )
    with hero_right:
        card(
            "Start fast",
            "Concept, passage, tract, or map.",
        )
        st.download_button(
            "Download Data",
            data=payload_to_json_bytes(data.dashboard),
            file_name="summa_moral_graph_dashboard_payload.json",
            mime="application/json",
            use_container_width=True,
            type="primary",
            key="smg-home-download-data",
        )
        if st.button("Open Audit", use_container_width=True):
            open_stats(session_state, tab_name="Reader stats")
            st.rerun()

    metric_cards(
        [
            MetricCard(
                "Parsed passages",
                compact_number(int(summary["passages_parsed"])),
            ),
            MetricCard(
                "Reviewed concepts",
                compact_number(reviewed_concept_count),
            ),
            MetricCard(
                "Reviewed doctrinal edges",
                compact_number(len(bundle.reviewed_doctrinal_edges)),
            ),
            MetricCard(
                "Tract overlays",
                compact_number(int(summary["reviewed_tract_blocks"])),
            ),
        ],
        columns=4,
    )
    pill_row(
        [
            "Evidence traceability is preserved",
            "Candidate layer present in "
            f"{compact_number(len(data.candidate_active_passage_ids))} passages",
            "Default graph view excludes editorial and candidate layers",
        ],
        tone="ok",
    )

    section_heading(
        "Start",
        "Pick a route.",
    )
    route_columns = st.columns(4, gap="large")
    with route_columns[0]:
        concept_options = list(data.home_start_concepts)
        selected_start_concept = st.selectbox(
            "High-value concept",
            options=concept_options,
            format_func=lambda value: bundle.registry[value].canonical_label,
            key="smg_home_start_concept",
            label_visibility="collapsed",
        )
        if _route_button(
            title="Concept",
            body="Read definition, edges, and passages.",
            button_label="Open concept",
            key="smg-home-open-concept",
        ):
            open_concept(session_state, selected_start_concept)
            st.rerun()
    with route_columns[1]:
        selected_start_passage = st.selectbox(
            "Starting passage",
            options=list(data.home_start_passages),
            format_func=lambda value: bundle.passages[value].citation_label,
            key="smg_home_start_passage",
            label_visibility="collapsed",
        )
        if _route_button(
            title="Passage",
            body="Read the text first.",
            button_label="Read passage",
            key="smg-home-open-passage",
        ):
            open_passage(session_state, selected_start_passage)
            st.rerun()
    with route_columns[2]:
        tract_options = sorted_preset_names()
        selected_start_preset = st.selectbox(
            "Tract route",
            options=tract_options,
            format_func=preset_label,
            key="smg_home_start_preset",
            label_visibility="collapsed",
        )
        if _route_button(
            title="Tract",
            body="Open a reviewed doctrinal block.",
            button_label="Open tract in concepts",
            key="smg-home-open-tract",
        ):
            session_state[ACTIVE_PRESET_KEY] = selected_start_preset
            set_active_view(session_state, CONCEPT_VIEW)
            st.rerun()
    with route_columns[3]:
        if _route_button(
            title="Map",
            body="Use local first. Open overall after narrowing.",
            button_label="Open overall map",
            key="smg-home-open-map",
        ):
            chosen_preset = str(session_state.get("smg_home_start_preset") or "")
            if chosen_preset:
                session_state[ACTIVE_PRESET_KEY] = chosen_preset
            open_map(
                session_state,
                concept_id=str(session_state[CONCEPT_ID_KEY]) or None,
            )
            st.rerun()

    lower_left, lower_right = st.columns((1.35, 0.65), gap="large")
    with lower_left:
        section_heading("Snapshot", None)
        chart_left, chart_right = st.columns(2, gap="large")
        with chart_left:
            st.caption("Reviewed edges by tract")
            tract_chart = records_frame(
                sorted(
                    tract_rows,
                    key=lambda row: int(row["reviewed_doctrinal_edges"]),
                    reverse=True,
                )[:8],
                columns=["label", "reviewed_doctrinal_edges"],
                rename={
                    "label": "tract",
                    "reviewed_doctrinal_edges": "reviewed_edges",
                },
            ).set_index("tract")
            st.bar_chart(tract_chart, height=240)
        with chart_right:
            st.caption("Layer mix")
            layer_chart = records_frame(
                [
                    {
                        "layer": "reviewed_doctrine",
                        "count": len(bundle.reviewed_doctrinal_edges),
                    },
                    {
                        "layer": "editorial",
                        "count": len(bundle.reviewed_structural_edges),
                    },
                    {
                        "layer": "candidate_relations",
                        "count": len(bundle.candidate_relations),
                    },
                ]
            ).set_index("layer")
            st.bar_chart(layer_chart, height=240)
    with lower_right:
        section_heading("Use", None)
        st.markdown(
            """
            <div class="smgv-card">
              <ul class="smgv-side-list">
                <li>Read concepts before opening large maps.</li>
                <li>Open passages from evidence cards, not from memory.</li>
                <li>Editorial and candidate layers stay secondary.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("Review workflow", expanded=False):
            summary_rows = data.dashboard["review_priority_rows"][:5]
            st.dataframe(
                records_frame(
                    summary_rows,
                    rename={
                        "tract": "Tract",
                        "packet_target_question": "Packet target",
                        "under_annotated_questions": "Under-annotated",
                        "normalization_risk_count": "Normalization risks",
                    },
                ),
                hide_index=True,
                use_container_width=True,
            )

    with st.expander("Exports", expanded=False):
        st.download_button(
            "Download dashboard payload JSON",
            data=payload_to_json_bytes(data.dashboard),
            file_name="summa_moral_graph_dashboard_payload.json",
            mime="application/json",
            use_container_width=True,
            key="smg-home-export-json",
        )


def _render_concept_explorer(data: ViewerAppData) -> None:
    bundle = data.bundle
    session_state = _session_state()
    preset_name = str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None

    section_heading(
        "Concept Explorer",
        (
            "Start with a concept, read the distinction notes, inspect the "
            "local map, then open supporting passages."
        ),
    )

    controls_left, controls_right = st.columns((0.9, 1.1), gap="large")
    with controls_left:
        query = st.text_input(
            "Search concepts",
            value=str(st.session_state.get("smg_concept_query", "")),
            key="smg_concept_query",
            placeholder="charity, prudence, justice, law, gift of counsel",
        )
    with controls_right:
        node_types = st.multiselect(
            "Node types",
            options=sorted({record.node_type for record in bundle.registry.values()}),
            key="smg_concept_node_types",
        )

    matches = concept_matches(
        data,
        query=query,
        node_types=set(node_types),
        preset_name=preset_name,
    )
    if not matches:
        empty_state(
            "No concepts matched",
            "Broaden the search, clear the tract preset, or remove a node-type filter.",
        )
        return

    selected_concept_id = str(session_state.get(CONCEPT_ID_KEY, "") or "")
    available_concept_ids = [concept_id for concept_id, _ in matches]
    if selected_concept_id not in available_concept_ids:
        selected_concept_id = available_concept_ids[0]
        session_state[CONCEPT_ID_KEY] = selected_concept_id

    nav_column, detail_column = st.columns((0.7, 1.45), gap="large")
    with nav_column:
        section_heading("Browse concepts", "Search stays narrow; the detail panel stays wide.")
        selected_concept_id = st.selectbox(
            "Concept",
            options=available_concept_ids,
            format_func=lambda value: data.concept_label_by_id[value],
            index=available_concept_ids.index(selected_concept_id),
            key="smg_concept_selectbox",
        )
        session_state[CONCEPT_ID_KEY] = selected_concept_id
        for concept_id, label in matches[:10]:
            if concept_id == selected_concept_id:
                continue
            if st.button(label, key=f"smg-concept-shortcut-{concept_id}", use_container_width=True):
                open_concept(session_state, concept_id, preset_name=preset_name)
                st.rerun()

    payload = concept_payload_for_selection(
        data,
        selected_concept_id,
        preset_name=preset_name,
    )
    concept = payload["concept"]
    reviewed_edges = list(payload.get("reviewed_doctrinal_edges", []))
    editorial_edges = list(payload.get("reviewed_structural_edges", []))
    candidate_mentions = list(payload.get("candidate_mentions", []))
    candidate_relations = list(payload.get("candidate_relations", []))
    supporting_passages = list(
        payload.get("supporting_passages", payload.get("top_supporting_passages", []))
    )
    ambiguity_notes = list(
        payload.get("ambiguity_notes", payload.get("unresolved_disambiguation_notes", []))
    )

    with detail_column:
        section_heading(
            str(concept["canonical_label"]),
            str(concept.get("description", "No description available.")),
        )
        pill_row(
            [
                str(concept["node_type"]),
                f"Scope: {active_scope_summary(session_state).label}",
                f"Registry: {concept.get('registry_status', 'reviewed')}",
            ],
            tone="accent",
        )
        if concept.get("aliases"):
            pill_row([f"Alias: {alias}" for alias in concept["aliases"]], tone="candidate")
        if ambiguity_notes:
            key_value_card(
                "Distinctions to keep in view",
                [
                    (f"Note {index}", str(note))
                    for index, note in enumerate(ambiguity_notes, start=1)
                ],
            )

        metric_cards(
            [
                MetricCard(
                    "Reviewed doctrine",
                    compact_number(len(reviewed_edges)),
                    "Incident doctrinal edges in the current scope.",
                ),
                MetricCard(
                    "Editorial correspondences",
                    compact_number(len(editorial_edges)),
                    "Visible, but separate from doctrine.",
                ),
                MetricCard(
                    "Candidate mentions",
                    compact_number(len(candidate_mentions)),
                    "Unreviewed detections touching this concept.",
                ),
                MetricCard(
                    "Supporting passages",
                    compact_number(len(supporting_passages)),
                    "Passage cards available below.",
                ),
            ]
        )

        map_column, summary_column = st.columns((1.05, 0.95), gap="large")
        with map_column:
            section_heading("Local map", "Use the local graph before opening the wider map.")
            include_editorial_map = st.checkbox(
                "Include editorial correspondences in local map",
                key="smg_concept_show_editorial_map",
            )
            local_edges = reviewed_edges + (editorial_edges if include_editorial_map else [])
            if local_edges:
                clicked_concept = render_clickable_graph(
                    graph_html=_graph_html_for_edges(local_edges, height=540),
                    height="560px",
                    key=f"smg-local-map-{selected_concept_id}",
                )
                if clicked_concept:
                    open_concept(
                        session_state,
                        clicked_concept,
                        preset_name=preset_name,
                    )
                    st.rerun()
            else:
                empty_state(
                    "No local reviewed map",
                    (
                        "This concept has no reviewed edges in the current scope. "
                        "Check supporting passages or candidate mentions below."
                    ),
                )
        with summary_column:
            relation_groups = relation_groups_for_concept(
                reviewed_edges,
                concept_id=selected_concept_id,
            )
            key_value_card(
                "Current scope",
                [
                    ("Reviewed groups", compact_number(len(relation_groups))),
                    (
                        "Related questions",
                        format_question_list(list(payload.get("related_questions", []))),
                    ),
                    (
                        "Open in map",
                        "Use the button below to inspect the wider neighborhood.",
                    ),
                ],
            )
            if st.button("Open overall map around this concept", use_container_width=True):
                open_map(
                    session_state,
                    concept_id=selected_concept_id,
                    preset_name=preset_name,
                    mode="Local map",
                )
                st.rerun()

        section_heading("Reviewed doctrinal edges", "Grouped by relation family for close reading.")
        if reviewed_edges:
            for relation_type, edges in relation_groups_for_concept(
                reviewed_edges,
                concept_id=selected_concept_id,
            ):
                with st.expander(f"{pretty_tag(relation_type)} ({len(edges)})", expanded=False):
                    for edge in edges:
                        counterparty_id, counterparty_label = _relation_counterparty(
                            edge,
                            selected_concept_id,
                        )
                        support_card(
                            counterparty_label,
                            body=(edge.get("evidence_snippets") or ["No snippet"])[0],
                            meta=(
                                f"{pretty_tag(relation_type)} · {_support_types_label(edge)} · "
                                f"{len(edge.get('source_passage_ids', []))} passages"
                            ),
                        )
                        action_left, action_mid, action_right = st.columns(3)
                        with action_left:
                            if st.button(
                                f"Open {counterparty_label}",
                                key=f"smg-edge-concept-{edge['edge_id']}",
                                use_container_width=True,
                            ):
                                open_concept(
                                    session_state,
                                    counterparty_id,
                                    preset_name=preset_name,
                                )
                                st.rerun()
                        with action_mid:
                            passage_ids = list(edge.get("source_passage_ids", []))
                            if passage_ids and st.button(
                                "Read passage",
                                key=f"smg-edge-passage-{edge['edge_id']}",
                                use_container_width=True,
                            ):
                                open_passage(
                                    session_state,
                                    str(passage_ids[0]),
                                    preset_name=preset_name,
                                )
                                st.rerun()
                        with action_right:
                            if st.button(
                                "Inspect in map",
                                key=f"smg-edge-map-{edge['edge_id']}",
                                use_container_width=True,
                            ):
                                open_map(
                                    session_state,
                                    concept_id=selected_concept_id,
                                    edge_id=str(edge["edge_id"]),
                                    preset_name=preset_name,
                                    mode="Overall map",
                                )
                                st.rerun()
        else:
            empty_state(
                "No reviewed doctrinal edges in this scope",
                (
                    "The concept may only have editorial correspondences or "
                    "candidate mentions under the current preset."
                ),
            )

        section_heading("Supporting passages", "Passages stay attached to the concept page.")
        if supporting_passages:
            for passage in supporting_passages[:8]:
                support_card(
                    str(passage["citation_label"]),
                    str(passage["text"]),
                    meta=str(passage["passage_id"]),
                )
                if st.button(
                    f"Read {passage['citation_label']}",
                    key=f"smg-support-passage-{passage['passage_id']}",
                    use_container_width=True,
                ):
                    open_passage(
                        session_state,
                        str(passage["passage_id"]),
                        preset_name=preset_name,
                    )
                    st.rerun()
        else:
            empty_state(
                "No supporting passages in view",
                "Broaden the scope or inspect the candidate layer for weaker signals.",
            )

        with st.expander("Editorial correspondences", expanded=False):
            if editorial_edges:
                layer_badges(["reviewed_structural"])
                for edge in editorial_edges:
                    counterparty_id, counterparty_label = _relation_counterparty(
                        edge,
                        selected_concept_id,
                    )
                    support_card(
                        counterparty_label,
                        body=(edge.get("evidence_snippets") or ["No snippet"])[0],
                        meta=f"{pretty_tag(str(edge['relation_type']))} · editorial correspondence",
                    )
                    if st.button(
                        f"Open {counterparty_label}",
                        key=f"smg-editorial-concept-{edge['edge_id']}",
                        use_container_width=True,
                    ):
                        open_concept(
                            session_state,
                            counterparty_id,
                            preset_name=preset_name,
                        )
                        st.rerun()
            else:
                empty_state(
                    "No editorial correspondences",
                    "None are available in the current scope.",
                )

        with st.expander("Candidate layer", expanded=False):
            if candidate_mentions:
                section_heading("Candidate mentions", None)
                mention_frame = records_frame(
                    candidate_mentions,
                    columns=[
                        "passage_id",
                        "matched_text",
                        "proposed_concept_id",
                        "match_method",
                        "confidence",
                    ],
                )
                st.dataframe(mention_frame, hide_index=True, use_container_width=True)
            else:
                st.caption("No candidate mentions in the current scope.")
            if candidate_relations:
                section_heading("Candidate relations", None)
                relation_frame = records_frame(
                    candidate_relations,
                    columns=[
                        "source_passage_id",
                        "subject_id",
                        "relation_type",
                        "object_id",
                        "proposal_method",
                        "confidence",
                    ],
                )
                st.dataframe(relation_frame, hide_index=True, use_container_width=True)
            else:
                st.caption("No candidate relations in the current scope.")


def _render_passage_explorer(data: ViewerAppData) -> None:
    bundle = data.bundle
    session_state = _session_state()
    preset_name = str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None

    section_heading(
        "Passage Explorer",
        (
            "Read the passage first. Filters stay simple up front; detailed "
            "constraints are tucked under advanced controls."
        ),
    )

    query = st.text_input(
        "Search passages",
        key="smg_passage_query",
        placeholder="passage id, citation label, text, or concept label",
    )
    with st.expander("Advanced passage filters", expanded=False):
        left, right = st.columns(2, gap="large")
        with left:
            st.selectbox(
                "Part",
                options=["", "i-ii", "ii-ii"],
                format_func=lambda value: "All parts" if not value else value.upper(),
                key="smg_passage_part",
            )
            st.selectbox(
                "Question",
                options=["", *sorted(bundle.questions)],
                format_func=lambda value: "All questions"
                if not value
                else data.question_label_by_id[value],
                key="smg_passage_question",
            )
        with right:
            article_options = [""] + sorted(
                {
                    passage.article_id
                    for passage in bundle.passages.values()
                    if not st.session_state["smg_passage_question"]
                    or passage.question_id == st.session_state["smg_passage_question"]
                }
            )
            st.selectbox(
                "Article",
                options=article_options,
                format_func=lambda value: "All articles" if not value else value,
                key="smg_passage_article",
            )
            st.selectbox(
                "Segment type",
                options=["", "obj", "sc", "resp", "ad"],
                format_func=lambda value: "All segment types" if not value else value,
                key="smg_passage_segment_type",
            )

    results = passage_results(
        data,
        query=query,
        part_id=str(st.session_state.get("smg_passage_part", "") or "") or None,
        question_id=str(st.session_state.get("smg_passage_question", "") or "") or None,
        article_id=str(st.session_state.get("smg_passage_article", "") or "") or None,
        segment_type=str(st.session_state.get("smg_passage_segment_type", "") or "") or None,
        preset_name=preset_name,
    )
    limit = int(cast(int, session_state.get("smg_passage_limit", 18)))
    visible_results = results[:limit]
    selected_passage = selected_passage_for_results(
        session_state,
        visible_results,
        bundle,
    )

    metric_cards(
        [
            MetricCard(
                "Matches",
                compact_number(len(results)),
                "Passages matching the current search.",
            ),
            MetricCard(
                "Visible results",
                compact_number(len(visible_results)),
                "Cards currently shown in the results column.",
            ),
            MetricCard(
                "Reviewed-active",
                compact_number(
                    sum(
                        1
                        for passage in visible_results
                        if (
                            passage_activity_summary(
                                bundle,
                                passage.segment_id,
                            )["reviewed_annotations"]
                            > 0
                        )
                    )
                ),
                "Visible passages with reviewed support.",
            ),
            MetricCard(
                "Candidate-active",
                compact_number(
                    sum(
                        1
                        for passage in visible_results
                        if (
                            passage_activity_summary(
                                bundle,
                                passage.segment_id,
                            )["candidate_mentions"]
                            > 0
                            or passage_activity_summary(
                                bundle,
                                passage.segment_id,
                            )["candidate_relations"]
                            > 0
                        )
                    )
                ),
                "Visible passages with candidate activity.",
            ),
        ]
    )

    results_column, reader_column = st.columns((0.82, 1.28), gap="large")
    with results_column:
        section_heading("Result list", "Open one result and keep reading on the right.")
        st.slider(
            "Visible result cards",
            min_value=8,
            max_value=40,
            step=2,
            key="smg_passage_limit",
        )
        if not visible_results:
            empty_state(
                "No passages matched",
                "Broaden the query or clear one of the advanced filters.",
            )
        for passage in visible_results:
            counts = passage_activity_summary(bundle, passage.segment_id)
            support_card(
                passage.citation_label,
                body=passage.text,
                meta=(
                    f"{passage.segment_id} · reviewed {counts['reviewed_annotations']} · "
                    f"candidate {counts['candidate_mentions'] + counts['candidate_relations']}"
                ),
            )
            if st.button(
                f"Open {passage.citation_label}",
                key=f"smg-open-passage-{passage.segment_id}",
                use_container_width=True,
            ):
                open_passage(
                    session_state,
                    passage.segment_id,
                    preset_name=preset_name,
                )
                st.rerun()

    with reader_column:
        section_heading(
            "Reading panel",
            (
                "The passage stays primary; linked concepts and relations stay "
                "beneath it."
            ),
        )
        if selected_passage is None:
            empty_state(
                "No passage selected",
                (
                    "Open one result from the left to read the passage and "
                    "inspect its evidence bundle."
                ),
            )
            return
        session_state[PASSAGE_ID_KEY] = selected_passage.segment_id
        reviewed_rows = reviewed_annotations_for_passage(bundle, selected_passage.segment_id)
        candidate_items = candidate_items_for_passage(bundle, selected_passage.segment_id)
        highlighted_html = highlight_passage_text(
            selected_passage.text,
            reviewed_rows,
            candidate_items["mentions"],
        )
        reading_panel(
            selected_passage.citation_label,
            [
                selected_passage.segment_id,
                f"{selected_passage.part_id.upper()} q.{selected_passage.question_number}",
                f"Article {selected_passage.article_number}",
                selected_passage.segment_type,
            ],
            highlighted_html,
        )
        all_result_ids = [passage.segment_id for passage in visible_results]
        previous_id = None
        next_id = None
        if selected_passage.segment_id in all_result_ids:
            index = all_result_ids.index(selected_passage.segment_id)
            previous_id = all_result_ids[index - 1] if index > 0 else None
            next_id = all_result_ids[index + 1] if index < len(all_result_ids) - 1 else None
        nav_left, nav_right = st.columns(2, gap="small")
        with nav_left:
            if previous_id and st.button("Previous passage", use_container_width=True):
                open_passage(session_state, previous_id, preset_name=preset_name)
                st.rerun()
        with nav_right:
            if next_id and st.button("Next passage", use_container_width=True):
                open_passage(session_state, next_id, preset_name=preset_name)
                st.rerun()

        counts = passage_activity_summary(bundle, selected_passage.segment_id)
        metric_cards(
            [
                MetricCard("Reviewed annotations", compact_number(counts["reviewed_annotations"])),
                MetricCard("Candidate mentions", compact_number(counts["candidate_mentions"])),
                MetricCard("Candidate relations", compact_number(counts["candidate_relations"])),
            ],
            columns=3,
        )

        linked = supporting_concepts_for_passage(data, selected_passage.segment_id)
        section_heading(
            "Linked concepts",
            "Reviewed links stay separate from candidate-only mentions.",
        )
        if linked["reviewed"]:
            pill_row(
                [
                    f"Reviewed: {record['label']}"
                    for record in linked["reviewed"][:8]
                ],
                tone="doctrine",
            )
            for record in linked["reviewed"][:8]:
                if st.button(
                    f"Open {record['label']}",
                    key=f"smg-pass-concept-{record['concept_id']}",
                    use_container_width=True,
                ):
                    open_concept(
                        session_state,
                        record["concept_id"],
                        preset_name=preset_name,
                    )
                    st.rerun()
        else:
            st.caption("No reviewed concepts are attached to this passage in the current data.")
        if linked["candidate"]:
            pill_row(
                [f"Candidate: {record['label']}" for record in linked["candidate"][:8]],
                tone="candidate",
            )

        section_heading(
            "Reviewed relations in this passage",
            "Evidence-backed relations appear first.",
        )
        if reviewed_rows:
            for row in reviewed_rows:
                relation_title = (
                    f"{row['subject_label']} · "
                    f"{pretty_tag(str(row['relation_type']))} · "
                    f"{row['object_label']}"
                )
                support_card(
                    relation_title,
                    str(
                        row.get("evidence_rationale")
                        or row.get("evidence_text")
                        or "No rationale"
                    ),
                    meta=f"{row['annotation_id']} · {row['support_type']}",
                )
                action_left, action_mid, action_right = st.columns(3)
                with action_left:
                    if st.button(
                        f"Open {row['subject_label']}",
                        key=f"smg-pass-subject-{row['annotation_id']}",
                        use_container_width=True,
                    ):
                        open_concept(
                            session_state,
                            str(row["subject_id"]),
                            preset_name=preset_name,
                        )
                        st.rerun()
                with action_mid:
                    if st.button(
                        f"Open {row['object_label']}",
                        key=f"smg-pass-object-{row['annotation_id']}",
                        use_container_width=True,
                    ):
                        open_concept(
                            session_state,
                            str(row["object_id"]),
                            preset_name=preset_name,
                        )
                        st.rerun()
                with action_right:
                    if st.button(
                        "Inspect in map",
                        key=f"smg-pass-map-{row['annotation_id']}",
                        use_container_width=True,
                    ):
                        open_map(
                            session_state,
                            concept_id=str(row["subject_id"]),
                            preset_name=preset_name,
                            mode="Overall map",
                        )
                        st.rerun()
        else:
            empty_state(
                "No reviewed relations here",
                "This passage may still carry candidate or structural activity.",
            )

        with st.expander("Candidate layer in this passage", expanded=False):
            if candidate_items["mentions"]:
                st.dataframe(
                    records_frame(candidate_items["mentions"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No candidate mentions in this passage.")
            if candidate_items["relations"]:
                st.dataframe(
                    records_frame(candidate_items["relations"]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No candidate relations in this passage.")


def _render_map_view(data: ViewerAppData) -> None:
    bundle = data.bundle
    session_state = _session_state()
    preset_name = str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None
    current_center = str(session_state.get("smg_map_center_concept", "") or "")
    if not current_center:
        current_center = str(session_state.get(CONCEPT_ID_KEY, "") or "")
        session_state["smg_map_center_concept"] = current_center

    section_heading(
        "Overall Map",
        (
            "Use the local map for a concept-centered read. Use the overall map "
            "only after narrowing the tract or relation family."
        ),
    )
    with st.expander("Map controls", expanded=False):
        control_left, control_mid, control_right = st.columns(3, gap="large")
        with control_left:
            st.radio(
                "Map mode",
                options=["Local map", "Overall map"],
                key=MAP_MODE_KEY,
                horizontal=True,
            )
            st.checkbox(
                "Include structural edges",
                key="smg_map_include_structural",
            )
            st.checkbox(
                "Include editorial correspondences",
                key="smg_map_include_editorial",
            )
            st.checkbox(
                "Include candidate proposals",
                key="smg_map_include_candidate",
            )
        with control_mid:
            st.selectbox(
                "Center concept",
                options=["", *sorted(bundle.registry)],
                format_func=lambda value: (
                    "None" if not value else bundle.registry[value].canonical_label
                ),
                key="smg_map_center_concept",
            )
            st.selectbox(
                "Question spotlight",
                options=["", *sorted(bundle.questions)],
                format_func=lambda value: "None" if not value else data.question_label_by_id[value],
                key="smg_map_question_spotlight",
            )
            st.multiselect(
                "Relation groups",
                options=list(RELATION_GROUPS),
                key="smg_map_relation_groups",
            )
        with control_right:
            st.slider(
                "Custom II-II range",
                min_value=1,
                max_value=182,
                key="smg_map_range",
            )
            st.multiselect(
                "Exact relation types",
                options=graph_relation_type_options(bundle),
                key="smg_map_relation_types",
            )
            st.multiselect(
                "Node types",
                options=sorted(
                    {record.node_type for record in bundle.registry.values()}
                    | {"question", "article"}
                ),
                key="smg_map_node_types",
            )

    include_structural = bool(session_state.get("smg_map_include_structural"))
    include_editorial = bool(session_state.get("smg_map_include_editorial"))
    include_candidate = bool(session_state.get("smg_map_include_candidate"))
    raw_map_range = session_state.get("smg_map_range", (1, 46))
    map_range = cast(tuple[int, int], raw_map_range)
    map_question = str(session_state.get("smg_map_question_spotlight", "") or "") or None
    center_concept = str(session_state.get("smg_map_center_concept", "") or "") or None
    relation_types = set(
        cast(list[str], session_state.get("smg_map_relation_types", []))
    )
    relation_groups = set(
        cast(list[str], session_state.get("smg_map_relation_groups", []))
    )
    node_types = set(cast(list[str], session_state.get("smg_map_node_types", [])))
    focus_tags = set(cast(list[str], session_state.get("smg_map_focus_tags", [])))
    segment_types = set(
        cast(list[str], session_state.get("smg_map_segment_types", []))
    )
    map_mode = str(session_state.get(MAP_MODE_KEY, "Overall map"))

    local_edges, local_reason = graph_edges_for_view(
        data,
        preset_name=preset_name,
        map_range=map_range,
        include_structural=False,
        include_editorial=include_editorial,
        include_candidate=False,
        relation_types=relation_types or None,
        relation_groups=relation_groups or None,
        node_types=node_types or None,
        focus_tags=focus_tags or None,
        question_id=map_question,
        center_concept=center_concept,
        segment_types=segment_types or None,
        local_only=True,
    )
    overall_edges, overall_reason = graph_edges_for_view(
        data,
        preset_name=preset_name,
        map_range=map_range,
        include_structural=include_structural,
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types or None,
        relation_groups=relation_groups or None,
        node_types=node_types or None,
        focus_tags=focus_tags or None,
        question_id=map_question,
        center_concept=None if map_mode == "Overall map" else center_concept,
        segment_types=segment_types or None,
        local_only=False,
    )
    visible_edges = local_edges if map_mode == "Local map" else overall_edges
    visible_reason = local_reason if map_mode == "Local map" else overall_reason

    available_focus_tags = graph_focus_tag_options(overall_edges or local_edges)
    if available_focus_tags:
        st.multiselect(
            "Focus tags",
            options=available_focus_tags,
            format_func=pretty_tag,
            key="smg_map_focus_tags",
        )
    st.multiselect(
        "Evidence segment types",
        options=["obj", "sc", "resp", "ad"],
        key="smg_map_segment_types",
        help="Filter edges by the segment types of their supporting passages.",
    )

    metric_cards(
        [
            MetricCard(
                "Visible edges",
                compact_number(len(visible_edges)),
                f"{map_mode} after filters.",
            ),
            MetricCard(
                "Visible nodes",
                compact_number(
                    len(
                        {str(edge["subject_id"]) for edge in visible_edges}
                        | {str(edge["object_id"]) for edge in visible_edges}
                    )
                ),
                "Distinct nodes touched by the current slice.",
            ),
            MetricCard(
                "Doctrinal edges",
                compact_number(
                    sum(
                        1
                        for edge in visible_edges
                        if edge["layer"] == "reviewed_doctrinal"
                    )
                ),
                "Default public graph layer.",
            ),
            MetricCard(
                "Non-doctrinal overlays",
                compact_number(
                    sum(
                        1
                        for edge in visible_edges
                        if edge["layer"] != "reviewed_doctrinal"
                    )
                ),
                "Editorial, structural, or candidate layers currently visible.",
            ),
        ]
    )

    if visible_reason:
        empty_state("Map needs one more step", visible_reason)
        return

    if not visible_edges:
        empty_state(
            "No edges in this slice",
            (
                "Broaden the preset or range, clear a relation filter, or "
                "switch off one of the stricter toggles."
            ),
        )
        return

    if len(visible_edges) > 280 and map_mode == "Overall map":
        empty_state(
            "Overall map paused",
            (
                "This slice is too large to read responsibly. Narrow it with a "
                "tract preset, a question spotlight, or a center concept."
            ),
        )
    else:
        graph_column, evidence_column = st.columns((1.35, 0.88), gap="large")
        with graph_column:
            section_heading(map_mode, "Click a node to jump back into the concept page.")
            clicked_concept = render_clickable_graph(
                graph_html=_graph_html_for_edges(visible_edges, height=720),
                height="740px",
                key=f"smg-map-{map_mode}",
            )
            if clicked_concept:
                open_concept(session_state, clicked_concept, preset_name=preset_name)
                st.rerun()
            node_rows, edge_rows = graph_rows(visible_edges)
            export_left, export_mid, export_right = st.columns(3, gap="small")
            with export_left:
                st.download_button(
                    "Download edges",
                    data=dataframe_to_csv_bytes(records_frame(edge_rows)),
                    file_name="summa_moral_graph_current_edges.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with export_mid:
                st.download_button(
                    "Download nodes",
                    data=dataframe_to_csv_bytes(records_frame(node_rows)),
                    file_name="summa_moral_graph_current_nodes.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with export_right:
                st.download_button(
                    "Download map snapshot",
                    data=payload_to_json_bytes(
                        graph_payload_for_export(
                            visible_edges,
                            scope_label=active_scope_summary(session_state).label,
                            preset_name=preset_name,
                            map_range=map_range,
                            question_id=map_question,
                            center_concept=center_concept,
                        )
                    ),
                    file_name="summa_moral_graph_map_snapshot.json",
                    mime="application/json",
                    use_container_width=True,
                )
        with evidence_column:
            section_heading(
                "Legend and evidence",
                "Graph colors indicate layer and node type, not certainty alone.",
            )
            layer_badges(["reviewed_doctrinal", "reviewed_structural", "structural", "candidate"])
            focus_counts = graph_focus_counts(visible_edges)
            if focus_counts:
                pill_row(
                    [f"{pretty_tag(tag)} ({count})" for tag, count in focus_counts.most_common(5)],
                    tone="candidate",
                )
            edge_by_id = {str(edge["edge_id"]): edge for edge in visible_edges}
            current_edge_id = str(session_state.get(EDGE_ID_KEY, "") or "")
            if current_edge_id not in edge_by_id:
                current_edge_id = next(iter(edge_by_id))
                session_state[EDGE_ID_KEY] = current_edge_id
            selected_edge_id = st.selectbox(
                "Evidence spotlight",
                options=list(edge_by_id),
                format_func=lambda value: format_edge_option(edge_by_id[value]),
                index=list(edge_by_id).index(current_edge_id),
                key="smg-map-edge-select",
            )
            session_state[EDGE_ID_KEY] = selected_edge_id
            selected_edge = edge_by_id[selected_edge_id]
            adapter = adapter_for_preset(preset_name)
            if selected_edge["layer"] == "structural":
                panel = {
                    "source_concept": selected_edge["subject_label"],
                    "relation_type": selected_edge["relation_type"],
                    "target_concept": selected_edge["object_label"],
                    "support_type": ["structural"],
                    "supporting_annotation_ids": [],
                    "supporting_passage_ids": [],
                    "evidence_snippets": [],
                    "layer": "structural",
                    "passages": [],
                }
            elif adapter is not None:
                panel = adapter.edge_evidence_panel(
                    bundle,
                    selected_edge_id,
                    edge_row=selected_edge,
                )
            else:
                panel = {
                    "source_concept": selected_edge["subject_label"],
                    "relation_type": selected_edge["relation_type"],
                    "target_concept": selected_edge["object_label"],
                    "support_type": selected_edge.get("support_types", []),
                    "supporting_annotation_ids": selected_edge.get("support_annotation_ids", []),
                    "supporting_passage_ids": selected_edge.get("source_passage_ids", []),
                    "evidence_snippets": selected_edge.get("evidence_snippets", []),
                    "layer": selected_edge["layer"],
                    "passages": [
                        {
                            "passage_id": passage_id,
                            "citation_label": bundle.passages[passage_id].citation_label,
                            "text": bundle.passages[passage_id].text,
                        }
                        for passage_id in selected_edge.get("source_passage_ids", [])
                        if passage_id in bundle.passages
                    ],
                }
            key_value_card(
                "Selected relation",
                [
                    ("Source", str(panel["source_concept"])),
                    ("Relation", pretty_tag(str(panel["relation_type"]))),
                    ("Target", str(panel["target_concept"])),
                    (
                        "Support type",
                        ", ".join(str(value) for value in panel.get("support_type", [])) or "None",
                    ),
                    (
                        "Annotation ids",
                        ", ".join(
                            str(value)
                            for value in panel.get("supporting_annotation_ids", [])
                        )
                        or "None",
                    ),
                    (
                        "Passage ids",
                        ", ".join(str(value) for value in panel.get("supporting_passage_ids", []))
                        or "None",
                    ),
                ],
            )
            snippets = list(panel.get("evidence_snippets", []))
            if snippets:
                section_heading("Evidence snippets", None)
                for snippet in snippets[:5]:
                    support_card("Snippet", str(snippet))
            passages = list(panel.get("passages", []))
            if passages:
                section_heading("Supporting passages", None)
                for passage in passages[:3]:
                    support_card(
                        str(passage["citation_label"]),
                        str(passage["text"]),
                        meta=str(passage["passage_id"]),
                    )
                    if st.button(
                        f"Read {passage['citation_label']}",
                        key=f"smg-map-passage-{passage['passage_id']}",
                        use_container_width=True,
                    ):
                        open_passage(
                            session_state,
                            str(passage["passage_id"]),
                            preset_name=preset_name,
                        )
                        st.rerun()
            action_left, action_right = st.columns(2, gap="small")
            with action_left:
                if st.button("Open source concept", use_container_width=True):
                    open_concept(
                        session_state,
                        str(selected_edge["subject_id"]),
                        preset_name=preset_name,
                    )
                    st.rerun()
            with action_right:
                if st.button("Open target concept", use_container_width=True):
                    open_concept(
                        session_state,
                        str(selected_edge["object_id"]),
                        preset_name=preset_name,
                    )
                    st.rerun()


def _render_stats_audit(data: ViewerAppData) -> None:
    bundle = data.bundle
    payload = stats_payload(bundle)
    session_state = _session_state()
    section_heading(
        "Stats / Audit",
        (
            "Reader-facing paths live elsewhere. This page keeps corpus "
            "coverage, validation, and review pressure visible without "
            "leading the app."
        ),
    )

    tab_names = ["Reader stats", "Corpus coverage", "Validation & review"]
    current_tab = str(session_state.get(STATS_TAB_KEY, "Reader stats"))
    selected_tab = st.radio(
        "Stats tabs",
        options=tab_names,
        index=tab_names.index(current_tab) if current_tab in tab_names else 0,
        horizontal=True,
        label_visibility="collapsed",
    )
    session_state[STATS_TAB_KEY] = selected_tab

    if selected_tab == "Reader stats":
        metric_cards(
            [
                MetricCard(
                    "Parsed questions",
                    compact_number(int(payload["summary"]["questions_parsed"])),
                    "Structurally parsed questions inside scope.",
                ),
                MetricCard(
                    "Reviewed annotations",
                    compact_number(int(payload["summary"]["reviewed_annotations"])),
                    "Reviewed support records across overlays.",
                ),
                MetricCard(
                    "Candidate mentions",
                    compact_number(int(payload["summary"]["candidate_mentions"])),
                    "Candidate review layer across the corpus.",
                ),
                MetricCard(
                    "Parse failures",
                    compact_number(int(payload["summary"]["parse_failure_count"])),
                    "Questions or articles still flagged as failed.",
                ),
            ]
        )
        left, right = st.columns(2, gap="large")
        with left:
            section_heading("Concept mix", None)
            st.dataframe(
                records_frame(
                    [
                        {"node_type": key, "count": value}
                        for key, value in payload["concept_type_counts"].items()
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
        with right:
            section_heading("Reviewed doctrinal relation types", None)
            st.dataframe(
                records_frame(
                    [
                        {"relation_type": key, "count": value}
                        for key, value in payload["reviewed_relation_type_counts"].items()
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )
    elif selected_tab == "Corpus coverage":
        with st.expander("Coverage filters", expanded=False):
            left, right = st.columns(2, gap="large")
            with left:
                st.selectbox(
                    "Part",
                    options=["", "i-ii", "ii-ii"],
                    format_func=lambda value: "All parts" if not value else value.upper(),
                    key="smg_stats_coverage_part",
                )
                st.multiselect(
                    "Parse status",
                    options=["parsed", "partial", "failed", "excluded"],
                    key="smg_stats_coverage_status",
                )
            with right:
                st.text_input(
                    "Question title search",
                    key="smg_stats_coverage_query",
                    placeholder="law, grace, justice, charity",
                )
        rows = corpus_browser_rows(
            bundle,
            level="question",
            part_id=str(session_state.get("smg_stats_coverage_part", "") or "") or None,
        )
        statuses = set(
            cast(list[str], session_state.get("smg_stats_coverage_status", []))
        )
        if statuses:
            rows = [row for row in rows if str(row["parse_status"]) in statuses]
        query = str(session_state.get("smg_stats_coverage_query", "") or "").casefold()
        if query:
            rows = [
                row
                for row in rows
                if query in str(row["question_title"]).casefold()
                or query in str(row["question_id"]).casefold()
            ]
        metric_cards(
            [
                MetricCard("Visible questions", compact_number(len(rows))),
                MetricCard(
                    "Parsed",
                    compact_number(sum(1 for row in rows if row["parse_status"] == "parsed")),
                ),
                MetricCard(
                    "Partial",
                    compact_number(sum(1 for row in rows if row["parse_status"] == "partial")),
                ),
                MetricCard(
                    "Excluded",
                    compact_number(sum(1 for row in rows if row["parse_status"] == "excluded")),
                ),
            ]
        )
        st.dataframe(
            records_frame(
                [
                    {
                        **row,
                        "missing_article_numbers": format_question_list(
                            list(row["missing_article_numbers"])
                        ),
                    }
                    for row in rows
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        review_rows = data.dashboard["review_priority_rows"]
        tract_rows = data.dashboard["tract_rows"]
        metric_cards(
            [
                MetricCard(
                    "Reviewed tract blocks",
                    compact_number(int(data.dashboard["summary"]["reviewed_tract_blocks"])),
                ),
                MetricCard(
                    "Validation OK",
                    compact_number(int(data.dashboard["summary"]["ok_validation_blocks"])),
                ),
                MetricCard(
                    "Synthesis exports",
                    compact_number(int(data.dashboard["summary"]["synthesis_exports"])),
                ),
            ],
            columns=3,
        )
        section_heading("Review pressure", None)
        st.dataframe(
            records_frame(review_rows),
            use_container_width=True,
            hide_index=True,
        )
        section_heading("Reviewed tract overlays", None)
        st.dataframe(
            records_frame(tract_rows),
            use_container_width=True,
            hide_index=True,
        )
