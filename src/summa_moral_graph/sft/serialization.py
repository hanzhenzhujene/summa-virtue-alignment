from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..utils.jsonl import write_jsonl
from .builders import BenchmarkExample, BuiltDataset, SFTExample


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def select_sample_examples(examples: list[SFTExample], sample_size: int) -> list[SFTExample]:
    if sample_size >= len(examples):
        return examples
    buckets: dict[str, list[SFTExample]] = defaultdict(list)
    for example in sorted(
        examples,
        key=lambda row: (
            row.task_type,
            str(row.metadata.get("tract", "")),
            str(row.metadata.get("primary_question_id", "")),
            row.example_id,
        ),
    ):
        buckets[example.task_type].append(example)

    sample: list[SFTExample] = []
    bucket_names = sorted(buckets)
    while len(sample) < sample_size and bucket_names:
        next_bucket_names: list[str] = []
        for bucket_name in bucket_names:
            bucket = buckets[bucket_name]
            if not bucket:
                continue
            sample.append(bucket.pop(0))
            if bucket:
                next_bucket_names.append(bucket_name)
            if len(sample) >= sample_size:
                break
        bucket_names = next_bucket_names
    return sample


def build_benchmark_examples_by_split(dataset: BuiltDataset) -> dict[str, list[BenchmarkExample]]:
    benchmarks: dict[str, list[BenchmarkExample]] = {}
    for split_name, rows in dataset.split_result.split_examples.items():
        if split_name == "train" or not rows:
            continue
        benchmarks[split_name] = [
            BenchmarkExample(
                example_id=row.example_id,
                task_type=row.task_type,
                split=split_name,
                messages=row.messages[:-1],
                metadata=row.metadata,
            )
            for row in rows
        ]
    return benchmarks


def serialize_built_dataset(dataset: BuiltDataset) -> dict[str, Any]:
    output_dir = dataset.config.serialization.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    all_examples = [
        row for split_rows in dataset.split_result.split_examples.values() for row in split_rows
    ]
    write_jsonl(output_dir / "all.jsonl", all_examples)
    for split_name, rows in dataset.split_result.split_examples.items():
        write_jsonl(output_dir / f"{split_name}.jsonl", rows)

    sample_examples = select_sample_examples(
        all_examples,
        dataset.config.serialization.sample_size,
    )
    write_jsonl(dataset.config.serialization.sample_output_path, sample_examples)
    benchmark_examples = build_benchmark_examples_by_split(dataset)
    benchmark_dir = output_dir / "benchmarks"
    for split_name, rows in benchmark_examples.items():
        write_jsonl(benchmark_dir / f"{split_name}.jsonl", rows)
    _write_json(output_dir / "manifest.json", dataset.manifest)
    _write_json(
        output_dir / "benchmark_manifest.json",
        {
            "benchmark_splits": {
                split_name: len(rows) for split_name, rows in sorted(benchmark_examples.items())
            }
        },
    )

    return {
        "benchmark_split_sizes": {
            split_name: len(rows) for split_name, rows in sorted(benchmark_examples.items())
        },
        "output_dir": str(output_dir),
        "sample_output_path": str(dataset.config.serialization.sample_output_path),
        "examples_written": len(all_examples),
        "split_sizes": dataset.manifest["split_sizes"],
    }
