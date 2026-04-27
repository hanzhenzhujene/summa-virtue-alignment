from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.temperance_closure_161_170 import (
    TEMPERANCE_CLOSURE_161_170_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    temperance_closure_161_170_concept_page_data,
)


def test_temperance_closure_presets_are_explicit() -> None:
    assert set(TEMPERANCE_CLOSURE_161_170_PRESETS) == {
        "humility_pride_161_162",
        "adams_first_sin_163_165",
        "studiousness_curiosity_166_167",
        "external_modesty_168_169",
        "precepts_of_temperance_q170",
        "temperance_full_synthesis",
        "temperance_doctrinal_only_synthesis",
        "temperance_doctrinal_editorial_synthesis",
    }


def test_filter_edges_by_preset_respects_studiousness_curiosity_focus(
    temperance_closure_161_170_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "studiousness_curiosity_166_167",
        focus_tags={"study_curiosity"},
        include_editorial=False,
    )

    assert edges
    for edge in edges:
        question_numbers = {
            bundle.passages[passage_id].question_number
            for passage_id in edge.get("source_passage_ids", [])
            if passage_id in bundle.passages
        }
        assert question_numbers.issubset({166, 167})
        assert "study_curiosity" in edge["temperance_closure_focus_tags"]


def test_temperance_full_synthesis_preset_keeps_phase1_and_closure_edges(
    temperance_closure_161_170_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "temperance_full_synthesis",
        include_editorial=False,
    )

    edge_ids = {str(edge["edge_id"]) for edge in edges}
    assert (
        "edge.temperance_proper.concept.temperance.species_of.concept.cardinal_virtue" in edge_ids
    )
    assert "edge.concept.adams_first_sin.case_of.concept.pride" in edge_ids
    assert any("synthesis" in edge["temperance_closure_focus_tags"] for edge in edges)


def test_temperance_closure_edge_evidence_panel_exposes_distinctions(
    temperance_closure_161_170_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.adams_first_sin.case_of.concept.pride",
    )

    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert "adam_case" in panel["temperance_closure_focus_tags"]
    assert panel["temperance_distinctions"]["pride_vs_adams_first_sin"] is True
    assert panel["temperance_distinctions"]["precept_linkage"] is False


def test_temperance_closure_concept_page_separates_reviewed_editorial_and_candidate_layers(
    temperance_closure_161_170_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = temperance_closure_161_170_concept_page_data(
        bundle,
        "concept.humility",
        start_question=141,
        end_question=170,
    )

    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
    assert payload["coverage"]["focus_counts"]["humility_pride"] >= 1
    assert "unresolved_disambiguation_notes" in payload
