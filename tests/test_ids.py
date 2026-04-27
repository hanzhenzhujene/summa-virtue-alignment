from __future__ import annotations

import pytest

from summa_moral_graph.utils.ids import article_id, question_id, segment_id


def test_stable_id_generation() -> None:
    qid = question_id("i-ii", 1)
    aid = article_id(qid, 1)
    resp_id = segment_id(aid, "resp", None)
    ad_id = segment_id(aid, "ad", 1)

    assert qid == "st.i-ii.q001"
    assert aid == "st.i-ii.q001.a001"
    assert resp_id == "st.i-ii.q001.a001.resp"
    assert ad_id == "st.i-ii.q001.a001.ad1"


@pytest.mark.parametrize(
    ("segment_type", "ordinal"),
    [
        ("obj", 1),
        ("sc", None),
    ],
)
def test_exported_segment_ids_reject_objection_and_sed_contra_types(
    segment_type: str,
    ordinal: int | None,
) -> None:
    qid = question_id("i-ii", 1)
    aid = article_id(qid, 1)

    with pytest.raises(ValueError):
        segment_id(aid, segment_type, ordinal)
