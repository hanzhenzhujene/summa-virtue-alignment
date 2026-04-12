from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
INTERIM_DIR = DATA_DIR / "interim"
NEWADVENT_CACHE_DIR = DATA_DIR / "cache" / "newadvent"

