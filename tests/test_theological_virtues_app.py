from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.theological_virtues import (
    THEOLOGICAL_VIRTUES_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    theological_virtues_concept_page_data,
)


def test_theological_virtues_presets_are_explicit() -> None:
    assert set(THEOLOGICAL_VIRTUES_PRESETS) == {
        "faith",
        "hope",
        "charity",
        "all_theological_virtues",
    }


def test_filter_edges_by_preset_respects_question_range(theological_virtues_artifacts) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(bundle, "faith", include_editorial=True)
    assert edges
    for edge in edges:
        question_numbers = {
            bundle.passages[passage_id].question_number
            for passage_id in edge.get("source_passage_ids", [])
            if passage_id in bundle.passages
        }
        assert question_numbers
        assert all(1 <= question_number <= 16 for question_number in question_numbers)


def test_theological_edge_evidence_panel_exposes_support_metadata(
    theological_virtues_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.charity.regulated_by.concept.precepts_of_charity",
    )
    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert panel["evidence_snippets"]
    assert panel["layer"] == "reviewed_doctrinal"


def test_theological_concept_page_keeps_editorial_and_candidate_layers_separate(
    theological_virtues_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = theological_virtues_concept_page_data(
        bundle,
        "concept.charity",
        start_question=23,
        end_question=46,
    )
    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert all(23 <= question_number <= 46 for question_number in payload["related_questions"])
