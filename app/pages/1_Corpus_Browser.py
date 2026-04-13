from __future__ import annotations

from summa_moral_graph.viewer.shell import render_dashboard

render_dashboard(
    default_view="Stats / Audit",
    default_stats_tab="Corpus coverage",
    entrypoint_id="page-corpus-browser",
)
