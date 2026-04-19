"""Build the reviewed fortitude-parts tract artifacts for II-II questions 129-135."""

from __future__ import annotations

import json

from summa_moral_graph.annotations.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_annotation_artifacts,
)
from summa_moral_graph.annotations.fortitude_parts_129_135_review import (
    build_fortitude_parts_129_135_review_queue,
)
from summa_moral_graph.graph.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_graph_artifacts,
)
from summa_moral_graph.validation.fortitude_parts_129_135 import (
    build_fortitude_parts_129_135_reports,
)


def main() -> None:
    print(
        json.dumps(
            {
                "annotations": build_fortitude_parts_129_135_annotation_artifacts(),
                "graph": build_fortitude_parts_129_135_graph_artifacts(),
                "reports": build_fortitude_parts_129_135_reports(),
                "review_queue": build_fortitude_parts_129_135_review_queue(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
