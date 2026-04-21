from __future__ import annotations

from summa_moral_graph.sft.config import ProtectedBucketQuota
from summa_moral_graph.sft.sampling import select_subset


def _row(task_type: str, tract: str, index: int) -> dict[str, object]:
    return {
        "example_id": f"{task_type}-{tract}-{index}",
        "task_type": task_type,
        "messages": [],
        "metadata": {"tract": tract},
    }


def _row_with_support(
    task_type: str,
    tract: str,
    support_type: str | None,
    index: int,
) -> dict[str, object]:
    row = _row(task_type, tract, index)
    if support_type is not None:
        row["metadata"] = {"tract": tract, "support_type": support_type}
    return row


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


def test_select_subset_task_tract_round_robin_with_32_examples_covers_all_task_families() -> None:
    task_types = [
        "citation_grounded_moral_answer",
        "passage_grounded_doctrinal_qa",
        "reviewed_relation_explanation",
        "virtue_concept_explanation",
    ]
    tracts = [
        "connected_virtues_109_120",
        "fortitude_closure_136_140",
        "fortitude_parts_129_135",
        "justice_core",
        "prudence",
        "temperance_141_160",
        "temperance_closure_161_170",
        "theological_virtues",
    ]
    rows = [
        _row(task_type, tract, 0)
        for task_type in task_types
        for tract in tracts
    ]

    selection = select_subset(
        rows,
        max_examples=32,
        strategy="task_tract_round_robin",
        split_name="val",
    )

    assert selection.summary["selected_examples"] == 32
    assert selection.summary["selected_counts_by_task_type"] == {
        "citation_grounded_moral_answer": 8,
        "passage_grounded_doctrinal_qa": 8,
        "reviewed_relation_explanation": 8,
        "virtue_concept_explanation": 8,
    }
    assert selection.summary["selected_counts_by_tract"] == {
        "connected_virtues_109_120": 4,
        "fortitude_closure_136_140": 4,
        "fortitude_parts_129_135": 4,
        "justice_core": 4,
        "prudence": 4,
        "temperance_141_160": 4,
        "temperance_closure_161_170": 4,
        "theological_virtues": 4,
    }


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


def test_select_subset_task_tract_quota_round_robin_respects_protected_buckets() -> None:
    rows = [
        _row_with_support(
            "citation_grounded_moral_answer",
            "justice_core",
            "strong_textual_inference",
            0,
        ),
        _row_with_support(
            "citation_grounded_moral_answer",
            "justice_core",
            "explicit_textual",
            1,
        ),
        _row_with_support(
            "passage_grounded_doctrinal_qa",
            "justice_core",
            "strong_textual_inference",
            0,
        ),
        _row_with_support(
            "passage_grounded_doctrinal_qa",
            "justice_core",
            "explicit_textual",
            1,
        ),
        _row_with_support(
            "reviewed_relation_explanation",
            "justice_core",
            "strong_textual_inference",
            0,
        ),
        _row_with_support(
            "reviewed_relation_explanation",
            "justice_core",
            "explicit_textual",
            1,
        ),
        _row_with_support(
            "citation_grounded_moral_answer",
            "prudence",
            "explicit_textual",
            0,
        ),
        _row_with_support(
            "passage_grounded_doctrinal_qa",
            "prudence",
            "explicit_textual",
            0,
        ),
    ]

    selection = select_subset(
        rows,
        max_examples=6,
        strategy="task_tract_quota_round_robin",
        split_name="train",
        task_type_quotas={
            "citation_grounded_moral_answer": 2,
            "passage_grounded_doctrinal_qa": 2,
            "reviewed_relation_explanation": 2,
        },
        protected_buckets=[
            ProtectedBucketQuota(
                label="justice-passage-sti",
                quota=1,
                task_type="passage_grounded_doctrinal_qa",
                tract="justice_core",
                support_type="strong_textual_inference",
            ),
            ProtectedBucketQuota(
                label="justice-relation-sti",
                quota=1,
                task_type="reviewed_relation_explanation",
                tract="justice_core",
                support_type="strong_textual_inference",
            ),
        ],
    )

    assert selection.summary["requested_protected_buckets"] == [
        {
            "label": "justice-passage-sti",
            "quota": 1,
            "task_type": "passage_grounded_doctrinal_qa",
            "tract": "justice_core",
            "support_type": "strong_textual_inference",
        },
        {
            "label": "justice-relation-sti",
            "quota": 1,
            "task_type": "reviewed_relation_explanation",
            "tract": "justice_core",
            "support_type": "strong_textual_inference",
        },
    ]
    assert selection.summary["protected_selected_examples"] == 2
    assert selection.summary["quota_selected_examples"] == 4
    assert selection.summary["remaining_task_type_quotas_after_protected"] == {
        "citation_grounded_moral_answer": 2,
        "passage_grounded_doctrinal_qa": 1,
        "reviewed_relation_explanation": 1,
    }
    assert selection.summary["selected_counts_by_support_type"] == {
        "explicit_textual": 3,
        "strong_textual_inference": 3,
    }
    assert selection.summary["selected_counts_by_task_type"] == {
        "citation_grounded_moral_answer": 2,
        "passage_grounded_doctrinal_qa": 2,
        "reviewed_relation_explanation": 2,
    }
    assert selection.summary["protected_bucket_results"] == [
        {
            "label": "justice-passage-sti",
            "quota": 1,
            "filters": {
                "label": "justice-passage-sti",
                "quota": 1,
                "task_type": "passage_grounded_doctrinal_qa",
                "tract": "justice_core",
                "support_type": "strong_textual_inference",
            },
            "available_examples": 1,
            "selected_examples": 1,
        },
        {
            "label": "justice-relation-sti",
            "quota": 1,
            "filters": {
                "label": "justice-relation-sti",
                "quota": 1,
                "task_type": "reviewed_relation_explanation",
                "tract": "justice_core",
                "support_type": "strong_textual_inference",
            },
            "available_examples": 1,
            "selected_examples": 1,
        },
    ]
