from __future__ import annotations

import json

from summa_moral_graph.annotations.religion_tract import (
    build_religion_tract_annotation_artifacts,
)
from summa_moral_graph.annotations.religion_tract_review import (
    build_religion_tract_review_queue,
)
from summa_moral_graph.graph.religion_tract import build_religion_tract_graph_artifacts
from summa_moral_graph.validation.religion_tract import build_religion_tract_reports


def main() -> None:
    summary = {
        "annotations": build_religion_tract_annotation_artifacts(),
        "graph": build_religion_tract_graph_artifacts(),
        "reports": build_religion_tract_reports(),
        "review_queue": build_religion_tract_review_queue(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
