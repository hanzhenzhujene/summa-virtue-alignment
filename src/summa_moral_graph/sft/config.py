from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..utils.paths import REPO_ROOT
from .runtime import RuntimeBackend, TorchDtypeSetting

DEFAULT_ALLOWED_SUBJECT_TYPES = [
    "virtue",
    "vice",
    "sin_type",
    "act_type",
    "act",
    "wrong_act",
    "prudence_part",
    "gift_holy_spirit",
    "habit",
    "precept",
    "defect",
    "passion",
    "doctrine",
]


def _resolve_repo_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


class CorpusPathsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    segments_path: Path = Field(default=REPO_ROOT / "data/interim/summa_moral_segments.jsonl")
    questions_path: Path = Field(default=REPO_ROOT / "data/interim/summa_moral_questions.jsonl")
    articles_path: Path = Field(default=REPO_ROOT / "data/interim/summa_moral_articles.jsonl")

    @field_validator("segments_path", "questions_path", "articles_path", mode="before")
    @classmethod
    def resolve_paths(cls, value: str | Path) -> Path:
        return _resolve_repo_path(value)


class SourceTractConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    tract: str = Field(min_length=1)
    annotations_path: Path

    @field_validator("annotations_path", mode="before")
    @classmethod
    def resolve_annotations_path(cls, value: str | Path) -> Path:
        return _resolve_repo_path(value)


class AnnotationFilterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed_review_statuses: list[str] = Field(min_length=1)
    allowed_support_types: list[str] = Field(min_length=1)
    required_edge_layer: str = Field(default="doctrinal", min_length=1)


class TaskTemplateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = True


class ConceptTemplateConfig(TaskTemplateConfig):
    max_supporting_passages: int = Field(default=3, ge=1)
    max_relations: int = Field(default=3, ge=1)
    allowed_subject_types: list[str] = Field(
        default_factory=lambda: list(DEFAULT_ALLOWED_SUBJECT_TYPES)
    )
    excluded_relation_types: list[str] = Field(default_factory=lambda: ["treated_in"])


class TemplateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    passage_grounded_doctrinal_qa: TaskTemplateConfig = Field(default_factory=TaskTemplateConfig)
    reviewed_relation_explanation: TaskTemplateConfig = Field(default_factory=TaskTemplateConfig)
    virtue_concept_explanation: ConceptTemplateConfig = Field(default_factory=ConceptTemplateConfig)
    citation_grounded_moral_answer: TaskTemplateConfig = Field(default_factory=TaskTemplateConfig)


class SplitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    group_by: Literal["question_id"] = "question_id"
    train_ratio: float = Field(gt=0, lt=1)
    val_ratio: float = Field(ge=0, lt=1)
    test_ratio: float = Field(ge=0, lt=1)
    seed: int = 17
    stratify_by_tract: bool = True
    min_eval_groups_per_tract: int = Field(default=1, ge=0)

    @model_validator(mode="after")
    def validate_ratio_sum(self) -> "SplitConfig":
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 1e-6:
            raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")
        return self


class OODSplitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="ood_test", min_length=1)
    held_out_tracts: list[str] = Field(default_factory=list)


class SerializationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    output_dir: Path
    sample_output_path: Path
    sample_size: int = Field(default=16, ge=1)

    @field_validator("output_dir", "sample_output_path", mode="before")
    @classmethod
    def resolve_output_paths(cls, value: str | Path) -> Path:
        return _resolve_repo_path(value)


class DatasetBuildConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dataset_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    system_prompt: str = Field(min_length=1)
    corpus: CorpusPathsConfig = Field(default_factory=CorpusPathsConfig)
    sources: list[SourceTractConfig] = Field(min_length=1)
    filters: AnnotationFilterConfig
    templates: TemplateConfig = Field(default_factory=TemplateConfig)
    splits: SplitConfig
    ood_split: OODSplitConfig = Field(default_factory=OODSplitConfig)
    serialization: SerializationConfig
    config_path: Path | None = None


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_name: str = Field(min_length=1)
    model_name_or_path: str = Field(min_length=1)
    dataset_dir: Path
    train_split: str = Field(default="train", min_length=1)
    eval_split: str = Field(default="val", min_length=1)
    output_dir: Path
    learning_rate: float = Field(default=2e-4, gt=0)
    num_train_epochs: float = Field(default=3.0, gt=0)
    max_seq_length: int = Field(default=2048, ge=128)
    max_train_examples: int | None = Field(default=None, ge=1)
    max_eval_examples: int | None = Field(default=None, ge=1)
    per_device_train_batch_size: int = Field(default=1, ge=1)
    per_device_eval_batch_size: int = Field(default=1, ge=1)
    gradient_accumulation_steps: int = Field(default=16, ge=1)
    warmup_ratio: float = Field(default=0.03, ge=0, lt=1)
    weight_decay: float = Field(default=0.0, ge=0)
    logging_steps: int = Field(default=10, ge=1)
    eval_steps: int = Field(default=100, ge=1)
    save_steps: int = Field(default=100, ge=1)
    save_total_limit: int = Field(default=2, ge=1)
    max_steps: int = Field(default=-1)
    seed: int = 17
    gradient_checkpointing: bool = True
    runtime_backend: RuntimeBackend = "auto"
    torch_dtype: TorchDtypeSetting = "auto"
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = Field(default="nf4", min_length=1)
    bnb_4bit_use_double_quant: bool = True
    lora_r: int = Field(default=32, ge=1)
    lora_alpha: int = Field(default=64, ge=1)
    lora_dropout: float = Field(default=0.05, ge=0, lt=1)
    lora_target_modules: list[str] | None = None
    report_to: list[str] = Field(default_factory=list)
    trust_remote_code: bool = False
    config_path: Path | None = None

    @field_validator("dataset_dir", "output_dir", mode="before")
    @classmethod
    def resolve_training_paths(cls, value: str | Path) -> Path:
        return _resolve_repo_path(value)


class InferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_name: str = Field(min_length=1)
    model_name_or_path: str = Field(min_length=1)
    dataset_dir: Path
    split_names: list[str] = Field(min_length=1)
    output_dir: Path
    adapter_path: Path | None = None
    trust_remote_code: bool = False
    runtime_backend: RuntimeBackend = "auto"
    torch_dtype: TorchDtypeSetting = "auto"
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = Field(default="nf4", min_length=1)
    bnb_4bit_use_double_quant: bool = True
    max_new_tokens: int = Field(default=256, ge=1)
    temperature: float = Field(default=0.0, ge=0)
    top_p: float = Field(default=1.0, gt=0, le=1)
    repetition_penalty: float = Field(default=1.0, gt=0)
    do_sample: bool = False
    seed: int = 17
    config_path: Path | None = None

    @field_validator("dataset_dir", "output_dir", "adapter_path", mode="before")
    @classmethod
    def resolve_inference_paths(cls, value: str | Path | None) -> Path | None:
        if value is None:
            return None
        return _resolve_repo_path(value)


def load_dataset_build_config(path: str | Path) -> DatasetBuildConfig:
    config_path = _resolve_repo_path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Dataset config must parse to an object: {config_path}")
    config = DatasetBuildConfig.model_validate(payload)
    return config.model_copy(update={"config_path": config_path})


def load_training_config(path: str | Path) -> TrainingConfig:
    config_path = _resolve_repo_path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Training config must parse to an object: {config_path}")
    config = TrainingConfig.model_validate(payload)
    return config.model_copy(update={"config_path": config_path})


def load_inference_config(path: str | Path) -> InferenceConfig:
    config_path = _resolve_repo_path(path)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Inference config must parse to an object: {config_path}")
    config = InferenceConfig.model_validate(payload)
    return config.model_copy(update={"config_path": config_path})
