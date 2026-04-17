from __future__ import annotations

from summa_moral_graph.sft import build_dataset
from summa_moral_graph.sft.templates import (
    render_citation_grounded_answer,
    render_passage_grounded_answer,
    render_relation_explanation_answer,
)
from tests.sft_test_utils import build_fixture_dataset_config


def test_template_answers_preserve_citations_and_support_language(tmp_path) -> None:
    config = build_fixture_dataset_config(tmp_path)
    dataset = build_dataset(config)
    strong_inference = next(
        annotation
        for annotation in dataset.annotations
        if annotation.annotation_id == "ann.charity-caused-by-holy-spirit"
    )

    passage_answer = render_passage_grounded_answer(strong_inference)
    relation_answer = render_relation_explanation_answer(strong_inference)
    moral_answer = render_citation_grounded_answer(strong_inference)

    assert "strong textual inference" in passage_answer.lower()
    assert "Holy Spirit" in relation_answer
    assert "st.ii-ii.q024.a002.resp" in moral_answer
    assert "II-II q.24 a.2 resp" in moral_answer
