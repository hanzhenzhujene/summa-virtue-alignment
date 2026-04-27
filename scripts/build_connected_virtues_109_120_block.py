"""Build the reviewed connected-virtues tract artifacts for II-II questions 109-120."""

from __future__ import annotations

import json

from summa_moral_graph.annotations.connected_virtues_109_120 import (
    build_connected_virtues_109_120_annotation_artifacts,
)
from summa_moral_graph.annotations.connected_virtues_109_120_review import (
    build_connected_virtues_109_120_review_queue,
)
from summa_moral_graph.graph.connected_virtues_109_120 import (
    build_connected_virtues_109_120_graph_artifacts,
)
from summa_moral_graph.validation.connected_virtues_109_120 import (
    build_connected_virtues_109_120_reports,
)


def main() -> None:
    summary = {
        "annotations": build_connected_virtues_109_120_annotation_artifacts(),
        "graph": build_connected_virtues_109_120_graph_artifacts(),
        "reports": build_connected_virtues_109_120_reports(),
        "review_queue": build_connected_virtues_109_120_review_queue(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
