from __future__ import annotations

from collections import Counter
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from summa_moral_graph.app.connected_virtues_109_120 import (
    edge_evidence_panel as connected_edge_evidence_panel,
)
from summa_moral_graph.app.connected_virtues_109_120 import (
    filter_edges_by_preset as filter_connected_edges_by_preset,
)
from summa_moral_graph.app.connected_virtues_109_120 import (
    filter_edges_by_question_range as filter_connected_edges_by_question_range,
)
from summa_moral_graph.app.corpus import (
    build_graph_for_edges,
    generate_structural_edges,
    graph_html,
    load_corpus_bundle,
)
from summa_moral_graph.app.fortitude_closure_136_140 import (
    edge_evidence_panel as fortitude_closure_edge_evidence_panel,
)
from summa_moral_graph.app.fortitude_closure_136_140 import (
    filter_edges_by_preset as filter_fortitude_closure_edges_by_preset,
)
from summa_moral_graph.app.fortitude_closure_136_140 import (
    filter_edges_by_question_range as filter_fortitude_closure_edges_by_question_range,
)
from summa_moral_graph.app.fortitude_parts_129_135 import (
    edge_evidence_panel as fortitude_edge_evidence_panel,
)
from summa_moral_graph.app.fortitude_parts_129_135 import (
    filter_edges_by_preset as filter_fortitude_edges_by_preset,
)
from summa_moral_graph.app.fortitude_parts_129_135 import (
    filter_edges_by_question_range as filter_fortitude_edges_by_question_range,
)
from summa_moral_graph.app.justice_core import (
    edge_evidence_panel as justice_edge_evidence_panel,
)
from summa_moral_graph.app.justice_core import (
    filter_edges_by_preset as filter_justice_edges_by_preset,
)
from summa_moral_graph.app.justice_core import (
    filter_edges_by_question_range as filter_justice_edges_by_question_range,
)
from summa_moral_graph.app.owed_relation_tract import (
    edge_evidence_panel as owed_edge_evidence_panel,
)
from summa_moral_graph.app.owed_relation_tract import (
    filter_edges_by_preset as filter_owed_edges_by_preset,
)
from summa_moral_graph.app.owed_relation_tract import (
    filter_edges_by_question_range as filter_owed_edges_by_question_range,
)
from summa_moral_graph.app.religion_tract import (
    edge_evidence_panel as religion_edge_evidence_panel,
)
from summa_moral_graph.app.religion_tract import (
    filter_edges_by_preset as filter_religion_edges_by_preset,
)
from summa_moral_graph.app.religion_tract import (
    filter_edges_by_question_range as filter_religion_edges_by_question_range,
)
from summa_moral_graph.app.temperance_141_160 import (
    edge_evidence_panel as temperance_edge_evidence_panel,
)
from summa_moral_graph.app.temperance_141_160 import (
    filter_edges_by_preset as filter_temperance_edges_by_preset,
)
from summa_moral_graph.app.temperance_141_160 import (
    filter_edges_by_question_range as filter_temperance_edges_by_question_range,
)
from summa_moral_graph.app.temperance_closure_161_170 import (
    edge_evidence_panel as temperance_closure_edge_evidence_panel,
)
from summa_moral_graph.app.temperance_closure_161_170 import (
    filter_edges_by_preset as filter_temperance_closure_edges_by_preset,
)
from summa_moral_graph.app.temperance_closure_161_170 import (
    filter_edges_by_question_range as filter_temperance_closure_edges_by_question_range,
)
from summa_moral_graph.app.theological_virtues import (
    edge_evidence_panel as theological_edge_evidence_panel,
)
from summa_moral_graph.app.theological_virtues import (
    filter_edges_by_preset as filter_theological_edges_by_preset,
)
from summa_moral_graph.app.theological_virtues import (
    filter_edges_by_question_range as filter_theological_edges_by_question_range,
)
from summa_moral_graph.app.tracts import TRACT_PRESETS, preset_family, preset_label, preset_range
from summa_moral_graph.app.ui import (
    GRAPH_FOCUS_TAG_OPTIONS,
    MetricCard,
    compact_number,
    configure_page,
    dataframe_to_csv_bytes,
    format_edge_option,
    payload_to_json_bytes,
    pretty_tag,
    records_frame,
    render_evidence_panel,
    render_key_value_card,
    render_metric_cards,
    render_pill_row,
    render_section_header,
)

configure_page(
    page_title="Relationship Map",
    title="Relationship Map",
    eyebrow="Graph",
    description="Filter graph edges, inspect support, and export the current slice.",
)

bundle = load_corpus_bundle()
FILTER_DEFAULTS = {
    "graph_include_structural": False,
    "graph_include_editorial": False,
    "graph_include_candidate": False,
    "graph_preset_filter": "",
    "graph_custom_range": (1, 79),
    "graph_focus_tag_filter": [],
    "graph_relation_filter": [],
    "graph_node_type_filter": [],
    "graph_segment_type_filter": [],
    "graph_question_filter": "",
    "graph_center_concept": "",
}

for key, default in FILTER_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = list(default) if isinstance(default, list) else default


def format_question_scope(value: str) -> str:
    if not value:
        return "No question spotlight"
    question = bundle.questions[value]
    return f"{question.part_id.upper()} q.{question.question_number} — {question.question_title}"


def infer_family(range_start: int, range_end: int) -> str:
    if 57 <= range_start <= 79 and 57 <= range_end <= 79:
        return "justice"
    if 109 <= range_start <= 120 and 109 <= range_end <= 120:
        return "connected"
    if (136 <= range_start <= 140 and 136 <= range_end <= 140) or (
        123 <= range_start <= 140
        and 123 <= range_end <= 140
        and not (129 <= range_start <= 135 and 129 <= range_end <= 135)
    ):
        return "fortitude_closure"
    if 129 <= range_start <= 135 and 129 <= range_end <= 135:
        return "fortitude"
    if 141 <= range_start <= 160 and 141 <= range_end <= 160:
        return "temperance"
    if (161 <= range_start <= 170 and 161 <= range_end <= 170) or (
        141 <= range_start <= 170 and 141 <= range_end <= 170 and range_end > 160
    ):
        return "temperance_closure"
    if 80 <= range_start <= 100 and 80 <= range_end <= 100:
        return "religion"
    if 101 <= range_start <= 108 and 101 <= range_end <= 108:
        return "owed"
    return "theological"


def filtered_edges_for_scope(
    family: str,
    *,
    preset_name: str | None,
    range_start: int,
    range_end: int,
    include_editorial: bool,
    include_candidate: bool,
    relation_types: set[str] | None,
    node_types: set[str] | None,
    center_concept: str | None,
    focus_tags: set[str] | None,
) -> list[dict[str, Any]]:
    if preset_name:
        key = preset_name.split(":", 1)[1]
        if family == "justice":
            return filter_justice_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "connected":
            return filter_connected_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "fortitude_closure":
            return filter_fortitude_closure_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "fortitude":
            return filter_fortitude_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "owed":
            return filter_owed_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "religion":
            return filter_religion_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "temperance":
            return filter_temperance_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        if family == "temperance_closure":
            return filter_temperance_closure_edges_by_preset(
                bundle,
                key,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
        return filter_theological_edges_by_preset(
            bundle,
            key,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
        )

    if family == "justice":
        return filter_justice_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "connected":
        return filter_connected_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "fortitude_closure":
        return filter_fortitude_closure_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "fortitude":
        return filter_fortitude_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "temperance":
        return filter_temperance_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "temperance_closure":
        return filter_temperance_closure_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "religion":
        return filter_religion_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    if family == "owed":
        return filter_owed_edges_by_question_range(
            bundle,
            start_question=range_start,
            end_question=range_end,
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    return filter_theological_edges_by_question_range(
        bundle,
        start_question=range_start,
        end_question=range_end,
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types,
        node_types=node_types,
        center_concept=center_concept,
    )


def evidence_panel_for_edge(edge_id: str, edge_row: dict[str, Any], family: str) -> dict[str, Any]:
    if edge_row["layer"] == "structural":
        return {
            "source_concept": edge_row["subject_label"],
            "target_concept": edge_row["object_label"],
            "relation_type": edge_row["relation_type"],
            "layer": edge_row["layer"],
            "support_type": ["structural"],
            "supporting_annotation_ids": [],
            "supporting_passage_ids": edge_row.get("source_passage_ids", []),
            "evidence_snippets": [],
            "passages": [],
        }
    if family == "justice" or "justice_focus_tags" in edge_row:
        return justice_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "connected" or "connected_virtues_focus_tags" in edge_row:
        return connected_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "fortitude_closure" or "fortitude_closure_focus_tags" in edge_row:
        return fortitude_closure_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "fortitude" or "fortitude_parts_focus_tags" in edge_row:
        return fortitude_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "owed" or "owed_relation_focus_tags" in edge_row:
        return owed_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "religion" or "religion_focus_tags" in edge_row:
        return religion_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "temperance" or "temperance_focus_tags" in edge_row:
        return temperance_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    if family == "temperance_closure" or "temperance_closure_focus_tags" in edge_row:
        return temperance_closure_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)
    return theological_edge_evidence_panel(bundle, edge_id, edge_row=edge_row)


with st.sidebar:
    st.markdown("### Graph Scope")
    if st.button("Reset filters", use_container_width=True):
        for key, default in FILTER_DEFAULTS.items():
            st.session_state[key] = list(default) if isinstance(default, list) else default
        st.rerun()
    include_structural = st.checkbox(
        "Include structural graph",
        key="graph_include_structural",
    )
    include_editorial = st.checkbox(
        "Include reviewed structural/editorial correspondences",
        key="graph_include_editorial",
    )
    include_candidate = st.checkbox(
        "Include candidate overlays",
        key="graph_include_candidate",
    )
    preset_filter = st.selectbox(
        "Saved tract preset",
        options=["", *TRACT_PRESETS],
        format_func=lambda value: "None" if not value else preset_label(value),
        key="graph_preset_filter",
    )
    custom_range = st.slider(
        "Custom II-II range",
        min_value=1,
        max_value=182,
        value=(1, 79),
        key="graph_custom_range",
    )

    st.markdown("### Filters")
    focus_tag_filter = st.multiselect(
        "Focus tags",
        options=GRAPH_FOCUS_TAG_OPTIONS,
        format_func=pretty_tag,
        key="graph_focus_tag_filter",
    )
    relation_options = sorted(
        {
            edge["relation_type"]
            for edge in [*bundle.reviewed_doctrinal_edges, *bundle.reviewed_structural_edges]
        }
        | {record.relation_type for record in bundle.candidate_relations}
    )
    relation_filter = st.multiselect(
        "Relation types",
        options=relation_options,
        key="graph_relation_filter",
    )
    node_type_filter = st.multiselect(
        "Node types",
        options=sorted(
            {record.node_type for record in bundle.registry.values()} | {"question", "article"}
        ),
        key="graph_node_type_filter",
    )
    segment_type_filter = st.multiselect(
        "Evidence segment types",
        options=["obj", "sc", "resp", "ad"],
        help="Filter edges by the segment types of their supporting passages.",
        key="graph_segment_type_filter",
    )
    question_filter = st.selectbox(
        "Question-scoped subgraph",
        options=["", *sorted(bundle.questions)],
        format_func=format_question_scope,
        key="graph_question_filter",
    )
    center_concept = st.selectbox(
        "Concept-centered view",
        options=["", *sorted(bundle.registry)],
        format_func=lambda value: "None" if not value else bundle.registry[value].canonical_label,
        key="graph_center_concept",
    )

range_start, range_end = preset_range(preset_filter) if preset_filter else custom_range
current_family = (
    preset_family(preset_filter) if preset_filter else infer_family(range_start, range_end)
)

edges = filtered_edges_for_scope(
    current_family,
    preset_name=preset_filter or None,
    range_start=range_start,
    range_end=range_end,
    include_editorial=include_editorial,
    include_candidate=include_candidate,
    relation_types=set(relation_filter) if relation_filter else None,
    node_types=set(node_type_filter) if node_type_filter else None,
    center_concept=center_concept or None,
    focus_tags=set(focus_tag_filter) if focus_tag_filter else None,
)

if include_structural:
    edges.extend(
        edge
        for edge in generate_structural_edges(bundle, question_id=question_filter or None)
        if edge["subject_id"].startswith("st.ii-ii.q")
        and range_start <= int(edge["subject_id"].split(".q")[1][:3]) <= range_end
    )
if question_filter:
    edges = [
        edge
        for edge in edges
        if question_filter in {edge["subject_id"], edge["object_id"]}
        or any(
            passage_id in bundle.passages
            and bundle.passages[passage_id].question_id == question_filter
            for passage_id in edge.get("source_passage_ids", [])
        )
    ]
if segment_type_filter:
    allowed_segment_types = set(segment_type_filter)
    edges = [
        edge
        for edge in edges
        if any(
            passage_id in bundle.passages
            and bundle.passages[passage_id].segment_type in allowed_segment_types
            for passage_id in edge.get("source_passage_ids", [])
        )
    ]
edges.sort(key=lambda item: (str(item["layer"]), str(item["edge_id"])))

layer_counts = Counter(str(edge["layer"]) for edge in edges)
edge_count = len(edges)
graph_node_count = len(
    {str(edge["subject_id"]) for edge in edges} | {str(edge["object_id"]) for edge in edges}
)
node_catalog = {
    str(edge[f"{side}_id"]): {
        "Node id": str(edge[f"{side}_id"]),
        "Label": str(edge[f"{side}_label"]),
        "Node type": str(edge[f"{side}_type"]),
    }
    for edge in edges
    for side in ("subject", "object")
}
focus_counts = Counter(
    pretty_tag(tag)
    for edge in edges
    for key, value in edge.items()
    if key.endswith("_focus_tags") and isinstance(value, list)
    for tag in value
)
node_rows = sorted(
    node_catalog.values(),
    key=lambda item: (str(item["Node type"]), str(item["Label"])),
)
node_frame = records_frame(node_rows)
edge_frame = records_frame(
    edges,
    columns=[
        "edge_id",
        "layer",
        "subject_label",
        "relation_type",
        "object_label",
        "support_types",
        "support_annotation_ids",
    ],
    rename={
        "edge_id": "Edge id",
        "layer": "Layer",
        "subject_label": "Subject",
        "relation_type": "Relation",
        "object_label": "Object",
        "support_types": "Support types",
        "support_annotation_ids": "Annotation ids",
    },
)
edge_by_id = {str(edge["edge_id"]): edge for edge in edges}

render_pill_row(
    [
        f"Preset: {preset_label(preset_filter) if preset_filter else 'Custom range'}",
        f"Family: {pretty_tag(current_family)}",
        f"Scope: II-II qq. {range_start}-{range_end}",
        f"Segments: {', '.join(segment_type_filter) if segment_type_filter else 'All'}",
        "Editorial included" if include_editorial else "Editorial hidden",
        "Candidate included" if include_candidate else "Candidate hidden",
    ],
    tone="info",
)

render_metric_cards(
    [
        MetricCard("Edges", compact_number(edge_count), "Edges after all active graph filters."),
        MetricCard(
            "Nodes",
            compact_number(graph_node_count),
            "Distinct nodes touched by the filtered edges.",
        ),
        MetricCard(
            "Reviewed doctrinal",
            compact_number(layer_counts.get("reviewed_doctrinal", 0)),
            "Default doctrinal layer that public graph views should privilege.",
        ),
        MetricCard(
            "Candidate / editorial",
            compact_number(
                layer_counts.get("candidate", 0) + layer_counts.get("reviewed_structural", 0)
            ),
            "Non-doctrinal overlays currently visible in this workspace.",
        ),
    ],
    columns=4,
)

render_section_header(
    "Fast Navigation",
    "This page works best when the user narrows to one tract or one concept first, then uses the "
    "evidence panel to confirm the exact claim before trusting the visual graph shape.",
)
nav_left, nav_right = st.columns((1.05, 0.95), gap="large")
with nav_left:
    render_key_value_card(
        "Recommended Flow",
        [
            ("1", "Choose a tract preset or a tight II-II question range."),
            ("2", "Add one focus tag or one relation family before reading the graph."),
            ("3", "Use the edge table when the graph gets dense."),
            ("4", "Open Evidence spotlight to verify support before interpreting the edge."),
        ],
    )
with nav_right:
    render_key_value_card(
        "Readability Guardrails",
        [
            ("Graph render limit", "The canvas pauses above 250 edges to avoid false clarity."),
            ("Best entry points", "Preset, question spotlight, concept-centered view."),
            (
                "Current dominant focus",
                ", ".join(
                    f"{label} ({count})"
                    for label, count in focus_counts.most_common(4)
                )
                or "No focus-tagged edges in current scope",
            ),
            (
                "Current layer mix",
                ", ".join(
                    f"{pretty_tag(layer)} ({count})"
                    for layer, count in sorted(layer_counts.items())
                )
                or "No edges",
            ),
        ],
    )

graph_column, side_column = st.columns((1.35, 0.9), gap="large")
with graph_column:
    render_section_header(
        "Graph Canvas",
        "The graph is optimized for tract-scale inspection, not for indiscriminate corpus dumping. "
        "If it gets too large, fall back to the edge table and export buttons below.",
    )
    if edge_count == 0:
        render_key_value_card(
            "No graph to render",
            [
                (
                    "Suggestion",
                    "Broaden the question range or remove one of the stricter relation "
                    "/ focus filters.",
                ),
                ("Current scope", f"II-II qq. {range_start}-{range_end}"),
            ],
        )
    elif edge_count > 250:
        render_key_value_card(
            "Graph intentionally paused",
            [
                ("Reason", "More than 250 edges would be visually noisy and misleading."),
                ("Current edge count", compact_number(edge_count)),
                ("Suggestion", "Filter by tract preset, question, concept, or relation family."),
            ],
        )
    else:
        graph = build_graph_for_edges(edges)
        components.html(graph_html(graph, height=760), height=820, scrolling=True)

    render_section_header(
        "Edge Table",
        "A structured table view is often easier than the graph itself for exact inspection.",
    )
    st.dataframe(
        edge_frame,
        use_container_width=True,
        hide_index=True,
    )
    download_left, download_mid, download_right = st.columns(3)
    with download_left:
        st.download_button(
            "Download current edges CSV",
            data=dataframe_to_csv_bytes(edge_frame),
            file_name="summa_moral_graph_current_edges.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_mid:
        st.download_button(
            "Download current nodes CSV",
            data=dataframe_to_csv_bytes(node_frame),
            file_name="summa_moral_graph_current_nodes.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_right:
        st.download_button(
            "Download graph snapshot JSON",
            data=payload_to_json_bytes(
                {
                    "scope": {
                        "preset": preset_filter or None,
                        "family": current_family,
                        "range_start": range_start,
                        "range_end": range_end,
                        "question_filter": question_filter or None,
                        "center_concept": center_concept or None,
                        "focus_tags": sorted(focus_tag_filter),
                        "relation_types": sorted(relation_filter),
                        "node_types": sorted(node_type_filter),
                        "include_structural": include_structural,
                        "include_editorial": include_editorial,
                        "include_candidate": include_candidate,
                    },
                    "counts": {
                        "edges": edge_count,
                        "nodes": graph_node_count,
                        "layers": dict(layer_counts),
                        "focus_tags": dict(focus_counts),
                    },
                    "edges": edges,
                }
            ),
            file_name="summa_moral_graph_graph_snapshot.json",
            mime="application/json",
            use_container_width=True,
        )

with side_column:
    render_section_header(
        "Legend and Layer Semantics",
        "This page treats graph layers as different epistemic states, not as cosmetic variants.",
    )
    render_pill_row(
        [
            "Reviewed doctrinal",
            "Reviewed structural/editorial",
            "Structural",
            "Candidate",
        ],
        tone="warn",
    )
    render_key_value_card(
        "What the colors mean",
        [
            ("Node colors", "Different concept and structural node types."),
            ("Solid edges", "Reviewed doctrinal or structural/editorial edges."),
            ("Dashed edges", "Candidate relation proposals."),
            ("Graph default", "Reviewed doctrine only, unless overlays are explicitly enabled."),
        ],
    )
    render_key_value_card(
        "Canvas Controls",
        [
            ("Drag", "Move the canvas to inspect local neighborhoods."),
            ("Scroll / pinch", "Zoom in when labels overlap; zoom out to recover structure."),
            ("Nav buttons", "Use the in-graph controls to zoom and fit without guessing gestures."),
            (
                "Tooltips",
                "Hover nodes or edges to read node type, layer, support type, and "
                "traceability counts.",
            ),
        ],
    )

    if edges:
        edge_options = list(edge_by_id)
        selected_edge = st.selectbox(
            "Evidence spotlight",
            options=edge_options,
            format_func=lambda value: format_edge_option(edge_by_id[value]),
        )
        selected_row = edge_by_id[selected_edge]
        panel = evidence_panel_for_edge(selected_edge, selected_row, current_family)
        render_evidence_panel(panel)
        st.download_button(
            "Download selected evidence JSON",
            data=payload_to_json_bytes(panel),
            file_name=f"{selected_edge.replace('.', '_')}_evidence_panel.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        render_key_value_card(
            "Evidence panel",
            [("Status", "Select filters that return at least one edge to inspect evidence here.")],
        )
