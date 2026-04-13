from __future__ import annotations

from summa_moral_graph.ontology import load_alias_overrides, match_concepts, normalize_lookup_text
from summa_moral_graph.ontology.registry import load_pilot_registry


def test_normalize_lookup_text_collapses_case_and_punctuation() -> None:
    assert normalize_lookup_text("Ultimate End!") == "ultimate end"


def test_alias_normalization_exact_and_ambiguous_matches(pilot_artifacts) -> None:
    registry = load_pilot_registry()
    overrides = load_alias_overrides()
    exact = match_concepts("last end", registry, overrides)
    assert exact.matched_concept_ids == ["concept.ultimate_end"]
    ambiguous = match_concepts("love", registry, overrides)
    assert ambiguous.is_ambiguous is True
    assert set(ambiguous.matched_concept_ids) == {"concept.charity", "concept.love_passion"}
