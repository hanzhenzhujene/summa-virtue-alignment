from __future__ import annotations

from summa_moral_graph.ingest.scope import parse_part_index_html


def test_in_scope_question_filtering_and_deduplication() -> None:
    html_text = """
    <html><body>
      <a href="../summa/2001.htm">last end (1)</a>
      <a href="../summa/2001.htm">duplicate last end (1)</a>
      <a href="../summa/2114.htm">merit (114)</a>
      <a href="../summa/3001.htm">wrong part</a>
      <a href="../summa/3182.htm">in scope ii-ii but wrong part index</a>
    </body></html>
    """
    entries = parse_part_index_html("i-ii", "https://www.newadvent.org/summa/2.htm", html_text)
    assert [entry.question_number for entry in entries] == [1, 114]


def test_ii_ii_scope_excludes_out_of_scope_questions() -> None:
    html_text = """
    <html><body>
      <a href="../summa/3182.htm">question 182</a>
      <a href="../summa/3183.htm">question 183</a>
      <a href="../summa/3189.htm">question 189</a>
    </body></html>
    """
    entries = parse_part_index_html("ii-ii", "https://www.newadvent.org/summa/3.htm", html_text)
    assert [entry.question_number for entry in entries] == [182]
