from __future__ import annotations

import pytest
from pydantic import ValidationError

from summa_moral_graph.sft import load_inference_config, load_training_config
from summa_moral_graph.sft.config import TrainingConfig


def test_load_small_smoke_training_config() -> None:
    config = load_training_config("configs/train/qwen3_0_6b_qlora_smoke.yaml")

    assert config.model_name_or_path == "Qwen/Qwen3-0.6B"
    assert config.max_steps == 4
    assert config.max_train_examples == 64
    assert config.max_eval_examples == 16
    assert config.output_dir.name == "smoke"
    assert config.config_path is not None
    assert config.config_path.name == "qwen3_0_6b_qlora_smoke.yaml"


def test_load_small_adapter_inference_config() -> None:
    config = load_inference_config("configs/inference/qwen3_0_6b_adapter_test.yaml")

    assert config.model_name_or_path == "Qwen/Qwen3-0.6B"
    assert config.adapter_path is not None
    assert config.adapter_path.name == "proto"
    assert config.output_dir.name == "adapter_test"
    assert config.config_path is not None
    assert config.config_path.name == "qwen3_0_6b_adapter_test.yaml"


def test_load_qwen2_5_local_mps_training_config() -> None:
    config = load_training_config("configs/train/qwen2_5_1_5b_instruct_lora_mps_smoke.yaml")

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.max_steps == 8
    assert config.max_eval_examples == 32
    assert config.train_subset_strategy == "task_tract_round_robin"
    assert config.eval_subset_strategy == "task_tract_round_robin"
    assert config.config_path is not None
    assert config.config_path.name == "qwen2_5_1_5b_instruct_lora_mps_smoke.yaml"


def test_load_qwen2_5_local_mps_local_baseline_training_config() -> None:
    config = load_training_config(
        "configs/train/qwen2_5_1_5b_instruct_lora_mps_local_baseline.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.max_steps == 20
    assert config.max_train_examples == 128
    assert config.max_eval_examples == 32
    assert config.train_subset_strategy == "task_tract_round_robin"
    assert config.eval_subset_strategy == "task_tract_round_robin"
    assert config.config_path is not None
    assert config.config_path.name == "qwen2_5_1_5b_instruct_lora_mps_local_baseline.yaml"


def test_load_qwen2_5_local_mps_extended_training_config() -> None:
    config = load_training_config("configs/train/qwen2_5_1_5b_instruct_lora_mps_extended.yaml")

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.max_steps == 100
    assert config.max_train_examples == 512
    assert config.max_eval_examples == 64
    assert config.train_subset_strategy == "task_tract_round_robin"
    assert config.eval_subset_strategy == "task_tract_round_robin"
    assert config.config_path is not None
    assert config.config_path.name == "qwen2_5_1_5b_instruct_lora_mps_extended.yaml"


def test_load_qwen2_5_local_mps_citation_frontier_training_config() -> None:
    config = load_training_config(
        "configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.max_steps == 20
    assert config.max_train_examples == 128
    assert config.max_eval_examples == 32
    assert config.train_subset_strategy == "task_tract_quota_round_robin"
    assert config.eval_subset_strategy == "task_tract_quota_round_robin"
    assert config.train_task_type_quotas == {
        "citation_grounded_moral_answer": 64,
        "reviewed_relation_explanation": 24,
        "virtue_concept_explanation": 24,
        "passage_grounded_doctrinal_qa": 16,
    }
    assert config.eval_task_type_quotas == {
        "citation_grounded_moral_answer": 16,
        "reviewed_relation_explanation": 8,
        "virtue_concept_explanation": 4,
        "passage_grounded_doctrinal_qa": 4,
    }
    assert config.config_path is not None
    assert config.config_path.name == "qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml"


def test_load_qwen2_5_local_mps_justice_guarded_training_config() -> None:
    config = load_training_config(
        "configs/train/qwen2_5_1_5b_instruct_lora_mps_justice_guarded_citation_repair.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.max_steps == 20
    assert config.max_train_examples == 128
    assert config.max_eval_examples == 32
    assert config.train_subset_strategy == "task_tract_quota_round_robin"
    assert config.eval_subset_strategy == "task_tract_quota_round_robin"
    assert config.train_task_type_quotas == {
        "citation_grounded_moral_answer": 50,
        "reviewed_relation_explanation": 28,
        "virtue_concept_explanation": 24,
        "passage_grounded_doctrinal_qa": 26,
    }
    assert config.eval_task_type_quotas == {
        "citation_grounded_moral_answer": 8,
        "reviewed_relation_explanation": 8,
        "virtue_concept_explanation": 8,
        "passage_grounded_doctrinal_qa": 8,
    }
    assert config.train_protected_buckets is not None
    assert [bucket.label for bucket in config.train_protected_buckets] == [
        "justice-passage-sti",
        "justice-relation-sti",
        "justice-passage-explicit",
        "justice-relation-explicit",
    ]
    assert config.config_path is not None
    assert (
        config.config_path.name
        == "qwen2_5_1_5b_instruct_lora_mps_justice_guarded_citation_repair.yaml"
    )


def test_load_qwen2_5_local_mps_accuracy_first_training_config() -> None:
    config = load_training_config(
        "configs/train/qwen2_5_1_5b_instruct_lora_mps_accuracy_first_hybrid.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.max_steps == 20
    assert config.max_train_examples == 128
    assert config.max_eval_examples == 32
    assert config.train_subset_strategy == "task_tract_quota_round_robin"
    assert config.eval_subset_strategy == "task_tract_quota_round_robin"
    assert config.train_task_type_quotas == {
        "citation_grounded_moral_answer": 56,
        "reviewed_relation_explanation": 26,
        "virtue_concept_explanation": 22,
        "passage_grounded_doctrinal_qa": 24,
    }
    assert config.eval_task_type_quotas == {
        "citation_grounded_moral_answer": 10,
        "reviewed_relation_explanation": 8,
        "virtue_concept_explanation": 6,
        "passage_grounded_doctrinal_qa": 8,
    }
    assert config.train_protected_buckets is not None
    assert [bucket.label for bucket in config.train_protected_buckets] == [
        "justice-passage-sti",
        "justice-relation-sti",
        "justice-passage-explicit",
        "justice-relation-explicit",
        "moral-qa-sti",
        "moral-qa-explicit",
    ]
    assert config.config_path is not None
    assert (
        config.config_path.name
        == "qwen2_5_1_5b_instruct_lora_mps_accuracy_first_hybrid.yaml"
    )


def test_training_config_rejects_filterless_protected_bucket() -> None:
    with pytest.raises(ValidationError, match="at least one of task_type, tract, or support_type"):
        TrainingConfig.model_validate(
            {
                "run_name": "fixture",
                "model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
                "dataset_dir": "data/processed/sft/exports/christian_virtue_v1",
                "output_dir": "runs/christian_virtue/qwen2_5_1_5b_instruct/fixture",
                "max_train_examples": 8,
                "max_eval_examples": 8,
                "train_subset_strategy": "task_tract_quota_round_robin",
                "eval_subset_strategy": "task_tract_quota_round_robin",
                "train_task_type_quotas": {"citation_grounded_moral_answer": 8},
                "eval_task_type_quotas": {"citation_grounded_moral_answer": 8},
                "train_protected_buckets": [{"quota": 1}],
            }
        )


def test_load_qwen2_5_local_adapter_inference_config() -> None:
    config = load_inference_config("configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml")

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.adapter_path is not None
    assert config.adapter_path.parent.name == "local_baseline"
    assert config.config_path is not None
    assert config.config_path.name == "qwen2_5_1_5b_instruct_adapter_test.yaml"


def test_load_qwen2_5_citation_frontier_adapter_inference_config() -> None:
    config = load_inference_config(
        "configs/inference/qwen2_5_1_5b_instruct_citation_frontier_adapter_test.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.adapter_path is not None
    assert config.adapter_path.parent.name == "citation_frontier"
    assert config.output_dir.name == "citation_frontier_adapter_test"
    assert config.config_path is not None
    assert (
        config.config_path.name == "qwen2_5_1_5b_instruct_citation_frontier_adapter_test.yaml"
    )


def test_load_qwen2_5_justice_guarded_adapter_inference_config() -> None:
    config = load_inference_config(
        "configs/inference/qwen2_5_1_5b_instruct_justice_guarded_adapter_test.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.adapter_path is not None
    assert config.adapter_path.parent.name == "justice_guarded_citation_repair"
    assert config.output_dir.name == "justice_guarded_citation_repair_adapter_test"
    assert config.config_path is not None
    assert (
        config.config_path.name
        == "qwen2_5_1_5b_instruct_justice_guarded_adapter_test.yaml"
    )


def test_load_qwen2_5_accuracy_first_adapter_inference_config() -> None:
    config = load_inference_config(
        "configs/inference/qwen2_5_1_5b_instruct_accuracy_first_adapter_test.yaml"
    )

    assert config.model_name_or_path == "Qwen/Qwen2.5-1.5B-Instruct"
    assert config.runtime_backend == "mps"
    assert config.torch_dtype == "float16"
    assert config.load_in_4bit is False
    assert config.adapter_path is not None
    assert config.adapter_path.parent.name == "accuracy_first_hybrid"
    assert config.output_dir.name == "accuracy_first_hybrid_adapter_test"
    assert config.config_path is not None
    assert (
        config.config_path.name
        == "qwen2_5_1_5b_instruct_accuracy_first_adapter_test.yaml"
    )
