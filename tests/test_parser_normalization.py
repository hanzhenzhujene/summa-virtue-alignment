from __future__ import annotations

from bs4 import BeautifulSoup

from summa_moral_graph.ingest.parser import parse_article_segments


def test_duplicate_reply_labels_are_normalized_by_occurrence_order() -> None:
    html_text = """
    <div>
      <p><strong>Objection 1.</strong> First objection.</p>
      <p><strong>Objection 1.</strong> Duplicated objection label in source.</p>
      <p><strong>On the contrary,</strong> Sed contra text.</p>
      <p><strong>I answer that,</strong> Respondeo text.</p>
      <p><strong>Reply to Objection 1.</strong> First reply.</p>
      <p><strong>Reply to Objection 1.</strong> Duplicated reply label in source.</p>
    </div>
    """
    soup = BeautifulSoup(html_text, "lxml")
    paragraphs = list(soup.find_all("p"))

    segments = parse_article_segments(paragraphs)

    assert [(segment.segment_type, segment.segment_ordinal) for segment in segments] == [
        ("obj", 1),
        ("obj", 2),
        ("sc", None),
        ("resp", None),
        ("ad", 1),
        ("ad", 2),
    ]


def test_repeated_sed_contra_labels_are_merged_into_one_segment() -> None:
    html_text = """
    <div>
      <p><strong>Objection 1.</strong> First objection.</p>
      <p><strong>On the contrary,</strong> First sed contra paragraph.</p>
      <p><strong>On the contrary,</strong> Second sed contra paragraph.</p>
      <p><strong>I answer that,</strong> Respondeo text.</p>
    </div>
    """
    soup = BeautifulSoup(html_text, "lxml")
    paragraphs = list(soup.find_all("p"))

    segments = parse_article_segments(paragraphs)

    assert [(segment.segment_type, segment.segment_ordinal) for segment in segments] == [
        ("obj", 1),
        ("sc", None),
        ("resp", None),
    ]
    assert segments[1].text == "First sed contra paragraph. Second sed contra paragraph."


def test_out_of_order_repeated_sed_contra_is_folded_into_current_reply() -> None:
    html_text = """
    <div>
      <p><strong>Objection 1.</strong> First objection.</p>
      <p><strong>On the contrary,</strong> Sed contra text.</p>
      <p><strong>I answer that,</strong> Respondeo text.</p>
      <p><strong>Reply to Objection 1.</strong> First reply paragraph.</p>
      <p><strong>On the contrary,</strong> Source typo but really continuation.</p>
    </div>
    """
    soup = BeautifulSoup(html_text, "lxml")
    paragraphs = list(soup.find_all("p"))

    segments = parse_article_segments(paragraphs)

    assert [(segment.segment_type, segment.segment_ordinal) for segment in segments] == [
        ("obj", 1),
        ("sc", None),
        ("resp", None),
        ("ad", 1),
    ]
    assert segments[-1].text == "First reply paragraph. Source typo but really continuation."


def test_late_objection_label_is_normalized_into_reply_section() -> None:
    html_text = """
    <div>
      <p><strong>Objection 1.</strong> First objection.</p>
      <p><strong>Objection 2.</strong> Second objection.</p>
      <p><strong>On the contrary,</strong> Sed contra text.</p>
      <p><strong>I answer that,</strong> Respondeo text.</p>
      <p><strong>Reply to Objection 1.</strong> First reply paragraph.</p>
      <p><strong>Objection 2.</strong> Source typo but actually second reply.</p>
    </div>
    """
    soup = BeautifulSoup(html_text, "lxml")
    paragraphs = list(soup.find_all("p"))

    segments = parse_article_segments(paragraphs)

    assert [(segment.segment_type, segment.segment_ordinal) for segment in segments] == [
        ("obj", 1),
        ("obj", 2),
        ("sc", None),
        ("resp", None),
        ("ad", 1),
        ("ad", 2),
    ]
