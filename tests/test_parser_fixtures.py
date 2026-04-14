from __future__ import annotations

from pathlib import Path

from summa_moral_graph.ingest.crossrefs import extract_crossrefs
from summa_moral_graph.ingest.parser import parse_question_html
from summa_moral_graph.ingest.pipeline import build_records_for_question
from summa_moral_graph.ingest.scope import ScopeEntry

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "html"


def test_parse_fixture_i_ii_question_page() -> None:
    html_text = (FIXTURE_DIR / "i_ii_q001_fixture.html").read_text(encoding="utf-8")
    parsed = parse_question_html(1, html_text)

    assert parsed.question_title == "Man's last end"
    assert len(parsed.articles) == 2
    first_article = parsed.articles[0]
    assert first_article.article_title == "Whether it belongs to man to act for an end?"
    assert [segment.segment_type for segment in first_article.segments] == [
        "resp",
        "ad",
        "ad",
    ]
    assert first_article.segments[1].text.endswith(
        "The same answer applies to the Second Objection, as regards all actions "
        "ordered to the good."
    )
    assert all("Objection 1." not in segment.text for segment in first_article.segments)
    assert all("On the contrary" not in segment.text for segment in first_article.segments)


def test_parse_fixture_ii_ii_question_page() -> None:
    html_text = (FIXTURE_DIR / "ii_ii_q001_fixture.html").read_text(encoding="utf-8")
    parsed = parse_question_html(1, html_text)

    assert parsed.question_title == "Faith"
    assert len(parsed.articles) == 1
    article = parsed.articles[0]
    assert article.article_title == "Is the object of faith the First Truth?"
    assert [segment.segment_type for segment in article.segments] == [
        "resp",
        "ad",
        "ad",
    ]
    assert all(segment.text for segment in article.segments)


def test_segment_ordering_and_crossref_occurrence_ids_are_stable() -> None:
    html_text = (FIXTURE_DIR / "i_ii_q001_fixture.html").read_text(encoding="utf-8")
    parsed = parse_question_html(1, html_text)
    scope_entry = ScopeEntry(
        part_id="i-ii",
        question_number=1,
        source_part_url="https://www.newadvent.org/summa/2.htm",
        source_url="https://www.newadvent.org/summa/2001.htm",
    )
    (
        _question_record,
        article_records,
        segment_records,
        crossref_records,
    ) = build_records_for_question(scope_entry, parsed)

    assert article_records[0].segment_ids == [
        "st.i-ii.q001.a001.resp",
        "st.i-ii.q001.a001.ad1",
        "st.i-ii.q001.a001.ad2",
    ]
    assert [record.crossref_id for record in crossref_records] == [
        "st.i-ii.q001.a001.ad2.xref01"
    ]
    assert all(segment.text.strip() for segment in segment_records)


def test_extract_crossrefs_from_fixture_segment_text() -> None:
    html_text = (FIXTURE_DIR / "ii_ii_q001_fixture.html").read_text(encoding="utf-8")
    parsed = parse_question_html(1, html_text)
    respondeo = parsed.articles[0].segments[0]
    reply_two = parsed.articles[0].segments[-1]

    assert [match.normalized_reference for match in extract_crossrefs(respondeo.text)] == []
    assert [match.normalized_reference for match in extract_crossrefs(reply_two.text)] == [
        "II-II:25:1"
    ]
