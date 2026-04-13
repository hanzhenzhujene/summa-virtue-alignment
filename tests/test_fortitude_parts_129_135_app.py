from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.fortitude_parts_129_135 import (
    FORTITUDE_PARTS_129_135_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    fortitude_parts_129_135_concept_page_data,
)


def test_fortitude_parts_presets_are_explicit() -> None:
    assert set(FORTITUDE_PARTS_129_135_PRESETS) == {
        "full_fortitude_parts_129_135",
        "magnanimity_cluster",
        "magnificence_cluster",
        "excess_opposition_view",
        "deficiency_opposition_view",
    }


def test_filter_edges_by_preset_respects_fortitude_focus_tags(
    fortitude_parts_129_135_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "excess_opposition_view",
        focus_tags={"excess_opposition"},
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
        assert all(129 <= question_number <= 135 for question_number in question_numbers)
        assert "excess_opposition" in edge["fortitude_parts_focus_tags"]


def test_fortitude_parts_edge_evidence_panel_exposes_cluster(
    fortitude_parts_129_135_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.magnificence.concerns_great_expenditure.concept.great_expenditure",
    )

    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert panel["fortitude_parts_cluster"] == "expenditure_work"
    assert "expenditure_related" in panel["fortitude_parts_focus_tags"]


def test_fortitude_parts_concept_page_keeps_editorial_and_candidate_layers_separate(
    fortitude_parts_129_135_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = fortitude_parts_129_135_concept_page_data(
        bundle,
        "concept.magnanimity",
        start_question=129,
        end_question=135,
    )

    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
    assert "honor_worthiness" in payload["coverage"]["reviewed_clusters"]
