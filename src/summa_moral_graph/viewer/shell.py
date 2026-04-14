from __future__ import annotations

from collections.abc import MutableMapping
from textwrap import shorten
from typing import Any, Literal, cast

import altair as alt
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
    MAP_RANGE_KEY,
    MAP_SELECTED_NODE_KEY,
    MAP_VIEW,
    PASSAGE_ID_KEY,
    PASSAGE_VIEW,
    PRIMARY_VIEWS,
    STATS_TAB_KEY,
    STATS_VIEW,
    consume_pending_map_action,
    consume_widget_updates,
    ensure_session_state,
    normalize_map_range,
    open_concept,
    open_map,
    open_passage,
    open_stats,
    queue_map_action,
    queue_widget_updates,
    select_map_node,
    set_active_view,
)
from .registry import (
    adapter_for_preset,
    preset_label,
    preset_range,
    sorted_preset_names,
)
from .render import (
    configure_viewer_page,
    empty_state,
    hero,
    info_note,
    key_value_card,
    layer_badges,
    meta_line,
    metric_cards,
    pager_chip,
    pill_row,
    reading_panel,
    section_heading,
    support_card,
    top_nav,
)
from .state import (
    RELATION_GROUPS,
    active_scope_summary,
    available_focus_tags_for_scope,
    concept_matches,
    concept_payload_for_selection,
    graph_edges_for_view,
    graph_focus_counts,
    graph_payload_for_export,
    graph_relation_type_options,
    graph_rows,
    normalize_passage_filter_state,
    passage_results,
    relation_groups_for_concept,
    selected_passage_for_results,
    supporting_concepts_for_passage,
)

SUMMA_STRUCTURE_URL = "https://en.wikipedia.org/wiki/Summa_Theologica"


def _session_state() -> MutableMapping[str, object]:
    return cast(MutableMapping[str, object], st.session_state)

def _route_intro(
    *,
    title: str,
    body: str,
    badge: str,
) -> None:
    st.markdown(
        (
            "<div class='smgv-route-card-head'>"
            f"<div class='smgv-route-index'>{badge}</div>"
            f"<div class='smgv-route-title'>{title}</div>"
            f"<div class='smgv-route-copy'>{body}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _route_button(
    *,
    button_label: str,
    key: str,
    button_type: Literal["primary", "secondary", "tertiary"] = "secondary",
    disabled: bool = False,
) -> bool:
    return st.button(
        button_label,
        key=key,
        use_container_width=True,
        type=button_type,
        disabled=disabled,
    )


def _route_preview_map() -> None:
    st.markdown(
        (
            "<div class='smgv-route-preview smgv-route-preview--map' aria-hidden='true'>"
            "<div class='smgv-route-preview-surface'>"
            "<svg class='smgv-route-map-svg' viewBox='0 0 520 220' role='img' "
            "aria-label='Static preview of the interactive concept graph'>"
            "<defs>"
            "<linearGradient id='smgv-map-stroke' x1='0%' x2='100%' y1='0%' y2='0%'>"
            "<stop offset='0%' stop-color='#214b66' stop-opacity='0.34'/>"
            "<stop offset='100%' stop-color='#8b442e' stop-opacity='0.42'/>"
            "</linearGradient>"
            "<radialGradient id='smgv-map-node-light' cx='35%' cy='30%' r='75%'>"
            "<stop offset='0%' stop-color='#ffffff'/>"
            "<stop offset='100%' stop-color='#e9e0d4'/>"
            "</radialGradient>"
            "<radialGradient id='smgv-map-node-core' cx='35%' cy='30%' r='75%'>"
            "<stop offset='0%' stop-color='#fefefe'/>"
            "<stop offset='100%' stop-color='#d7e6ef'/>"
            "</radialGradient>"
            "</defs>"
            "<line x1='112' y1='94' x2='240' y2='72' stroke='url(#smgv-map-stroke)' "
            "stroke-width='4' stroke-linecap='round'/>"
            "<line x1='240' y1='72' x2='356' y2='100' stroke='url(#smgv-map-stroke)' "
            "stroke-width='4' stroke-linecap='round'/>"
            "<line x1='136' y1='150' x2='258' y2='126' stroke='url(#smgv-map-stroke)' "
            "stroke-width='4' stroke-linecap='round'/>"
            "<line x1='258' y1='126' x2='376' y2='148' stroke='url(#smgv-map-stroke)' "
            "stroke-width='4' stroke-linecap='round'/>"
            "<line x1='240' y1='72' x2='258' y2='126' stroke='url(#smgv-map-stroke)' "
            "stroke-width='4' stroke-linecap='round'/>"
            "<circle cx='112' cy='94' r='18' fill='url(#smgv-map-node-light)' "
            "stroke='#142235' stroke-opacity='0.12' stroke-width='2'/>"
            "<circle cx='240' cy='72' r='21' fill='url(#smgv-map-node-core)' "
            "stroke='#214b66' stroke-opacity='0.18' stroke-width='2'/>"
            "<circle cx='356' cy='100' r='18' fill='url(#smgv-map-node-light)' "
            "stroke='#142235' stroke-opacity='0.12' stroke-width='2'/>"
            "<circle cx='136' cy='150' r='16' fill='url(#smgv-map-node-light)' "
            "stroke='#142235' stroke-opacity='0.11' stroke-width='2'/>"
            "<circle cx='258' cy='126' r='18' fill='url(#smgv-map-node-light)' "
            "stroke='#142235' stroke-opacity='0.12' stroke-width='2'/>"
            "<circle cx='376' cy='148' r='16' fill='url(#smgv-map-node-light)' "
            "stroke='#142235' stroke-opacity='0.11' stroke-width='2'/>"
            "</svg>"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


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


def _summa_structure_note_html() -> str:
    def linked(token: str) -> str:
        return (
            f"<a href='{SUMMA_STRUCTURE_URL}' target='_blank' rel='noopener noreferrer'>"
            f"{token}</a>"
        )

    return (
        f"Only <strong>{linked('resp')}</strong> and <strong>{linked('ad')}</strong> "
        "are included here as Thomas's own answer; "
        f"no {linked('obj')} or {linked('sc')} opening objections are included."
    )


def _relation_counterparty(edge: dict[str, Any], concept_id: str) -> tuple[str, str]:
    if str(edge["subject_id"]) == concept_id:
        return str(edge["object_id"]), str(edge["object_label"])
    return str(edge["subject_id"]), str(edge["subject_label"])


def _question_for_article(bundle: Any, article_id: str) -> str | None:
    for passage in bundle.passages.values():
        if passage.article_id == article_id:
            return str(passage.question_id)
    return None


def _current_tract_rows(
    tract_rows: list[dict[str, Any]],
    *,
    preset_name: str | None,
) -> list[dict[str, Any]]:
    if not preset_name:
        return tract_rows
    start_question, end_question = preset_range(preset_name)
    return [
        row
        for row in tract_rows
        if int(row["start_question"]) <= start_question <= end_question <= int(row["end_question"])
    ]


def _scope_aware_reviewed_edges(
    data: ViewerAppData,
    *,
    preset_name: str | None,
) -> list[dict[str, Any]]:
    if not preset_name:
        return list(data.bundle.reviewed_doctrinal_edges)
    adapter = adapter_for_preset(preset_name)
    if adapter is None:
        return list(data.bundle.reviewed_doctrinal_edges)
    return adapter.filter_edges_by_preset(
        data.bundle,
        preset_name.split(":", 1)[1],
        include_editorial=False,
        include_candidate=False,
        relation_types=None,
        node_types=None,
        center_concept=None,
        focus_tags=None,
    )


def _download_config_for_scope(
    data: ViewerAppData,
    *,
    preset_name: str | None,
    export_target: str,
) -> tuple[bytes, str, str, str]:
    tract_rows = _current_tract_rows(list(data.dashboard["tract_rows"]), preset_name=preset_name)
    reviewed_edges = _scope_aware_reviewed_edges(data, preset_name=preset_name)
    scope_note = (
        f"Current tract preset: {preset_label(preset_name)}"
        if preset_name
        else "Scope: full corpus"
    )

    if export_target == "Corpus summary (JSON)":
        return (
            payload_to_json_bytes(data.dashboard),
            "summa_moral_graph_dashboard_payload.json",
            "application/json",
            "Full corpus snapshot · not limited by tract preset",
        )
    if export_target == "Tract coverage (CSV)":
        return (
            dataframe_to_csv_bytes(records_frame(tract_rows)),
            "summa_moral_graph_tract_coverage.csv",
            "text/csv",
            scope_note,
        )
    return (
        dataframe_to_csv_bytes(records_frame(reviewed_edges)),
        "summa_moral_graph_reviewed_edges.csv",
        "text/csv",
        (
            f"{scope_note} · "
            f"{compact_number(len(reviewed_edges))} reviewed doctrinal edges"
        ),
    )


def _resolve_download_scope(
    session_state: MutableMapping[str, object],
    *,
    key: str,
    fallback_preset_name: str | None,
) -> str | None:
    options = {"", *sorted_preset_names()}
    current_value = str(session_state.get(key, "") or "")
    if key not in session_state or current_value not in options:
        session_state[key] = fallback_preset_name if fallback_preset_name in options else ""
    resolved = str(session_state.get(key, "") or "")
    return resolved or None


def _render_download_panel(
    data: ViewerAppData,
    *,
    panel_key: str,
    fallback_preset_name: str | None,
    stats_button_label: str | None = None,
) -> None:
    session_state = _session_state()
    preset_key = f"{panel_key}_download_scope"
    export_key = f"{panel_key}_export_target"
    download_key = f"{panel_key}_download_button"
    stats_key = f"{panel_key}_open_stats"

    _resolve_download_scope(
        session_state,
        key=preset_key,
        fallback_preset_name=fallback_preset_name,
    )

    st.markdown(
        (
            "<div class='smgv-download-note'>"
            "Choose the tract preset for this file here. It only changes the export."
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    preset_tab, file_tab = st.tabs(["Tract preset", "Export type"])
    with preset_tab:
        st.selectbox(
            "For this download",
            options=["", *sorted_preset_names()],
            format_func=lambda value: "Full corpus" if not value else preset_label(value),
            key=preset_key,
        )
        st.caption("Download scope only.")
    with file_tab:
        st.selectbox(
            "File",
            options=[
                "Reviewed graph edges (CSV)",
                "Tract coverage (CSV)",
                "Corpus summary (JSON)",
            ],
            key=export_key,
            label_visibility="collapsed",
        )

    export_data, export_name, export_mime, export_scope_note = _download_config_for_scope(
        data,
        preset_name=str(session_state.get(preset_key, "") or "") or None,
        export_target=str(session_state.get(export_key, "Reviewed graph edges (CSV)") or ""),
    )
    st.caption(export_scope_note)
    st.download_button(
        "Download data",
        data=export_data,
        file_name=export_name,
        mime=export_mime,
        use_container_width=True,
        type="primary",
        key=download_key,
    )
    if stats_button_label:
        if st.button(
            stats_button_label,
            key=stats_key,
            use_container_width=True,
        ):
            open_stats(session_state, tab_name="Reader stats")
            st.rerun()


def _graph_html_for_edges(
    edges: list[dict[str, Any]],
    *,
    height: int,
    show_relation_labels: bool = False,
) -> str:
    graph = build_graph_for_edges(edges)
    return with_graph_click_bridge(
        graph_html(graph, height=height, show_relation_labels=show_relation_labels)
    )


def _support_types_label(edge: dict[str, Any]) -> str:
    support_types = edge.get("support_types", [])
    if isinstance(support_types, list) and support_types:
        return ", ".join(str(value) for value in support_types)
    return "structural"


def _home_bar_chart(
    rows: list[dict[str, Any]],
    *,
    x_field: str,
    y_field: str,
    color: str,
) -> alt.Chart:
    frame = records_frame(rows)
    return cast(
        alt.Chart,
        alt.Chart(frame)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=color)
        .encode(
            x=alt.X(f"{x_field}:N", sort="-y", axis=alt.Axis(labelAngle=-28, title=None)),
            y=alt.Y(f"{y_field}:Q", axis=alt.Axis(title=None, grid=True, tickCount=4)),
            tooltip=[x_field, y_field],
        )
        .properties(height=238)
        .configure_view(strokeOpacity=0)
        .configure_axis(
            labelColor="#5f6f82",
            domainColor="rgba(20,34,53,0.12)",
            gridColor="rgba(20,34,53,0.08)",
            tickColor="rgba(20,34,53,0.08)",
        )
        .configure(background="transparent"),
    )


def _open_overall_map_route(
    session_state: MutableMapping[str, object],
    *,
    concept_id: str | None = None,
    preset_name: str | None = None,
    edge_id: str | None = None,
) -> None:
    open_map(
        session_state,
        concept_id=concept_id,
        edge_id=edge_id,
        preset_name=preset_name,
        mode="Overall map",
    )


def _map_filter_pills(
    *,
    map_mode: str,
    map_range: tuple[int, int],
    map_question: str | None,
    relation_groups: set[str],
    relation_types: set[str],
    node_types: set[str],
    focus_tags: set[str],
    segment_types: set[str],
    include_structural: bool,
    include_editorial: bool,
    include_candidate: bool,
) -> list[str]:
    pills = [f"Mode: {map_mode}", f"Range: {map_range[0]}–{map_range[1]}"]
    if map_question:
        pills.append(f"Question spotlight: {map_question}")
    if relation_groups:
        pills.append(f"Relation groups: {len(relation_groups)}")
    if relation_types:
        pills.append(f"Exact relations: {len(relation_types)}")
    if node_types:
        pills.append(f"Node types: {len(node_types)}")
    if focus_tags:
        pills.append("Focus tags active")
    if segment_types:
        pills.append(f"Segment types: {', '.join(sorted(segment_types))}")
    if include_editorial:
        pills.append("Editorial on")
    if include_structural:
        pills.append("Structural on")
    if include_candidate:
        pills.append("Candidate on")
    return pills


def _map_empty_state_body(
    *,
    base_message: str,
    focus_tags: set[str],
    relation_groups: set[str],
    relation_types: set[str],
    node_types: set[str],
    segment_types: set[str],
    map_question: str | None,
) -> str:
    active_filters: list[str] = []
    if focus_tags:
        active_filters.append(
            "focus tags " + ", ".join(pretty_tag(tag) for tag in sorted(focus_tags))
        )
    if relation_groups:
        active_filters.append(
            "relation groups " + ", ".join(sorted(relation_groups))
        )
    if relation_types:
        active_filters.append(f"{len(relation_types)} exact relation filters")
    if node_types:
        active_filters.append(f"{len(node_types)} node-type filters")
    if segment_types:
        active_filters.append("segment types " + ", ".join(sorted(segment_types)))
    if map_question:
        active_filters.append(f"question spotlight {map_question}")
    if not active_filters:
        return base_message
    return f"{base_message} Active filters: {'; '.join(active_filters)}."


def _render_map_reset_actions(session_state: MutableMapping[str, object]) -> None:
    has_focus_tags = bool(session_state.get("smg_map_focus_tags"))
    has_other_filters = any(
        [
            bool(session_state.get("smg_map_relation_groups")),
            bool(session_state.get("smg_map_relation_types")),
            bool(session_state.get("smg_map_node_types")),
            bool(session_state.get("smg_map_segment_types")),
            bool(session_state.get("smg_map_question_spotlight")),
            bool(session_state.get("smg_map_include_structural")),
            bool(session_state.get("smg_map_include_editorial")),
            bool(session_state.get("smg_map_include_candidate")),
            normalize_map_range(session_state.get(MAP_RANGE_KEY, (1, 46))) != (1, 46),
        ]
    )
    if not has_focus_tags and not has_other_filters:
        return
    action_left, action_right = st.columns(2, gap="small")
    with action_left:
        if has_focus_tags and st.button(
            "Clear focus",
            key="smg-map-clear-focus-tags",
            use_container_width=True,
        ):
            queue_map_action(session_state, "clear_focus_tags")
            st.rerun()
    with action_right:
        if has_other_filters and st.button(
            "Reset all filters",
            key="smg-map-reset-filters",
            use_container_width=True,
        ):
            queue_map_action(session_state, "reset_filters")
            st.rerun()


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
    consume_widget_updates(session_state)

    with st.sidebar:
        st.markdown("## Summa Virtutum")
        st.caption("Thomas Aquinas moral corpus viewer for concepts, passages, and maps")
        current_view = str(session_state[ACTIVE_VIEW_KEY])
        next_view = st.radio(
            "Navigate",
            options=list(PRIMARY_VIEWS),
            index=list(PRIMARY_VIEWS).index(current_view),
            label_visibility="collapsed",
        )
        if next_view != current_view:
            if next_view == MAP_VIEW:
                _open_overall_map_route(
                    session_state,
                    concept_id=str(session_state.get(CONCEPT_ID_KEY, "") or "") or None,
                    preset_name=str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None,
                )
            elif next_view == STATS_VIEW:
                open_stats(session_state)
            else:
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
        meta_line(_scope_pills(data))
        st.markdown("### Download data")
        _render_download_panel(
            data,
            panel_key="smg_sidebar",
            fallback_preset_name=str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None,
            stats_button_label="Open Stats",
        )

    chosen_view = top_nav(str(session_state[ACTIVE_VIEW_KEY]), PRIMARY_VIEWS)
    if chosen_view == MAP_VIEW:
        _open_overall_map_route(
            session_state,
            concept_id=str(session_state.get(CONCEPT_ID_KEY, "") or "") or None,
            preset_name=str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None,
        )
        st.rerun()
    elif chosen_view == STATS_VIEW:
        open_stats(session_state)
        st.rerun()
    elif chosen_view and chosen_view != session_state[ACTIVE_VIEW_KEY]:
        set_active_view(session_state, chosen_view)
        st.rerun()

    active_view = str(session_state[ACTIVE_VIEW_KEY])
    doctrine_note_html = _summa_structure_note_html() if active_view != HOME_VIEW else None
    meta_line(_scope_pills(data), note_html=doctrine_note_html)

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
    preset_name = str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None
    reviewed_concept_count = len(data.reviewed_concept_ids)
    tract_rows = list(data.dashboard["tract_rows"])
    hero_byline = (
        "<div class='smgv-hero-byline'>"
        "<a href='https://www.linkedin.com/in/hanzhen-zhu/' target='_blank' "
        "rel='noopener noreferrer' aria-label='Jenny Zhu on LinkedIn'>"
        "<span>By Jenny Zhu</span>"
        "<svg viewBox='0 0 16 16' fill='currentColor' aria-hidden='true'>"
        "<path d='M0 1.146C0 .513.526 0 1.175 0h13.65C15.474 0 16 .513 16 1.146v13.708"
        "C16 15.487 15.474 16 14.825 16H1.175C.526 16 0 15.487 0 14.854zM4.943 13.5V6.169H2.542"
        "V13.5zm-1.2-8.333c.837 0 1.358-.554 1.358-1.248-.015-.709-.52-1.248-1.341-1.248S2.4"
        " 3.21 2.4 3.919c0 .694.521 1.248 1.327 1.248zm9.757 8.333v-4.086c0-2.19-1.168-3.208-"
        "2.725-3.208-1.255 0-1.815.69-2.129 1.176V6.169H6.244c.03.803 0 7.331 0 7.331h2.401v-"
        "4.094c0-.219.016-.438.08-.594.173-.438.568-.891 1.232-.891.869 0 1.216.672 1.216 1.65"
        "V13.5z'/>"
        "</svg>"
        "</a>"
        "</div>"
    )

    hero(
        "Summa Virtutum",
        "Interactive map of Thomas Aquinas's moral corpus in the Summa Theologiae",
        eyebrow="Thomas Aquinas",
    )

    main_left, main_right = st.columns((1.18, 0.82), gap="large")
    with main_left:
        st.markdown(
            (
                "<div class='smgv-shell-note smgv-shell-note--hero'>"
                "Corpus scope: Summa Theologiae I-II qq. 1-114 and II-II qq. 1-182, "
                "with II-II qq. 183-189 excluded."
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.markdown(hero_byline, unsafe_allow_html=True)
        st.markdown("<div class='smgv-start-tight'></div>", unsafe_allow_html=True)
        section_heading(
            "Start",
            None,
        )
        st.markdown(
            "<div class='smgv-start-divider smgv-start-divider--top'></div>",
            unsafe_allow_html=True,
        )
        start_grid_top = st.columns((1, 0.072, 1), gap="medium")
        start_grid_bottom = st.columns((1, 0.072, 1), gap="medium")

        concept_options = list(data.home_start_concepts)
        tract_options = sorted_preset_names()
        selected_start_concept = ""
        selected_start_passage = ""
        selected_start_preset = ""

        with start_grid_top[0]:
            _route_intro(
                title="Concept",
                body="Read one concept through doctrine, passages, and nearby links.",
                badge="I",
            )
            selected_start_concept = st.selectbox(
                "High-value concept",
                options=concept_options,
                format_func=lambda value: bundle.registry[value].canonical_label,
                key="smg_home_start_concept",
                label_visibility="collapsed",
            )
            st.markdown("<div class='smgv-route-control-spacer'></div>", unsafe_allow_html=True)
            if _route_button(
                button_label="Open concept",
                key="smg-home-open-concept",
            ):
                open_concept(session_state, selected_start_concept)
                st.rerun()

        with start_grid_top[1]:
            st.markdown("<div class='smgv-start-v-divider'></div>", unsafe_allow_html=True)

        with start_grid_top[2]:
            _route_intro(
                title="Passage",
                body="Start from one passage, then step out to its concepts and evidence.",
                badge="II",
            )
            selected_start_passage = st.selectbox(
                "Starting passage",
                options=list(data.home_start_passages),
                format_func=lambda value: bundle.passages[value].citation_label,
                key="smg_home_start_passage",
                label_visibility="collapsed",
            )
            st.markdown("<div class='smgv-route-control-spacer'></div>", unsafe_allow_html=True)
            if _route_button(
                button_label="Open passage",
                key="smg-home-open-passage",
            ):
                open_passage(session_state, selected_start_passage)
                st.rerun()

        st.markdown(
            "<div class='smgv-start-divider smgv-start-divider--rows'></div>",
            unsafe_allow_html=True,
        )

        with start_grid_bottom[0]:
            _route_intro(
                title="Tract",
                body="Enter one reviewed tract scope directly.",
                badge="III",
            )
            current_home_preset = str(session_state.get("smg_home_start_preset", "") or "")
            if current_home_preset not in tract_options and tract_options:
                session_state["smg_home_start_preset"] = (
                    preset_name if preset_name in tract_options else tract_options[0]
                )
            selected_start_preset = st.selectbox(
                "Tract route",
                options=tract_options,
                format_func=preset_label,
                key="smg_home_start_preset",
                label_visibility="collapsed",
            )
            st.markdown(
                "<div class='smgv-route-control-spacer smgv-route-control-spacer--tract'></div>",
                unsafe_allow_html=True,
            )
            if _route_button(
                button_label="Open tract",
                key="smg-home-open-tract",
            ):
                queue_widget_updates(
                    session_state,
                    **{ACTIVE_PRESET_KEY: selected_start_preset},
                )
                set_active_view(session_state, CONCEPT_VIEW)
                st.rerun()

        with start_grid_bottom[1]:
            st.markdown("<div class='smgv-start-v-divider'></div>", unsafe_allow_html=True)

        with start_grid_bottom[2]:
            _route_intro(
                title="Map",
                body="See the graph first, then jump back into concepts and passages.",
                badge="IV",
            )
            _route_preview_map()
            st.markdown(
                "<div class='smgv-route-control-spacer smgv-route-control-spacer--map'></div>",
                unsafe_allow_html=True,
            )
            if _route_button(
                button_label="Open interactive map",
                key="smg-home-open-map",
                button_type="primary",
            ):
                chosen_preset = str(session_state.get("smg_home_start_preset") or "")
                _open_overall_map_route(
                    session_state,
                    concept_id=selected_start_concept,
                    preset_name=chosen_preset or None,
                )
                st.rerun()

    with main_right:
        section_heading("Download data", None)
        _render_download_panel(
            data,
            panel_key="smg_home",
            fallback_preset_name=preset_name,
            stats_button_label="Open Audit",
        )
        section_heading("At a glance", None)
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
            columns=2,
            row_gap=0.78,
        )

    st.markdown("<div class='smgv-home-snapshot-lift'></div>", unsafe_allow_html=True)
    section_heading("Snapshot", None)
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.caption("Reviewed edges by tract")
        st.altair_chart(
            _home_bar_chart(
                [
                    {
                        "tract": str(row["label"]),
                        "reviewed_edges": int(row["reviewed_doctrinal_edges"]),
                    }
                    for row in sorted(
                        tract_rows,
                        key=lambda row: int(row["reviewed_doctrinal_edges"]),
                        reverse=True,
                    )[:8]
                ],
                x_field="tract",
                y_field="reviewed_edges",
                color="#214b66",
            ),
            use_container_width=True,
        )
    with chart_right:
        st.caption("Graph layers")
        st.caption("Public reviewed edges versus optional overlays.")
        st.altair_chart(
            _home_bar_chart(
                [
                    {
                        "layer": "Public reviewed graph",
                        "count": len(bundle.reviewed_doctrinal_edges),
                    },
                    {
                        "layer": "Editorial overlay",
                        "count": len(bundle.reviewed_structural_edges),
                    },
                    {
                        "layer": "Candidate proposals",
                        "count": len(bundle.candidate_relations),
                    },
                ],
                x_field="layer",
                y_field="count",
                color="#8b442e",
            ),
            use_container_width=True,
        )

def _render_concept_explorer(data: ViewerAppData) -> None:
    bundle = data.bundle
    session_state = _session_state()
    preset_name = str(session_state.get(ACTIVE_PRESET_KEY, "") or "") or None

    section_heading(
        "Concept Explorer",
        "Start with one concept, then move between nearby doctrine, passages, and map context.",
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

    nav_column, detail_column = st.columns((0.48, 1.72), gap="large")
    with nav_column:
        section_heading("Browse concepts", "Pick one concept and keep the reading panel open.")
        pending_concept_widget = str(
            session_state.pop("smg_pending_concept_selectbox", "") or ""
        )
        if pending_concept_widget in available_concept_ids:
            session_state["smg_concept_selectbox"] = pending_concept_widget
        elif session_state.get("smg_concept_selectbox") not in available_concept_ids:
            session_state["smg_concept_selectbox"] = selected_concept_id
        selected_concept_id = st.selectbox(
            "Concept",
            options=available_concept_ids,
            format_func=lambda value: data.concept_label_by_id[value],
            index=available_concept_ids.index(
                str(session_state.get("smg_concept_selectbox") or selected_concept_id)
            ),
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
    scope_label = str(payload.get("scope_label") or active_scope_summary(session_state).label)
    scope_mode = str(payload.get("scope_mode") or "full_corpus")
    fallback_note = str(payload.get("scope_fallback_note") or "")

    with detail_column:
        st.markdown("<div style='height:0.05rem'></div>", unsafe_allow_html=True)
        section_heading(
            str(concept["canonical_label"]),
            str(concept.get("description", "No description available.")),
        )
        if fallback_note:
            st.warning(fallback_note, icon="⚠️")
        if ambiguity_notes:
            key_value_card(
                "Distinctions to keep in view",
                [
                    (f"Note {index}", str(note))
                    for index, note in enumerate(ambiguity_notes, start=1)
                ],
            )

        st.markdown("<div class='smgv-map-section-tight'></div>", unsafe_allow_html=True)
        map_column, summary_column = st.columns((1.92, 0.44), gap="medium")
        with map_column:
            section_heading("Local map", None)
            local_map_controls_left, local_map_controls_right = st.columns(2, gap="small")
            with local_map_controls_left:
                include_editorial_map = st.checkbox(
                    "Include editorial correspondences in local map",
                    key="smg_concept_show_editorial_map",
                )
            with local_map_controls_right:
                show_relation_labels = st.checkbox(
                    "Show relation labels",
                    key="smg_concept_show_relation_labels",
                    help="Render relation names directly on the local map edges.",
                )
            local_edges = reviewed_edges + (editorial_edges if include_editorial_map else [])
            if local_edges:
                graph_result = render_clickable_graph(
                    graph_html=_graph_html_for_edges(
                        local_edges,
                        height=760,
                        show_relation_labels=show_relation_labels,
                    ),
                    height="780px",
                    key=f"smg-local-map-{selected_concept_id}-{int(show_relation_labels)}",
                )
                if graph_result.warning:
                    st.warning(graph_result.warning, icon="⚠️")
                if graph_result.clicked_concept_id:
                    open_concept(
                        session_state,
                        graph_result.clicked_concept_id,
                        preset_name=preset_name,
                    )
                    st.rerun()
            else:
                empty_state(
                    "No local reviewed map",
                    (
                        "This concept has no reviewed edges in the current scope. "
                        f"{scope_label} is still active. Check supporting passages "
                        "or candidate mentions below."
                    ),
                )
        with summary_column:
            relation_groups = relation_groups_for_concept(
                reviewed_edges,
                concept_id=selected_concept_id,
            )
            st.markdown(
                (
                    "<div class='smgv-map-summary-note'>"
                    f"{scope_label} · {compact_number(len(relation_groups))} relation groups · "
                    f"{compact_number(len(list(payload.get('related_questions', []))))} "
                    "related questions"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            pill_row(
                [
                    f"Reviewed {compact_number(len(reviewed_edges))}",
                    f"Editorial {compact_number(len(editorial_edges))}",
                    f"Candidates {compact_number(len(candidate_mentions))}",
                ],
                tone="accent",
            )
            if st.button(
                "← Return to overall map",
                key="smg-concept-open-overall-map",
                use_container_width=True,
            ):
                _open_overall_map_route(
                    session_state,
                    concept_id=selected_concept_id,
                    preset_name=preset_name,
                )
                st.rerun()
            if concept.get("aliases"):
                with st.expander("Registry notes", expanded=False):
                    st.caption(
                        "Type: "
                        f"{concept['node_type']} · Registry: "
                        f"{concept.get('registry_status', 'reviewed')} · "
                        "Mode: "
                        + (
                            "tract-scoped"
                            if scope_mode == "tract"
                            else "broader corpus fallback"
                            if scope_mode == "broader_corpus_fallback"
                            else "full corpus"
                        )
                    )
                    st.caption(
                        "Aliases: " + ", ".join(str(alias) for alias in concept["aliases"][:8])
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
            ],
            row_gap=0.22,
        )

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
                                _open_overall_map_route(
                                    session_state,
                                    concept_id=selected_concept_id,
                                    edge_id=str(edge["edge_id"]),
                                    preset_name=preset_name,
                                )
                                st.rerun()
        else:
            empty_state(
                "No reviewed doctrinal edges in this scope",
                (
                    f"{scope_label} is still active. This concept may only have "
                    "editorial correspondences or candidate mentions here."
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
    filter_state = normalize_passage_filter_state(
        data,
        part_id=str(session_state.get("smg_passage_part", "") or "") or None,
        question_id=str(session_state.get("smg_passage_question", "") or "") or None,
        article_id=str(session_state.get("smg_passage_article", "") or "") or None,
        preset_name=preset_name,
    )
    session_state["smg_passage_part"] = filter_state.selected_part
    session_state["smg_passage_question"] = filter_state.selected_question
    session_state["smg_passage_article"] = filter_state.selected_article

    section_heading(
        "¶ Passage Explorer",
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
                options=list(filter_state.part_options),
                format_func=lambda value: "All parts" if not value else value.upper(),
                key="smg_passage_part",
                disabled=filter_state.part_locked,
            )
            st.selectbox(
                "Question",
                options=["", *filter_state.question_options],
                format_func=lambda value: "All questions"
                if not value
                else data.question_label_by_id[value],
                key="smg_passage_question",
            )
        with right:
            st.selectbox(
                "Article",
                options=["", *filter_state.article_options],
                format_func=lambda value: "All articles" if not value else value,
                key="smg_passage_article",
            )
            st.selectbox(
                "Segment type",
                options=["", "resp", "ad"],
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
    result_signature = (
        query,
        str(st.session_state.get("smg_passage_part", "") or ""),
        str(st.session_state.get("smg_passage_question", "") or ""),
        str(st.session_state.get("smg_passage_article", "") or ""),
        str(st.session_state.get("smg_passage_segment_type", "") or ""),
        str(st.session_state.get("smg_passage_page_size", 4) or 4),
        str(preset_name or ""),
    )
    if session_state.get("smg_passage_result_signature") != result_signature:
        session_state["smg_passage_result_signature"] = result_signature
        session_state["smg_passage_page"] = 1
    page_size = int(cast(int, session_state.get("smg_passage_page_size", 4)))
    total_pages = max(1, (len(results) + page_size - 1) // page_size)
    current_page = int(cast(int, session_state.get("smg_passage_page", 1)))
    if current_page < 1 or current_page > total_pages:
        current_page = 1
        session_state["smg_passage_page"] = current_page
    page_start = (current_page - 1) * page_size
    page_end = page_start + page_size
    visible_results = results[page_start:page_end]
    previous_selected_passage_id = str(session_state.get(PASSAGE_ID_KEY, "") or "")
    selected_passage = selected_passage_for_results(
        session_state,
        visible_results,
        bundle,
    )
    selected_visible_ids = {passage.segment_id for passage in visible_results}
    selection_shifted = bool(previous_selected_passage_id) and (
        previous_selected_passage_id not in selected_visible_ids
    )
    if selected_passage is None:
        session_state[PASSAGE_ID_KEY] = ""
    else:
        session_state[PASSAGE_ID_KEY] = selected_passage.segment_id

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
                f"Cards on page {current_page} of {total_pages}.",
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

    results_column, reader_column = st.columns((0.9, 1.2), gap="large")
    with results_column:
        section_heading("Result list", None)
        st.markdown(
            "<div class='smgv-control-note'>Select a passage on the left.</div>",
            unsafe_allow_html=True,
        )
        pager_left, pager_mid, pager_right = st.columns(
            (0.72, 1.44, 0.98),
            gap="medium",
        )
        with pager_left:
            st.markdown(
                "<div class='smgv-control-note'>Results per page</div>",
                unsafe_allow_html=True,
            )
            st.selectbox(
                "Per page",
                options=[4, 6, 8, 12],
                key="smg_passage_page_size",
                label_visibility="collapsed",
            )
        with pager_mid:
            prev_col, next_col = st.columns(2, gap="small")
            with prev_col:
                if st.button(
                    "← Previous",
                    key="smg_passage_previous_page",
                    use_container_width=True,
                    disabled=current_page <= 1,
                    type="secondary",
                ):
                    session_state["smg_passage_page"] = max(1, current_page - 1)
                    st.rerun()
            with next_col:
                if st.button(
                    "Next →",
                    key="smg_passage_next_page",
                    use_container_width=True,
                    disabled=current_page >= total_pages,
                    type="primary",
                ):
                    session_state["smg_passage_page"] = min(total_pages, current_page + 1)
                    st.rerun()
        with pager_right:
            pager_chip(
                "Page",
                f"{current_page} / {total_pages:,}",
                (
                    f"{page_start + 1 if visible_results else 0}–"
                    f"{page_start + len(visible_results)} of {len(results):,}"
                ),
            )
        if not visible_results:
            empty_state(
                "No passages matched",
                "Broaden the query or clear one of the advanced filters.",
            )
            if st.button(
                "Clear advanced filters",
                key="smg-pass-clear-advanced-filters",
                use_container_width=True,
                type="secondary",
            ):
                session_state["smg_passage_part"] = "ii-ii" if preset_name else ""
                session_state["smg_passage_question"] = ""
                session_state["smg_passage_article"] = ""
                session_state["smg_passage_segment_type"] = ""
                session_state["smg_passage_page"] = 1
                st.rerun()
        for passage in visible_results:
            counts = passage_activity_summary(bundle, passage.segment_id)
            support_card(
                passage.citation_label,
                body=shorten(passage.text, width=260, placeholder="…"),
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
        if selection_shifted and selected_passage is not None:
            info_note(
                "The previous passage fell outside the active results, so the reader moved "
                "to the first visible passage."
            )
        elif selection_shifted and selected_passage is None:
            info_note(
                "The previous passage is outside the active filters and there are no "
                "visible results right now."
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
            if previous_id and st.button(
                "Previous passage",
                key="smg-pass-prev",
                use_container_width=True,
            ):
                open_passage(session_state, previous_id, preset_name=preset_name)
                st.rerun()
        with nav_right:
            if next_id and st.button(
                "Next passage",
                key="smg-pass-next",
                use_container_width=True,
            ):
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
                        _open_overall_map_route(
                            session_state,
                            concept_id=str(row["subject_id"]),
                            preset_name=preset_name,
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
    consume_pending_map_action(session_state)
    normalized_initial_range = normalize_map_range(session_state.get(MAP_RANGE_KEY, (1, 46)))
    if session_state.get(MAP_RANGE_KEY) != normalized_initial_range:
        session_state[MAP_RANGE_KEY] = normalized_initial_range
    current_center = str(session_state.get("smg_map_center_concept", "") or "")
    if not current_center:
        current_center = str(session_state.get(CONCEPT_ID_KEY, "") or "")
        session_state["smg_map_center_concept"] = current_center

    st.markdown(
        (
            "<div class='smgv-map-intro'>"
            "<h2>Overall Map</h2>"
            "<p>Reviewed doctrine first. Narrow only when the graph gets too large to read.</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.markdown("<div class='smgv-map-section-tight'></div>", unsafe_allow_html=True)
    st.markdown("<div class='smgv-map-controls-lift'></div>", unsafe_allow_html=True)
    top_control_left, top_control_mid, top_control_right = st.columns(
        (0.54, 2.36, 1.1),
        gap="medium",
    )
    with top_control_left:
        st.markdown("<div class='smgv-map-controls-note'>Map mode</div>", unsafe_allow_html=True)
        st.radio(
            "Map mode",
            options=["Local map", "Overall map"],
            key=MAP_MODE_KEY,
            horizontal=True,
            label_visibility="collapsed",
            format_func=lambda value: "Local" if value == "Local map" else "Overall",
        )
    with top_control_mid:
        st.markdown("<div class='smgv-map-controls-note'>Quick spans</div>", unsafe_allow_html=True)
        quick_ranges = [
            ("1–46", (1, 46)),
            ("47–56", (47, 56)),
            ("57–122", (57, 122)),
            ("123–140", (123, 140)),
            ("141–170", (141, 170)),
        ]
        quick_columns = st.columns((1, 1, 1.12, 1.12, 1.12), gap="small")
        for column, (label, range_value) in zip(quick_columns, quick_ranges, strict=False):
            with column:
                if st.button(
                    label,
                    key=f"smg-map-quick-range-{label}",
                    use_container_width=True,
                ):
                    queue_widget_updates(session_state, **{MAP_RANGE_KEY: range_value})
                    st.rerun()
    with top_control_right:
        st.markdown(
            "<div class='smgv-map-controls-note'>Question span</div>",
            unsafe_allow_html=True,
        )
        st.slider(
            "Question span",
            min_value=1,
            max_value=182,
            key="smg_map_range",
            label_visibility="collapsed",
            help=(
                "Numeric question span. Pair it with a tract preset or question "
                "spotlight when you want a tighter overall map."
            ),
        )

    preliminary_map_range = normalize_map_range(session_state.get("smg_map_range", (1, 46)))
    available_focus_tags = sorted(
        set(
            available_focus_tags_for_scope(
                data,
                preset_name=preset_name,
                map_range=preliminary_map_range,
            )
        )
        | set(cast(list[str], session_state.get("smg_map_focus_tags", [])))
    )
    advanced_filter_active = any(
        [
            bool(session_state.get("smg_map_include_structural")),
            bool(session_state.get("smg_map_include_editorial")),
            bool(session_state.get("smg_map_include_candidate")),
            bool(session_state.get("smg_map_relation_groups")),
            bool(session_state.get("smg_map_relation_types")),
            bool(session_state.get("smg_map_node_types")),
            bool(session_state.get("smg_map_focus_tags")),
            bool(session_state.get("smg_map_segment_types")),
            bool(session_state.get("smg_map_question_spotlight")),
        ]
    )
    show_more_filters = st.toggle(
        "Show more filters",
        key="smg_map_show_filters",
        help="Reveal layer toggles, focus tags, relation filters, and other advanced controls.",
    )
    if show_more_filters or advanced_filter_active:
        control_left, control_mid, control_right = st.columns(3, gap="large")
        with control_left:
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
            if available_focus_tags:
                st.multiselect(
                    "Focus tags",
                    options=available_focus_tags,
                    format_func=pretty_tag,
                    key="smg_map_focus_tags",
                    help=(
                        "Focus tags stay visible even when they filter the graph down to zero. "
                        "Clear them here if you need to recover the map."
                    ),
                )
            else:
                st.caption("No tract-specific focus tags are available in this span yet.")
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
            st.multiselect(
                "Exact relation types",
                options=graph_relation_type_options(bundle),
                key="smg_map_relation_types",
            )
        with control_right:
            st.multiselect(
                "Node types",
                options=sorted(
                    {record.node_type for record in bundle.registry.values()}
                    | {"question", "article"}
                ),
                key="smg_map_node_types",
            )
            st.multiselect(
                "Evidence segment types",
                options=["resp", "ad"],
                key="smg_map_segment_types",
                help="Filter edges by the segment types of their supporting passages.",
            )

    include_structural = bool(session_state.get("smg_map_include_structural"))
    include_editorial = bool(session_state.get("smg_map_include_editorial"))
    include_candidate = bool(session_state.get("smg_map_include_candidate"))
    map_range = normalize_map_range(session_state.get("smg_map_range", (1, 46)))
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
    _render_map_reset_actions(session_state)

    overall_edges_unfocused, _ = graph_edges_for_view(
        data,
        preset_name=preset_name,
        map_range=map_range,
        include_structural=include_structural,
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types or None,
        relation_groups=relation_groups or None,
        node_types=node_types or None,
        focus_tags=None,
        question_id=map_question,
        center_concept=None if map_mode == "Overall map" else center_concept,
        segment_types=segment_types or None,
        local_only=False,
    )
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

    map_notice_title: str | None = None
    map_notice_body: str | None = None
    if visible_reason:
        map_notice_title = "Map needs one more step"
        map_notice_body = _map_empty_state_body(
            base_message=visible_reason,
            focus_tags=focus_tags,
            relation_groups=relation_groups,
            relation_types=relation_types,
            node_types=node_types,
            segment_types=segment_types,
            map_question=map_question,
        )
    elif not visible_edges:
        map_notice_title = "No edges in this slice"
        map_notice_body = _map_empty_state_body(
            base_message=(
                "Broaden the preset or range, clear a relation filter, or "
                "switch off one of the stricter toggles."
            ),
            focus_tags=focus_tags,
            relation_groups=relation_groups,
            relation_types=relation_types,
            node_types=node_types,
            segment_types=segment_types,
            map_question=map_question,
        )
    elif len(visible_edges) > 280 and map_mode == "Overall map":
        map_notice_title = "Overall map paused"
        map_notice_body = _map_empty_state_body(
            base_message=(
                "This slice is too large to read responsibly. Narrow it with a "
                "tract preset, a question spotlight, or a center concept."
            ),
            focus_tags=focus_tags,
            relation_groups=relation_groups,
            relation_types=relation_types,
            node_types=node_types,
            segment_types=segment_types,
            map_question=map_question,
        )

    graph_column, evidence_column = st.columns((1.72, 0.74), gap="large")
    node_rows, edge_rows = graph_rows(visible_edges)
    node_catalog = {str(row["node_id"]): row for row in node_rows}
    with graph_column:
        if map_mode == "Local map":
            if st.button(
                "← Back to overall map",
                key="smg-map-back-to-overall",
                use_container_width=False,
            ):
                queue_widget_updates(session_state, **{MAP_MODE_KEY: "Overall map"})
                st.rerun()
        st.markdown(
            (
                "<div class='smgv-map-controls-note'>"
                "Click a node to inspect it here first, then step outward to concept "
                "or passage views."
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        show_relation_labels = st.checkbox(
            "Show relation labels",
            key="smg_map_show_relation_labels",
            help="Render relation names directly on edges. Turn this off for a cleaner map.",
        )
        if map_notice_title and map_notice_body:
            empty_state(map_notice_title, map_notice_body)
        else:
            graph_result = render_clickable_graph(
                graph_html=_graph_html_for_edges(
                    visible_edges,
                    height=760,
                    show_relation_labels=show_relation_labels,
                ),
                height="780px",
                key=f"smg-map-{map_mode}-{int(show_relation_labels)}",
            )
            if graph_result.warning:
                st.warning(graph_result.warning, icon="⚠️")
            if graph_result.clicked_concept_id:
                select_map_node(session_state, graph_result.clicked_concept_id)
                st.rerun()
            export_left, export_mid, export_right = st.columns(3, gap="small")
            with export_left:
                st.download_button(
                    "Download edges",
                    data=dataframe_to_csv_bytes(records_frame(edge_rows)),
                    file_name="summa_moral_graph_current_edges.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="smg-map-download-edges",
                )
            with export_mid:
                st.download_button(
                    "Download nodes",
                    data=dataframe_to_csv_bytes(records_frame(node_rows)),
                    file_name="summa_moral_graph_current_nodes.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="smg-map-download-nodes",
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
                    key="smg-map-download-snapshot",
                )
    with evidence_column:
        section_heading(
            "Legend and evidence",
            "Use the selected node and selected edge panels as the bridge back to text.",
        )
        layer_badges(["reviewed_doctrinal", "reviewed_structural", "structural", "candidate"])
        focus_counts = graph_focus_counts(visible_edges)
        if focus_counts:
            pill_row(
                [f"{pretty_tag(tag)} ({count})" for tag, count in focus_counts.most_common(5)],
                tone="candidate",
            )
        if map_notice_title and map_notice_body:
            key_value_card(
                "Current slice",
                [
                    ("Mode", map_mode),
                    ("Range", f"{map_range[0]}–{map_range[1]}"),
                    ("Preset", preset_label(preset_name) if preset_name else "None"),
                    ("Question", map_question or "None"),
                ],
            )
            if center_concept and center_concept in bundle.registry:
                support_card(
                    "Center concept",
                    bundle.registry[center_concept].canonical_label,
                    meta=str(center_concept),
                )
            return

        selected_node_id = str(session_state.get(MAP_SELECTED_NODE_KEY, "") or "")
        if selected_node_id not in node_catalog:
            selected_node_id = (
                current_center
                if current_center in node_catalog
                else next(iter(node_catalog), "")
            )
            session_state[MAP_SELECTED_NODE_KEY] = selected_node_id
        selected_node = node_catalog.get(selected_node_id)
        if selected_node is not None:
            key_value_card(
                "Selected node",
                [
                    ("Label", str(selected_node["label"])),
                    ("Type", str(selected_node["node_type"])),
                    ("Id", str(selected_node["node_id"])),
                ],
            )
            node_left, node_mid = st.columns(2, gap="small")
            if selected_node_id in bundle.registry:
                with node_left:
                    if st.button(
                        "Open concept",
                        key="smg-map-open-selected-concept",
                        use_container_width=True,
                    ):
                        open_concept(
                            session_state,
                            selected_node_id,
                            preset_name=preset_name,
                        )
                        st.rerun()
                with node_mid:
                    if st.button(
                        "Set local center",
                        key="smg-map-center-selected-concept",
                        use_container_width=True,
                    ):
                        queue_widget_updates(
                            session_state,
                            smg_map_center_concept=selected_node_id,
                            **{MAP_MODE_KEY: "Local map"},
                        )
                        st.rerun()
            elif selected_node_id in bundle.questions:
                with node_left:
                    if st.button(
                        "Open passages",
                        key="smg-map-open-selected-question",
                        use_container_width=True,
                    ):
                        question_record = bundle.questions[selected_node_id]
                        session_state["smg_passage_query"] = ""
                        session_state["smg_passage_part"] = str(question_record.part_id)
                        session_state["smg_passage_question"] = selected_node_id
                        session_state["smg_passage_article"] = ""
                        session_state["smg_passage_segment_type"] = ""
                        session_state["smg_passage_page"] = 1
                        set_active_view(session_state, PASSAGE_VIEW)
                        st.rerun()
                with node_mid:
                    if st.button(
                        "Set spotlight",
                        key="smg-map-spotlight-selected-question",
                        use_container_width=True,
                    ):
                        queue_widget_updates(
                            session_state,
                            smg_map_question_spotlight=selected_node_id,
                        )
                        st.rerun()
            elif str(selected_node.get("node_type")) == "article":
                article_question_id = _question_for_article(bundle, selected_node_id)
                with node_left:
                    if st.button(
                        "Open article",
                        key="smg-map-open-selected-article",
                        use_container_width=True,
                    ):
                        session_state["smg_passage_query"] = ""
                        session_state["smg_passage_article"] = selected_node_id
                        session_state["smg_passage_question"] = article_question_id or ""
                        session_state["smg_passage_part"] = (
                            str(bundle.questions[article_question_id].part_id)
                            if article_question_id and article_question_id in bundle.questions
                            else ""
                        )
                        session_state["smg_passage_segment_type"] = ""
                        session_state["smg_passage_page"] = 1
                        set_active_view(session_state, PASSAGE_VIEW)
                        st.rerun()

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
        relation_focus_tags = sorted(
            {
                str(tag)
                for key, value in panel.items()
                if key.endswith("_focus_tags") and isinstance(value, list)
                for tag in value
            }
        )
        if relation_focus_tags:
            pill_row(
                [f"Focus: {pretty_tag(tag)}" for tag in relation_focus_tags],
                tone="candidate",
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
            if st.button(
                "Open source concept",
                key="smg-map-open-source",
                use_container_width=True,
            ):
                open_concept(
                    session_state,
                    str(selected_edge["subject_id"]),
                    preset_name=preset_name,
                )
                st.rerun()
        with action_right:
            if st.button(
                "Open target concept",
                key="smg-map-open-target",
                use_container_width=True,
            ):
                open_concept(
                    session_state,
                    str(selected_edge["object_id"]),
                    preset_name=preset_name,
                )
                st.rerun()

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
        ],
        row_gap=0.22,
    )
    pill_row(
        _map_filter_pills(
            map_mode=map_mode,
            map_range=map_range,
            map_question=map_question,
            relation_groups=relation_groups,
            relation_types=relation_types,
            node_types=node_types,
            focus_tags=focus_tags,
            segment_types=segment_types,
            include_structural=include_structural,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
        ),
        tone="accent",
    )


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
            section_heading("Doctrinal relation types", None)
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
            records_frame(
                review_rows,
                columns=[
                    "tract",
                    "range",
                    "validation_status",
                    "packet_target_question",
                    "under_annotated_questions",
                    "normalization_risk_count",
                ],
                rename={
                    "tract": "Tract",
                    "range": "Range",
                    "validation_status": "Validation",
                    "packet_target_question": "Packet target",
                    "under_annotated_questions": "Under-annotated",
                    "normalization_risk_count": "Normalization risks",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
        section_heading("Reviewed tract overlays", None)
        st.dataframe(
            records_frame(
                tract_rows,
                columns=[
                    "label",
                    "range_label",
                    "validation_status",
                    "question_count",
                    "passage_count",
                    "reviewed_annotations",
                    "reviewed_doctrinal_edges",
                    "reviewed_structural_editorial",
                    "candidate_mentions",
                    "candidate_relation_proposals",
                    "normalization_risk_count",
                ],
                rename={
                    "label": "Tract",
                    "range_label": "Range",
                    "validation_status": "Validation",
                    "question_count": "Questions",
                    "passage_count": "Passages",
                    "reviewed_annotations": "Reviewed annotations",
                    "reviewed_doctrinal_edges": "Reviewed edges",
                    "reviewed_structural_editorial": "Editorial",
                    "candidate_mentions": "Candidate mentions",
                    "candidate_relation_proposals": "Candidate relations",
                    "normalization_risk_count": "Normalization risks",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
