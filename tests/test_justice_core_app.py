from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.justice_core import (
    JUSTICE_CORE_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    justice_core_concept_page_data,
)


def test_justice_core_presets_are_explicit() -> None:
    assert set(JUSTICE_CORE_PRESETS) == {
        "justice_overview",
        "justice_foundations",
        "bodily_property_wrongs",
        "judicial_process_wrongs",
        "verbal_injuries",
        "exchange_wrongs",
    }


def test_filter_edges_by_preset_respects_justice_focus_tags(
    justice_core_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "judicial_process_wrongs",
        focus_tags={"judicial_process"},
        include_editorial=False,
    )
    assert edges
    for edge in edges:
        question_numbers = {
            bundle.passages[passage_id].question_number
            for passage_id in edge.get("source_passage_ids", [])
            if passage_id in bundle.passages
        }
        assert question_numbers
        assert all(67 <= question_number <= 71 for question_number in question_numbers)
        assert "judicial_process" in edge["justice_focus_tags"]


def test_justice_edge_evidence_panel_exposes_focus_tags(justice_core_artifacts) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.theft.harms_domain.concept.property",
    )
    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert "harmed_domain" in panel["justice_focus_tags"]


def test_justice_concept_page_keeps_editorial_and_candidate_layers_separate(
    justice_core_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = justice_core_concept_page_data(
        bundle,
        "concept.theft",
        start_question=57,
        end_question=79,
    )
    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
