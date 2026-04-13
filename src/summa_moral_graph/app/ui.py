from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path
from textwrap import shorten
from typing import Any, Iterable, Sequence

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class MetricCard:
    label: str
    value: str
    caption: str = ""
    tone: str = "ink"
    tooltip: str = ""


APP_PAGE_LINKS: list[dict[str, str]] = [
    {
        "label": "Dashboard",
        "path": "Home.py",
        "description": "Tract status, review queues, and exports.",
    },
    {
        "label": "Corpus Coverage",
        "path": "pages/1_Corpus_Browser.py",
        "description": "Question and article coverage.",
    },
    {
        "label": "Evidence Browser",
        "path": "pages/2_Passage_Explorer.py",
        "description": "Search passages and inspect evidence.",
    },
    {
        "label": "Concept Network",
        "path": "pages/3_Concept_Explorer.py",
        "description": "Concepts, edges, and supporting passages.",
    },
    {
        "label": "Relationship Map",
        "path": "pages/4_Graph_View.py",
        "description": "Filter graph edges and inspect support.",
    },
    {
        "label": "Health & Audit",
        "path": "pages/5_Stats.py",
        "description": "Diagnostics and validation.",
    },
]


GRAPH_FOCUS_TAG_OPTIONS: list[str] = [
    "justice_species",
    "harmed_domain",
    "judicial_process",
    "restitution_related",
    "positive_act",
    "excess",
    "deficiency",
    "divine_name_related",
    "offering_promise_exchange",
    "sacred_object",
    "origin_due",
    "excellence_due",
    "authority_due",
    "benefaction_due",
    "rectificatory_due",
    "role_level",
    "self_presentation",
    "social_interaction",
    "external_goods",
    "legal_equity",
    "schema_extension",
    "excess_opposition",
    "deficiency_opposition",
    "honor_related",
    "expenditure_related",
    "fortitude_related",
    "patience",
    "perseverance",
    "opposed_vice",
    "gift",
    "precept",
    "synthesis",
    "temperance_proper",
    "general_integral",
    "food_drink",
    "sexual",
    "potential_parts",
    "integral_part",
    "subjective_part",
    "potential_part",
    "food",
    "drink",
    "sex",
    "continence_incontinence",
    "meekness_anger",
    "clemency_cruelty",
    "modesty_general",
    "humility_pride",
    "adams_first_sin",
    "adam_case",
    "study_curiosity",
    "external_modesty",
    "external_behavior",
    "external_attire",
    "precept_linkage",
]


def configure_page(
    *,
    page_title: str,
    title: str,
    description: str,
    eyebrow: str,
) -> None:
    st.set_page_config(
        page_title=page_title,
        page_icon="§",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()
    render_sidebar(page_title=title, description=description)
    render_page_header(eyebrow=eyebrow, title=title, description=description)


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');

        :root {
          --smg-bg: #f6efe3;
          --smg-surface: rgba(255, 251, 245, 0.84);
          --smg-surface-strong: rgba(255, 251, 245, 0.96);
          --smg-ink: #13273f;
          --smg-muted: #53657d;
          --smg-line: rgba(19, 39, 63, 0.12);
          --smg-accent: #a64b2a;
          --smg-accent-soft: rgba(166, 75, 42, 0.12);
          --smg-olive: #6a7c48;
          --smg-gold: #c18d2d;
          --smg-shadow: 0 18px 44px rgba(33, 44, 55, 0.10);
          --smg-radius-lg: 24px;
          --smg-radius-md: 18px;
          --smg-radius-sm: 12px;
        }

        .stApp {
          background:
            radial-gradient(circle at 4% 0%, rgba(193, 141, 45, 0.15), transparent 24%),
            radial-gradient(circle at 84% 8%, rgba(106, 124, 72, 0.12), transparent 26%),
            linear-gradient(180deg, #f4ecdf 0%, #fbf7f0 42%, #f3eadb 100%);
          color: var(--smg-ink);
          font-family: "Public Sans", sans-serif;
        }

        [data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, rgba(255, 252, 247, 0.94), rgba(247, 241, 231, 0.96));
          border-right: 1px solid var(--smg-line);
        }

        h1, h2, h3, h4 {
          color: var(--smg-ink);
          font-family: "Fraunces", Georgia, serif;
          letter-spacing: -0.02em;
        }

        p, li, label, [data-testid="stMarkdownContainer"] {
          font-family: "Public Sans", sans-serif;
        }

        code, pre {
          font-family: "JetBrains Mono", monospace !important;
        }

        .smg-hero {
          padding: 1.4rem 1.4rem 1.2rem 1.4rem;
          border: 1px solid var(--smg-line);
          border-radius: var(--smg-radius-lg);
          background:
            linear-gradient(135deg, rgba(255, 252, 247, 0.98), rgba(250, 244, 235, 0.86));
          box-shadow: var(--smg-shadow);
          margin-bottom: 1rem;
        }

        .smg-eyebrow {
          margin-bottom: 0.35rem;
          color: var(--smg-accent);
          font-size: 0.78rem;
          letter-spacing: 0.16em;
          font-weight: 700;
          text-transform: uppercase;
        }

        .smg-hero h1 {
          margin: 0;
          font-size: clamp(2rem, 4vw, 3.3rem);
          line-height: 1.02;
        }

        .smg-hero p {
          margin: 0.8rem 0 0 0;
          max-width: 56rem;
          font-size: 1rem;
          line-height: 1.72;
          color: var(--smg-muted);
        }

        .smg-section-title {
          margin: 1.1rem 0 0.3rem 0;
          font-family: "Fraunces", Georgia, serif;
          font-size: 1.35rem;
        }

        .smg-section-copy {
          margin: 0 0 0.8rem 0;
          color: var(--smg-muted);
          line-height: 1.65;
        }

        .smg-card {
          padding: 1rem 1rem 0.95rem 1rem;
          border-radius: var(--smg-radius-md);
          border: 1px solid var(--smg-line);
          background: var(--smg-surface);
          box-shadow: 0 10px 28px rgba(33, 44, 55, 0.06);
          backdrop-filter: blur(12px);
        }

        .smg-card + .smg-card {
          margin-top: 0.8rem;
        }

        .smg-metric-card {
          min-height: 132px;
        }

        .smg-metric-label {
          color: var(--smg-muted);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-size: 0.72rem;
          font-weight: 700;
        }

        .smg-metric-value {
          margin-top: 0.55rem;
          color: var(--smg-ink);
          font-family: "Fraunces", Georgia, serif;
          font-size: clamp(1.7rem, 2vw, 2.4rem);
          line-height: 1;
        }

        .smg-metric-caption {
          margin-top: 0.55rem;
          color: var(--smg-muted);
          font-size: 0.9rem;
          line-height: 1.5;
        }

        .smg-help {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 1rem;
          height: 1rem;
          margin-left: 0.35rem;
          border-radius: 999px;
          background: rgba(19, 39, 63, 0.08);
          color: var(--smg-ink);
          font-size: 0.68rem;
          font-weight: 800;
          vertical-align: middle;
          cursor: help;
        }

        .smg-pill-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.42rem;
          margin: 0.65rem 0 0.25rem 0;
        }

        .smg-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.34rem 0.7rem;
          border-radius: 999px;
          border: 1px solid rgba(19, 39, 63, 0.09);
          background: rgba(255, 255, 255, 0.58);
          color: var(--smg-ink);
          font-size: 0.78rem;
          font-weight: 600;
        }

        .smg-pill.ok { background: rgba(106, 124, 72, 0.14); }
        .smg-pill.warn { background: rgba(193, 141, 45, 0.18); }
        .smg-pill.alert { background: rgba(166, 75, 42, 0.16); }
        .smg-pill.info { background: rgba(19, 39, 63, 0.08); }

        .smg-kv {
          display: grid;
          grid-template-columns: minmax(7rem, 9rem) 1fr;
          gap: 0.35rem 1rem;
          align-items: start;
        }

        .smg-kv strong {
          color: var(--smg-ink);
          font-size: 0.82rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .smg-kv span {
          color: var(--smg-muted);
          line-height: 1.6;
        }

        .smg-snippet {
          padding: 0.9rem 1rem;
          border-radius: var(--smg-radius-md);
          background: rgba(255, 255, 255, 0.72);
          border-left: 4px solid var(--smg-accent);
          border: 1px solid rgba(19, 39, 63, 0.08);
          line-height: 1.72;
        }

        .smg-sidebar-brand {
          padding: 1rem 0.1rem 0.4rem 0.1rem;
        }

        .smg-sidebar-brand h2 {
          margin: 0;
          font-size: 1.5rem;
        }

        .smg-sidebar-brand p {
          margin: 0.45rem 0 0 0;
          color: var(--smg-muted);
          line-height: 1.6;
          font-size: 0.92rem;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.55rem;
          background: rgba(255, 255, 255, 0.42);
          border-radius: 999px;
          padding: 0.35rem;
          border: 1px solid var(--smg-line);
        }

        .stTabs [data-baseweb="tab"] {
          height: auto;
          border-radius: 999px;
          padding: 0.45rem 0.95rem;
          font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
          background: rgba(19, 39, 63, 0.92) !important;
          color: #fff !important;
        }

        .streamlit-expanderHeader {
          font-weight: 700;
          color: var(--smg-ink);
        }

        div[data-testid="stDataFrame"] {
          border-radius: var(--smg-radius-md);
          border: 1px solid var(--smg-line);
          overflow: hidden;
          box-shadow: 0 8px 24px rgba(33, 44, 55, 0.05);
        }

        mark {
          background: rgba(193, 141, 45, 0.25);
          padding: 0.1rem 0.18rem;
          border-radius: 0.3rem;
        }

        u {
          text-decoration-color: rgba(166, 75, 42, 0.8);
          text-decoration-thickness: 2px;
          text-underline-offset: 0.16rem;
        }

        @media (max-width: 900px) {
          .smg-hero {
            padding: 1.1rem;
            border-radius: 20px;
          }

          .smg-kv {
            grid-template-columns: 1fr;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(*, page_title: str, description: str) -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="smg-sidebar-brand">
              <div class="smg-eyebrow">Summa Moral Graph</div>
              <h2>{escape(page_title)}</h2>
              <p>{escape(description)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("### Navigate")
        for item in APP_PAGE_LINKS:
            st.page_link(item["path"], label=item["label"], use_container_width=True)
            st.caption(item["description"])
        st.markdown("### Evidence Discipline")
        render_pill_row(
            [
                "Reviewed doctrine",
                "Structural/editorial",
                "Candidate review",
                "Segment-level evidence",
            ],
            tone="info",
        )
        st.caption(
            "Reviewed facts, editorial correspondences, and candidate proposals remain "
            "separate throughout the app."
        )


def render_page_header(*, eyebrow: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <section class="smg-hero">
          <div class="smg-eyebrow">{escape(eyebrow)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(description)}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str | None = None) -> None:
    st.markdown(f"<div class='smg-section-title'>{escape(title)}</div>", unsafe_allow_html=True)
    if description:
        st.markdown(
            f"<div class='smg-section-copy'>{escape(description)}</div>",
            unsafe_allow_html=True,
        )


def render_metric_cards(metrics: Sequence[MetricCard], *, columns: int = 4) -> None:
    if not metrics:
        return
    row_columns = st.columns(columns)
    for index, metric in enumerate(metrics):
        column = row_columns[index % columns]
        with column:
            label_markup = escape(metric.label)
            if metric.tooltip:
                label_markup += (
                    f"<span class='smg-help' title='{escape(metric.tooltip)}'>?</span>"
                )
            st.markdown(
                f"""
                <div class="smg-card smg-metric-card">
                  <div class="smg-metric-label">{label_markup}</div>
                  <div class="smg-metric-value">{escape(metric.value)}</div>
                  <div class="smg-metric-caption">{escape(metric.caption)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if (index + 1) % columns == 0 and index + 1 < len(metrics):
            row_columns = st.columns(columns)


def render_pill_row(
    items: Iterable[str],
    *,
    tone: str = "info",
) -> None:
    badges = [
        f"<span class='smg-pill {escape(tone)}'>{escape(str(item))}</span>"
        for item in items
        if str(item).strip()
    ]
    if not badges:
        return
    st.markdown(
        "<div class='smg-pill-row'>" + "".join(badges) + "</div>",
        unsafe_allow_html=True,
    )


def render_key_value_card(title: str, rows: Sequence[tuple[str, str]]) -> None:
    parts = [
        f"<strong>{escape(key)}</strong><span>{escape(value)}</span>"
        for key, value in rows
        if value
    ]
    st.markdown(
        f"""
        <div class="smg-card">
          <div class="smg-section-title" style="margin-top:0;">{escape(title)}</div>
          <div class="smg-kv">{"".join(parts)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_surface_card(title: str, body: str, *, tone: str = "info") -> None:
    st.markdown(
        f"""
        <div class="smg-card">
          <div class="smg-pill-row">
            <span class="smg-pill {escape(tone)}">{escape(title)}</span>
          </div>
          <div class="smg-section-copy" style="margin-top:0.65rem;">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_navigation_cards() -> None:
    render_section_header(
        "Start Here",
        "Pick a path.",
    )
    columns = st.columns(3)
    for index, item in enumerate(APP_PAGE_LINKS):
        with columns[index % 3]:
            st.markdown(
                f"""
                <div class="smg-card">
                  <div class="smg-section-title" style="margin-top:0;">{escape(item["label"])}</div>
                  <div class="smg-section-copy">{escape(item["description"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(item["path"], label=f"Open {item['label']}", use_container_width=True)


def pretty_tag(tag: str) -> str:
    return tag.replace("_", " ").replace("-", " ").strip().title()


def compact_number(value: int) -> str:
    return f"{value:,}"


def format_question_list(values: Sequence[int], *, limit: int = 6) -> str:
    if not values:
        return "None"
    ordered = [str(value) for value in values]
    if len(ordered) <= limit:
        return ", ".join(ordered)
    head = ", ".join(ordered[:limit])
    return f"{head}, +{len(ordered) - limit} more"


def status_tone(status: str) -> str:
    normalized = status.casefold()
    if normalized in {"ok", "parsed", "complete"}:
        return "ok"
    if normalized in {"partial", "warning", "warn"}:
        return "warn"
    return "alert"


def basename(path: str | None) -> str:
    if not path:
        return "None"
    return Path(path).name


def records_frame(
    records: Sequence[dict[str, Any]],
    *,
    columns: Sequence[str] | None = None,
    rename: dict[str, str] | None = None,
) -> pd.DataFrame:
    if not records:
        if columns is None:
            return pd.DataFrame()
        frame = pd.DataFrame(columns=list(columns))
    else:
        frame = pd.DataFrame.from_records(records)
    if columns is not None:
        available = [column for column in columns if column in frame.columns]
        frame = frame.loc[:, available]
    if rename:
        frame = frame.rename(columns=rename)
    return frame


def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    csv_text: str = frame.to_csv(index=False)
    return csv_text.encode("utf-8")


def payload_to_json_bytes(payload: Any) -> bytes:
    serialized: str = json.dumps(payload, ensure_ascii=False, indent=2)
    return serialized.encode("utf-8")


def format_edge_option(edge: dict[str, Any]) -> str:
    layer = str(edge.get("layer", "reviewed_doctrinal")).replace("_", " ")
    subject = str(edge.get("subject_label", edge.get("subject_id", "subject")))
    relation = str(edge.get("relation_type", "relation")).replace("_", " ")
    object_label = str(edge.get("object_label", edge.get("object_id", "object")))
    return shorten(
        f"{layer}: {subject} -> {relation} -> {object_label}",
        width=108,
        placeholder="…",
    )


def render_passage_cards(
    passages: Sequence[dict[str, Any]],
    *,
    max_items: int = 6,
) -> None:
    for passage in passages[:max_items]:
        citation = str(passage.get("citation_label", "Passage"))
        passage_id = str(passage.get("passage_id", ""))
        text = shorten(str(passage.get("text", "")), width=420, placeholder="…")
        st.markdown(
            f"""
            <div class="smg-card">
              <div class="smg-section-title" style="margin-top:0;">{escape(citation)}</div>
              <div class="smg-section-copy"><code>{escape(passage_id)}</code></div>
              <div class="smg-snippet">{escape(text)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_evidence_panel(panel: dict[str, Any]) -> None:
    source = str(panel.get("source_concept", "Source"))
    relation = str(panel.get("relation_type", "relation"))
    target = str(panel.get("target_concept", "Target"))
    support_type = panel.get("support_type")
    support_text = ", ".join(support_type) if isinstance(support_type, list) else str(support_type)
    layer_text = str(panel.get("layer", "reviewed_doctrinal"))
    st.markdown(
        f"""
        <div class="smg-card">
          <div class="smg-section-title" style="margin-top:0;">Evidence Panel</div>
          <div class="smg-kv">
            <strong>Source</strong><span>{escape(source)}</span>
            <strong>Relation</strong><span>{escape(relation)}</span>
            <strong>Target</strong><span>{escape(target)}</span>
            <strong>Layer</strong><span>{escape(layer_text)}</span>
            <strong>Support</strong><span>{escape(support_text or "n/a")}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    focus_tags = [
        pretty_tag(tag)
        for key, value in panel.items()
        if key.endswith("_focus_tags") and isinstance(value, list)
        for tag in value
    ]
    if focus_tags:
        render_pill_row(focus_tags, tone="info")

    for key, value in panel.items():
        if key.endswith("_scope_cluster") and value:
            render_pill_row([pretty_tag(str(value))], tone="warn")

    distinctions = next(
        (
            value
            for key, value in panel.items()
            if key.endswith("_distinctions") and isinstance(value, dict)
        ),
        None,
    )
    if distinctions:
        render_key_value_card(
            "Distinctions",
            [
                (pretty_tag(str(key)), "Yes" if bool(value) else "No")
                for key, value in distinctions.items()
            ],
        )

    render_key_value_card(
        "Traceability",
        [
            (
                "Annotation ids",
                ", ".join(str(value) for value in panel.get("supporting_annotation_ids", []))
                or "None",
            ),
            (
                "Passage ids",
                ", ".join(str(value) for value in panel.get("supporting_passage_ids", []))
                or "None",
            ),
        ],
    )

    snippets = panel.get("evidence_snippets", [])
    if snippets:
        render_section_header(
            "Evidence Snippets",
            "Short textual supports attached to the selected relation.",
        )
        for snippet in snippets[:5]:
            st.markdown(
                f"<div class='smg-snippet'>{escape(str(snippet))}</div>",
                unsafe_allow_html=True,
            )

    passages = panel.get("passages", [])
    if passages:
        render_section_header(
            "Supporting Passages",
            "Passages backing the selected edge after range and layer filters are applied.",
        )
        render_passage_cards(passages, max_items=4)
