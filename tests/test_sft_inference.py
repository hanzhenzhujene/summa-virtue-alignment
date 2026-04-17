from __future__ import annotations

from pathlib import Path

from summa_moral_graph.sft.config import InferenceConfig
from summa_moral_graph.sft.inference import (
    _clean_assistant_text,
    describe_inference_plan,
    resolve_inference_runtime,
)


def _build_inference_config(tmp_path: Path) -> InferenceConfig:
    return InferenceConfig.model_validate(
        {
            "run_name": "fixture-inference",
            "model_name_or_path": "Qwen/Qwen3-4B",
            "dataset_dir": str(tmp_path / "dataset"),
            "split_names": ["test"],
            "output_dir": str(tmp_path / "eval"),
            "load_in_4bit": True,
        }
    )


def test_resolve_inference_runtime_falls_back_from_4bit_without_cuda(tmp_path) -> None:
    config = _build_inference_config(tmp_path)

    runtime = resolve_inference_runtime(
        config,
        cuda_available=False,
        mps_available=True,
        bf16_supported=False,
    )

    assert runtime.device_type == "mps"
    assert runtime.effective_load_in_4bit is False
    assert runtime.torch_dtype_name == "float16"
    assert runtime.warnings


def test_resolve_inference_runtime_keeps_4bit_on_cuda(tmp_path) -> None:
    config = _build_inference_config(tmp_path)

    runtime = resolve_inference_runtime(
        config,
        cuda_available=True,
        mps_available=False,
        bf16_supported=True,
    )

    assert runtime.device_type == "cuda"
    assert runtime.effective_load_in_4bit is True
    assert runtime.torch_dtype_name == "bfloat16"
    assert runtime.warnings == ()


def test_describe_inference_plan_reports_runtime_fields(tmp_path) -> None:
    config = _build_inference_config(tmp_path)

    plan = describe_inference_plan(config)

    assert plan["resolved_device"] in {"cuda", "mps", "cpu"}
    assert "effective_load_in_4bit" in plan
    assert "torch_dtype" in plan


def test_clean_assistant_text_removes_qwen_think_blocks() -> None:
    text = "<think>\ninternal reasoning\n</think>\n\nFinal answer with citations."

    assert _clean_assistant_text(text) == "Final answer with citations."
