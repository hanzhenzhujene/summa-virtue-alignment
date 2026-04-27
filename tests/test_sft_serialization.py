from __future__ import annotations

from summa_moral_graph.sft import build_dataset, serialize_built_dataset
from tests.sft_test_utils import build_fixture_dataset_config


def test_serialize_built_dataset_writes_prompt_only_benchmarks(tmp_path) -> None:
    base_config = build_fixture_dataset_config(
        tmp_path,
        ood_holdout_tracts=["temperance_closure_161_170"],
    )
    config = base_config.model_copy(
        update={
            "splits": base_config.splits.model_copy(
                update={"min_eval_groups_per_tract": 1, "stratify_by_tract": False}
            )
        }
    )
    dataset = build_dataset(config)
    summary = serialize_built_dataset(dataset)

    benchmark_dir = config.serialization.output_dir / "benchmarks"
    benchmark_splits = summary["benchmark_split_sizes"]
    assert benchmark_splits
    assert set(benchmark_splits).issubset({"val", "test", "ood_test"})

    for split_name in benchmark_splits:
        benchmark_path = benchmark_dir / f"{split_name}.jsonl"
        assert benchmark_path.exists()
        first_line = benchmark_path.read_text(encoding="utf-8").splitlines()[0]
        assert '"role": "assistant"' not in first_line
