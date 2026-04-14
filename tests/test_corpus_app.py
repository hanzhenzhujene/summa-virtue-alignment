from __future__ import annotations

import pytest

from summa_moral_graph.app.corpus import (
    build_graph_for_edges,
    concept_page_data,
    corpus_browser_rows,
    filter_graph_edges,
    graph_html,
    load_corpus_bundle,
    passage_search,
    stats_payload,
)


@pytest.fixture(scope="module")
def corpus_bundle():
    return load_corpus_bundle()


def test_corpus_browser_rows_expose_coverage(corpus_bundle) -> None:
    question_rows = corpus_browser_rows(corpus_bundle, level="question")

    q100 = next(row for row in question_rows if row["question_id"] == "st.i-ii.q100")
    excluded = next(row for row in question_rows if row["question_id"] == "st.ii-ii.q183")

    assert q100["candidate_mention_count"] == 549
    assert q100["candidate_relation_count"] == 150
    assert q100["parse_status"] == "partial"
    assert excluded["parse_status"] == "excluded"


def test_passage_search_and_concept_page_keep_reviewed_and_candidate_separate(
    corpus_bundle,
) -> None:
    passages = passage_search(
        corpus_bundle,
        query="prudence",
        question_id="st.ii-ii.q047",
    )
    payload = concept_page_data(corpus_bundle, "concept.prudence")

    assert passages
    assert any(passage.question_id == "st.ii-ii.q047" for passage in passages)
    assert payload["coverage"]["reviewed_annotation_count"] == 95
    assert payload["coverage"]["candidate_mention_count"] == 2481
    assert payload["reviewed_doctrinal_edges"]
    assert payload["candidate_mentions"]
    assert all(
        row["subject_id"] == "concept.prudence" or row["object_id"] == "concept.prudence"
        for row in payload["reviewed_doctrinal_edges"]
    )


def test_filter_graph_edges_does_not_mix_candidate_into_reviewed_default(corpus_bundle) -> None:
    reviewed_only = filter_graph_edges(
        corpus_bundle,
        center_concept="concept.prudence",
    )
    with_candidate = filter_graph_edges(
        corpus_bundle,
        include_candidate=True,
        center_concept="concept.prudence",
    )

    assert reviewed_only
    assert {row["layer"] for row in reviewed_only} == {"reviewed_doctrinal"}
    assert "candidate" not in {row["layer"] for row in reviewed_only}
    assert "candidate" in {row["layer"] for row in with_candidate}


def test_stats_payload_matches_corpus_audit(corpus_bundle) -> None:
    payload = stats_payload(corpus_bundle)

    assert payload["summary"]["questions_parsed"] == 296
    assert payload["summary"]["articles_parsed"] == 1482
    assert payload["summary"]["passages_parsed"] == 6032
    assert payload["summary"]["candidate_mentions"] == len(corpus_bundle.candidate_mentions)
    assert (
        payload["summary"]["candidate_relation_proposals"]
        == len(corpus_bundle.candidate_relations)
    )
    assert payload["top_under_reviewed_clusters"][0]["question_range"] == [2, 5]


def test_graph_html_includes_navigation_controls_and_traceability_tooltips(
    corpus_bundle,
) -> None:
    edges = filter_graph_edges(
        corpus_bundle,
        center_concept="concept.prudence",
    )[:3]
    graph = build_graph_for_edges(edges)
    html = graph_html(graph)

    assert '"navigationButtons": true' in html
    assert '"selectConnectedEdges": true' in html
    assert "Annotations:" in html
    assert "Passages:" in html
