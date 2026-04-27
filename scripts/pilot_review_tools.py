"""Generate and inspect pilot-slice review helpers for legacy reviewed annotation workflows."""

from __future__ import annotations

import argparse

from summa_moral_graph.annotations.pilot_review import build_pilot_review_artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build pilot review queue artifacts.")
    parser.add_argument(
        "--question-id",
        help="Optional question id for the concrete review packet, e.g. st.i-ii.q109",
    )
    args = parser.parse_args()
    print(build_pilot_review_artifacts(question_id=args.question_id))


if __name__ == "__main__":
    main()
