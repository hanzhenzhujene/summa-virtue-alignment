from __future__ import annotations

from summa_moral_graph.viewer.shell import render_dashboard

render_dashboard(
    default_view="Stats / Audit",
    default_stats_tab="Reader stats",
    entrypoint_id="page-stats",
)
