from __future__ import annotations

from summa_moral_graph.sft.sampling import select_subset


def _row(task_type: str, tract: str, index: int) -> dict[str, object]:
    return {
        "example_id": f"{task_type}-{tract}-{index}",
        "task_type": task_type,
        "messages": [],
        "metadata": {"tract": tract},
    }


def test_select_subset_first_rows_preserves_order() -> None:
    rows = [_row("reviewed_relation_explanation", "prudence", idx) for idx in range(5)]

    selection = select_subset(
        rows,
        max_examples=3,
        strategy="first_rows",
        split_name="train",
    )

    assert [row["example_id"] for row in selection.rows] == [
        "reviewed_relation_explanation-prudence-0",
        "reviewed_relation_explanation-prudence-1",
        "reviewed_relation_explanation-prudence-2",
    ]
    assert selection.summary["selection_strategy"] == "first_rows"


def test_select_subset_task_tract_round_robin_balances_groups() -> None:
    rows = [
        _row("citation_grounded_moral_answer", "prudence", 0),
        _row("citation_grounded_moral_answer", "prudence", 1),
        _row("citation_grounded_moral_answer", "justice_core", 0),
        _row("citation_grounded_moral_answer", "justice_core", 1),
        _row("virtue_concept_explanation", "prudence", 0),
        _row("virtue_concept_explanation", "prudence", 1),
        _row("virtue_concept_explanation", "justice_core", 0),
        _row("virtue_concept_explanation", "justice_core", 1),
    ]

    selection = select_subset(
        rows,
        max_examples=4,
        strategy="task_tract_round_robin",
        split_name="train",
    )

    assert selection.summary["selected_counts_by_task_type"] == {
        "citation_grounded_moral_answer": 2,
        "virtue_concept_explanation": 2,
    }
    assert selection.summary["selected_counts_by_tract"] == {
        "justice_core": 2,
        "prudence": 2,
    }
    assert [row["example_id"] for row in selection.rows] == [
        "citation_grounded_moral_answer-justice_core-0",
        "citation_grounded_moral_answer-prudence-0",
        "virtue_concept_explanation-justice_core-0",
        "virtue_concept_explanation-prudence-0",
    ]


def test_select_subset_without_cap_uses_full_dataset() -> None:
    rows = [_row("reviewed_relation_explanation", "prudence", idx) for idx in range(2)]

    selection = select_subset(
        rows,
        max_examples=None,
        strategy="task_tract_round_robin",
        split_name="val",
    )

    assert len(selection.rows) == 2
    assert selection.summary["selected_examples"] == 2
    assert selection.summary["requested_examples"] is None


def test_select_subset_task_tract_quota_round_robin_prioritizes_target_task() -> None:
    rows = [
        _row("citation_grounded_moral_answer", "prudence", 0),
        _row("citation_grounded_moral_answer", "prudence", 1),
        _row("citation_grounded_moral_answer", "justice_core", 0),
        _row("citation_grounded_moral_answer", "justice_core", 1),
        _row("reviewed_relation_explanation", "prudence", 0),
        _row("reviewed_relation_explanation", "justice_core", 0),
        _row("virtue_concept_explanation", "prudence", 0),
        _row("passage_grounded_doctrinal_qa", "prudence", 0),
    ]

    selection = select_subset(
        rows,
        max_examples=6,
        strategy="task_tract_quota_round_robin",
        split_name="train",
        task_type_quotas={
            "citation_grounded_moral_answer": 4,
            "reviewed_relation_explanation": 1,
        },
    )

    assert selection.summary["requested_task_type_quotas"] == {
        "citation_grounded_moral_answer": 4,
        "reviewed_relation_explanation": 1,
    }
    assert selection.summary["selected_counts_by_task_type"] == {
        "citation_grounded_moral_answer": 4,
        "passage_grounded_doctrinal_qa": 1,
        "reviewed_relation_explanation": 1,
    }
    assert selection.summary["quota_selected_examples"] == 5
    assert selection.summary["quota_fill_remainder_examples"] == 1
