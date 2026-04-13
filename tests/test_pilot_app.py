from __future__ import annotations

from summa_moral_graph.app.pilot import (
    annotations_for_passage,
    concept_evidence_bundle,
    concept_search,
    edge_evidence_bundle,
    filter_edges,
    load_pilot_bundle,
    passage_search,
    stats_payload,
)


def test_pilot_passage_search_and_annotations(pilot_artifacts) -> None:
    bundle = load_pilot_bundle()
    results = passage_search(bundle, query="common good", question_id="st.i-ii.q090")
    assert results
    linked = [annotations_for_passage(bundle, passage.segment_id) for passage in results]
    assert any(rows for rows in linked)


def test_pilot_concept_search_finds_aliases(pilot_artifacts) -> None:
    bundle = load_pilot_bundle()
    results = concept_search(bundle, "creed")
    assert any(record.concept_id == "concept.symbol_of_faith" for record in results)


def test_pilot_edge_and_concept_evidence_bundles(pilot_artifacts) -> None:
    bundle = load_pilot_bundle()
    concept_payload = concept_evidence_bundle(bundle, "concept.prudence", include_structural=True)
    assert "treated_in" in concept_payload["grouped_edges"]
    edge = next(record for record in bundle.doctrinal_edges if record.relation_type == "has_act")
    edge_payload = edge_evidence_bundle(bundle, edge.edge_id)
    assert edge_payload["annotations"]
    assert edge_payload["passages"]


def test_pilot_graph_filters_and_stats(pilot_artifacts) -> None:
    bundle = load_pilot_bundle()
    filtered = filter_edges(
        bundle,
        relation_types={"has_act"},
        include_structural=False,
        center_concept="concept.prudence",
    )
    assert filtered
    payload = stats_payload(bundle)
    assert payload["doctrinal_edge_count"] == len(bundle.doctrinal_edges)
    assert payload["structural_edge_count"] == len(bundle.structural_edges)
