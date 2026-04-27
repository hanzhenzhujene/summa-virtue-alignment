"""Build the connected-virtues review queue and packet artifacts for II-II questions 109-120."""

from __future__ import annotations

import json

from summa_moral_graph.annotations.connected_virtues_109_120_review import (
    build_connected_virtues_109_120_review_queue,
)


def main() -> None:
    print(json.dumps(build_connected_virtues_109_120_review_queue(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
