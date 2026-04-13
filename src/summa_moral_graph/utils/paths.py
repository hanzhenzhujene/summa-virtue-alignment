from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
INTERIM_DIR = DATA_DIR / "interim"
GOLD_DIR = DATA_DIR / "gold"
PROCESSED_DIR = DATA_DIR / "processed"
CANDIDATE_DIR = DATA_DIR / "candidate"
NEWADVENT_CACHE_DIR = DATA_DIR / "cache" / "newadvent"
