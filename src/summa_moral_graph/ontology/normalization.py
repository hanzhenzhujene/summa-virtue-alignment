from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Protocol, TypeVar

import yaml

from ..utils.paths import GOLD_DIR

LOOKUP_PUNCT_RE = re.compile(r"[^a-z0-9\s]+")
LOOKUP_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class ConceptMatch:
    query: str
    normalized_query: str
    matched_concept_ids: list[str]
    match_method: str
    is_ambiguous: bool


class LookupConcept(Protocol):
    concept_id: str
    canonical_label: str
    aliases: list[str]


LookupConceptT = TypeVar("LookupConceptT", bound=LookupConcept)


def normalize_lookup_text(text: str) -> str:
    """Normalize user-facing labels for conservative alias matching."""

    normalized = unicodedata.normalize("NFKC", text).casefold().replace("&", " and ")
    normalized = LOOKUP_PUNCT_RE.sub(" ", normalized)
    return LOOKUP_SPACE_RE.sub(" ", normalized).strip()


def load_alias_overrides(path: Path | None = None) -> dict[str, dict[str, object]]:
    """Load hand-authored alias overrides and ambiguity declarations."""

    target = path or GOLD_DIR / "pilot_alias_overrides.yml"
    if not target.exists():
        return {"exact": {}, "normalized": {}, "ambiguous": {}}
    payload = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    return {
        "exact": dict(payload.get("exact", {})),
        "normalized": dict(payload.get("normalized", {})),
        "ambiguous": dict(payload.get("ambiguous", {})),
    }


def match_concepts(
    query: str,
    registry: Mapping[str, LookupConceptT],
    alias_overrides: dict[str, dict[str, object]] | None = None,
) -> ConceptMatch:
    """Resolve a query to one or more concept ids using conservative alias logic."""

    overrides = alias_overrides or {"exact": {}, "normalized": {}, "ambiguous": {}}
    normalized_query = normalize_lookup_text(query)

    exact_target = overrides["exact"].get(query)
    if isinstance(exact_target, str):
        return ConceptMatch(
            query=query,
            normalized_query=normalized_query,
            matched_concept_ids=[exact_target],
            match_method="override_exact",
            is_ambiguous=False,
        )

    normalized_target = overrides["normalized"].get(normalized_query)
    if isinstance(normalized_target, str):
        return ConceptMatch(
            query=query,
            normalized_query=normalized_query,
            matched_concept_ids=[normalized_target],
            match_method="override_normalized",
            is_ambiguous=False,
        )

    ambiguous = overrides["ambiguous"].get(normalized_query)
    if isinstance(ambiguous, list):
        return ConceptMatch(
            query=query,
            normalized_query=normalized_query,
            matched_concept_ids=sorted(str(item) for item in ambiguous),
            match_method="declared_ambiguous",
            is_ambiguous=True,
        )

    exact_matches = [
        record.concept_id
        for record in registry.values()
        if query == record.canonical_label or query in record.aliases
    ]
    if exact_matches:
        return ConceptMatch(
            query=query,
            normalized_query=normalized_query,
            matched_concept_ids=sorted(exact_matches),
            match_method="exact",
            is_ambiguous=len(exact_matches) > 1,
        )

    normalized_matches = []
    for record in registry.values():
        candidates = [record.canonical_label, *record.aliases]
        if normalized_query in {normalize_lookup_text(candidate) for candidate in candidates}:
            normalized_matches.append(record.concept_id)
    return ConceptMatch(
        query=query,
        normalized_query=normalized_query,
        matched_concept_ids=sorted(normalized_matches),
        match_method="normalized" if normalized_matches else "none",
        is_ambiguous=len(normalized_matches) > 1,
    )


def search_registry(
    query: str,
    registry: Mapping[str, LookupConceptT],
) -> list[LookupConceptT]:
    """Search by canonical label or alias using normalized substring matching."""

    if not query.strip():
        return sorted(registry.values(), key=lambda record: record.canonical_label)
    normalized_query = normalize_lookup_text(query)
    matches: list[LookupConceptT] = []
    for record in registry.values():
        haystack = [
            normalize_lookup_text(record.canonical_label),
            *[normalize_lookup_text(alias) for alias in record.aliases],
        ]
        if any(normalized_query in candidate for candidate in haystack):
            matches.append(record)
    return sorted(matches, key=lambda record: record.canonical_label)


def find_alias_collisions(
    registry: Mapping[str, LookupConcept],
    alias_overrides: dict[str, dict[str, object]] | None = None,
) -> list[str]:
    """Flag suspicious alias collisions not explicitly allowed as ambiguous."""

    overrides = alias_overrides or {"exact": {}, "normalized": {}, "ambiguous": {}}
    declared_ambiguous = {
        key: {str(item) for item in value}
        for key, value in overrides["ambiguous"].items()
        if isinstance(value, list)
    }
    collisions: dict[str, set[str]] = {}
    for record in registry.values():
        for label in [record.canonical_label, *record.aliases]:
            collisions.setdefault(normalize_lookup_text(label), set()).add(record.concept_id)

    flagged: list[str] = []
    for key, concept_ids in sorted(collisions.items()):
        if len(concept_ids) <= 1:
            continue
        if declared_ambiguous.get(key) == concept_ids:
            continue
        flagged.append(f"{key}: {', '.join(sorted(concept_ids))}")
    return flagged
