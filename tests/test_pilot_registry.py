from __future__ import annotations

from summa_moral_graph.ontology.registry import load_pilot_registry


def test_pilot_registry_integrity(pilot_artifacts) -> None:
    registry = load_pilot_registry()
    assert len(registry) >= 60
    assert registry["concept.prudence"].canonical_label == "Prudence"
    assert "charity" in registry["concept.charity"].aliases
    assert registry["concept.prudence"].source_scope
