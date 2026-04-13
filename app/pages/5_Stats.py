from __future__ import annotations

import streamlit as st

from summa_moral_graph.app.connected_virtues_109_120 import (
    load_connected_virtues_109_120_summary,
)
from summa_moral_graph.app.corpus import load_corpus_bundle, stats_payload
from summa_moral_graph.app.dashboard import load_dashboard_payload
from summa_moral_graph.app.fortitude_closure_136_140 import (
    load_fortitude_closure_136_140_summary,
)
from summa_moral_graph.app.fortitude_parts_129_135 import (
    load_fortitude_parts_129_135_summary,
)
from summa_moral_graph.app.justice_core import load_justice_core_summary
from summa_moral_graph.app.owed_relation_tract import load_owed_relation_tract_summary
from summa_moral_graph.app.religion_tract import load_religion_tract_summary
from summa_moral_graph.app.temperance_141_160 import load_temperance_141_160_summary
from summa_moral_graph.app.temperance_closure_161_170 import (
    load_temperance_closure_161_170_summary,
)
from summa_moral_graph.app.theological_virtues import (
    load_theological_virtues_summary,
)
from summa_moral_graph.app.ui import (
    MetricCard,
    compact_number,
    configure_page,
    dataframe_to_csv_bytes,
    payload_to_json_bytes,
    records_frame,
    render_key_value_card,
    render_metric_cards,
    render_pill_row,
    render_section_header,
)

configure_page(
    page_title="Health & Audit",
    title="Health & Audit",
    eyebrow="Diagnostics",
    description="Coverage, validation, and tract health.",
)

bundle = load_corpus_bundle()
payload = stats_payload(bundle)
dashboard = load_dashboard_payload()

tract_summaries = [
    ("Theological Virtues", load_theological_virtues_summary()["summary"]),
    ("Justice Core", load_justice_core_summary()["summary"]),
    ("Religion Tract", load_religion_tract_summary()["summary"]),
    ("Owed-Relation Tract", load_owed_relation_tract_summary()["summary"]),
    ("Connected Virtues 109-120", load_connected_virtues_109_120_summary()["summary"]),
    ("Fortitude Parts 129-135", load_fortitude_parts_129_135_summary()["summary"]),
    ("Fortitude Closure 136-140", load_fortitude_closure_136_140_summary()["summary"]),
    ("Temperance 141-160", load_temperance_141_160_summary()["summary"]),
    (
        "Temperance Closure 161-170",
        load_temperance_closure_161_170_summary()["summary"],
    ),
]

summary = payload["summary"]
render_metric_cards(
    [
        MetricCard(
            "Parsed questions",
            compact_number(int(summary["questions_parsed"])),
            "Structurally parsed questions in the in-scope moral corpus.",
            tooltip="The number of included moral-corpus questions with structural coverage rows.",
        ),
        MetricCard(
            "Reviewed tract blocks",
            compact_number(int(dashboard["summary"]["reviewed_tract_blocks"])),
            "Reviewed overlays currently available to users.",
            tooltip=(
                "A tract block is a reviewed doctrinal layer with its own coverage "
                "and validation."
            ),
        ),
        MetricCard(
            "Reviewed doctrinal edges",
            compact_number(len(bundle.reviewed_doctrinal_edges)),
            "Reviewed doctrinal edges available in the shared app bundle.",
            tooltip=(
                "Reviewed doctrinal relationships, kept distinct from structural/"
                "editorial and candidate layers."
            ),
        ),
        MetricCard(
            "Reviewed annotations",
            compact_number(int(summary["reviewed_annotations"])),
            "Human-reviewed support records backing doctrinal overlays.",
            tooltip=(
                "Annotation records that provide explicit support, rationale, and "
                "review status."
            ),
        ),
        MetricCard(
            "Synthesis exports",
            compact_number(int(dashboard["summary"]["synthesis_exports"])),
            "Controlled graph synthesis exports currently available.",
            tooltip=(
                "Reviewed synthesis exports that combine tract knowledge without "
                "mixing in candidate data by default."
            ),
        ),
        MetricCard(
            "Parse failures",
            compact_number(int(summary["parse_failure_count"])),
            "Current structural parse failures needing attention.",
            tooltip="Question or article structures still flagged as failed or unresolved.",
        ),
    ],
    columns=3,
)

overview_tab, graph_tab, tracts_tab = st.tabs(
    ["Corpus Health", "Graph Diagnostics", "Reviewed Tracts"]
)

with overview_tab:
    left_column, right_column = st.columns((1.0, 1.0), gap="large")
    with left_column:
        render_section_header(
            "Corpus Summary",
            "These numbers describe the full moral corpus backbone, not just the "
            "currently reviewed tracts.",
        )
        render_key_value_card(
            "Structural Completeness",
            [
                ("Questions expected", compact_number(int(summary["questions_expected"]))),
                ("Questions parsed", compact_number(int(summary["questions_parsed"]))),
                ("Articles expected", compact_number(int(summary["articles_expected"]))),
                ("Articles parsed", compact_number(int(summary["articles_parsed"]))),
                ("Parse failures", compact_number(int(summary["parse_failure_count"]))),
                ("Ambiguity count", compact_number(int(summary["ambiguity_count"]))),
            ],
        )
    with right_column:
        render_section_header(
            "Reviewed Portfolio Readiness",
            "A compact status readout for how much of the app is backed by tract-level "
            "reviewed overlays.",
        )
        render_key_value_card(
            "Portfolio Status",
            [
                (
                    "Reviewed tract blocks",
                    compact_number(int(dashboard["summary"]["reviewed_tract_blocks"])),
                ),
                (
                    "Validation reports passing",
                    compact_number(int(dashboard["summary"]["ok_validation_blocks"])),
                ),
                (
                    "Synthesis exports",
                    compact_number(int(dashboard["summary"]["synthesis_exports"])),
                ),
            ],
        )

    render_section_header(
        "Top Under-Reviewed Clusters",
        "These corpus clusters have significant structural or candidate activity "
        "relative to current reviewed density.",
    )
    st.dataframe(
        records_frame(
            [
                {
                    **row,
                    "question_range": (
                        f"{row['question_range'][0]}-{row['question_range'][1]}"
                        if isinstance(row.get("question_range"), list)
                        and len(row["question_range"]) == 2
                        else row.get("question_range")
                    ),
                }
                for row in payload["top_under_reviewed_clusters"]
            ],
            rename={
                "part_id": "Part",
                "question_range": "Question range",
                "reviewed_annotation_count": "Reviewed annotations",
                "candidate_mention_count": "Candidate mentions",
                "candidate_relation_count": "Candidate relations",
            },
        ),
        use_container_width=True,
        hide_index=True,
    )
    overview_download_left, overview_download_right = st.columns(2)
    with overview_download_left:
        st.download_button(
            "Download under-reviewed clusters CSV",
            data=dataframe_to_csv_bytes(
                records_frame(
                    [
                        {
                            **row,
                            "question_range": (
                                f"{row['question_range'][0]}-{row['question_range'][1]}"
                                if isinstance(row.get("question_range"), list)
                                and len(row["question_range"]) == 2
                                else row.get("question_range")
                            ),
                        }
                        for row in payload["top_under_reviewed_clusters"]
                    ]
                )
            ),
            file_name="summa_moral_graph_under_reviewed_clusters.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with overview_download_right:
        st.download_button(
            "Download stats snapshot JSON",
            data=payload_to_json_bytes(payload),
            file_name="summa_moral_graph_stats_snapshot.json",
            mime="application/json",
            use_container_width=True,
        )

with graph_tab:
    render_section_header(
        "Concept and Relation Mix",
        "These distributions help explain what the graph is actually made of before "
        "any visual styling is applied.",
    )
    left_column, right_column = st.columns(2, gap="large")
    with left_column:
        st.caption("Concepts by node type")
        concept_type_frame = records_frame(
            [
                {"node_type": key, "count": value}
                for key, value in payload["concept_type_counts"].items()
            ],
            rename={"node_type": "Node type", "count": "Count"},
        )
        st.dataframe(
            concept_type_frame,
            use_container_width=True,
            hide_index=True,
        )
    with right_column:
        st.caption("Reviewed doctrinal relation types")
        reviewed_relation_frame = records_frame(
            [
                {"relation_type": key, "count": value}
                for key, value in payload["reviewed_relation_type_counts"].items()
            ],
            rename={"relation_type": "Relation type", "count": "Count"},
        )
        st.dataframe(
            reviewed_relation_frame,
            use_container_width=True,
            hide_index=True,
        )

    render_section_header(
        "Candidate and Parse Diagnostics",
        "Candidate volume and parse-warning patterns are workflow signals, not public doctrine.",
    )
    diag_left, diag_right = st.columns(2, gap="large")
    with diag_left:
        candidate_relation_frame = records_frame(
            [
                {"relation_type": key, "count": value}
                for key, value in payload["candidate_relation_type_counts"].items()
            ],
            rename={"relation_type": "Candidate relation type", "count": "Count"},
        )
        st.dataframe(
            candidate_relation_frame,
            use_container_width=True,
            hide_index=True,
        )
    with diag_right:
        parse_warning_frame = records_frame(
            [
                {"warning_type": key, "count": value}
                for key, value in payload["parse_warnings_grouped_by_type"].items()
            ],
            rename={"warning_type": "Parse warning type", "count": "Count"},
        )
        st.dataframe(
            parse_warning_frame,
            use_container_width=True,
            hide_index=True,
        )
    render_pill_row(
        ["Candidate layer", "Parse warnings", "Validation artifacts", "Not doctrinal by default"],
        tone="warn",
    )
    graph_download_left, graph_download_mid, graph_download_right, graph_download_far = (
        st.columns(4)
    )
    with graph_download_left:
        st.download_button(
            "Download concept types CSV",
            data=dataframe_to_csv_bytes(concept_type_frame),
            file_name="summa_moral_graph_concept_types.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with graph_download_mid:
        st.download_button(
            "Download reviewed relations CSV",
            data=dataframe_to_csv_bytes(reviewed_relation_frame),
            file_name="summa_moral_graph_reviewed_relation_types.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with graph_download_right:
        st.download_button(
            "Download candidate relations CSV",
            data=dataframe_to_csv_bytes(candidate_relation_frame),
            file_name="summa_moral_graph_candidate_relation_types.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with graph_download_far:
        st.download_button(
            "Download parse warnings CSV",
            data=dataframe_to_csv_bytes(parse_warning_frame),
            file_name="summa_moral_graph_parse_warning_types.csv",
            mime="text/csv",
            use_container_width=True,
        )

with tracts_tab:
    render_section_header(
        "Reviewed Block Summaries",
        "Tract-level reviewed overlays are the app's real maturity units, so they "
        "deserve their own audit surface.",
    )
    tract_rows = []
    for label, tract_summary in tract_summaries:
        tract_rows.append(
            {
                "Tract": label,
                "Questions": tract_summary.get("question_count", "—"),
                "Passages": tract_summary.get("passage_count", "—"),
                "Reviewed annotations": tract_summary.get("reviewed_annotation_count", "—"),
                "Doctrinal edges": tract_summary.get("reviewed_doctrinal_edge_count", "—"),
                "Structural/editorial": tract_summary.get(
                    "reviewed_structural_editorial_count",
                    "—",
                ),
                "Candidate mentions": tract_summary.get("candidate_mention_count", "—"),
                "Candidate relations": tract_summary.get("candidate_relation_count", "—"),
            }
        )
    st.dataframe(
        records_frame(tract_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download reviewed block summary CSV",
        data=dataframe_to_csv_bytes(records_frame(tract_rows)),
        file_name="summa_moral_graph_reviewed_block_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )
