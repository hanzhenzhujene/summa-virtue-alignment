from __future__ import annotations

from summa_moral_graph.sft import load_inference_config, load_training_config


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
