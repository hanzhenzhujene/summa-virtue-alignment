from __future__ import annotations

from collections import Counter

import streamlit as st

from summa_moral_graph.app.connected_virtues_109_120 import (
    connected_virtues_109_120_concept_page_data,
)
from summa_moral_graph.app.corpus import concept_page_data, load_corpus_bundle
from summa_moral_graph.app.fortitude_closure_136_140 import (
    fortitude_closure_136_140_concept_page_data,
)
from summa_moral_graph.app.fortitude_parts_129_135 import (
    fortitude_parts_129_135_concept_page_data,
)
from summa_moral_graph.app.justice_core import justice_core_concept_page_data
from summa_moral_graph.app.owed_relation_tract import owed_relation_tract_concept_page_data
from summa_moral_graph.app.religion_tract import religion_tract_concept_page_data
from summa_moral_graph.app.temperance_141_160 import (
    temperance_141_160_concept_page_data,
)
from summa_moral_graph.app.temperance_closure_161_170 import (
    temperance_closure_161_170_concept_page_data,
)
from summa_moral_graph.app.theological_virtues import (
    theological_virtues_concept_page_data,
)
from summa_moral_graph.app.tracts import TRACT_PRESETS, preset_family, preset_label, preset_range
from summa_moral_graph.app.ui import (
    MetricCard,
    compact_number,
    configure_page,
    dataframe_to_csv_bytes,
    payload_to_json_bytes,
    records_frame,
    render_key_value_card,
    render_metric_cards,
    render_passage_cards,
    render_pill_row,
    render_section_header,
)
from summa_moral_graph.ontology import search_registry

configure_page(
    page_title="Concept Network",
    title="Concept Network",
    eyebrow="Concepts",
    description="Concepts, edges, evidence bundles, and candidate layers.",
)

bundle = load_corpus_bundle()
FILTER_DEFAULTS = {
    "concept_node_type_filter": [],
    "concept_query": "",
    "concept_preset_filter": "",
    "concept_custom_range": (1, 79),
    "concept_selected": "",
}

for key, default in FILTER_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = list(default) if isinstance(default, list) else default

with st.sidebar:
    st.markdown("### Concept Filters")
    if st.button("Reset filters", use_container_width=True):
        for key, default in FILTER_DEFAULTS.items():
            st.session_state[key] = list(default) if isinstance(default, list) else default
        st.rerun()
    node_type_filter = st.multiselect(
        "Node types",
        options=sorted({record.node_type for record in bundle.registry.values()}),
        key="concept_node_type_filter",
    )
    query = st.text_input(
        "Search by canonical label or alias",
        placeholder="charity, prudence, law, gift of counsel",
        key="concept_query",
    )
    preset_filter = st.selectbox(
        "Saved tract preset",
        options=["", *TRACT_PRESETS],
        format_func=lambda value: "None" if not value else preset_label(value),
        key="concept_preset_filter",
    )
    custom_range = st.slider(
        "Custom II-II range",
        min_value=1,
        max_value=182,
        value=(1, 79),
        key="concept_custom_range",
    )

if query.strip():
    matches = search_registry(query, bundle.registry)
else:
    matches = sorted(bundle.registry.values(), key=lambda record: record.canonical_label.casefold())
if node_type_filter:
    matches = [record for record in matches if record.node_type in set(node_type_filter)]

concept_options = {
    "": "Choose a concept",
    **{record.concept_id: f"{record.canonical_label} · {record.node_type}" for record in matches},
}
if st.session_state["concept_selected"] not in concept_options:
    st.session_state["concept_selected"] = ""
selected = st.selectbox(
    "Concept spotlight",
    options=list(concept_options),
    format_func=lambda value: concept_options[value],
    key="concept_selected",
)

render_pill_row(
    [
        f"Matches: {len(matches)}",
        f"Preset: {preset_label(preset_filter) if preset_filter else 'Custom / none'}",
    ],
    tone="info",
)

if not selected:
    render_section_header(
        "How to Use This View",
        "Search for a concept, filter by node type, and then choose a tract preset "
        "or question range "
        "to inspect only the reviewed and candidate evidence relevant to that scope.",
    )
    render_key_value_card(
        "Explorer Guidance",
        [
            (
                "Best for",
                "Comparing reviewed doctrine against candidate mentions and top support passages.",
            ),
            (
                "Start with",
                "A tract preset if you want coherent local doctrine before full-corpus context.",
            ),
            (
                "Watch for",
                "Ambiguity notes: they often signal where English labels are unsafe to flatten.",
            ),
        ],
    )
    st.stop()

start_question, end_question = preset_range(preset_filter) if preset_filter else custom_range
family = preset_family(preset_filter) if preset_filter else ""
if family == "justice" or (57 <= start_question <= 79 and 57 <= end_question <= 79):
    payload = justice_core_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif family == "connected" or (109 <= start_question <= 120 and 109 <= end_question <= 120):
    payload = connected_virtues_109_120_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif family == "fortitude_closure" or (123 <= start_question <= 140 and 123 <= end_question <= 140):
    payload = fortitude_closure_136_140_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif family == "fortitude" or (129 <= start_question <= 135 and 129 <= end_question <= 135):
    payload = fortitude_parts_129_135_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif family == "owed" or (101 <= start_question <= 108 and 101 <= end_question <= 108):
    payload = owed_relation_tract_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif family == "religion" or (80 <= start_question <= 100 and 80 <= end_question <= 100):
    payload = religion_tract_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif family == "temperance" or (141 <= start_question <= 160 and 141 <= end_question <= 160):
    payload = temperance_141_160_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
elif (
    family == "temperance_closure"
    or (161 <= start_question <= 170 and 161 <= end_question <= 170)
    or (141 <= start_question <= 170 and 141 <= end_question <= 170 and end_question > 160)
):
    payload = temperance_closure_161_170_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )
else:
    payload = theological_virtues_concept_page_data(
        bundle,
        selected,
        start_question=start_question,
        end_question=end_question,
    )

if not payload.get("reviewed_incident_edges") and not payload.get("candidate_mentions"):
    payload = concept_page_data(bundle, selected)

concept = payload["concept"]
reviewed_edges = payload.get(
    "reviewed_doctrinal_edges",
    payload.get("reviewed_incident_edges", []),
)
editorial_edges = payload.get(
    "reviewed_structural_edges",
    payload.get("editorial_correspondences", []),
)
candidate_mentions = payload.get("candidate_mentions", [])
candidate_relations = payload.get("candidate_relations", [])
supporting_passages = payload.get(
    "supporting_passages",
    payload.get("top_supporting_passages", []),
)
coverage = payload.get("coverage", {})
related_questions = payload.get("related_questions", [])
ambiguity_notes = payload.get("ambiguity_notes") or payload.get(
    "unresolved_disambiguation_notes",
    [],
)
reviewed_relation_counts = Counter(
    str(edge["relation_type"]) for edge in reviewed_edges if edge.get("relation_type")
)

render_pill_row(
    [
        concept["node_type"],
        f"Registry: {concept.get('registry_status', 'reviewed')}",
        f"Scope: II-II qq. {start_question}-{end_question}",
    ],
    tone="info",
)
render_metric_cards(
    [
        MetricCard(
            "Reviewed edges",
            compact_number(int(coverage.get("reviewed_edge_count", len(reviewed_edges)))),
            "Incident reviewed doctrinal edges in the active question range.",
        ),
        MetricCard(
            "Editorial edges",
            compact_number(int(coverage.get("editorial_edge_count", len(editorial_edges)))),
            "Structural/editorial correspondences kept distinct from doctrine.",
        ),
        MetricCard(
            "Candidate mentions",
            compact_number(int(coverage.get("candidate_mention_count", len(candidate_mentions)))),
            "Unreviewed concept detections touching this concept id.",
        ),
        MetricCard(
            "Candidate relations",
            compact_number(int(coverage.get("candidate_relation_count", len(candidate_relations)))),
            "Unreviewed relation proposals in the current range.",
        ),
    ],
    columns=4,
)

if concept.get("aliases"):
    render_pill_row([str(alias) for alias in concept["aliases"]], tone="warn")
if ambiguity_notes:
    render_section_header(
        "Disambiguation Notes",
        "These notes flag where matching or doctrinal normalization should stay conservative.",
    )
    for note in ambiguity_notes:
        st.warning(str(note))

download_left, download_right = st.columns(2)
with download_left:
    st.download_button(
        "Download concept bundle JSON",
        data=payload_to_json_bytes(payload),
        file_name=f"{selected.replace('.', '_')}_concept_bundle.json",
        mime="application/json",
        use_container_width=True,
    )
with download_right:
    st.download_button(
        "Download reviewed edge CSV",
        data=dataframe_to_csv_bytes(records_frame(reviewed_edges)),
        file_name=f"{selected.replace('.', '_')}_reviewed_edges.csv",
        mime="text/csv",
        use_container_width=True,
    )

overview_tab, reviewed_tab, candidate_tab, evidence_tab = st.tabs(
    ["Overview", "Reviewed Graph", "Candidate Layer", "Evidence"]
)

with overview_tab:
    overview_left, overview_right = st.columns((1.1, 0.9), gap="large")
    with overview_left:
        render_key_value_card(
            str(concept["canonical_label"]),
            [
                ("Concept id", str(concept["concept_id"])),
                ("Node type", str(concept["node_type"])),
                ("Description", str(concept.get("description", "None"))),
                ("Notes", "; ".join(concept.get("notes", [])) or "None"),
                (
                    "Related questions",
                    ", ".join(str(value) for value in related_questions) or "None",
                ),
            ],
        )
    with overview_right:
        render_key_value_card(
            "Relation Mix",
            [
                (relation.replace("_", " "), compact_number(count))
                for relation, count in reviewed_relation_counts.most_common(6)
            ]
            or [("Reviewed relations", "None in active range")],
        )

with reviewed_tab:
    left_column, right_column = st.columns((1.05, 0.95), gap="large")
    with left_column:
        render_section_header(
            "Reviewed Doctrinal Edges",
            "Only reviewed doctrinal edges are shown here by default.",
        )
        st.dataframe(
            records_frame(
                reviewed_edges,
                columns=[
                    "subject_label",
                    "relation_type",
                    "object_label",
                    "support_types",
                    "support_annotation_ids",
                ],
                rename={
                    "subject_label": "Subject",
                    "relation_type": "Relation",
                    "object_label": "Object",
                    "support_types": "Support types",
                    "support_annotation_ids": "Annotation ids",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download doctrinal edge table CSV",
            data=dataframe_to_csv_bytes(records_frame(reviewed_edges)),
            file_name=f"{selected.replace('.', '_')}_doctrinal_edges.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{selected}-doctrinal-download",
        )
    with right_column:
        render_section_header(
            "Structural / Editorial Correspondences",
            "These are visible for interpretation support but remain distinct from "
            "doctrinal graph facts.",
        )
        st.dataframe(
            records_frame(
                editorial_edges,
                columns=[
                    "subject_label",
                    "relation_type",
                    "object_label",
                    "support_types",
                    "support_annotation_ids",
                ],
                rename={
                    "subject_label": "Subject",
                    "relation_type": "Relation",
                    "object_label": "Object",
                    "support_types": "Support types",
                    "support_annotation_ids": "Annotation ids",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download editorial edge table CSV",
            data=dataframe_to_csv_bytes(records_frame(editorial_edges)),
            file_name=f"{selected.replace('.', '_')}_editorial_edges.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{selected}-editorial-download",
        )

with candidate_tab:
    candidate_left, candidate_right = st.columns(2, gap="large")
    with candidate_left:
        render_section_header(
            "Candidate Mentions",
            "Potential mentions awaiting review or normalization decisions.",
        )
        st.dataframe(
            records_frame(
                candidate_mentions,
                columns=[
                    "passage_id",
                    "matched_text",
                    "proposed_concept_id",
                    "match_method",
                    "confidence",
                    "ambiguity_flag",
                ],
                rename={
                    "passage_id": "Passage",
                    "matched_text": "Matched text",
                    "proposed_concept_id": "Proposed concept",
                    "match_method": "Method",
                    "confidence": "Confidence",
                    "ambiguity_flag": "Ambiguous?",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download candidate mentions CSV",
            data=dataframe_to_csv_bytes(records_frame(candidate_mentions)),
            file_name=f"{selected.replace('.', '_')}_candidate_mentions.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{selected}-candidate-mentions-download",
        )
    with candidate_right:
        render_section_header(
            "Candidate Relations",
            "Proposal rows are visible as workflow support, not as approved graph facts.",
        )
        st.dataframe(
            records_frame(
                candidate_relations,
                columns=[
                    "source_passage_id",
                    "subject_id",
                    "relation_type",
                    "object_id",
                    "proposal_method",
                    "confidence",
                    "review_status",
                ],
                rename={
                    "source_passage_id": "Passage",
                    "subject_id": "Subject",
                    "relation_type": "Relation",
                    "object_id": "Object",
                    "proposal_method": "Method",
                    "confidence": "Confidence",
                    "review_status": "Status",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download candidate relations CSV",
            data=dataframe_to_csv_bytes(records_frame(candidate_relations)),
            file_name=f"{selected.replace('.', '_')}_candidate_relations.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"{selected}-candidate-relations-download",
        )

with evidence_tab:
    render_section_header(
        "Supporting Passages",
        "Top reviewed or candidate-supporting passages for this concept in the active range.",
    )
    render_passage_cards(supporting_passages, max_items=8)
    st.download_button(
        "Download supporting passages CSV",
        data=dataframe_to_csv_bytes(records_frame(supporting_passages)),
        file_name=f"{selected.replace('.', '_')}_supporting_passages.csv",
        mime="text/csv",
        use_container_width=True,
        key=f"{selected}-supporting-passages-download",
    )
