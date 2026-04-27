from __future__ import annotations

from summa_moral_graph.sft import build_dataset
from tests.sft_test_utils import build_fixture_dataset_config


def test_build_dataset_emits_all_required_task_families_and_metadata(tmp_path) -> None:
    config = build_fixture_dataset_config(tmp_path)
    dataset = build_dataset(config)

    task_types = {example.task_type for example in dataset.examples}
    assert task_types == {
        "citation_grounded_moral_answer",
        "passage_grounded_doctrinal_qa",
        "reviewed_relation_explanation",
        "virtue_concept_explanation",
    }
    first_relation = next(
        example
        for example in dataset.examples
        if example.task_type == "reviewed_relation_explanation"
    )
    assert first_relation.metadata["source_passage_id"].startswith("st.ii-ii.q")
    assert first_relation.metadata["citation_label"].startswith("II-II q.")
    assert first_relation.metadata["tract"] in {
        "theological_virtues",
        "prudence",
        "temperance_closure_161_170",
    }
    concept_example = next(
        example
        for example in dataset.examples
        if example.task_type == "virtue_concept_explanation"
        and example.metadata["subject_id"] == "concept.charity"
        and example.metadata["primary_question_id"] == "st.ii-ii.q023"
    )
    assistant_text = concept_example.messages[-1].content
    assert "Beneficence" in assistant_text
    assert "treated in" not in assistant_text.lower()
    assert "st.ii-ii.q023.a001.resp" in assistant_text
