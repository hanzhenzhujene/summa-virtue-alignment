from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Literal

RuntimeBackend = Literal["auto", "cuda", "mps", "cpu"]
TorchDtypeSetting = Literal["auto", "bfloat16", "float16", "float32"]
ResolvedDevice = Literal["cuda", "mps", "cpu"]
ResolvedTorchDtype = Literal["bfloat16", "float16", "float32"]


@dataclass(frozen=True)
class TorchAvailability:
    cuda_available: bool
    mps_available: bool
    bf16_supported: bool


@dataclass(frozen=True)
class ModelRuntime:
    device_type: ResolvedDevice
    effective_load_in_4bit: bool
    torch_dtype_name: ResolvedTorchDtype
    warnings: tuple[str, ...] = ()


def detect_torch_availability() -> TorchAvailability | None:
    if importlib.util.find_spec("torch") is None:
        return None

    import torch

    mps_backend = getattr(torch.backends, "mps", None)
    return TorchAvailability(
        cuda_available=bool(torch.cuda.is_available()),
        mps_available=bool(mps_backend is not None and mps_backend.is_available()),
        bf16_supported=bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported()),
    )


def resolve_model_runtime(
    *,
    runtime_backend: RuntimeBackend,
    torch_dtype: TorchDtypeSetting,
    load_in_4bit: bool,
    cuda_available: bool,
    mps_available: bool,
    bf16_supported: bool,
) -> ModelRuntime:
    device_type: ResolvedDevice
    if runtime_backend == "auto":
        if cuda_available:
            device_type = "cuda"
        elif mps_available:
            device_type = "mps"
        else:
            device_type = "cpu"
    elif runtime_backend == "cuda":
        if not cuda_available:
            raise ValueError("runtime_backend='cuda' was requested, but CUDA is unavailable.")
        device_type = "cuda"
    elif runtime_backend == "mps":
        if not mps_available:
            raise ValueError("runtime_backend='mps' was requested, but MPS is unavailable.")
        device_type = "mps"
    else:
        device_type = "cpu"

    warnings: list[str] = []
    effective_load_in_4bit = load_in_4bit and device_type == "cuda"
    if load_in_4bit and not effective_load_in_4bit:
        warnings.append(
            "4-bit quantization is CUDA-only in this runner; using standard weights on "
            f"{device_type} instead."
        )

    if torch_dtype == "auto":
        if device_type == "cuda":
            resolved_torch_dtype: ResolvedTorchDtype = (
                "bfloat16" if bf16_supported else "float16"
            )
        elif device_type == "mps":
            resolved_torch_dtype = "float16"
        else:
            resolved_torch_dtype = "float32"
    else:
        resolved_torch_dtype = torch_dtype

    if device_type == "mps" and resolved_torch_dtype == "bfloat16":
        raise ValueError("MPS execution does not support bfloat16 in this training/inference path.")

    return ModelRuntime(
        device_type=device_type,
        effective_load_in_4bit=effective_load_in_4bit,
        torch_dtype_name=resolved_torch_dtype,
        warnings=tuple(warnings),
    )
