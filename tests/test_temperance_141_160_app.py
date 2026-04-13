from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.temperance_141_160 import (
    TEMPERANCE_141_160_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    temperance_141_160_concept_page_data,
)


def test_temperance_presets_are_explicit() -> None:
    assert set(TEMPERANCE_141_160_PRESETS) == {
        "temperance_overview_141_160",
        "temperance_proper_141_143",
        "integral_parts_144_145",
        "food_drink_146_150",
        "chastity_lust_151_154",
        "potential_parts_155_160",
        "temperance_doctrinal_only_synthesis",
        "temperance_doctrinal_editorial_synthesis",
    }


def test_filter_edges_by_preset_respects_food_drink_focus(
    temperance_141_160_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "food_drink_146_150",
        focus_tags={"food", "drink"},
        include_editorial=False,
    )

    assert edges
    for edge in edges:
        question_numbers = {
            bundle.passages[passage_id].question_number
            for passage_id in edge.get("source_passage_ids", [])
            if passage_id in bundle.passages
        }
        assert question_numbers.issubset({146, 147, 148, 149, 150})
        assert {"food", "drink"}.intersection(edge["temperance_focus_tags"])


def test_temperance_edge_evidence_panel_exposes_taxonomy_and_domain_distinctions(
    temperance_141_160_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.potential_parts.concept.modesty_general.potential_part_of.concept.temperance",
    )

    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert "potential_part" in panel["temperance_focus_tags"]
    assert "modesty_general" in panel["temperance_focus_tags"]
    assert panel["temperance_distinctions"]["part_taxonomy"] == ["potential_part"]
    assert "modesty_general" in panel["temperance_distinctions"]["matter_domains"]


def test_temperance_concept_page_separates_reviewed_editorial_and_candidate_layers(
    temperance_141_160_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = temperance_141_160_concept_page_data(
        bundle,
        "concept.abstinence",
        start_question=141,
        end_question=160,
    )

    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
    assert payload["coverage"]["focus_counts"]["food"] >= 1
    assert payload["ambiguity_notes"]
