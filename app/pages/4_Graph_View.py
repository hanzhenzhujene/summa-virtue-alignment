"""Legacy multipage entrypoint for the overall moral-graph view."""

from __future__ import annotations

from summa_moral_graph.viewer.shell import render_dashboard

render_dashboard(default_view="Overall Map", entrypoint_id="page-map")
