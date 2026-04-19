"""Build the religion-tract review queue and packet artifacts for II-II questions 80-100."""

from __future__ import annotations

import json

from summa_moral_graph.annotations.religion_tract_review import (
    build_religion_tract_review_queue,
)


def main() -> None:
    print(json.dumps(build_religion_tract_review_queue(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
