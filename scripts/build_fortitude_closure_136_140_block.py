from __future__ import annotations

import json

from summa_moral_graph.annotations.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_annotation_artifacts,
)
from summa_moral_graph.annotations.fortitude_closure_136_140_review import (
    build_fortitude_closure_136_140_review_queue,
)
from summa_moral_graph.graph.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_graph_artifacts,
)
from summa_moral_graph.validation.fortitude_closure_136_140 import (
    build_fortitude_closure_136_140_reports,
)


def main() -> None:
    print(
        json.dumps(
            {
                "annotations": build_fortitude_closure_136_140_annotation_artifacts(),
                "graph": build_fortitude_closure_136_140_graph_artifacts(),
                "reports": build_fortitude_closure_136_140_reports(),
                "review_queue": build_fortitude_closure_136_140_review_queue(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
