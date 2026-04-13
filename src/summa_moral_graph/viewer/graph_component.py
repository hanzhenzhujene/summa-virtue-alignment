from __future__ import annotations

import importlib
from functools import cache
from hashlib import sha1
from typing import Any

import streamlit.components.v1 as legacy_components

_COMPONENT_HTML = "<div id='smg-graph-component-root'></div>"

_COMPONENT_CSS = """
:host {
    display: block;
    width: 100%;
}

#smg-graph-component-root {
    width: 100%;
}

.smg-graph-frame {
    width: 100%;
    border: none;
    border-radius: 18px;
    background: transparent;
}
"""

_COMPONENT_JS = """
export default function(component) {
    const { data, parentElement, setTriggerValue } = component;
    let root = parentElement.querySelector("#smg-graph-component-root");
    if (!root) {
        root = document.createElement("div");
        root.id = "smg-graph-component-root";
        parentElement.appendChild(root);
    }

    let frame = root.querySelector("iframe");
    if (!frame) {
        frame = document.createElement("iframe");
        frame.className = "smg-graph-frame";
        frame.setAttribute("sandbox", "allow-scripts allow-same-origin");
        root.appendChild(frame);
    }

    frame.style.height = data?.height ?? "680px";
    const nextHash = String(data?.graphHash ?? "");
    if (frame.dataset.graphHash !== nextHash) {
        frame.srcdoc = data?.graphHtml ?? "";
        frame.dataset.graphHash = nextHash;
    }

    const handleMessage = (event) => {
        if (event.source !== frame.contentWindow) {
            return;
        }
        const payload = event.data;
        if (!payload || payload.type !== "smg-node-click") {
            return;
        }
        if (typeof payload.conceptId !== "string" || !payload.conceptId) {
            return;
        }
        setTriggerValue("clicked", {
            conceptId: payload.conceptId,
            token: Date.now(),
        });
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
}
"""

_CLICK_BRIDGE = """
if (typeof network !== "undefined") {
    const emitNavigation = function(params) {
        if (!params || !Array.isArray(params.nodes) || params.nodes.length === 0) {
            return;
        }
        window.parent.postMessage(
            { type: "smg-node-click", conceptId: String(params.nodes[0]) },
            "*"
        );
    };
    network.on("click", emitNavigation);
    network.on("doubleClick", emitNavigation);
    network.on("selectNode", emitNavigation);
    network.on("hoverNode", function() {
        if (network.canvas && network.canvas.body && network.canvas.body.container) {
            network.canvas.body.container.style.cursor = "pointer";
        }
    });
    network.on("blurNode", function() {
        if (network.canvas && network.canvas.body && network.canvas.body.container) {
            network.canvas.body.container.style.cursor = "default";
        }
    });
}
"""


def with_graph_click_bridge(graph_html: str) -> str:
    if "smg-node-click" in graph_html:
        return graph_html
    return graph_html.replace("</body>", f"<script>{_CLICK_BRIDGE}</script></body>", 1)


@cache
def _graph_component() -> Any | None:
    try:
        components = importlib.import_module("streamlit.components.v2")
    except Exception:
        return None
    return components.component(
        "smg_clickable_graph",
        html=_COMPONENT_HTML,
        css=_COMPONENT_CSS,
        js=_COMPONENT_JS,
        isolate_styles=False,
    )


def render_clickable_graph(
    *,
    graph_html: str,
    height: str,
    key: str,
) -> str | None:
    component = _graph_component()
    if component is None:
        height_value = int(height.removesuffix("px")) if height.endswith("px") else 760
        legacy_components.html(graph_html, height=height_value + 44, scrolling=True)
        return None

    graph_hash = sha1(graph_html.encode("utf-8")).hexdigest()
    try:
        result = component(
            key=key,
            data={
                "graphHtml": graph_html,
                "graphHash": graph_hash,
                "height": height,
            },
            default={"clicked": None},
            on_clicked_change=lambda: None,
        )
    except Exception:
        height_value = int(height.removesuffix("px")) if height.endswith("px") else 760
        legacy_components.html(graph_html, height=height_value + 44, scrolling=True)
        return None
    clicked = getattr(result, "clicked", None)
    if isinstance(clicked, dict):
        concept_id = clicked.get("conceptId")
        if isinstance(concept_id, str) and concept_id:
            return concept_id
    return None
