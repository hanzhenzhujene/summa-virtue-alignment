"""Run a lightweight end-to-end smoke test over the Christian virtue SFT pipeline."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from summa_moral_graph.sft import (
    build_dataset,
    describe_inference_plan,
    describe_training_plan,
    evaluate_predictions,
    load_dataset_build_config,
    load_inference_config,
    load_training_config,
    serialize_built_dataset,
    write_markdown_report,
)


def _override_build_paths(config_path: str, root: Path) -> tuple[object, Path]:
    config = load_dataset_build_config(config_path)
    output_dir = root / config.dataset_name
    sample_output_path = output_dir / "sample.jsonl"
    serialization = config.serialization.model_copy(
        update={
            "output_dir": output_dir,
            "sample_output_path": sample_output_path,
        }
    )
    return (config.model_copy(update={"serialization": serialization}), output_dir)


def _override_training_paths(config_path: str, dataset_dir: Path, root: Path) -> dict[str, object]:
    config = load_training_config(config_path)
    config = config.model_copy(
        update={
            "dataset_dir": dataset_dir,
            "output_dir": root / config.run_name,
        }
    )
    return describe_training_plan(config)


def _override_inference_plan(
    config_path: str,
    dataset_dir: Path,
    root: Path,
) -> dict[str, object]:
    config = load_inference_config(config_path)
    config = config.model_copy(
        update={
            "dataset_dir": dataset_dir,
            "output_dir": root / config.run_name,
        }
    )
    return describe_inference_plan(config)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        base_config, base_output_dir = _override_build_paths(
            "configs/sft/christian_virtue_v1.yaml",
            root,
        )
        ood_config, ood_output_dir = _override_build_paths(
            "configs/sft/christian_virtue_v1_ood.yaml",
            root,
        )

        base_dataset = build_dataset(base_config)
        base_summary = serialize_built_dataset(base_dataset)
        ood_dataset = build_dataset(ood_config)
        ood_summary = serialize_built_dataset(ood_dataset)

        if base_summary["examples_written"] <= 0:
            raise RuntimeError("Base SFT build produced no examples")
        if "ood_test" not in ood_summary["split_sizes"]:
            raise RuntimeError("OOD build did not produce an ood_test split")

        metrics = evaluate_predictions(base_output_dir)
        if metrics["overall"]["citation_exact_match"] != 1.0:
            raise RuntimeError(
                "Smoke evaluation should achieve perfect self-eval citation exact match"
            )

        report_path = base_output_dir / "smoke_eval_report.md"
        write_markdown_report(metrics, report_path)

        training_plans = {
            "qwen3_4b": _override_training_paths(
                "configs/train/qwen3_4b_qlora.yaml",
                base_output_dir,
                root / "outputs",
            ),
            "qwen3_8b": _override_training_paths(
                "configs/train/qwen3_8b_qlora.yaml",
                base_output_dir,
                root / "outputs",
            ),
        }
        inference_plans = {
            "qwen3_4b_base_test": _override_inference_plan(
                "configs/inference/qwen3_4b_base_test.yaml",
                base_output_dir,
                root / "eval",
            ),
            "qwen3_4b_base_ood": _override_inference_plan(
                "configs/inference/qwen3_4b_base_ood.yaml",
                ood_output_dir,
                root / "eval",
            ),
        }

        print(
            json.dumps(
                {
                    "base_build": base_summary,
                    "ood_build": ood_summary,
                    "evaluation": metrics["overall"],
                    "inference_plans": inference_plans,
                    "report_path": str(report_path),
                    "training_plans": training_plans,
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
