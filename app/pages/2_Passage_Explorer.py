"""Legacy multipage entrypoint for the passage-level reader and explorer view."""

from __future__ import annotations

from summa_moral_graph.viewer.shell import render_dashboard

render_dashboard(default_view="Passage Explorer", entrypoint_id="page-passage")
