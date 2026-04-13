from __future__ import annotations

from html import escape
from textwrap import shorten
from typing import Iterable

import streamlit as st

from ..app.ui import MetricCard

LAYER_LABELS = {
    "reviewed_doctrinal": "Reviewed doctrine",
    "reviewed_structural": "Editorial correspondence",
    "structural": "Structural",
    "candidate": "Candidate",
}

LAYER_TONES = {
    "reviewed_doctrinal": "doctrine",
    "reviewed_structural": "editorial",
    "structural": "structural",
    "candidate": "candidate",
}


def configure_viewer_page(*, page_title: str = "Summa Moral Graph") -> None:
    st.set_page_config(
        page_title=page_title,
        page_icon="§",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_viewer_css()


def inject_viewer_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Newsreader:opsz,wght@6..72,500;6..72,700&family=JetBrains+Mono:wght@500&display=swap');

        :root {
          --smg-bg: #f4efe7;
          --smg-panel: rgba(255, 251, 246, 0.92);
          --smg-panel-strong: rgba(255, 252, 248, 0.98);
          --smg-line: rgba(22, 33, 49, 0.11);
          --smg-ink: #142235;
          --smg-muted: #5f6f82;
          --smg-accent: #8b442e;
          --smg-accent-soft: rgba(139, 68, 46, 0.12);
          --smg-doctrine: #214b66;
          --smg-editorial: #66788d;
          --smg-structural: #8c98a8;
          --smg-candidate: #af6f16;
          --smg-ok: #587041;
          --smg-shadow: 0 16px 38px rgba(29, 39, 49, 0.09);
          --smg-radius-xl: 28px;
          --smg-radius-lg: 22px;
          --smg-radius-md: 16px;
          --smg-radius-sm: 12px;
        }

        .stApp {
          background:
            radial-gradient(circle at 0% 0%, rgba(139, 68, 46, 0.07), transparent 26%),
            radial-gradient(circle at 100% 0%, rgba(33, 75, 102, 0.08), transparent 28%),
            linear-gradient(180deg, #f6f1ea 0%, #f4efe7 48%, #f1ebe1 100%);
          color: var(--smg-ink);
          font-family: "Manrope", sans-serif;
        }

        [data-testid="stSidebar"] {
          background:
            linear-gradient(180deg, rgba(255, 252, 247, 0.98), rgba(248, 242, 234, 0.98));
          border-right: 1px solid var(--smg-line);
        }

        .block-container {
          max-width: 1320px;
          padding-top: 2.1rem;
          padding-bottom: 3rem;
        }

        h1, h2, h3, h4 {
          font-family: "Newsreader", Georgia, serif;
          color: var(--smg-ink);
          letter-spacing: -0.02em;
        }

        p, li, label, [data-testid="stMarkdownContainer"] {
          font-family: "Manrope", sans-serif;
        }

        code, pre {
          font-family: "JetBrains Mono", monospace !important;
        }

        .smgv-shell-note {
          color: var(--smg-muted);
          font-size: 0.76rem;
          line-height: 1.35;
          margin-bottom: 0.25rem;
          opacity: 0.9;
        }

        .smgv-hero {
          padding: 1.15rem 1.2rem 1rem 1.2rem;
          border: 1px solid var(--smg-line);
          border-radius: var(--smg-radius-xl);
          background:
            linear-gradient(135deg, rgba(255, 252, 248, 0.99), rgba(249, 242, 234, 0.9));
          box-shadow: var(--smg-shadow);
          margin-bottom: 0.8rem;
        }

        .smgv-kicker {
          color: var(--smg-accent);
          font-size: 0.68rem;
          font-weight: 800;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          margin-bottom: 0.3rem;
        }

        .smgv-hero h1 {
          margin: 0;
          font-size: clamp(1.8rem, 3vw, 2.6rem);
          line-height: 1.02;
        }

        .smgv-hero p {
          margin: 0.45rem 0 0 0;
          max-width: 42rem;
          color: var(--smg-muted);
          font-size: 0.86rem;
          line-height: 1.55;
        }

        .smgv-section {
          margin: 0.8rem 0 0.4rem 0;
        }

        .smgv-section h2,
        .smgv-section h3 {
          margin: 0 0 0.2rem 0;
          font-size: 1.15rem;
        }

        .smgv-section p {
          margin: 0;
          color: var(--smg-muted);
          line-height: 1.45;
          font-size: 0.82rem;
          max-width: 56rem;
        }

        .smgv-card {
          border: 1px solid var(--smg-line);
          border-radius: var(--smg-radius-lg);
          background: var(--smg-panel);
          padding: 0.8rem 0.9rem;
          box-shadow: 0 10px 26px rgba(29, 39, 49, 0.05);
          height: 100%;
        }

        .smgv-card h3, .smgv-card h4 {
          margin: 0 0 0.2rem 0;
          line-height: 1.16;
          font-size: 1rem;
        }

        .smgv-card p {
          margin: 0;
          color: var(--smg-ink);
          line-height: 1.45;
          font-size: 0.84rem;
        }

        .smgv-small {
          color: var(--smg-muted);
          font-size: 0.76rem;
          line-height: 1.38;
        }

        .smgv-metric-card {
          border: 1px solid var(--smg-line);
          border-radius: 18px;
          background: rgba(255, 252, 248, 0.96);
          padding: 0.7rem 0.85rem;
          box-shadow: 0 8px 20px rgba(29, 39, 49, 0.04);
          min-height: 88px;
        }

        .smgv-metric-label {
          color: var(--smg-muted);
          text-transform: uppercase;
          font-size: 0.64rem;
          font-weight: 800;
          letter-spacing: 0.09em;
        }

        .smgv-metric-value {
          font-family: "Newsreader", Georgia, serif;
          font-size: 1.45rem;
          line-height: 1;
          margin-top: 0.28rem;
          color: var(--smg-ink);
        }

        .smgv-metric-caption {
          color: var(--smg-muted);
          font-size: 0.7rem;
          line-height: 1.28;
          margin-top: 0.24rem;
        }

        .smgv-side-list {
          margin: 0;
          padding-left: 1rem;
          color: var(--smg-muted);
          font-size: 0.8rem;
          line-height: 1.5;
        }

        .smgv-chart-shell {
          border: 1px solid var(--smg-line);
          border-radius: var(--smg-radius-lg);
          background: rgba(255, 252, 248, 0.95);
          padding: 0.7rem 0.8rem 0.3rem 0.8rem;
          box-shadow: 0 10px 26px rgba(29, 39, 49, 0.05);
        }

        .smgv-kv {
          display: grid;
          grid-template-columns: minmax(7rem, 9rem) 1fr;
          gap: 0.35rem 0.9rem;
        }

        .smgv-kv strong {
          color: var(--smg-muted);
          font-size: 0.82rem;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        .smgv-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 0.4rem;
          margin: 0.65rem 0 0.2rem 0;
        }

        .smgv-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.34rem 0.72rem;
          border-radius: 999px;
          border: 1px solid rgba(22, 33, 49, 0.10);
          background: rgba(255, 255, 255, 0.65);
          color: var(--smg-ink);
          font-size: 0.78rem;
          font-weight: 700;
        }

        .smgv-pill--doctrine { background: rgba(33, 75, 102, 0.12); }
        .smgv-pill--editorial { background: rgba(102, 120, 141, 0.14); }
        .smgv-pill--candidate { background: rgba(175, 111, 22, 0.14); }
        .smgv-pill--structural { background: rgba(140, 152, 168, 0.18); }
        .smgv-pill--ok { background: rgba(88, 112, 65, 0.14); }
        .smgv-pill--accent { background: rgba(139, 68, 46, 0.12); }

        .smgv-reading {
          border: 1px solid var(--smg-line);
          border-radius: var(--smg-radius-lg);
          background: var(--smg-panel-strong);
          padding: 1.15rem 1.2rem;
          line-height: 1.86;
          font-size: 1rem;
          box-shadow: 0 12px 28px rgba(29, 39, 49, 0.05);
        }

        .smgv-reading mark {
          background: rgba(139, 68, 46, 0.18);
          padding: 0.08rem 0.18rem;
          border-radius: 0.3rem;
        }

        .smgv-reading u {
          text-decoration-color: rgba(175, 111, 22, 0.95);
          text-decoration-thickness: 2px;
          text-underline-offset: 0.14rem;
        }

        .smgv-evidence {
          border-left: 3px solid rgba(33, 75, 102, 0.32);
          padding-left: 0.8rem;
          margin-top: 0.7rem;
        }

        .smgv-divider {
          height: 1px;
          background: var(--smg-line);
          margin: 0.9rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def top_nav(active_view: str, view_names: Iterable[str]) -> str:
    columns = st.columns(len(tuple(view_names)), gap="small")
    ordered = list(view_names)
    for column, view_name in zip(columns, ordered, strict=False):
        with column:
            if st.button(
                view_name,
                use_container_width=True,
                type="primary" if view_name == active_view else "secondary",
                key=f"smgv-nav-{view_name}",
            ):
                return view_name
    return active_view


def section_heading(title: str, description: str | None = None) -> None:
    description_html = f"<p>{escape(description)}</p>" if description else ""
    st.markdown(
        (
            "<div class='smgv-section'>"
            f"<h2>{escape(title)}</h2>"
            f"{description_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def hero(title: str, description: str, *, eyebrow: str) -> None:
    st.markdown(
        (
            "<div class='smgv-hero'>"
            f"<div class='smgv-kicker'>{escape(eyebrow)}</div>"
            f"<h1>{escape(title)}</h1>"
            f"<p>{escape(description)}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def card(title: str, body: str, *, kicker: str | None = None) -> None:
    kicker_html = f"<div class='smgv-kicker'>{escape(kicker)}</div>" if kicker else ""
    st.markdown(
        (
            "<div class='smgv-card'>"
            f"{kicker_html}"
            f"<h3>{escape(title)}</h3>"
            f"<p>{escape(body)}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def key_value_card(title: str, rows: list[tuple[str, str]]) -> None:
    items = "".join(
        f"<strong>{escape(label)}</strong><div>{escape(value)}</div>" for label, value in rows
    )
    st.markdown(
        (
            "<div class='smgv-card'>"
            f"<h3>{escape(title)}</h3>"
            f"<div class='smgv-kv'>{items}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def metric_cards(cards: list[MetricCard], *, columns: int = 4) -> None:
    if not cards:
        return
    rows = [cards[index : index + columns] for index in range(0, len(cards), columns)]
    for row in rows:
        cols = st.columns(len(row), gap="small")
        for column, metric in zip(cols, row, strict=False):
            with column:
                caption_html = (
                    (
                        "<div class='smgv-metric-caption'>"
                        f"{escape(metric.caption)}"
                        "</div>"
                    )
                    if metric.caption
                    else ""
                )
                st.markdown(
                    (
                        "<div class='smgv-metric-card'>"
                        f"<div class='smgv-metric-label'>{escape(metric.label)}</div>"
                        f"<div class='smgv-metric-value'>{escape(str(metric.value))}</div>"
                        f"{caption_html}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )


def pill_row(values: Iterable[str], *, tone: str = "accent") -> None:
    pills = "".join(
        f"<span class='smgv-pill smgv-pill--{escape(tone)}'>{escape(value)}</span>"
        for value in values
        if value
    )
    if not pills:
        return
    st.markdown(f"<div class='smgv-pills'>{pills}</div>", unsafe_allow_html=True)


def layer_badges(layers: Iterable[str]) -> None:
    values = [
        f"{LAYER_LABELS.get(layer, layer)}"
        for layer in layers
    ]
    pills = "".join(
        f"<span class='smgv-pill smgv-pill--{LAYER_TONES.get(layer, 'accent')}'>"
        f"{escape(LAYER_LABELS.get(layer, layer))}</span>"
        for layer in layers
    )
    if not values:
        return
    st.markdown(f"<div class='smgv-pills'>{pills}</div>", unsafe_allow_html=True)


def empty_state(title: str, body: str) -> None:
    card(title, body)


def reading_panel(title: str, metadata: list[str], html_body: str) -> None:
    pill_row(metadata, tone="accent")
    st.markdown(
        (
            "<div class='smgv-reading'>"
            f"<div style='font-family:Newsreader,serif;font-size:1.35rem;margin-bottom:0.9rem'>"
            f"{escape(title)}</div>"
            f"{html_body}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def support_card(title: str, body: str, *, meta: str | None = None) -> None:
    meta_html = (
        (
            "<div class='smgv-small' style='margin-bottom:0.45rem'>"
            f"{escape(meta)}"
            "</div>"
        )
        if meta
        else ""
    )
    st.markdown(
        (
            "<div class='smgv-card'>"
            f"<h4>{escape(title)}</h4>"
            f"{meta_html}"
            f"<p>{escape(shorten(body, width=420, placeholder='…'))}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def info_note(text: str) -> None:
    st.markdown(
        f"<div class='smgv-shell-note'>{escape(text)}</div>",
        unsafe_allow_html=True,
    )
