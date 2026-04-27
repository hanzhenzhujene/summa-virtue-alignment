from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

from ..utils.paths import NEWADVENT_CACHE_DIR


class NewAdventClient:
    def __init__(
        self,
        cache_dir: Path | None = None,
        timeout_seconds: float = 20.0,
        retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> None:
        self.cache_dir = cache_dir or NEWADVENT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.client = httpx.Client(
            follow_redirects=True,
            headers={"User-Agent": "summa-moral-graph/0.1.0"},
            timeout=httpx.Timeout(timeout_seconds),
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "NewAdventClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def fetch_text(self, url: str, refresh_cache: bool = False) -> str:
        cache_path = self.cache_path_for_url(url)
        if cache_path.exists() and not refresh_cache:
            return cache_path.read_text(encoding="utf-8")

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                cache_path.write_text(response.text, encoding="utf-8")
                return response.text
            except Exception as exc:  # pragma: no cover - exercised in live runs
                last_error = exc
                if attempt == self.retries:
                    break
                time.sleep(self.backoff_seconds * attempt)
        if last_error is None:  # pragma: no cover - defensive fallback
            raise RuntimeError(f"Unknown fetch failure for {url}")
        raise last_error

    def cache_path_for_url(self, url: str) -> Path:
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename:
            raise ValueError(f"Cannot derive cache filename for URL: {url}")
        return self.cache_dir / filename
