from __future__ import annotations

import json

from summa_moral_graph.annotations.temperance_141_160 import (
    build_temperance_141_160_annotation_artifacts,
)
from summa_moral_graph.annotations.temperance_141_160_review import (
    build_temperance_141_160_review_queue,
)
from summa_moral_graph.graph.temperance_141_160 import (
    build_temperance_141_160_graph_artifacts,
)
from summa_moral_graph.validation.temperance_141_160 import (
    build_temperance_141_160_reports,
)


def main() -> None:
    print(
        json.dumps(
            {
                "annotations": build_temperance_141_160_annotation_artifacts(),
                "graph": build_temperance_141_160_graph_artifacts(),
                "reports": build_temperance_141_160_reports(),
                "review_queue": build_temperance_141_160_review_queue(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
