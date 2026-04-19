from __future__ import annotations

import argparse
import json
from pathlib import Path

from summa_moral_graph.sft.public_artifacts import (
    DEFAULT_PUBLICATION_PACKAGE_MANIFEST,
    verify_publication_bundle,
)
from summa_moral_graph.utils.paths import REPO_ROOT


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--package-manifest-path",
        type=Path,
        default=DEFAULT_PUBLICATION_PACKAGE_MANIFEST,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = verify_publication_bundle(
        repo_root=args.repo_root.resolve(),
        package_manifest_path=args.package_manifest_path.resolve(),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
