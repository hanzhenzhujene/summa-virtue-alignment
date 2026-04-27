from __future__ import annotations

from summa_moral_graph.sft import build_dataset
from summa_moral_graph.sft.builders import JoinedAnnotationRecord
from summa_moral_graph.sft.templates import (
    render_citation_grounded_answer,
    render_citation_grounded_question,
    render_passage_grounded_answer,
    render_relation_explanation_answer,
)
from summa_moral_graph.sft.utils import relation_fragment, relation_sentence
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


def test_opposition_templates_preserve_vice_to_virtue_polarity() -> None:
    annotation = JoinedAnnotationRecord.model_validate(
        {
            "annotation_id": (
                "ann.concept-lust-excess-opposed-to-concept-chastity-"
                "st-ii-ii-q153-a001-resp"
            ),
            "confidence": 0.95,
            "connected_virtues_cluster": None,
            "due_mode": None,
            "edge_layer": "doctrinal",
            "evidence_rationale": "Article 1 treats lust as the disordered contrary of chastity.",
            "evidence_text": "lust is the disordered contrary of chastity",
            "object_id": "concept.chastity",
            "object_label": "Chastity",
            "object_type": "virtue",
            "relation_type": "excess_opposed_to",
            "review_status": "approved",
            "source_passage_id": "st.ii-ii.q153.a001.resp",
            "subject_id": "concept.lust",
            "subject_label": "Lust",
            "subject_type": "vice",
            "support_type": "explicit_textual",
            "tract": "temperance_141_160",
            "tract_display_label": "Temperance (II-II qq.141-160)",
            "source_file": "temperance_141_160_reviewed_doctrinal_annotations.jsonl",
            "article_id": "st.ii-ii.q153.a001",
            "article_number": 1,
            "article_title": "Whether lust is a sin?",
            "part_id": "ii-ii",
            "question_id": "st.ii-ii.q153",
            "question_number": 153,
            "question_title": "Lust",
            "source_passage_citation_label": "II-II q.153 a.1 resp",
            "source_passage_source_url": "https://www.newadvent.org/summa/3153.htm#article1",
            "source_passage_text": "Lust is opposed to chastity as excess is opposed to virtue.",
            "source_segment_type": "resp",
        }
    )

    question = render_citation_grounded_question(annotation, "test-seed")
    answer = render_citation_grounded_answer(annotation)

    assert question == "According to Aquinas, what vice is opposed to Chastity by excess?"
    assert "According to the cited passage, Lust is opposed to Chastity by excess." in answer
    assert relation_sentence("Lust", "excess_opposed_to", "Chastity") == (
        "Lust is opposed to Chastity by excess"
    )
    assert relation_fragment("excess_opposed_to", "Chastity") == "is opposed to Chastity by excess"
