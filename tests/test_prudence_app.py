from __future__ import annotations

from summa_moral_graph.app.prudence import (
    PRUDENCE_PRESETS,
    concept_page_data,
    edge_evidence_panel,
    filter_edges_by_part_taxonomy,
    filter_edges_by_preset,
    load_prudence_bundle,
)


def test_prudence_presets_are_explicit() -> None:
    assert set(PRUDENCE_PRESETS) == {
        "overview",
        "core",
        "parts",
        "gift_defects_counterfeit",
    }


def test_part_taxonomy_filter_only_keeps_requested_subtypes(prudence_artifacts) -> None:
    bundle = load_prudence_bundle()
    part_edges = filter_edges_by_preset(bundle, "parts")
    filtered = filter_edges_by_part_taxonomy(part_edges, {"integral"})
    assert filtered
    assert all(edge.part_taxonomy in {None, "integral"} for edge in filtered)


def test_edge_evidence_panel_exposes_support_metadata(prudence_artifacts) -> None:
    bundle = load_prudence_bundle()
    target_edge = next(
        edge for edge in bundle.doctrinal_edges if edge.relation_type == "integral_part_of"
    )
    panel = edge_evidence_panel(bundle, target_edge.edge_id)
    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert panel["evidence_snippets"]
    assert panel["part_subtype"] == "integral"


def test_concept_page_data_separates_editorial_and_candidate_layers(prudence_artifacts) -> None:
    bundle = load_prudence_bundle()
    payload = concept_page_data(bundle, "concept.prudence")
    assert payload["reviewed_incident_edges"]
    assert "candidate_mentions" in payload
    assert "editorial_correspondences" in payload
