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

NAV_LABELS = {
    "Home": "Home",
    "Concept Explorer": "Concepts",
    "Passage Explorer": "Passages",
    "Overall Map": "Map",
    "Stats / Audit": "Stats",
}


def configure_viewer_page(*, page_title: str = "Summa Virtutum") -> None:
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
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&family=Cinzel+Decorative:wght@700&family=Cormorant+Garamond:ital,wght@0,500;0,600;0,700;1,500;1,600;1,700&family=JetBrains+Mono:wght@500&family=Manrope:wght@400;500;600;700;800&display=swap');

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
          max-width: 1460px;
          padding-top: 2.86rem;
          padding-bottom: 2.55rem;
        }

        h1, h2, h3, h4 {
          font-family: "Cormorant Garamond", Georgia, serif;
          color: var(--smg-ink);
          letter-spacing: -0.02em;
          font-weight: 600;
        }

        p, li, label, [data-testid="stMarkdownContainer"] {
          font-family: "Manrope", sans-serif;
        }

        code, pre {
          font-family: "JetBrains Mono", monospace !important;
        }

        .smgv-shell-note {
          color: var(--smg-muted);
          font-size: 0.72rem;
          line-height: 1.35;
          margin-bottom: 0.25rem;
          opacity: 0.9;
        }

        .smgv-shell-note--hero {
          display: inline-flex;
          align-items: center;
          gap: 0.52rem;
          color: rgba(20, 34, 53, 0.72);
          font-size: 0.66rem;
          font-family: "Cinzel", Georgia, serif;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin-bottom: 0.14rem;
        }

        .smgv-shell-note--hero::before {
          content: "";
          width: 2.2rem;
          height: 1px;
          background: linear-gradient(
            90deg,
            rgba(139, 68, 46, 0),
            rgba(139, 68, 46, 0.26) 35%,
            rgba(139, 68, 46, 0.52)
          );
        }

        .smgv-hero {
          padding: 0.82rem 1.12rem 0.72rem 1.12rem;
          border: 1px solid var(--smg-line);
          border-radius: var(--smg-radius-xl);
          background:
            linear-gradient(135deg, rgba(255, 252, 248, 0.99), rgba(249, 242, 234, 0.9));
          box-shadow: var(--smg-shadow);
          margin-bottom: 0.28rem;
          position: relative;
          overflow: hidden;
        }

        .smgv-hero::before {
          content: "";
          position: absolute;
          inset: 10px;
          border: 1px solid rgba(20, 34, 53, 0.08);
          border-radius: calc(var(--smg-radius-xl) - 10px);
          pointer-events: none;
        }

        .smgv-kicker {
          display: inline-flex;
          align-items: center;
          gap: 0.52rem;
          color: var(--smg-accent);
          font-size: 0.68rem;
          font-family: "Cinzel", "Cormorant Garamond", Georgia, serif;
          font-weight: 600;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          margin-bottom: 0.18rem;
        }

        .smgv-kicker::before,
        .smgv-kicker::after {
          content: "";
          width: 2.4rem;
          height: 1px;
          background: linear-gradient(
            90deg,
            rgba(139, 68, 46, 0),
            rgba(139, 68, 46, 0.34) 35%,
            rgba(139, 68, 46, 0.58)
          );
        }

        .smgv-kicker::after {
          background: linear-gradient(
            90deg,
            rgba(139, 68, 46, 0.58),
            rgba(139, 68, 46, 0.34) 65%,
            rgba(139, 68, 46, 0)
          );
        }

        .smgv-hero h1 {
          margin: 0;
          font-family: "Cinzel Decorative", "Cinzel", "Cormorant Garamond", Georgia, serif;
          font-size: clamp(2.85rem, 4.8vw, 4.35rem);
          line-height: 0.92;
          letter-spacing: 0.012em;
          font-weight: 700;
          text-wrap: balance;
        }

        .smgv-hero-subtitle {
          margin: 0.28rem 0 0 0;
          max-width: 40rem;
          color: rgba(36, 56, 77, 0.82);
          font-family: "Cormorant Garamond", Georgia, serif;
          font-size: 1.18rem;
          font-style: italic;
          font-weight: 600;
          line-height: 1.12;
          letter-spacing: 0.015em;
          text-wrap: balance;
        }

        .smgv-hero-subtitle::after {
          content: "";
          display: block;
          width: 8.8rem;
          height: 1px;
          margin-top: 0.46rem;
          background: linear-gradient(
            90deg,
            rgba(139, 68, 46, 0.62),
            rgba(139, 68, 46, 0.18) 72%,
            rgba(139, 68, 46, 0)
          );
        }

        .smgv-hero-byline {
          display: inline-flex;
          align-items: center;
          gap: 0.38rem;
          margin-top: 0.18rem;
          color: rgba(20, 34, 53, 0.7);
          font-size: 0.64rem;
          font-family: "Cinzel", Georgia, serif;
          line-height: 1;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }

        .smgv-hero-byline a {
          display: inline-flex;
          align-items: center;
          gap: 0.32rem;
          color: rgba(20, 34, 53, 0.72);
          text-decoration: none;
          transition: color 120ms ease;
        }

        .smgv-hero-byline a:hover {
          color: var(--smg-accent);
        }

        .smgv-hero-byline svg {
          width: 0.82rem;
          height: 0.82rem;
          display: block;
          opacity: 0.88;
        }

        .smgv-section {
          margin: 0.62rem 0 0.34rem 0;
        }

        .smgv-section h2,
        .smgv-section h3 {
          margin: 0 0 0.2rem 0;
          font-size: 1.18rem;
          line-height: 1.02;
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
          padding: 0.92rem 1rem;
          box-shadow: 0 10px 26px rgba(29, 39, 49, 0.05);
          height: 100%;
          position: relative;
          overflow: hidden;
        }

        .smgv-card::before {
          content: "";
          position: absolute;
          inset: 8px;
          border: 1px solid rgba(20, 34, 53, 0.05);
          border-radius: calc(var(--smg-radius-lg) - 8px);
          pointer-events: none;
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

        .smgv-route-card-head {
          margin: 0.04rem 0 0.32rem 0;
          padding-top: 0.02rem;
        }

        .smgv-route-index {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 2.1rem;
          height: 1.62rem;
          padding: 0 0.62rem;
          margin-bottom: 0.46rem;
          border-radius: 999px;
          border: 1px solid rgba(139, 68, 46, 0.24);
          background:
            linear-gradient(180deg, rgba(255,255,255,0.95), rgba(246, 237, 225, 0.96));
          color: var(--smg-accent);
          font-size: 0.72rem;
          font-family: "Cinzel", Georgia, serif;
          font-weight: 700;
          letter-spacing: 0.08em;
          box-shadow:
            inset 0 0 0 1px rgba(20, 34, 53, 0.05),
            0 6px 14px rgba(29, 39, 49, 0.05);
        }

        .smgv-route-title {
          color: var(--smg-ink);
          font-size: 0.9rem;
          font-family: "Cinzel", "Cormorant Garamond", Georgia, serif;
          font-weight: 600;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          margin-bottom: 0.18rem;
        }

        .smgv-route-copy {
          color: var(--smg-muted);
          font-size: 0.72rem;
          line-height: 1.34;
          min-height: 2.02rem;
        }

        .smgv-route-preview {
          position: relative;
          margin: -0.2rem 0 0.08rem 0;
          border-radius: 0;
          overflow: visible;
          border: none;
          box-shadow: none;
          background: transparent;
        }

        .smgv-route-preview-surface {
          position: relative;
          width: 100%;
          height: 3.72rem;
        }

        .smgv-route-preview::after {
          content: "";
          position: absolute;
          inset: 0;
          background: none;
          pointer-events: none;
        }

        .smgv-route-preview--map {
          background: transparent;
        }

        .smgv-route-preview--map::after {
          background: none;
        }

        .smgv-route-map-svg {
          display: block;
          width: 100%;
          height: 100%;
        }

        .smgv-route-control-spacer {
          height: 0.06rem;
        }

        .smgv-route-control-spacer--tract {
          height: 0.58rem;
        }

        .smgv-route-control-spacer--map {
          height: 0.04rem;
        }

        .smgv-start-divider {
          position: relative;
          height: 0.62rem;
          margin: 0.04rem 0 0.1rem 0;
        }

        .smgv-start-divider--top {
          height: 0.36rem;
          margin: 0 0 0.12rem 0;
        }

        .smgv-start-divider--rows {
          height: 1.12rem;
          margin: 0.22rem 0 0.34rem 0;
        }

        .smgv-start-tight {
          height: 0.01rem;
          margin-top: -0.18rem;
          margin-bottom: -0.02rem;
        }

        .smgv-start-divider::before {
          content: "";
          position: absolute;
          left: 0;
          right: 0;
          top: 50%;
          height: 1px;
          background: linear-gradient(
            90deg,
            rgba(20, 34, 53, 0),
            rgba(20, 34, 53, 0.12) 18%,
            rgba(139, 68, 46, 0.18) 50%,
            rgba(20, 34, 53, 0.12) 82%,
            rgba(20, 34, 53, 0)
          );
          transform: translateY(-50%);
        }

        .smgv-start-divider--rows::after {
          content: "";
          position: absolute;
          left: 50%;
          top: 50%;
          width: 5.4rem;
          height: 0.32rem;
          border-radius: 999px;
          transform: translate(-50%, -50%);
          background: linear-gradient(
            90deg,
            rgba(20, 34, 53, 0),
            rgba(139, 68, 46, 0.3) 24%,
            rgba(139, 68, 46, 0.56) 50%,
            rgba(139, 68, 46, 0.3) 76%,
            rgba(20, 34, 53, 0)
          );
          pointer-events: none;
          box-shadow:
            0 -5px 0 rgba(20, 34, 53, 0.08),
            0 5px 0 rgba(20, 34, 53, 0.08);
        }

        .smgv-home-snapshot-lift {
          height: 0.04rem;
          margin-top: -2.72rem;
        }

        .smgv-start-v-divider {
          position: relative;
          min-height: 100%;
          height: 9.65rem;
          margin: 0.12rem 0 0.16rem 0;
        }

        .smgv-start-v-divider::before {
          content: "";
          position: absolute;
          top: 0;
          bottom: 0;
          left: 50%;
          width: 2px;
          transform: translateX(-50%);
          background: linear-gradient(
            180deg,
            rgba(20, 34, 53, 0),
            rgba(20, 34, 53, 0.18) 14%,
            rgba(139, 68, 46, 0.28) 50%,
            rgba(20, 34, 53, 0.18) 86%,
            rgba(20, 34, 53, 0)
          );
          box-shadow:
            0 0 0 1px rgba(255,255,255,0.18),
            0 0 24px rgba(139, 68, 46, 0.06);
        }

        .smgv-start-v-divider::after {
          content: "";
          position: absolute;
          left: 50%;
          top: 50%;
          width: 0.52rem;
          height: 0.52rem;
          transform: translate(-50%, -50%);
          border-radius: 999px;
          background:
            radial-gradient(circle, rgba(139, 68, 46, 0.34), rgba(139, 68, 46, 0.02) 72%);
        }

        .smgv-small {
          color: var(--smg-muted);
          font-size: 0.76rem;
          line-height: 1.38;
        }

        .smgv-download-note {
          margin: 0.06rem 0 0.38rem 0;
          color: rgba(20, 34, 53, 0.66);
          font-size: 0.68rem;
          line-height: 1.35;
        }

        .smgv-meta-line {
          display: flex;
          flex-wrap: wrap;
          gap: 0.45rem 0.75rem;
          margin: 0.4rem 0 0.35rem 0;
          color: var(--smg-muted);
          font-size: 0.77rem;
          line-height: 1.4;
        }

        .smgv-meta-item {
          display: inline-flex;
          align-items: baseline;
          gap: 0.3rem;
        }

        .smgv-meta-label {
          color: var(--smg-muted);
          text-transform: uppercase;
          letter-spacing: 0.06em;
          font-size: 0.66rem;
          font-weight: 800;
        }

        .smgv-meta-value {
          color: var(--smg-ink);
          font-weight: 600;
        }

        .smgv-inline-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 0.38rem 0.62rem;
          margin: 0.3rem 0 0.2rem 0;
          color: var(--smg-muted);
          font-size: 0.74rem;
          line-height: 1.35;
        }

        .smgv-inline-meta span {
          display: inline-flex;
          align-items: center;
          gap: 0.2rem;
        }

        .smgv-metric-card {
          border: 1px solid var(--smg-line);
          border-radius: 18px;
          background: rgba(255, 252, 248, 0.96);
          padding: 0.54rem 0.78rem 0.48rem 0.78rem;
          box-shadow: 0 8px 20px rgba(29, 39, 49, 0.04);
          position: relative;
          overflow: hidden;
        }

        .smgv-metric-card::before {
          content: "";
          position: absolute;
          inset: 7px;
          border: 1px solid rgba(20, 34, 53, 0.045);
          border-radius: 12px;
          pointer-events: none;
        }

        .smgv-metric-label {
          color: var(--smg-muted);
          text-transform: uppercase;
          font-size: 0.64rem;
          font-weight: 800;
          letter-spacing: 0.09em;
        }

        .smgv-metric-value {
          font-family: "Cormorant Garamond", Georgia, serif;
          font-size: 1.28rem;
          line-height: 1;
          margin-top: 0.12rem;
          color: var(--smg-ink);
        }

        .smgv-top-nav-band {
          display: flex;
          align-items: center;
          gap: 0.8rem;
          margin: 0.18rem 0 0.08rem 0;
          color: var(--smg-muted);
        }

        .smgv-top-nav-rule {
          flex: 1 1 auto;
          height: 1px;
          background: linear-gradient(
            90deg,
            rgba(20, 34, 53, 0),
            rgba(20, 34, 53, 0.14) 20%,
            rgba(139, 68, 46, 0.18) 50%,
            rgba(20, 34, 53, 0.14) 80%,
            rgba(20, 34, 53, 0)
          );
        }

        .smgv-top-nav-title {
          font-family: "Cinzel", Georgia, serif;
          font-size: 0.64rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--smg-accent);
          white-space: nowrap;
        }

        .smgv-top-nav-tail {
          height: 0.38rem;
          margin-top: -0.02rem;
          margin-bottom: 0.12rem;
          position: relative;
        }

        .smgv-top-nav-tail::before {
          content: "";
          position: absolute;
          left: 0;
          right: 0;
          top: 50%;
          height: 1px;
          transform: translateY(-50%);
          background: linear-gradient(
            90deg,
            rgba(20, 34, 53, 0),
            rgba(20, 34, 53, 0.10) 18%,
            rgba(139, 68, 46, 0.15) 50%,
            rgba(20, 34, 53, 0.10) 82%,
            rgba(20, 34, 53, 0)
          );
        }

        .smgv-metric-caption {
          color: var(--smg-muted);
          font-size: 0.66rem;
          line-height: 1.28;
          margin-top: 0.1rem;
        }

        .smgv-map-summary {
          display: flex;
          flex-direction: column;
          gap: 0.52rem;
        }

        .smgv-map-summary-note {
          color: var(--smg-muted);
          font-size: 0.72rem;
          line-height: 1.35;
          margin-top: 0.02rem;
        }

        .smgv-map-section-tight {
          margin-top: -0.08rem;
        }

        .smgv-map-intro {
          margin: 0.34rem 0 0.14rem 0;
        }

        .smgv-map-intro h2 {
          margin: 0 0 0.08rem 0;
          font-size: 1.18rem;
          line-height: 1.02;
          font-family: "Cormorant Garamond", Georgia, serif;
          color: var(--smg-ink);
        }

        .smgv-map-intro p {
          margin: 0;
          color: var(--smg-muted);
          line-height: 1.3;
          font-size: 0.77rem;
          max-width: 44rem;
        }

        .smgv-map-controls-lift {
          height: 0.01rem;
          margin-top: -0.1rem;
          margin-bottom: -0.02rem;
        }

        .smgv-map-controls-note {
          color: var(--smg-muted);
          font-size: 0.7rem;
          line-height: 1.18;
          margin: 0 0 0.18rem 0;
        }

        .smgv-pager-chip {
          border: 1px solid rgba(20, 34, 53, 0.1);
          border-radius: 18px;
          background: rgba(255, 252, 248, 0.96);
          box-shadow: 0 8px 18px rgba(29, 39, 49, 0.05);
          padding: 0.5rem 0.78rem;
          min-height: 2.72rem;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }

        .smgv-pager-label {
          color: var(--smg-muted);
          font-size: 0.62rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          line-height: 1.1;
        }

        .smgv-pager-value {
          color: var(--smg-ink);
          font-size: 0.94rem;
          font-weight: 800;
          line-height: 1.2;
          margin-top: 0.12rem;
        }

        .smgv-pager-sub {
          color: var(--smg-muted);
          font-size: 0.67rem;
          line-height: 1.18;
          margin-top: 0.08rem;
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

        div.stButton > button,
        div.stDownloadButton > button {
          width: 100%;
          min-height: 2.65rem;
          border-radius: 16px;
          border: 1px solid rgba(20, 34, 53, 0.18);
          background: linear-gradient(180deg, rgba(255, 253, 250, 0.98), rgba(246, 239, 230, 0.98));
          color: var(--smg-ink);
          font-family: "Manrope", sans-serif;
          font-weight: 700;
          letter-spacing: 0.01em;
          box-shadow: 0 10px 22px rgba(29, 39, 49, 0.07);
          transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }

        [class*="st-key-smg-home-open-"] button {
          min-height: 2.92rem !important;
          border-radius: 18px !important;
          border: 1px solid rgba(139, 68, 46, 0.24) !important;
          background:
            linear-gradient(
              145deg,
              rgba(255, 254, 251, 0.99) 0%,
              rgba(249, 241, 231, 0.99) 42%,
              rgba(232, 219, 202, 0.98) 100%
            ) !important;
          box-shadow:
            0 16px 28px rgba(29, 39, 49, 0.09),
            0 3px 0 rgba(125, 91, 62, 0.16),
            inset 0 1px 0 rgba(255,255,255,0.82),
            inset -1px -4px 8px rgba(139, 68, 46, 0.08) !important;
          font-family: "Cinzel", Georgia, serif !important;
          font-size: 0.8rem !important;
          font-weight: 700 !important;
          letter-spacing: 0.08em !important;
          text-transform: uppercase !important;
        }

        [class*="st-key-smg-home-open-tract"],
        [class*="st-key-smg-home-open-map"] {
          margin-top: -0.14rem;
        }

        [class*="st-key-smg-home-open-"] button:hover {
          border-color: rgba(139, 68, 46, 0.42) !important;
          background:
            linear-gradient(
              145deg,
              rgba(255, 254, 251, 1) 0%,
              rgba(250, 243, 234, 0.99) 42%,
              rgba(236, 224, 209, 0.99) 100%
            ) !important;
          box-shadow:
            0 20px 36px rgba(29, 39, 49, 0.11),
            0 3px 0 rgba(125, 91, 62, 0.19),
            inset 0 1px 0 rgba(255,255,255,0.9),
            inset -1px -5px 9px rgba(139, 68, 46, 0.1) !important;
          transform: translateY(-1px);
        }

        [class*="st-key-smg-home-open-map"] button {
          background:
            linear-gradient(
              145deg,
              #6f97b5 0%,
              #4d7899 42%,
              #2d5874 100%
            ) !important;
          color: #fdf8f2 !important;
          border-color: rgba(32, 68, 93, 0.94) !important;
          box-shadow:
            0 18px 34px rgba(20, 44, 65, 0.24),
            0 4px 0 rgba(18, 40, 57, 0.42),
            inset 0 1px 0 rgba(255,255,255,0.24),
            inset -1px -6px 10px rgba(13, 30, 43, 0.2),
            inset 0 0 0 1px rgba(255,255,255,0.08) !important;
          text-shadow: 0 1px 0 rgba(8, 16, 24, 0.28);
        }

        [class*="st-key-smg-home-open-map"] button:hover {
          border-color: rgba(33, 78, 112, 0.98) !important;
          background:
            linear-gradient(
              145deg,
              #7aa3c1 0%,
              #5683a5 42%,
              #376785 100%
            ) !important;
          box-shadow:
            0 22px 40px rgba(20, 44, 65, 0.28),
            0 4px 0 rgba(18, 40, 57, 0.46),
            inset 0 1px 0 rgba(255,255,255,0.3),
            inset -1px -6px 10px rgba(13, 30, 43, 0.18),
            inset 0 0 0 1px rgba(255,255,255,0.12) !important;
        }

        [class*="st-key-smgv-nav-"] button {
          min-height: 2.46rem !important;
          border-radius: 18px !important;
          border: 1px solid rgba(139, 68, 46, 0.18) !important;
          background:
            linear-gradient(
              180deg,
              rgba(255, 251, 246, 0.98),
              rgba(246, 238, 228, 0.94)
            ) !important;
          box-shadow:
            0 8px 16px rgba(29, 39, 49, 0.04),
            inset 0 0 0 1px rgba(20, 34, 53, 0.03) !important;
          font-family: "Cinzel", Georgia, serif !important;
          font-size: 0.74rem !important;
          font-weight: 600 !important;
          letter-spacing: 0.12em !important;
          text-transform: uppercase !important;
          position: relative;
          padding-left: 1.28rem !important;
          padding-right: 1.28rem !important;
        }

        [class*="st-key-smgv-nav-"] button[kind="primary"] {
          background:
            linear-gradient(
              135deg,
              rgba(30, 64, 90, 0.98),
              rgba(20, 44, 65, 0.98)
            ) !important;
          color: #fdf8f2 !important;
          border-color: rgba(20, 44, 65, 0.92) !important;
          box-shadow: 0 10px 18px rgba(20, 44, 65, 0.16) !important;
        }

        [class*="st-key-smgv-nav-"] button::before {
          content: "";
          position: absolute;
          left: 0.8rem;
          right: 0.8rem;
          top: 0.36rem;
          height: 1px;
          background: linear-gradient(
            90deg,
            rgba(139, 68, 46, 0),
            rgba(139, 68, 46, 0.24) 20%,
            rgba(139, 68, 46, 0.35) 50%,
            rgba(139, 68, 46, 0.24) 80%,
            rgba(139, 68, 46, 0)
          );
        }

        [class*="st-key-smgv-nav-"] button[kind="primary"]::before {
          background: linear-gradient(
            90deg,
            rgba(253, 248, 242, 0),
            rgba(253, 248, 242, 0.32) 20%,
            rgba(253, 248, 242, 0.54) 50%,
            rgba(253, 248, 242, 0.32) 80%,
            rgba(253, 248, 242, 0)
          );
        }

        div.stButton,
        div.stDownloadButton {
          margin-top: 0.18rem;
          margin-bottom: 0.32rem;
        }

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {
          border-color: rgba(139, 68, 46, 0.4);
          box-shadow: 0 12px 24px rgba(29, 39, 49, 0.08);
          transform: translateY(-1px);
        }

        div.stButton > button[kind="primary"],
        div.stDownloadButton > button[kind="primary"] {
          background: linear-gradient(135deg, #234d68, #18344d);
          color: #fdf8f2;
          border-color: rgba(24, 52, 77, 0.84);
        }

        div.stButton > button[kind="secondary"] {
          background: rgba(255, 252, 248, 0.94);
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
          border-radius: 16px;
          border-color: rgba(20, 34, 53, 0.12);
          background: rgba(255, 252, 248, 0.9);
          box-shadow: 0 6px 16px rgba(29, 39, 49, 0.03);
        }

        [data-testid="stExpander"] {
          border: 1px solid var(--smg-line);
          border-radius: 18px;
          background: rgba(255, 252, 248, 0.82);
          overflow: hidden;
        }

        [data-testid="stExpander"] details summary p {
          font-weight: 700;
          color: var(--smg-ink);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def top_nav(active_view: str, view_names: Iterable[str]) -> str | None:
    ordered = list(view_names)
    st.markdown(
        (
            "<div class='smgv-top-nav-band'>"
            "<div class='smgv-top-nav-rule'></div>"
            "<div class='smgv-top-nav-title'>Guide</div>"
            "<div class='smgv-top-nav-rule'></div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    columns = st.columns(len(ordered), gap="small")
    for column, view_name in zip(columns, ordered, strict=False):
        view_slug = (
            view_name.lower()
            .replace(" / ", "-")
            .replace("/", "-")
            .replace(" ", "-")
        )
        with column:
            if st.button(
                NAV_LABELS.get(view_name, view_name),
                use_container_width=True,
                type="primary" if view_name == active_view else "secondary",
                key=f"smgv-nav-{view_slug}",
            ):
                return view_name
    st.markdown("<div class='smgv-top-nav-tail'></div>", unsafe_allow_html=True)
    return None


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


def hero(
    title: str,
    description: str,
    *,
    eyebrow: str,
    byline_html: str | None = None,
) -> None:
    byline_block = byline_html or ""
    st.markdown(
        (
            "<div class='smgv-hero'>"
            f"<div class='smgv-kicker'>{escape(eyebrow)}</div>"
            f"<h1>{escape(title)}</h1>"
            f"<p class='smgv-hero-subtitle'>{escape(description)}</p>"
            f"{byline_block}"
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


def pager_chip(label: str, value: str, subtitle: str) -> None:
    st.markdown(
        (
            "<div class='smgv-pager-chip'>"
            f"<div class='smgv-pager-label'>{escape(label)}</div>"
            f"<div class='smgv-pager-value'>{escape(value)}</div>"
            f"<div class='smgv-pager-sub'>{escape(subtitle)}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def metric_cards(
    cards: list[MetricCard],
    *,
    columns: int = 4,
    row_gap: float = 0.46,
) -> None:
    if not cards:
        return
    rows = [cards[index : index + columns] for index in range(0, len(cards), columns)]
    for row_index, row in enumerate(rows):
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
        if row_index < len(rows) - 1 and row_gap > 0:
            st.markdown(
                f"<div style='height:{row_gap:.2f}rem'></div>",
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


def meta_line(values: Iterable[str]) -> None:
    items = "".join(
        f"<span>{escape(str(value))}</span>"
        for value in values
        if str(value).strip()
    )
    if not items:
        return
    st.markdown(f"<div class='smgv-inline-meta'>{items}</div>", unsafe_allow_html=True)


def empty_state(title: str, body: str) -> None:
    card(title, body)


def reading_panel(title: str, metadata: list[str], html_body: str) -> None:
    pill_row(metadata, tone="accent")
    title_style = (
        "font-family:Cormorant Garamond,serif;"
        "font-size:1.35rem;"
        "margin-bottom:0.9rem"
    )
    st.markdown(
        (
            "<div class='smgv-reading'>"
            f"<div style='{title_style}'>"
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
