from __future__ import annotations

import json

from summa_moral_graph.annotations.temperance_141_160_review import (
    build_temperance_141_160_review_queue,
)


def main() -> None:
    print(json.dumps(build_temperance_141_160_review_queue(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
