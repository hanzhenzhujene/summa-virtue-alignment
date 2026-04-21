from __future__ import annotations

from pathlib import Path

import pytest

from summa_moral_graph.sft import training as training_module
from summa_moral_graph.sft.config import TrainingConfig
from summa_moral_graph.sft.runtime import ModelRuntime
from summa_moral_graph.sft.training import (
    describe_training_plan,
    ensure_training_dependencies,
    resolve_training_runtime,
)


def _build_training_config(tmp_path: Path, **overrides: object) -> TrainingConfig:
    payload: dict[str, object] = {
        "run_name": "fixture-training",
        "model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
        "dataset_dir": str(tmp_path / "dataset"),
        "output_dir": str(tmp_path / "runs" / "local_baseline"),
        "load_in_4bit": True,
        "runtime_backend": "auto",
        "torch_dtype": "auto",
        "train_subset_strategy": "first_rows",
        "eval_subset_strategy": "first_rows",
    }
    payload.update(overrides)
    return TrainingConfig.model_validate(payload)


def test_resolve_training_runtime_disables_4bit_on_mps(tmp_path) -> None:
    config = _build_training_config(tmp_path, runtime_backend="mps", torch_dtype="float16")

    runtime = resolve_training_runtime(
        config,
        cuda_available=False,
        mps_available=True,
        bf16_supported=False,
    )

    assert runtime.device_type == "mps"
    assert runtime.effective_load_in_4bit is False
    assert runtime.torch_dtype_name == "float16"
    assert runtime.warnings


def test_ensure_training_dependencies_only_requires_bitsandbytes_on_cuda_quantization(
    tmp_path, monkeypatch
) -> None:
    sentinel = object()

    def fake_find_spec(name: str) -> object | None:
        if name == "bitsandbytes":
            return None
        return sentinel

    monkeypatch.setattr(training_module, "find_spec", fake_find_spec)

    monkeypatch.setattr(
        training_module,
        "_detect_runtime",
        lambda config: ModelRuntime(
            device_type="mps",
            effective_load_in_4bit=False,
            torch_dtype_name="float16",
            warnings=(),
        ),
    )
    mps_config = _build_training_config(tmp_path, runtime_backend="mps", torch_dtype="float16")
    ensure_training_dependencies(mps_config)

    monkeypatch.setattr(
        training_module,
        "_detect_runtime",
        lambda config: ModelRuntime(
            device_type="cuda",
            effective_load_in_4bit=True,
            torch_dtype_name="float16",
            warnings=(),
        ),
    )
    cuda_config = _build_training_config(tmp_path, runtime_backend="cuda", torch_dtype="float16")
    with pytest.raises(RuntimeError, match="bitsandbytes"):
        ensure_training_dependencies(cuda_config)


def test_describe_training_plan_includes_subset_strategies(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        training_module,
        "_detect_runtime",
        lambda config: ModelRuntime(
            device_type="mps",
            effective_load_in_4bit=False,
            torch_dtype_name="float16",
            warnings=("using-mps",),
        ),
    )
    config = _build_training_config(
        tmp_path,
        runtime_backend="mps",
        torch_dtype="float16",
        train_subset_strategy="task_tract_round_robin",
        eval_subset_strategy="task_tract_round_robin",
    )

    plan = describe_training_plan(config)

    assert plan["train_subset_strategy"] == "task_tract_round_robin"
    assert plan["eval_subset_strategy"] == "task_tract_round_robin"
    assert plan["resolved_device"] == "mps"


def test_describe_training_plan_includes_task_type_quotas(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        training_module,
        "_detect_runtime",
        lambda config: ModelRuntime(
            device_type="mps",
            effective_load_in_4bit=False,
            torch_dtype_name="float16",
            warnings=(),
        ),
    )
    config = _build_training_config(
        tmp_path,
        runtime_backend="mps",
        torch_dtype="float16",
        max_train_examples=128,
        max_eval_examples=32,
        train_subset_strategy="task_tract_quota_round_robin",
        eval_subset_strategy="task_tract_quota_round_robin",
        train_task_type_quotas={"citation_grounded_moral_answer": 64},
        eval_task_type_quotas={"citation_grounded_moral_answer": 16},
    )

    plan = describe_training_plan(config)

    assert plan["train_task_type_quotas"] == {"citation_grounded_moral_answer": 64}
    assert plan["eval_task_type_quotas"] == {"citation_grounded_moral_answer": 16}


def test_describe_training_plan_includes_protected_buckets(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        training_module,
        "_detect_runtime",
        lambda config: ModelRuntime(
            device_type="mps",
            effective_load_in_4bit=False,
            torch_dtype_name="float16",
            warnings=(),
        ),
    )
    config = _build_training_config(
        tmp_path,
        runtime_backend="mps",
        torch_dtype="float16",
        max_train_examples=128,
        max_eval_examples=32,
        train_subset_strategy="task_tract_quota_round_robin",
        eval_subset_strategy="task_tract_quota_round_robin",
        train_task_type_quotas={"citation_grounded_moral_answer": 48},
        eval_task_type_quotas={"citation_grounded_moral_answer": 12},
        train_protected_buckets=[
            {
                "label": "justice-relation-sti",
                "quota": 2,
                "task_type": "reviewed_relation_explanation",
                "tract": "justice_core",
                "support_type": "strong_textual_inference",
            }
        ],
        eval_protected_buckets=[
            {
                "label": "justice-passage-sti",
                "quota": 1,
                "task_type": "passage_grounded_doctrinal_qa",
                "tract": "justice_core",
                "support_type": "strong_textual_inference",
            }
        ],
    )

    plan = describe_training_plan(config)

    assert plan["train_protected_buckets"] == [
        {
            "label": "justice-relation-sti",
            "quota": 2,
            "task_type": "reviewed_relation_explanation",
            "tract": "justice_core",
            "support_type": "strong_textual_inference",
        }
    ]
    assert plan["eval_protected_buckets"] == [
        {
            "label": "justice-passage-sti",
            "quota": 1,
            "task_type": "passage_grounded_doctrinal_qa",
            "tract": "justice_core",
            "support_type": "strong_textual_inference",
        }
    ]
