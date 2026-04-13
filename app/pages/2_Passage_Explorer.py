from __future__ import annotations

import streamlit as st

from summa_moral_graph.app.corpus import (
    candidate_items_for_passage,
    highlight_passage_text,
    load_corpus_bundle,
    passage_activity_summary,
    passage_search,
    reviewed_annotations_for_passage,
)
from summa_moral_graph.app.tracts import TRACT_PRESETS, preset_label, preset_range
from summa_moral_graph.app.ui import (
    MetricCard,
    compact_number,
    configure_page,
    dataframe_to_csv_bytes,
    records_frame,
    render_key_value_card,
    render_metric_cards,
    render_pill_row,
    render_section_header,
)

configure_page(
    page_title="Evidence Browser",
    title="Evidence Browser",
    eyebrow="Evidence",
    description="Search passages and inspect reviewed and candidate evidence.",
)

bundle = load_corpus_bundle()
FILTER_DEFAULTS = {
    "passage_preset_filter": "",
    "passage_part_filter": "",
    "passage_question_filter": "",
    "passage_article_filter": "",
    "passage_segment_filter": "",
    "passage_query": "",
    "passage_result_limit": 24,
    "passage_question_range": (1, 182),
}

for key, default in FILTER_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

with st.sidebar:
    st.markdown("### Search Scope")
    if st.button("Reset filters", use_container_width=True):
        for key, default in FILTER_DEFAULTS.items():
            st.session_state[key] = default
        st.rerun()
    preset_filter = st.selectbox(
        "Saved tract preset",
        options=["", *TRACT_PRESETS],
        format_func=lambda value: "None" if not value else preset_label(value),
        key="passage_preset_filter",
    )
    part_filter = st.selectbox(
        "Part",
        options=["", "i-ii", "ii-ii"],
        format_func=lambda value: "All parts" if not value else value.upper(),
        key="passage_part_filter",
    )

    question_options = {
        "": "All questions",
        **{
            question_id: (
                f"{record.part_id.upper()} q.{record.question_number} — {record.question_title}"
            )
            for question_id, record in sorted(bundle.questions.items())
        },
    }
    question_filter = st.selectbox(
        "Question",
        options=list(question_options),
        format_func=lambda value: question_options[value],
        key="passage_question_filter",
    )

    article_options = {
        "": "All articles",
        **{
            row["article_id"]: str(row["citation_label"])
            for row in bundle.coverage["articles"]
            if not question_filter or row["question_id"] == question_filter
        },
    }
    if st.session_state["passage_article_filter"] not in article_options:
        st.session_state["passage_article_filter"] = ""
    article_filter = st.selectbox(
        "Article",
        options=list(article_options),
        format_func=lambda value: article_options[value],
        key="passage_article_filter",
    )
    segment_filter = st.selectbox(
        "Segment type",
        options=["", "obj", "sc", "resp", "ad"],
        format_func=lambda value: "All segment types" if not value else value,
        key="passage_segment_filter",
    )
    query = st.text_input(
        "Search",
        placeholder="passage id, citation, text, or concept label",
        key="passage_query",
    )
    result_limit = st.slider(
        "Visible results",
        min_value=8,
        max_value=60,
        step=4,
        key="passage_result_limit",
    )

question_range = (1, 182)
if (part_filter or "") == "ii-ii" or preset_filter:
    question_range = preset_range(preset_filter) if preset_filter else question_range
    with st.sidebar:
        question_range = st.slider(
            "II-II question range",
            min_value=1,
            max_value=182,
            value=question_range,
            key="passage_question_range",
        )

results = passage_search(
    bundle,
    query=query,
    part_id=("ii-ii" if preset_filter else part_filter) or None,
    question_id=question_filter or None,
    article_id=article_filter or None,
    segment_type=segment_filter or None,
)
if (part_filter or "") == "ii-ii" or preset_filter:
    start_question, end_question = question_range
    results = [
        passage
        for passage in results
        if passage.part_id == "ii-ii" and start_question <= passage.question_number <= end_question
    ]

activity_by_id = {
    passage.segment_id: passage_activity_summary(bundle, passage.segment_id) for passage in results
}
activity_rows = list(activity_by_id.values())
reviewed_hits = sum(1 for row in activity_rows if row["reviewed_annotations"] > 0)
candidate_hits = sum(
    1 for row in activity_rows if row["candidate_mentions"] > 0 or row["candidate_relations"] > 0
)

render_pill_row(
    [
        f"Preset: {preset_label(preset_filter) if preset_filter else 'None'}",
        f"Part: {(part_filter or 'all').upper() if part_filter else 'All parts'}",
        f"Range: II-II qq. {question_range[0]}-{question_range[1]}"
        if ((part_filter or "") == "ii-ii" or preset_filter)
        else "Range: full selected scope",
    ],
    tone="info",
)

render_metric_cards(
    [
        MetricCard(
            "Matching passages",
            compact_number(len(results)),
            "Canonical segments matching the current scope and query.",
        ),
        MetricCard(
            "Reviewed hits",
            compact_number(reviewed_hits),
            "Results with at least one reviewed annotation attached.",
        ),
        MetricCard(
            "Candidate-active hits",
            compact_number(candidate_hits),
            "Results carrying candidate mentions or relation proposals.",
        ),
        MetricCard(
            "Visible now",
            compact_number(min(len(results), result_limit)),
            "Result cards currently rendered on the page.",
        ),
    ],
    columns=4,
)

render_section_header(
    "Reading Key",
    "Reviewed evidence snippets are highlighted with a warm mark; candidate mention "
    "matches stay separately underlined.",
)
render_pill_row(["Reviewed evidence highlight", "Candidate mention underline"], tone="warn")

visible_results = results[:result_limit]
if not visible_results:
    render_key_value_card(
        "No passages matched",
        [
            (
                "Try",
                "Broaden the query, remove article filters, or switch to a wider tract preset.",
            ),
            ("Current query", query or "None"),
        ],
    )

visible_result_rows = [
    {
        "Passage id": passage.segment_id,
        "Citation": passage.citation_label,
        "Question": f"{passage.part_id.upper()} q.{passage.question_number}",
        "Article": passage.article_number,
        "Segment": passage.segment_type,
        "Reviewed annotations": activity_by_id[passage.segment_id]["reviewed_annotations"],
        "Candidate mentions": activity_by_id[passage.segment_id]["candidate_mentions"],
        "Candidate relations": activity_by_id[passage.segment_id]["candidate_relations"],
    }
    for passage in visible_results
]

if visible_result_rows:
    render_section_header(
        "Visible Result Index",
        "A compact index so users can scan the current result set quickly before opening "
        "individual passage cards.",
    )
    result_frame = records_frame(visible_result_rows)
    st.dataframe(result_frame, use_container_width=True, hide_index=True)
    download_left, download_right = st.columns(2)
    with download_left:
        st.download_button(
            "Download visible passages CSV",
            data=dataframe_to_csv_bytes(result_frame),
            file_name="summa_moral_graph_visible_passages.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with download_right:
        st.download_button(
            "Download visible passage ids CSV",
            data=dataframe_to_csv_bytes(
                records_frame(
                    [{"Passage id": row["Passage id"]} for row in visible_result_rows]
                )
            ),
            file_name="summa_moral_graph_visible_passage_ids.csv",
            mime="text/csv",
            use_container_width=True,
        )

for passage in visible_results:
    reviewed_rows = reviewed_annotations_for_passage(bundle, passage.segment_id)
    candidate_items = candidate_items_for_passage(bundle, passage.segment_id)
    counts = passage_activity_summary(bundle, passage.segment_id)
    expander_label = (
        f"{passage.citation_label} · {passage.segment_id} · "
        f"{counts['reviewed_annotations']} reviewed / "
        f"{counts['candidate_mentions']} candidate mentions"
    )
    with st.expander(expander_label):
        render_pill_row(
            [
                passage.part_id.upper(),
                f"q.{passage.question_number}",
                f"a.{passage.article_number}",
                f"segment: {passage.segment_type}",
                f"{counts['reviewed_annotations']} reviewed",
                f"{counts['candidate_mentions']} candidate mentions",
                f"{counts['candidate_relations']} candidate relations",
            ],
            tone="info",
        )
        render_key_value_card(
            "Passage Metadata",
            [
                ("Passage id", passage.segment_id),
                ("Citation", passage.citation_label),
                ("Question", passage.question_title),
                ("Article", passage.article_title),
                ("Characters", compact_number(int(passage.char_count))),
                ("Source", passage.source_url),
            ],
        )
        st.markdown(
            highlight_passage_text(
                passage.text,
                reviewed_rows,
                candidate_items["mentions"],
            ),
            unsafe_allow_html=True,
        )

        overview_tab, reviewed_tab, candidate_tab = st.tabs(
            ["Overview", "Reviewed Layer", "Candidate Layer"]
        )

        with overview_tab:
            render_key_value_card(
                "Activity Summary",
                [
                    ("Reviewed annotations", compact_number(counts["reviewed_annotations"])),
                    ("Candidate mentions", compact_number(counts["candidate_mentions"])),
                    ("Candidate relations", compact_number(counts["candidate_relations"])),
                ],
            )

        with reviewed_tab:
            render_section_header(
                "Reviewed Annotations",
                "Doctrinal and editorial review records tied directly to this passage.",
            )
            st.dataframe(
                records_frame(
                    reviewed_rows,
                    columns=[
                        "annotation_id",
                        "subject_label",
                        "relation_type",
                        "object_label",
                        "support_type",
                        "confidence",
                        "review_status",
                    ],
                    rename={
                        "annotation_id": "Annotation id",
                        "subject_label": "Subject",
                        "relation_type": "Relation",
                        "object_label": "Object",
                        "support_type": "Support",
                        "confidence": "Confidence",
                        "review_status": "Status",
                    },
                ),
                use_container_width=True,
                hide_index=True,
            )

        with candidate_tab:
            left_column, right_column = st.columns(2, gap="large")
            with left_column:
                render_section_header(
                    "Candidate Mentions",
                    "Potential concept detections awaiting human review.",
                )
                st.dataframe(
                    records_frame(
                        candidate_items["mentions"],
                        columns=[
                            "candidate_id",
                            "matched_text",
                            "proposed_concept_id",
                            "match_method",
                            "confidence",
                            "ambiguity_flag",
                        ],
                        rename={
                            "candidate_id": "Candidate id",
                            "matched_text": "Matched text",
                            "proposed_concept_id": "Proposed concept",
                            "match_method": "Match method",
                            "confidence": "Confidence",
                            "ambiguity_flag": "Ambiguous?",
                        },
                    ),
                    use_container_width=True,
                    hide_index=True,
                )
            with right_column:
                render_section_header(
                    "Candidate Relations",
                    "Unreviewed relation proposals derived from local textual or structural cues.",
                )
                st.dataframe(
                    records_frame(
                        candidate_items["relations"],
                        columns=[
                            "proposal_id",
                            "subject_id",
                            "relation_type",
                            "object_id",
                            "proposal_method",
                            "confidence",
                            "review_status",
                        ],
                        rename={
                            "proposal_id": "Proposal id",
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
