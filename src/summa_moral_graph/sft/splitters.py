from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .config import OODSplitConfig, SplitConfig
from .utils import stable_hash


@dataclass(frozen=True)
class SplitResult:
    split_examples: dict[str, list[Any]]
    split_group_counts: dict[str, int]
    split_tract_counts: dict[str, dict[str, int]]


def _question_group_for_example(example: Any, group_by: str) -> str:
    group_keys = example.metadata.get("group_keys", {})
    if group_by in group_keys:
        return str(group_keys[group_by])
    if group_by == "question_id":
        return str(example.metadata.get("primary_question_id"))
    raise KeyError(f"Example {example.example_id} does not expose group key {group_by}")


def _tract_for_example(example: Any) -> str:
    tract = example.metadata.get("tract")
    if not isinstance(tract, str) or not tract:
        raise ValueError(f"Example {example.example_id} is missing metadata.tract")
    return tract


def _group_counts_for_tract(group_count: int, config: SplitConfig) -> tuple[int, int, int]:
    if group_count <= 0:
        return (0, 0, 0)
    min_eval = config.min_eval_groups_per_tract if group_count >= 3 else 0
    val_groups = max(min_eval if config.val_ratio > 0 else 0, round(group_count * config.val_ratio))
    test_groups = max(
        min_eval if config.test_ratio > 0 else 0, round(group_count * config.test_ratio)
    )
    while val_groups + test_groups > max(group_count - 1, 0):
        if val_groups >= test_groups and val_groups > min_eval:
            val_groups -= 1
        elif test_groups > min_eval:
            test_groups -= 1
        elif val_groups > 0:
            val_groups -= 1
        elif test_groups > 0:
            test_groups -= 1
        else:
            break
    train_groups = group_count - val_groups - test_groups
    if train_groups <= 0:
        raise ValueError("Grouped split policy must leave at least one train group")
    return (train_groups, val_groups, test_groups)


def assign_dataset_splits(
    examples: Sequence[Any],
    split_config: SplitConfig,
    ood_config: OODSplitConfig,
) -> SplitResult:
    split_examples: dict[str, list[Any]] = {"train": [], "val": [], "test": []}
    held_out_tracts = set(ood_config.held_out_tracts)
    if held_out_tracts:
        split_examples[ood_config.name] = []

    tract_buckets: dict[str, list[Any]] = defaultdict(list)
    for example in examples:
        tract = _tract_for_example(example)
        if tract in held_out_tracts:
            split_examples[ood_config.name].append(
                example.model_copy(update={"split": ood_config.name})
            )
            continue
        tract_buckets[tract].append(example)

    split_group_counts: dict[str, set[str]] = {name: set() for name in split_examples}
    split_tract_counts: dict[str, dict[str, int]] = {
        name: defaultdict(int) for name in split_examples
    }

    for split_name, split_rows in split_examples.items():
        for row in split_rows:
            split_tract_counts[split_name][_tract_for_example(row)] += 1
            split_group_counts[split_name].add(
                _question_group_for_example(row, split_config.group_by)
            )

    remaining_examples = [example for bucket in tract_buckets.values() for example in bucket]
    tract_items = (
        tract_buckets.items() if split_config.stratify_by_tract else [("all", remaining_examples)]
    )
    for tract, tract_examples in tract_items:
        groups: dict[str, list[Any]] = defaultdict(list)
        for example in tract_examples:
            groups[_question_group_for_example(example, split_config.group_by)].append(example)

        ordered_group_ids = sorted(
            groups,
            key=lambda group_id: stable_hash(f"{split_config.seed}:{tract}:{group_id}"),
        )
        train_groups, val_groups, test_groups = _group_counts_for_tract(
            len(ordered_group_ids),
            split_config,
        )
        val_ids = set(ordered_group_ids[:val_groups])
        test_ids = set(ordered_group_ids[val_groups : val_groups + test_groups])

        for group_id, group_examples in groups.items():
            if group_id in val_ids:
                split_name = "val"
            elif group_id in test_ids:
                split_name = "test"
            else:
                split_name = "train"
            for example in group_examples:
                assigned = example.model_copy(update={"split": split_name})
                split_examples[split_name].append(assigned)
                split_tract_counts[split_name][_tract_for_example(assigned)] += 1
                split_group_counts[split_name].add(group_id)

    normalized_split_examples = {
        name: sorted(rows, key=lambda row: (row.task_type, row.example_id))
        for name, rows in split_examples.items()
    }
    normalized_group_counts = {
        name: len(group_ids) for name, group_ids in split_group_counts.items()
    }
    normalized_tract_counts = {
        name: dict(sorted(counts.items())) for name, counts in split_tract_counts.items()
    }
    return SplitResult(
        split_examples=normalized_split_examples,
        split_group_counts=normalized_group_counts,
        split_tract_counts=normalized_tract_counts,
    )
