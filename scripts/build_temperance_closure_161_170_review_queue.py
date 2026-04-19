"""Build the temperance-closure review queue and packet artifacts for II-II questions 161-170."""

from __future__ import annotations

import json

from summa_moral_graph.annotations.temperance_closure_161_170_review import (
    build_temperance_closure_161_170_review_queue,
)

if __name__ == "__main__":
    print(json.dumps(build_temperance_closure_161_170_review_queue(), indent=2, sort_keys=True))
