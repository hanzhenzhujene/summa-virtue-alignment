from __future__ import annotations

from summa_moral_graph.utils.ids import article_id, question_id, segment_id


def test_stable_id_generation() -> None:
    qid = question_id("i-ii", 1)
    aid = article_id(qid, 1)
    obj_id = segment_id(aid, "obj", 1)
    sc_id = segment_id(aid, "sc", None)
    resp_id = segment_id(aid, "resp", None)
    ad_id = segment_id(aid, "ad", 1)

    assert qid == "st.i-ii.q001"
    assert aid == "st.i-ii.q001.a001"
    assert obj_id == "st.i-ii.q001.a001.obj1"
    assert sc_id == "st.i-ii.q001.a001.sc"
    assert resp_id == "st.i-ii.q001.a001.resp"
    assert ad_id == "st.i-ii.q001.a001.ad1"

