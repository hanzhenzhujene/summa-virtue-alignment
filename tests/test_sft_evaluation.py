from __future__ import annotations

import json

from summa_moral_graph.sft import build_dataset, evaluate_predictions, serialize_built_dataset
from tests.sft_test_utils import build_fixture_dataset_config


def test_evaluate_predictions_respects_reference_split_filter(tmp_path) -> None:
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
    serialize_built_dataset(dataset)
    predictions_path = tmp_path / "predictions.jsonl"

    test_examples = dataset.split_result.split_examples["test"]
    with predictions_path.open("w", encoding="utf-8") as handle:
        for example in test_examples:
            assistant_text = example.messages[-1].content
            handle.write(
                json.dumps(
                    {
                        "assistant_text": assistant_text,
                        "example_id": example.example_id,
                        "split": "test",
                    },
                    sort_keys=True,
                )
            )
            handle.write("\n")

    metrics = evaluate_predictions(
        dataset_dir=config.serialization.output_dir,
        predictions_path=predictions_path,
        reference_splits=["test"],
    )

    assert metrics["evaluated_splits"] == ["test"]
    assert metrics["overall"]["count"] == len(test_examples)
    assert metrics["missing_prediction_count"] == 0
    assert metrics["overall"]["citation_exact_match"] == 1.0
