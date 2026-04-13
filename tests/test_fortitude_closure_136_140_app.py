from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.fortitude_closure_136_140 import (
    FORTITUDE_CLOSURE_136_140_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    fortitude_closure_136_140_concept_page_data,
)


def test_fortitude_closure_presets_are_explicit() -> None:
    assert set(FORTITUDE_CLOSURE_136_140_PRESETS) == {
        "patience_q136",
        "perseverance_q137",
        "opposed_vices_q138",
        "gift_of_fortitude_q139",
        "precepts_of_fortitude_q140",
        "fortitude_tract_full_synthesis",
        "fortitude_tract_doctrinal_only_synthesis",
        "fortitude_tract_doctrinal_editorial_synthesis",
    }


def test_filter_edges_by_preset_respects_gift_focus(
    fortitude_closure_136_140_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "gift_of_fortitude_q139",
        focus_tags={"gift"},
        include_editorial=False,
    )

    assert edges
    for edge in edges:
        question_numbers = {
            bundle.passages[passage_id].question_number
            for passage_id in edge.get("source_passage_ids", [])
            if passage_id in bundle.passages
        }
        assert question_numbers == {139}
        assert "gift" in edge["fortitude_closure_focus_tags"]


def test_full_fortitude_synthesis_preset_keeps_prior_and_closure_edges(
    fortitude_closure_136_140_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "fortitude_tract_full_synthesis",
        include_editorial=False,
    )

    edge_ids = {str(edge["edge_id"]) for edge in edges}
    assert (
        "edge.concept.magnanimity.concerns_honor.concept.honor_recognition" in edge_ids
    )
    assert "edge.concept.fortitude_gift.corresponding_gift_of.concept.fortitude" in edge_ids
    assert any("synthesis" in edge["fortitude_closure_focus_tags"] for edge in edges)


def test_fortitude_closure_edge_evidence_panel_exposes_distinctions(
    fortitude_closure_136_140_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.fortitude_gift.corresponding_gift_of.concept.fortitude",
    )

    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert "gift" in panel["fortitude_closure_focus_tags"]
    assert panel["fortitude_distinctions"]["gift_vs_virtue_fortitude"] is True
    assert panel["fortitude_distinctions"]["precept_linkage"] is False


def test_fortitude_closure_concept_page_separates_reviewed_editorial_and_candidate_layers(
    fortitude_closure_136_140_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = fortitude_closure_136_140_concept_page_data(
        bundle,
        "concept.perseverance_virtue",
        start_question=136,
        end_question=140,
    )

    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
    assert payload["coverage"]["focus_counts"]["perseverance"] >= 1
    assert payload["unresolved_disambiguation_notes"]
