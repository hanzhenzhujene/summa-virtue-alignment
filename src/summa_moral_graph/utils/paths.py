"""Shared repository path constants and repo-relative path helpers."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
INTERIM_DIR = DATA_DIR / "interim"
GOLD_DIR = DATA_DIR / "gold"
PROCESSED_DIR = DATA_DIR / "processed"
CANDIDATE_DIR = DATA_DIR / "candidate"
NEWADVENT_CACHE_DIR = DATA_DIR / "cache" / "newadvent"


def repo_relative_path(path: Path) -> Path:
    """Return a repo-relative path when the input lives under the current checkout."""

    candidate = path if path.is_absolute() else REPO_ROOT / path
    try:
        return candidate.resolve(strict=False).relative_to(REPO_ROOT.resolve(strict=False))
    except ValueError:
        return path


def repo_relative_path_str(path: Path) -> str:
    """Format a path for public artifacts without leaking machine-specific absolute prefixes."""

    relative = repo_relative_path(path)
    if relative.is_absolute():
        return str(relative)
    return relative.as_posix()
