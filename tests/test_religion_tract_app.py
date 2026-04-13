from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.religion_tract import (
    RELIGION_TRACT_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    religion_tract_concept_page_data,
)


def test_religion_tract_presets_are_explicit() -> None:
    assert set(RELIGION_TRACT_PRESETS) == {
        "annexed_gateway",
        "religion_acts",
        "superstition_excess",
        "irreligion_deficiency",
        "full_religion_tract",
    }


def test_filter_edges_by_preset_respects_religion_focus_tags(
    religion_tract_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "superstition_excess",
        focus_tags={"excess"},
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
        assert all(92 <= question_number <= 96 for question_number in question_numbers)
        assert "excess" in edge["religion_focus_tags"]


def test_religion_edge_evidence_panel_exposes_focus_tags(religion_tract_artifacts) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.oath.concerns_sacred_object.concept.divine_name",
    )
    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert "divine_name_related" in panel["religion_focus_tags"]


def test_religion_concept_page_keeps_editorial_and_candidate_layers_separate(
    religion_tract_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = religion_tract_concept_page_data(
        bundle,
        "concept.simony",
        start_question=80,
        end_question=100,
    )
    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
