from __future__ import annotations

from summa_moral_graph.sft.builders import ChatMessage, SFTExample
from summa_moral_graph.sft.config import OODSplitConfig, SplitConfig
from summa_moral_graph.sft.splitters import assign_dataset_splits


def _example(example_id: str, tract: str, question_id: str) -> SFTExample:
    return SFTExample(
        example_id=example_id,
        task_type="citation_grounded_moral_answer",
        messages=[
            ChatMessage(role="system", content="system"),
            ChatMessage(role="user", content="user"),
            ChatMessage(role="assistant", content="assistant"),
        ],
        metadata={
            "tract": tract,
            "group_keys": {"question_id": question_id},
            "primary_question_id": question_id,
            "support_types": ["explicit_textual"],
        },
    )


def test_assign_dataset_splits_keeps_question_groups_intact_and_supports_ood() -> None:
    examples = [
        _example("a1", "theological_virtues", "st.ii-ii.q023"),
        _example("a2", "theological_virtues", "st.ii-ii.q023"),
        _example("b1", "theological_virtues", "st.ii-ii.q024"),
        _example("c1", "theological_virtues", "st.ii-ii.q025"),
        _example("d1", "theological_virtues", "st.ii-ii.q026"),
        _example("e1", "prudence", "st.ii-ii.q047"),
        _example("f1", "temperance_closure_161_170", "st.ii-ii.q162"),
    ]
    result = assign_dataset_splits(
        examples,
        SplitConfig(
            group_by="question_id",
            train_ratio=0.6,
            val_ratio=0.2,
            test_ratio=0.2,
            seed=7,
            stratify_by_tract=True,
            min_eval_groups_per_tract=1,
        ),
        OODSplitConfig(name="ood_test", held_out_tracts=["temperance_closure_161_170"]),
    )

    split_by_example = {
        row.example_id: split_name
        for split_name, rows in result.split_examples.items()
        for row in rows
    }
    assert split_by_example["a1"] == split_by_example["a2"]
    assert split_by_example["f1"] == "ood_test"
    assert result.split_group_counts["ood_test"] == 1
    assert {"train", "val", "test"}.issubset(result.split_examples)
