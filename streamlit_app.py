from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main() -> None:
    from summa_moral_graph.viewer import render_dashboard

    render_dashboard(entrypoint_id="root")


if __name__ == "__main__":
    main()
