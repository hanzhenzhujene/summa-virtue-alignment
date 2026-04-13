from __future__ import annotations

import json

from summa_moral_graph.annotations.fortitude_closure_136_140_review import (
    build_fortitude_closure_136_140_review_queue,
)


def main() -> None:
    print(json.dumps(build_fortitude_closure_136_140_review_queue(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
