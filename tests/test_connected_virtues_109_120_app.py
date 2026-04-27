from __future__ import annotations

from summa_moral_graph.app.connected_virtues_109_120 import (
    CONNECTED_VIRTUES_109_120_PRESETS,
    connected_virtues_109_120_concept_page_data,
    edge_evidence_panel,
    filter_edges_by_preset,
)
from summa_moral_graph.app.corpus import load_corpus_bundle


def test_connected_virtues_presets_are_explicit() -> None:
    assert set(CONNECTED_VIRTUES_109_120_PRESETS) == {
        "full_connected_virtues_109_120",
        "truth_self_presentation",
        "social_interaction",
        "external_goods_liberality",
        "epikeia_equity",
    }


def test_filter_edges_by_preset_respects_connected_virtues_focus_tags(
    connected_virtues_109_120_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "truth_self_presentation",
        focus_tags={"self_presentation"},
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
        assert all(109 <= question_number <= 113 for question_number in question_numbers)
        assert "self_presentation" in edge["connected_virtues_focus_tags"]


def test_connected_virtues_edge_evidence_panel_exposes_cluster(
    connected_virtues_109_120_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.epikeia.corrects_legal_letter.concept.legal_letter",
    )

    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert panel["connected_virtues_cluster"] == "legal_equity"
    assert "legal_equity" in panel["connected_virtues_focus_tags"]
    assert "schema_extension" in panel["connected_virtues_focus_tags"]


def test_connected_virtues_concept_page_keeps_editorial_and_candidate_layers_separate(
    connected_virtues_109_120_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = connected_virtues_109_120_concept_page_data(
        bundle,
        "concept.truth_self_presentation",
        start_question=109,
        end_question=120,
    )

    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
    assert payload["coverage"]["reviewed_clusters"] == ["self_presentation"]
