"""Deterministic subset-selection helpers for small Christian virtue SFT runs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from .config import ProtectedBucketQuota, TrainingSubsetStrategy

_MISSING_TASK_TYPE = "__missing_task_type__"
_MISSING_TRACT = "__missing_tract__"
_MISSING_SUPPORT_TYPE = "none"


@dataclass(frozen=True)
class SelectedSubset:
    rows: list[dict[str, Any]]
    summary: dict[str, Any]


def select_subset(
    rows: list[dict[str, Any]],
    *,
    max_examples: int | None,
    strategy: TrainingSubsetStrategy,
    split_name: str,
    task_type_quotas: dict[str, int] | None = None,
    protected_buckets: list[ProtectedBucketQuota] | None = None,
) -> SelectedSubset:
    summary_extras: dict[str, Any] = {}
    if max_examples is None or max_examples >= len(rows):
        selected_rows = list(rows)
    elif strategy == "first_rows":
        selected_rows = list(rows[:max_examples])
    elif strategy == "task_tract_round_robin":
        selected_rows = _task_tract_round_robin(rows, max_examples)
    elif strategy == "task_tract_quota_round_robin":
        selected_rows, summary_extras = _task_tract_quota_round_robin(
            rows,
            max_examples,
            task_type_quotas=task_type_quotas or {},
            protected_buckets=protected_buckets or [],
        )
    else:
        raise ValueError(f"Unsupported subset strategy: {strategy}")

    return SelectedSubset(
        rows=selected_rows,
        summary=_build_subset_summary(
            rows,
            selected_rows,
            max_examples=max_examples,
            strategy=strategy,
            split_name=split_name,
            task_type_quotas=task_type_quotas,
            protected_buckets=protected_buckets,
            summary_extras=summary_extras,
        ),
    )


def _task_tract_round_robin(
    rows: list[dict[str, Any]],
    max_examples: int,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (_task_type(row), _tract(row))
        buckets.setdefault(key, []).append(row)

    bucket_positions = {key: 0 for key in buckets}
    bucket_keys = sorted(buckets)
    selected_rows: list[dict[str, Any]] = []

    while len(selected_rows) < max_examples:
        progressed = False
        for key in bucket_keys:
            position = bucket_positions[key]
            bucket = buckets[key]
            if position >= len(bucket):
                continue
            selected_rows.append(bucket[position])
            bucket_positions[key] = position + 1
            progressed = True
            if len(selected_rows) >= max_examples:
                break
        if not progressed:
            break

    return selected_rows


def _task_tract_quota_round_robin(
    rows: list[dict[str, Any]],
    max_examples: int,
    *,
    task_type_quotas: dict[str, int],
    protected_buckets: list[ProtectedBucketQuota],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_rows: list[dict[str, Any]] = []
    selected_example_ids: set[str] = set()
    protected_bucket_results: list[dict[str, Any]] = []

    for bucket in protected_buckets:
        available_rows = [
            row
            for row in rows
            if str(row.get("example_id", "")) not in selected_example_ids
            and _matches_protected_bucket(row, bucket)
        ]
        bucket_rows = _task_tract_round_robin(available_rows, bucket.quota)
        selected_rows.extend(bucket_rows)
        selected_example_ids.update(str(row.get("example_id", "")) for row in bucket_rows)
        protected_bucket_results.append(
            {
                "label": _protected_bucket_label(bucket),
                "quota": bucket.quota,
                "filters": _serialize_protected_bucket(bucket),
                "available_examples": len(available_rows),
                "selected_examples": len(bucket_rows),
            }
        )

    remaining_task_type_quotas = dict(task_type_quotas)
    for row in selected_rows:
        task_type = _task_type(row)
        if task_type in remaining_task_type_quotas:
            remaining_task_type_quotas[task_type] = max(
                0,
                remaining_task_type_quotas[task_type] - 1,
            )

    quota_rows: list[dict[str, Any]] = []
    for task_type, quota in sorted(remaining_task_type_quotas.items()):
        if quota <= 0:
            continue
        task_rows = [
            row
            for row in rows
            if _task_type(row) == task_type
            and str(row.get("example_id", "")) not in selected_example_ids
        ]
        task_selection = _tract_round_robin(task_rows, quota)
        quota_rows.extend(task_selection)
        selected_rows.extend(task_selection)
        selected_example_ids.update(str(row.get("example_id", "")) for row in task_selection)

    quota_selected_examples = len(selected_rows)
    remaining_budget = max_examples - quota_selected_examples
    fill_rows: list[dict[str, Any]] = []
    if remaining_budget > 0:
        remaining_rows = [
            row
            for row in rows
            if str(row.get("example_id", "")) not in selected_example_ids
        ]
        fill_rows = _task_tract_round_robin(remaining_rows, remaining_budget)
        selected_rows.extend(fill_rows)

    return selected_rows, {
        "protected_bucket_results": protected_bucket_results,
        "protected_selected_examples": sum(
            bucket_result["selected_examples"] for bucket_result in protected_bucket_results
        ),
        "quota_fill_remainder_examples": len(fill_rows),
        "quota_selected_examples": len(quota_rows),
        "remaining_task_type_quotas_after_protected": dict(
            sorted(remaining_task_type_quotas.items())
        ),
    }


def _tract_round_robin(rows: list[dict[str, Any]], max_examples: int) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        buckets.setdefault(_tract(row), []).append(row)

    bucket_positions = {key: 0 for key in buckets}
    bucket_keys = sorted(buckets)
    selected_rows: list[dict[str, Any]] = []

    while len(selected_rows) < max_examples:
        progressed = False
        for key in bucket_keys:
            position = bucket_positions[key]
            bucket = buckets[key]
            if position >= len(bucket):
                continue
            selected_rows.append(bucket[position])
            bucket_positions[key] = position + 1
            progressed = True
            if len(selected_rows) >= max_examples:
                break
        if not progressed:
            break

    return selected_rows


def _build_subset_summary(
    source_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    *,
    max_examples: int | None,
    strategy: TrainingSubsetStrategy,
    split_name: str,
    task_type_quotas: dict[str, int] | None,
    protected_buckets: list[ProtectedBucketQuota] | None,
    summary_extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = {
        "available_examples": len(source_rows),
        "requested_examples": max_examples,
        "requested_task_type_quotas": dict(sorted((task_type_quotas or {}).items())),
        "requested_protected_buckets": [
            _serialize_protected_bucket(bucket) for bucket in protected_buckets or []
        ],
        "selected_examples": len(selected_rows),
        "selected_fraction": (
            0.0 if not source_rows else round(len(selected_rows) / len(source_rows), 6)
        ),
        "selection_grouping_keys": (
            ["task_type", "metadata.tract"]
            if strategy in {"task_tract_round_robin", "task_tract_quota_round_robin"}
            else []
        ),
        "selection_strategy": strategy,
        "source_counts_by_support_type": _counts_by_support_type(source_rows),
        "source_counts_by_task_and_tract": _counts_by_task_and_tract(source_rows),
        "source_counts_by_task_type": _counts_by_task_type(source_rows),
        "source_counts_by_tract": _counts_by_tract(source_rows),
        "selected_counts_by_support_type": _counts_by_support_type(selected_rows),
        "selected_counts_by_task_and_tract": _counts_by_task_and_tract(selected_rows),
        "selected_counts_by_task_type": _counts_by_task_type(selected_rows),
        "selected_counts_by_tract": _counts_by_tract(selected_rows),
        "split_name": split_name,
    }
    if summary_extras:
        summary.update(summary_extras)
    return summary


def _counts_by_task_type(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(_task_type(row) for row in rows)
    return dict(sorted(counts.items()))


def _counts_by_tract(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(_tract(row) for row in rows)
    return dict(sorted(counts.items()))


def _counts_by_task_and_tract(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((_task_type(row), _tract(row)) for row in rows)
    return [
        {"count": count, "task_type": task_type, "tract": tract}
        for (task_type, tract), count in sorted(counts.items())
    ]


def _counts_by_support_type(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(_support_type(row) for row in rows)
    return dict(sorted(counts.items()))


def _task_type(row: dict[str, Any]) -> str:
    value = row.get("task_type")
    if value in (None, ""):
        return _MISSING_TASK_TYPE
    return str(value)


def _tract(row: dict[str, Any]) -> str:
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("tract")
        if value not in (None, ""):
            return str(value)
    return _MISSING_TRACT


def _support_type(row: dict[str, Any]) -> str:
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("support_type")
        if value not in (None, ""):
            return str(value)
    return _MISSING_SUPPORT_TYPE


def _matches_protected_bucket(row: dict[str, Any], bucket: ProtectedBucketQuota) -> bool:
    if bucket.task_type is not None and _task_type(row) != bucket.task_type:
        return False
    if bucket.tract is not None and _tract(row) != bucket.tract:
        return False
    if bucket.support_type is not None and _support_type(row) != bucket.support_type:
        return False
    return True


def _serialize_protected_bucket(bucket: ProtectedBucketQuota) -> dict[str, Any]:
    payload: dict[str, Any] = {"quota": bucket.quota}
    if bucket.label is not None:
        payload["label"] = bucket.label
    if bucket.task_type is not None:
        payload["task_type"] = bucket.task_type
    if bucket.tract is not None:
        payload["tract"] = bucket.tract
    if bucket.support_type is not None:
        payload["support_type"] = bucket.support_type
    return payload


def _protected_bucket_label(bucket: ProtectedBucketQuota) -> str:
    if bucket.label is not None:
        return bucket.label
    parts: list[str] = []
    if bucket.task_type is not None:
        parts.append(bucket.task_type)
    if bucket.tract is not None:
        parts.append(bucket.tract)
    if bucket.support_type is not None:
        parts.append(bucket.support_type)
    return " / ".join(parts)
