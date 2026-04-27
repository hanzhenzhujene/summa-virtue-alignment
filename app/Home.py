"""Legacy multipage home entrypoint that delegates to the unified viewer shell."""

from __future__ import annotations

from summa_moral_graph.viewer.shell import render_dashboard

render_dashboard(default_view="Home", entrypoint_id="page-home")
