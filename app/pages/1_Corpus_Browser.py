from __future__ import annotations

import streamlit as st

from summa_moral_graph.app.corpus import corpus_browser_rows, load_corpus_bundle
from summa_moral_graph.app.ui import (
    MetricCard,
    compact_number,
    configure_page,
    dataframe_to_csv_bytes,
    format_question_list,
    records_frame,
    render_key_value_card,
    render_metric_cards,
    render_pill_row,
    render_section_header,
    status_tone,
)

configure_page(
    page_title="Corpus Coverage",
    title="Corpus Coverage",
    eyebrow="Coverage",
    description="Question and article coverage across the corpus.",
)

bundle = load_corpus_bundle()
FILTER_DEFAULTS = {
    "corpus_part_filter": "",
    "corpus_status_filter": ["parsed", "partial"],
    "corpus_title_query": "",
    "corpus_question_filter": "",
}

for key, default in FILTER_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = list(default) if isinstance(default, list) else default

with st.sidebar:
    st.markdown("### Filters")
    if st.button("Reset filters", use_container_width=True):
        for key, default in FILTER_DEFAULTS.items():
            st.session_state[key] = list(default) if isinstance(default, list) else default
        st.rerun()
    part_filter = st.selectbox(
        "Part",
        options=["", "i-ii", "ii-ii"],
        format_func=lambda value: "All parts" if not value else value.upper(),
        key="corpus_part_filter",
    )

    status_options = ["parsed", "partial", "failed", "excluded"]
    status_filter = st.multiselect(
        "Parse status",
        options=status_options,
        default=["parsed", "partial"],
        key="corpus_status_filter",
    )
    title_query = st.text_input(
        "Question title search",
        placeholder="law, grace, justice, charity",
        key="corpus_title_query",
    )

question_rows = corpus_browser_rows(bundle, level="question", part_id=part_filter or None)
if status_filter:
    status_set = set(status_filter)
    question_rows = [row for row in question_rows if str(row["parse_status"]) in status_set]
if title_query.strip():
    normalized = title_query.casefold()
    question_rows = [
        row
        for row in question_rows
        if normalized in str(row["question_title"]).casefold()
        or normalized in str(row["question_id"]).casefold()
    ]

question_options = {
    "": "All visible questions",
    **{
        row["question_id"]: (
            f"{row['part_id'].upper()} q.{row['question_number']} — {row['question_title']}"
        )
        for row in question_rows
    },
}
if st.session_state["corpus_question_filter"] not in question_options:
    st.session_state["corpus_question_filter"] = ""

with st.sidebar:
    question_filter = st.selectbox(
        "Question spotlight",
        options=list(question_options),
        format_func=lambda value: question_options[value],
        key="corpus_question_filter",
    )

visible_question_count = len(question_rows)
parsed_question_count = sum(1 for row in question_rows if row["parse_status"] == "parsed")
partial_question_count = sum(1 for row in question_rows if row["parse_status"] == "partial")
excluded_question_count = sum(1 for row in question_rows if row["parse_status"] == "excluded")

render_metric_cards(
    [
        MetricCard(
            "Visible questions",
            compact_number(visible_question_count),
            "Questions remaining after the current structural filters.",
        ),
        MetricCard(
            "Parsed cleanly",
            compact_number(parsed_question_count),
            "Questions whose structural parse is currently complete.",
        ),
        MetricCard(
            "Partial parse",
            compact_number(partial_question_count),
            "Questions whose article or segment coverage still needs attention.",
        ),
        MetricCard(
            "Excluded",
            compact_number(excluded_question_count),
            "Rows preserved for scope audit rather than silently dropped.",
        ),
    ],
    columns=4,
)

if question_filter:
    spotlight = next(row for row in question_rows if row["question_id"] == question_filter)
    render_section_header(
        "Question Spotlight",
        "A focused structural view for the selected question before dropping to article level.",
    )
    render_pill_row(
        [
            f"{spotlight['part_id'].upper()} q.{spotlight['question_number']}",
            f"Status: {spotlight['parse_status']}",
            f"{spotlight['parsed_passage_count']} parsed passages",
            f"{spotlight['reviewed_annotation_count']} reviewed annotations",
        ],
        tone=status_tone(str(spotlight["parse_status"])),
    )
    render_key_value_card(
        str(spotlight["question_title"]),
        [
            ("Expected articles", compact_number(int(spotlight["expected_article_count"]))),
            ("Parsed articles", compact_number(int(spotlight["parsed_article_count"]))),
            ("Missing articles", format_question_list(list(spotlight["missing_article_numbers"]))),
            ("Warnings", compact_number(int(spotlight["warning_count"]))),
            ("Candidate mentions", compact_number(int(spotlight["candidate_mention_count"]))),
            (
                "Candidate relations",
                compact_number(int(spotlight["candidate_relation_count"])),
            ),
            ("Source", str(spotlight["source_url"])),
        ],
    )

render_section_header(
    "Question Coverage",
    "Question-level rows let you audit where the textual substrate is strong, partial, "
    "or intentionally excluded by scope.",
)
question_table = [
    {
        **row,
        "missing_article_numbers": format_question_list(list(row["missing_article_numbers"])),
    }
    for row in question_rows
]
st.dataframe(
    records_frame(
        question_table,
        columns=[
            "question_id",
            "question_title",
            "part_id",
            "question_number",
            "parse_status",
            "parsed_article_count",
            "expected_article_count",
            "parsed_passage_count",
            "reviewed_annotation_count",
            "candidate_mention_count",
            "candidate_relation_count",
            "warning_count",
            "missing_article_numbers",
        ],
        rename={
            "question_id": "Question id",
            "question_title": "Question title",
            "part_id": "Part",
            "question_number": "Q",
            "parse_status": "Status",
            "parsed_article_count": "Parsed articles",
            "expected_article_count": "Expected articles",
            "parsed_passage_count": "Parsed passages",
            "reviewed_annotation_count": "Reviewed annotations",
            "candidate_mention_count": "Candidate mentions",
            "candidate_relation_count": "Candidate relations",
            "warning_count": "Warnings",
            "missing_article_numbers": "Missing articles",
        },
    ),
    use_container_width=True,
    hide_index=True,
)
st.download_button(
    "Download question coverage CSV",
    data=dataframe_to_csv_bytes(
        records_frame(
            question_table,
            columns=[
                "question_id",
                "question_title",
                "part_id",
                "question_number",
                "parse_status",
                "parsed_article_count",
                "expected_article_count",
                "parsed_passage_count",
                "reviewed_annotation_count",
                "candidate_mention_count",
                "candidate_relation_count",
                "warning_count",
                "missing_article_numbers",
            ],
        )
    ),
    file_name="summa_moral_graph_question_coverage.csv",
    mime="text/csv",
    use_container_width=True,
)

if question_filter:
    article_rows = corpus_browser_rows(
        bundle,
        level="article",
        part_id=part_filter or None,
        question_id=question_filter,
    )
    article_table = [
        {
            **row,
            "missing_segment_types": ", ".join(str(value) for value in row["missing_segment_types"])
            or "None",
            "warning_types": ", ".join(str(value) for value in row["warning_types"]) or "None",
        }
        for row in article_rows
    ]
    render_section_header(
        "Article Coverage",
        "Article rows surface suspiciously short items, missing segment types, and "
        "review density inside the selected question.",
    )
    st.dataframe(
        records_frame(
            article_table,
            columns=[
                "article_id",
                "citation_label",
                "article_title",
                "parse_status",
                "segment_count",
                "char_count",
                "missing_segment_types",
                "reviewed_annotation_count",
                "candidate_mention_count",
                "candidate_relation_count",
                "warning_count",
                "suspiciously_short",
            ],
            rename={
                "article_id": "Article id",
                "citation_label": "Citation",
                "article_title": "Article title",
                "parse_status": "Status",
                "segment_count": "Segments",
                "char_count": "Characters",
                "missing_segment_types": "Missing segment types",
                "reviewed_annotation_count": "Reviewed annotations",
                "candidate_mention_count": "Candidate mentions",
                "candidate_relation_count": "Candidate relations",
                "warning_count": "Warnings",
                "suspiciously_short": "Short?",
            },
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download article coverage CSV",
        data=dataframe_to_csv_bytes(
            records_frame(
                article_table,
                columns=[
                    "article_id",
                    "citation_label",
                    "article_title",
                    "parse_status",
                    "segment_count",
                    "char_count",
                    "missing_segment_types",
                    "reviewed_annotation_count",
                    "candidate_mention_count",
                    "candidate_relation_count",
                    "warning_count",
                    "suspiciously_short",
                ],
            )
        ),
        file_name=f"{question_filter.replace('.', '_')}_article_coverage.csv",
        mime="text/csv",
        use_container_width=True,
    )
