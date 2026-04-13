from __future__ import annotations

from pathlib import Path

from ..models import ConceptRegistryRecord, CorpusConceptRecord
from ..utils.jsonl import load_jsonl
from ..utils.paths import GOLD_DIR


def load_pilot_registry(path: Path | None = None) -> dict[str, ConceptRegistryRecord]:
    """Load the stable pilot concept registry."""

    target = path or GOLD_DIR / "pilot_concept_registry.jsonl"
    return {
        record.concept_id: record
        for record in (
            ConceptRegistryRecord.model_validate(payload) for payload in load_jsonl(target)
        )
    }


def load_corpus_registry(path: Path | None = None) -> dict[str, CorpusConceptRecord]:
    """Load the broader corpus concept registry."""

    target = path or GOLD_DIR / "corpus_concept_registry.jsonl"
    return {
        record.concept_id: record
        for record in (
            CorpusConceptRecord.model_validate(payload) for payload in load_jsonl(target)
        )
    }
