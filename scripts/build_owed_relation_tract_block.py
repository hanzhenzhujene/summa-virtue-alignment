"""Build the reviewed owed-relation tract artifacts for II-II questions 101-108."""

from __future__ import annotations

import json

from summa_moral_graph.annotations.owed_relation_tract import (
    build_owed_relation_tract_annotation_artifacts,
)
from summa_moral_graph.annotations.owed_relation_tract_review import (
    build_owed_relation_tract_review_queue,
)
from summa_moral_graph.graph.owed_relation_tract import build_owed_relation_tract_graph_artifacts
from summa_moral_graph.validation.owed_relation_tract import build_owed_relation_tract_reports


def main() -> None:
    summary = {
        "annotations": build_owed_relation_tract_annotation_artifacts(),
        "graph": build_owed_relation_tract_graph_artifacts(),
        "reports": build_owed_relation_tract_reports(),
        "review_queue": build_owed_relation_tract_review_queue(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
