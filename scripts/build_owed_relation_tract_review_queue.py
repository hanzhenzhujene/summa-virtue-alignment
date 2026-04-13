from __future__ import annotations

import json

from summa_moral_graph.annotations.owed_relation_tract_review import (
    build_owed_relation_tract_review_queue,
)


def main() -> None:
    print(json.dumps(build_owed_relation_tract_review_queue(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
