from __future__ import annotations

import os

import pytest

from summa_moral_graph.ingest.crossrefs import extract_crossrefs
from summa_moral_graph.ingest.parser import parse_question_html
from summa_moral_graph.ingest.source import NewAdventClient

RUN_NETWORK = os.getenv("SUMMA_MORAL_GRAPH_RUN_NETWORK") == "1"
SKIP_REASON = "Set SUMMA_MORAL_GRAPH_RUN_NETWORK=1 to run live source tests."


@pytest.mark.network
@pytest.mark.skipif(not RUN_NETWORK, reason=SKIP_REASON)
def test_parse_live_i_ii_question_page(tmp_path) -> None:
    with NewAdventClient(cache_dir=tmp_path) as client:
        html_text = client.fetch_text(
            "https://www.newadvent.org/summa/2001.htm",
            refresh_cache=True,
        )
    parsed = parse_question_html(1, html_text)
    assert parsed.question_title == "Man's last end"
    assert len(parsed.articles) == 8
    assert all(segment.text for article in parsed.articles for segment in article.segments)
    assert all(
        segment.segment_type in {"resp", "ad"}
        for article in parsed.articles
        for segment in article.segments
    )


@pytest.mark.network
@pytest.mark.skipif(not RUN_NETWORK, reason=SKIP_REASON)
def test_parse_live_ii_ii_question_page_and_crossrefs(tmp_path) -> None:
    with NewAdventClient(cache_dir=tmp_path) as client:
        html_text = client.fetch_text(
            "https://www.newadvent.org/summa/3001.htm",
            refresh_cache=True,
        )
    parsed = parse_question_html(1, html_text)
    assert parsed.question_title == "Faith"
    assert len(parsed.articles) == 10
    first_article = parsed.articles[0]
    crossrefs = [
        match.normalized_reference
        for segment in first_article.segments
        for match in extract_crossrefs(segment.text)
    ]
    assert "II-II:25:1" in crossrefs
