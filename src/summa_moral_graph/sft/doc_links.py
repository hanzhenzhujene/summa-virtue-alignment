"""Utilities for extracting and validating internal markdown links in public repo surfaces."""

from __future__ import annotations

import re
from pathlib import Path

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def _normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target and not target.startswith(("http://", "https://")):
        target = target.split(" ", maxsplit=1)[0]
    return target


def extract_markdown_targets(markdown_text: str) -> list[str]:
    return [_normalize_target(match.group(1)) for match in MARKDOWN_LINK_RE.finditer(markdown_text)]


def _is_external_target(target: str) -> bool:
    return target.startswith(
        (
            "#",
            "http://",
            "https://",
            "mailto:",
            "tel:",
        )
    )


def resolve_internal_markdown_target(document_path: Path, target: str) -> Path | None:
    if _is_external_target(target):
        return None
    normalized_target = target.split("#", maxsplit=1)[0].strip()
    if not normalized_target:
        return None
    target_path = Path(normalized_target)
    if target_path.is_absolute():
        return target_path
    return (document_path.parent / target_path).resolve()


def validate_internal_markdown_links(document_path: Path) -> list[str]:
    markdown_text = document_path.read_text(encoding="utf-8")
    missing_targets: list[str] = []
    for target in extract_markdown_targets(markdown_text):
        resolved = resolve_internal_markdown_target(document_path, target)
        if resolved is None:
            continue
        if not resolved.exists():
            missing_targets.append(target)
    return missing_targets
