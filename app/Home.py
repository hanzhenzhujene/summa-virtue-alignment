from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from summa_moral_graph.app.dashboard import load_dashboard_payload
from summa_moral_graph.app.ui import (
    MetricCard,
    basename,
    compact_number,
    configure_page,
    dataframe_to_csv_bytes,
    format_question_list,
    payload_to_json_bytes,
    records_frame,
    render_key_value_card,
    render_metric_cards,
    render_pill_row,
    render_section_header,
    status_tone,
)

configure_page(
    page_title="Summa Moral Graph Dashboard",
    title="Dashboard",
    eyebrow="Summa Moral Graph",
    description="Corpus status, reviewed tracts, review queues, and exports.",
)

payload = load_dashboard_payload()
summary = payload["summary"]
tract_rows = payload["tract_rows"]
review_priority_rows = payload["review_priority_rows"]
synthesis_rows = payload["synthesis_rows"]


def tract_table_rows() -> list[dict[str, object]]:
    return [
        {
            "Tract": row["label"],
            "Range": row["range_label"],
            "Status": row["validation_status"],
            "Questions": row["question_count"],
            "Passages": row["passage_count"],
            "Reviewed annotations": row["reviewed_annotations"],
            "Doctrinal edges": row["reviewed_doctrinal_edges"],
            "Structural/editorial": row["reviewed_structural_editorial"],
            "Candidate mentions": row["candidate_mentions"],
            "Candidate relations": row["candidate_relation_proposals"],
            "Density": row["annotation_density"],
            "Review packet": (
                f"II-II q.{row['review_packet_question']}"
                if row["review_packet_question"] is not None
                else "None"
            ),
        }
        for row in tract_rows
    ]


def executive_report_markdown() -> str:
    top_ready = sorted(
        tract_rows,
        key=lambda row: (
            str(row["validation_status"]) != "ok",
            -int(row["reviewed_doctrinal_edges"]),
            -int(row["reviewed_annotations"]),
        ),
    )[:3]
    review_pressure = sorted(
        tract_rows,
        key=lambda row: (
            -int(row["normalization_risk_count"]),
            -len(list(row["under_annotated_questions"])),
        ),
    )[:3]
    lines = [
        "# Summa Moral Graph Dashboard Snapshot",
        "",
        "## Portfolio Summary",
        f"- Questions parsed: {summary['questions_parsed']}",
        f"- Passages parsed: {summary['passages_parsed']}",
        f"- Reviewed tract blocks: {summary['reviewed_tract_blocks']}",
        f"- Validation OK blocks: {summary['ok_validation_blocks']}",
        f"- Parse failures: {summary['parse_failure_count']}",
        "",
        "## Strongest Reviewed Blocks",
    ]
    lines.extend(
        [
            (
                f"- {row['label']} ({row['range_label']}): "
                f"{row['reviewed_annotations']} reviewed annotations, "
                f"{row['reviewed_doctrinal_edges']} doctrinal edges, "
                f"validation={row['validation_status']}"
            )
            for row in top_ready
        ]
    )
    lines.append("")
    lines.append("## Highest Review Pressure")
    lines.extend(
        [
            (
                f"- {row['label']} ({row['range_label']}): "
                f"{len(list(row['under_annotated_questions']))} under-annotated questions, "
                f"{row['normalization_risk_count']} normalization risks, "
                f"review packet target={row['review_packet_question'] or 'None'}"
            )
            for row in review_pressure
        ]
    )
    return "\n".join(lines) + "\n"


def compare_rows(left_slug: str, right_slug: str) -> list[dict[str, object]]:
    rows_by_slug = {str(row["slug"]): row for row in tract_rows}
    left = rows_by_slug[left_slug]
    right = rows_by_slug[right_slug]
    metrics = [
        ("Questions", int(left["question_count"]), int(right["question_count"])),
        ("Passages", int(left["passage_count"]), int(right["passage_count"])),
        (
            "Reviewed annotations",
            int(left["reviewed_annotations"]),
            int(right["reviewed_annotations"]),
        ),
        (
            "Doctrinal edges",
            int(left["reviewed_doctrinal_edges"]),
            int(right["reviewed_doctrinal_edges"]),
        ),
        (
            "Structural/editorial",
            int(left["reviewed_structural_editorial"]),
            int(right["reviewed_structural_editorial"]),
        ),
        ("Candidate mentions", int(left["candidate_mentions"]), int(right["candidate_mentions"])),
        (
            "Candidate relations",
            int(left["candidate_relation_proposals"]),
            int(right["candidate_relation_proposals"]),
        ),
    ]
    return [
        {
            "Metric": label,
            str(left["label"]): left_value,
            str(right["label"]): right_value,
            "Delta": left_value - right_value,
        }
        for label, left_value, right_value in metrics
    ]


def render_tract_card(row: dict[str, Any]) -> None:
    status = str(row["validation_status"])
    under_reviewed = format_question_list(list(row["under_annotated_questions"]))
    normalization = format_question_list(list(row["normalization_risk_questions"]))
    packet = (
        f"II-II q.{row['review_packet_question']}"
        if row["review_packet_question"] is not None
        else "None"
    )
    highlights = list(row["highlights"])
    st.markdown(
        f"""
        <div class="smg-card">
          <div class="smg-section-title" style="margin-top:0;">{escape(str(row["label"]))}</div>
          <div class="smg-section-copy">{escape(str(row["range_label"]))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_pill_row(
        [
            f"Validation: {status}",
            f"{row['question_count']} questions",
            f"{row['passage_count']} passages",
            f"{row['reviewed_doctrinal_edges']} doctrinal edges",
        ],
        tone=status_tone(status),
    )
    render_key_value_card(
        "Status",
        [
            ("Reviewed annotations", compact_number(int(row["reviewed_annotations"]))),
            (
                "Structural/editorial",
                compact_number(int(row["reviewed_structural_editorial"])),
            ),
            ("Candidate mentions", compact_number(int(row["candidate_mentions"]))),
            (
                "Candidate relations",
                compact_number(int(row["candidate_relation_proposals"])),
            ),
            ("Review packet", packet),
            ("Under-annotated", under_reviewed),
            ("Normalization risk", normalization),
            ("Review queue", basename(row["review_queue_path"])),
        ],
    )
    if highlights:
        render_pill_row(highlights, tone="warn")


render_section_header(
    "Start Here",
    "Use the landing page to see scope, tract maturity, and the fastest path into "
    "evidence or the graph.",
)
path_left, path_mid, path_right = st.columns(3, gap="large")
with path_left:
    render_key_value_card(
        "1. Read the dashboard",
        [
            ("Use", "Overview"),
            ("For", "Scope, maturity, and review pressure"),
        ],
    )
    st.caption("You are here.")
with path_mid:
    render_key_value_card(
        "2. Read evidence",
        [
            ("Use", "Evidence Browser"),
            ("For", "Search passages and inspect reviewed support"),
        ],
    )
    st.page_link(
        "pages/2_Passage_Explorer.py",
        label="Open Evidence Browser",
        use_container_width=True,
    )
with path_right:
    render_key_value_card(
        "3. Inspect the graph",
        [
            ("Use", "Relationship Map"),
            ("For", "Filter edges, inspect support, and export graph slices"),
        ],
    )
    st.page_link(
        "pages/4_Graph_View.py",
        label="Open Relationship Map",
        use_container_width=True,
    )

action_left, action_mid, action_right = st.columns(3, gap="large")
with action_left:
    st.download_button(
        "Download Data Snapshot",
        data=payload_to_json_bytes(payload),
        file_name="summa_moral_graph_dashboard_snapshot.json",
        mime="application/json",
        use_container_width=True,
    )
with action_mid:
    st.download_button(
        "Export Dashboard Report",
        data=executive_report_markdown().encode("utf-8"),
        file_name="summa_moral_graph_dashboard_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
with action_right:
    st.page_link(
        "pages/4_Graph_View.py",
        label="Open Relationship Map",
        use_container_width=True,
    )

render_metric_cards(
    [
        MetricCard(
            "Questions parsed",
            compact_number(int(summary["questions_parsed"])),
            "Included questions structurally parsed across I-II and II-II.",
            tooltip=(
                "The count of in-scope moral-corpus questions currently available "
                "in the dashboard."
            ),
        ),
        MetricCard(
            "Passages parsed",
            compact_number(int(summary["passages_parsed"])),
            "Canonical segment records available for evidence-first browsing.",
            tooltip=(
                "Segment-level evidence records across objections, sed contra, "
                "respondeo, and replies."
            ),
        ),
        MetricCard(
            "Reviewed tract edges",
            compact_number(sum(int(row["reviewed_doctrinal_edges"]) for row in tract_rows)),
            "Reviewed doctrinal edges currently surfaced across tract overlays.",
            tooltip=(
                "This is the tract-overlay edge count, not a claim that the whole "
                "corpus is fully reviewed."
            ),
        ),
        MetricCard(
            "Reviewed blocks",
            compact_number(int(summary["reviewed_tract_blocks"])),
            "Distinct reviewed tract overlays currently available.",
            tooltip=(
                "A tract block is a reviewed doctrinal layer with its own coverage "
                "and validation report."
            ),
        ),
        MetricCard(
            "Validation OK",
            compact_number(int(summary["ok_validation_blocks"])),
            "Reviewed blocks whose tract-specific validation reports currently pass.",
            tooltip="Counts tract overlays whose current validation report status is OK.",
        ),
        MetricCard(
            "Parse failures",
            compact_number(int(summary["parse_failure_count"])),
            "Questions or articles currently flagged as failed.",
            tooltip=(
                "Structural ingest failures or unresolved parse problems in the "
                "corpus backbone."
            ),
        ),
    ],
    columns=3,
)

overview_tab, blocks_tab, workflow_tab = st.tabs(
    ["Overview", "Reviewed Tracts", "Review & Export"]
)

with overview_tab:
    left_column, right_column = st.columns((1.05, 0.95), gap="large")

    with left_column:
        render_section_header(
            "What This Dashboard Shows",
            "The dashboard separates structural coverage, reviewed doctrine, "
            "editorial correspondences, and candidate workflow.",
        )
        render_key_value_card(
            "Corpus Scope",
            [
                ("Included", ", ".join(payload["scope"]["included"])),
                ("Excluded", ", ".join(payload["scope"]["excluded"])),
            ],
        )
        render_key_value_card(
            "Ground Rules",
            [(f"Rule {index + 1}", note) for index, note in enumerate(payload["layer_discipline"])],
        )

    with right_column:
        render_section_header(
            "Current State",
            "The textual corpus is broad. Reviewed doctrinal work is still tract-based.",
        )
        render_metric_cards(
            [
                MetricCard(
                    "Questions expected",
                    compact_number(int(summary["questions_expected"])),
                    "Expected in-scope questions.",
                ),
                MetricCard(
                    "Articles parsed",
                    compact_number(int(summary["articles_parsed"])),
                    f"Of {compact_number(int(summary['articles_expected']))} expected articles.",
                ),
                MetricCard(
                    "Parse failures",
                    compact_number(int(summary["parse_failure_count"])),
                    "Questions or articles currently flagged as failed.",
                ),
                MetricCard(
                    "Ambiguity count",
                    compact_number(int(summary["ambiguity_count"])),
                    "Candidate-level ambiguity hotspots across the corpus.",
                ),
            ],
            columns=2,
        )

    render_section_header(
        "Reviewed Tract Snapshot",
        "Use this view to see which reviewed blocks are dense, thin, or still risky.",
    )
    tract_frame = records_frame(tract_table_rows())
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.caption("Reviewed doctrinal edge volume by tract")
        st.bar_chart(
            tract_frame.set_index("Tract")[["Doctrinal edges"]],
            use_container_width=True,
        )
    with chart_right:
        st.caption("Reviewed annotation density by tract")
        st.bar_chart(
            tract_frame.set_index("Tract")[["Density"]],
            use_container_width=True,
        )
    download_left, download_right = st.columns(2)
    with download_left:
        st.download_button(
            "Download tract portfolio CSV",
            data=dataframe_to_csv_bytes(tract_frame),
            file_name="summa_moral_graph_tract_portfolio.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_right:
        st.download_button(
            "Download dashboard snapshot JSON",
            data=payload_to_json_bytes(payload),
            file_name="summa_moral_graph_dashboard_snapshot.json",
            mime="application/json",
            use_container_width=True,
        )

with blocks_tab:
    render_section_header(
        "Reviewed Tract Portfolio",
        "Each tract card shows validation, scale, and the next review target.",
    )
    tract_columns = st.columns(2, gap="large")
    for index, tract_row in enumerate(tract_rows):
        with tract_columns[index % 2]:
            render_tract_card(tract_row)

    render_section_header(
        "Portfolio Table",
        "A compact table of tract counts and review targets.",
    )
    st.dataframe(
        records_frame(tract_table_rows()),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download reviewed tract table CSV",
        data=dataframe_to_csv_bytes(records_frame(tract_table_rows())),
        file_name="summa_moral_graph_reviewed_tracts.csv",
        mime="text/csv",
        use_container_width=True,
    )

    render_section_header(
        "Quick Compare",
        "Compare two tracts directly.",
    )
    compare_options = {
        str(row["slug"]): f"{row['label']} · {row['range_label']}" for row in tract_rows
    }
    default_left = tract_rows[0]["slug"]
    default_right = tract_rows[1]["slug"] if len(tract_rows) > 1 else tract_rows[0]["slug"]
    compare_left_col, compare_right_col = st.columns(2, gap="large")
    with compare_left_col:
        left_slug = st.selectbox(
            "Compare tract A",
            options=list(compare_options),
            format_func=lambda value: compare_options[value],
            index=list(compare_options).index(str(default_left)),
        )
    with compare_right_col:
        right_slug = st.selectbox(
            "Compare tract B",
            options=list(compare_options),
            format_func=lambda value: compare_options[value],
            index=list(compare_options).index(str(default_right)),
        )
    comparison_frame = records_frame(compare_rows(left_slug, right_slug))
    st.dataframe(comparison_frame, use_container_width=True, hide_index=True)
    st.download_button(
        "Download tract comparison CSV",
        data=dataframe_to_csv_bytes(comparison_frame),
        file_name="summa_moral_graph_tract_comparison.csv",
        mime="text/csv",
        use_container_width=True,
    )

with workflow_tab:
    workflow_left, workflow_right = st.columns((1.08, 0.92), gap="large")

    with workflow_left:
        render_section_header(
            "Current Review Priorities",
            "Review queues already identify the next questions that need work.",
        )
        st.dataframe(
            records_frame(
                [
                    {
                        **row,
                        "under_annotated_questions": format_question_list(
                            list(row["under_annotated_questions"])
                        ),
                        "review_queue_path": basename(str(row["review_queue_path"])),
                    }
                    for row in review_priority_rows
                ],
                rename={
                    "tract": "Tract",
                    "range": "Range",
                    "validation_status": "Status",
                    "packet_target_question": "Packet target",
                    "under_annotated_questions": "Under-annotated questions",
                    "normalization_risk_count": "Normalization risk count",
                    "review_queue_path": "Review queue",
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.download_button(
            "Download review priorities CSV",
            data=dataframe_to_csv_bytes(
                records_frame(
                    [
                        {
                            **row,
                            "under_annotated_questions": format_question_list(
                                list(row["under_annotated_questions"])
                            ),
                            "review_queue_path": basename(str(row["review_queue_path"])),
                        }
                        for row in review_priority_rows
                    ]
                )
            ),
            file_name="summa_moral_graph_review_priorities.csv",
            mime="text/csv",
            use_container_width=True,
        )

        render_section_header(
            "Under-Reviewed Clusters",
            "Corpus clusters with low reviewed density.",
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

    with workflow_right:
        render_section_header(
            "Synthesis Exports",
            "Reviewed synthesis exports. Candidate data stays out by default.",
        )
        for row in synthesis_rows:
            st.markdown(
                f"""
                <div class="smg-card">
                  <div class="smg-section-title" style="margin-top:0;">
                    {escape(str(row["label"]))}
                  </div>
                  <div class="smg-section-copy">{escape(str(row["range_label"]))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_pill_row(
                [
                    f"{row['nodes']} nodes",
                    f"{row['edges']} edges",
                    f"GraphML: {basename(row['graphml_path'])}",
                    f"Editorial: {basename(row['editorial_graphml_path'])}",
                ],
                tone="info",
            )
        st.download_button(
            "Download synthesis inventory CSV",
            data=dataframe_to_csv_bytes(records_frame(synthesis_rows)),
            file_name="summa_moral_graph_synthesis_inventory.csv",
            mime="text/csv",
            use_container_width=True,
        )

        render_section_header(
            "Display Rules",
            "How to read the app.",
        )
        render_key_value_card(
            "Rules",
            [
                ("Default graph mode", "Reviewed doctrinal edges only"),
                ("Editorial layer", "Visible, inspectable, but distinctly labeled"),
                ("Candidate layer", "Review aid only, never public doctrine by default"),
                ("Evidence model", "Segment-first, not article-wide by convenience"),
            ],
        )
