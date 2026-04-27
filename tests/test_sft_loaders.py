from __future__ import annotations

from summa_moral_graph.sft.loaders import load_corpus_context, load_doctrinal_annotation_sources
from tests.sft_test_utils import build_fixture_dataset_config


def test_loaders_materialize_fixture_and_default_missing_edge_layer(tmp_path) -> None:
    config = build_fixture_dataset_config(tmp_path)
    corpus = load_corpus_context(config.corpus)
    annotations = load_doctrinal_annotation_sources(config.sources)

    assert set(corpus.segments) == {
        "st.ii-ii.q023.a001.resp",
        "st.ii-ii.q024.a002.resp",
        "st.ii-ii.q047.a002.resp",
        "st.ii-ii.q162.a001.ad1",
    }
    assert len(corpus.questions) == 4
    assert len(corpus.articles) == 4
    assert len(annotations) == 5
    assert {row.edge_layer for row in annotations} == {"doctrinal"}
    assert {row.tract for row in annotations} == {
        "theological_virtues",
        "prudence",
        "temperance_closure_161_170",
    }
