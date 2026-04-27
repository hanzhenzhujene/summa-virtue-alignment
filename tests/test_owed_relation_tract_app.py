from __future__ import annotations

from summa_moral_graph.app.corpus import load_corpus_bundle
from summa_moral_graph.app.owed_relation_tract import (
    OWED_RELATION_TRACT_PRESETS,
    edge_evidence_panel,
    filter_edges_by_preset,
    owed_relation_tract_concept_page_data,
)


def test_owed_relation_tract_presets_are_explicit() -> None:
    assert set(OWED_RELATION_TRACT_PRESETS) == {
        "full_owed_relation_tract",
        "origin_piety",
        "excellence_observance_honor",
        "authority_obedience",
        "benefit_gratitude",
        "wrong_rectification_vengeance",
    }


def test_filter_edges_by_preset_respects_due_mode_focus_tags(
    owed_relation_tract_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    edges = filter_edges_by_preset(
        bundle,
        "authority_obedience",
        focus_tags={"authority_due"},
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
        assert all(104 <= question_number <= 105 for question_number in question_numbers)
        assert "authority_due" in edge["owed_relation_focus_tags"]


def test_owed_relation_edge_evidence_panel_exposes_due_mode(
    owed_relation_tract_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    panel = edge_evidence_panel(
        bundle,
        "edge.concept.gratitude.responds_to_benefaction.concept.benefaction",
    )
    assert panel["supporting_annotation_ids"]
    assert panel["supporting_passage_ids"]
    assert panel["due_mode"] == "benefaction"
    assert "benefaction_due" in panel["owed_relation_focus_tags"]


def test_owed_relation_concept_page_keeps_editorial_and_candidate_layers_separate(
    owed_relation_tract_artifacts,
) -> None:
    bundle = load_corpus_bundle()
    payload = owed_relation_tract_concept_page_data(
        bundle,
        "concept.obedience",
        start_question=101,
        end_question=108,
    )
    assert payload["reviewed_incident_edges"]
    assert "editorial_correspondences" in payload
    assert "candidate_mentions" in payload
    assert payload["coverage"]["reviewed_edge_count"] >= 1
