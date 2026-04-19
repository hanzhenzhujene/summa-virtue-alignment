"""Assemble Christian virtue SFT examples, manifests, and benchmark exports."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .config import DatasetBuildConfig
from .filters import apply_annotation_filters
from .loaders import (
    CorpusContext,
    LoadedAnnotationRecord,
    load_corpus_context,
    load_doctrinal_annotation_sources,
)
from .splitters import SplitResult, assign_dataset_splits
from .templates import (
    render_citation_grounded_answer,
    render_citation_grounded_question,
    render_concept_explanation_answer,
    render_concept_explanation_user_prompt,
    render_passage_grounded_answer,
    render_passage_grounded_user_prompt,
    render_relation_explanation_answer,
    render_relation_explanation_user_prompt,
)
from .utils import dedupe_preserving_order, question_sort_key, segment_sort_key


class JoinedAnnotationRecord(LoadedAnnotationRecord):
    model_config = ConfigDict(extra="forbid", frozen=True)

    article_id: str = Field(min_length=1)
    article_number: int = Field(ge=1)
    article_title: str = Field(min_length=1)
    part_id: str = Field(min_length=1)
    question_id: str = Field(min_length=1)
    question_number: int = Field(ge=1)
    question_title: str = Field(min_length=1)
    source_passage_citation_label: str = Field(min_length=1)
    source_passage_source_url: str = Field(min_length=1)
    source_passage_text: str = Field(min_length=1)
    source_segment_type: str = Field(min_length=1)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class SFTExample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    example_id: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    split: str | None = None
    messages: list[ChatMessage] = Field(min_length=3)
    metadata: dict[str, Any]


class BenchmarkExample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    example_id: str = Field(min_length=1)
    task_type: str = Field(min_length=1)
    split: str = Field(min_length=1)
    messages: list[ChatMessage] = Field(min_length=2, max_length=2)
    metadata: dict[str, Any]


@dataclass(frozen=True)
class BuiltDataset:
    config: DatasetBuildConfig
    annotations: list[JoinedAnnotationRecord]
    examples: list[SFTExample]
    split_result: SplitResult
    manifest: dict[str, Any]


def _join_annotations_to_corpus(
    annotations: list[LoadedAnnotationRecord],
    corpus: CorpusContext,
) -> list[JoinedAnnotationRecord]:
    joined: list[JoinedAnnotationRecord] = []
    for annotation in annotations:
        segment = corpus.segments.get(annotation.source_passage_id)
        if segment is None:
            raise ValueError(f"Missing source passage for annotation {annotation.annotation_id}")
        article = corpus.articles.get(segment.article_id)
        if article is None:
            raise ValueError(f"Missing article metadata for annotation {annotation.annotation_id}")
        question = corpus.questions.get(segment.question_id)
        if question is None:
            raise ValueError(f"Missing question metadata for annotation {annotation.annotation_id}")
        joined.append(
            JoinedAnnotationRecord(
                **annotation.model_dump(),
                article_id=segment.article_id,
                article_number=segment.article_number,
                article_title=segment.article_title,
                part_id=segment.part_id,
                question_id=segment.question_id,
                question_number=segment.question_number,
                question_title=segment.question_title,
                source_passage_citation_label=segment.citation_label,
                source_passage_source_url=segment.source_url,
                source_passage_text=segment.text,
                source_segment_type=segment.segment_type,
            )
        )
    return sorted(
        joined,
        key=lambda row: (
            row.tract,
            question_sort_key(row.question_id),
            segment_sort_key(row.source_passage_id),
            row.annotation_id,
        ),
    )


def _build_metadata(annotation: JoinedAnnotationRecord, task_type: str) -> dict[str, Any]:
    return {
        "annotation_id": annotation.annotation_id,
        "annotation_ids": [annotation.annotation_id],
        "citation_label": annotation.source_passage_citation_label,
        "citation_labels": [annotation.source_passage_citation_label],
        "group_keys": {"question_id": annotation.question_id},
        "object_id": annotation.object_id,
        "object_label": annotation.object_label,
        "object_type": annotation.object_type,
        "part_id": annotation.part_id,
        "primary_question_id": annotation.question_id,
        "question_ids": [annotation.question_id],
        "question_title": annotation.question_title,
        "relation_type": annotation.relation_type,
        "source_file": annotation.source_file,
        "source_files": [annotation.source_file],
        "source_passage_id": annotation.source_passage_id,
        "source_passage_ids": [annotation.source_passage_id],
        "source_url": annotation.source_passage_source_url,
        "subject_id": annotation.subject_id,
        "subject_label": annotation.subject_label,
        "subject_type": annotation.subject_type,
        "support_type": annotation.support_type,
        "support_types": [annotation.support_type],
        "task_type": task_type,
        "tract": annotation.tract,
        "tract_display_label": annotation.tract_display_label,
    }


def _make_example(
    *,
    example_id: str,
    task_type: str,
    system_prompt: str,
    user_prompt: str,
    assistant_response: str,
    metadata: Mapping[str, Any],
) -> SFTExample:
    return SFTExample(
        example_id=example_id,
        task_type=task_type,
        messages=[
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
            ChatMessage(role="assistant", content=assistant_response),
        ],
        metadata=dict(metadata),
    )


def _build_annotation_examples(
    annotations: list[JoinedAnnotationRecord],
    config: DatasetBuildConfig,
) -> tuple[list[SFTExample], dict[str, int]]:
    examples: list[SFTExample] = []
    counts = Counter[str]()
    for annotation in annotations:
        if config.templates.passage_grounded_doctrinal_qa.enabled:
            task_type = "passage_grounded_doctrinal_qa"
            examples.append(
                _make_example(
                    example_id=f"{config.dataset_name}.{task_type}.{annotation.annotation_id}",
                    task_type=task_type,
                    system_prompt=config.system_prompt,
                    user_prompt=render_passage_grounded_user_prompt(
                        annotation,
                        f"{task_type}:{annotation.annotation_id}",
                    ),
                    assistant_response=render_passage_grounded_answer(annotation),
                    metadata=_build_metadata(annotation, task_type),
                )
            )
            counts[task_type] += 1
        if config.templates.reviewed_relation_explanation.enabled:
            task_type = "reviewed_relation_explanation"
            examples.append(
                _make_example(
                    example_id=f"{config.dataset_name}.{task_type}.{annotation.annotation_id}",
                    task_type=task_type,
                    system_prompt=config.system_prompt,
                    user_prompt=render_relation_explanation_user_prompt(
                        annotation,
                        f"{task_type}:{annotation.annotation_id}",
                    ),
                    assistant_response=render_relation_explanation_answer(annotation),
                    metadata=_build_metadata(annotation, task_type),
                )
            )
            counts[task_type] += 1
        if config.templates.citation_grounded_moral_answer.enabled:
            task_type = "citation_grounded_moral_answer"
            examples.append(
                _make_example(
                    example_id=f"{config.dataset_name}.{task_type}.{annotation.annotation_id}",
                    task_type=task_type,
                    system_prompt=config.system_prompt,
                    user_prompt=render_citation_grounded_question(
                        annotation,
                        f"{task_type}:{annotation.annotation_id}",
                    ),
                    assistant_response=render_citation_grounded_answer(annotation),
                    metadata=_build_metadata(annotation, task_type),
                )
            )
            counts[task_type] += 1
    return (examples, dict(sorted(counts.items())))


def _build_concept_examples(
    annotations: list[JoinedAnnotationRecord],
    config: DatasetBuildConfig,
) -> tuple[list[SFTExample], dict[str, int]]:
    concept_config = config.templates.virtue_concept_explanation
    if not concept_config.enabled:
        return ([], {})

    grouped: dict[tuple[str, str, str], list[JoinedAnnotationRecord]] = defaultdict(list)
    skipped = Counter[str]()
    for annotation in annotations:
        if annotation.subject_type not in concept_config.allowed_subject_types:
            skipped["disallowed_subject_type"] += 1
            continue
        grouped[(annotation.tract, annotation.question_id, annotation.subject_id)].append(
            annotation
        )

    examples: list[SFTExample] = []
    counts = Counter[str]()
    for (_, question_id, subject_id), records in grouped.items():
        ordered = sorted(
            records, key=lambda row: (segment_sort_key(row.source_passage_id), row.annotation_id)
        )
        substantive = [
            row
            for row in ordered
            if row.relation_type not in concept_config.excluded_relation_types
        ]
        if not substantive:
            skipped["no_substantive_relations"] += 1
            continue

        selected: list[JoinedAnnotationRecord] = []
        seen_passage_ids: list[str] = []
        seen_relation_pairs: set[tuple[str, str]] = set()
        for record in substantive:
            relation_pair = (record.relation_type, record.object_id)
            if relation_pair in seen_relation_pairs:
                continue
            if (
                len(dedupe_preserving_order(seen_passage_ids + [record.source_passage_id]))
                > concept_config.max_supporting_passages
            ):
                continue
            selected.append(record)
            seen_relation_pairs.add(relation_pair)
            seen_passage_ids.append(record.source_passage_id)
            if len(selected) >= concept_config.max_relations:
                break

        if not selected:
            skipped["empty_selected_relations"] += 1
            continue

        anchor = selected[0]
        task_type = "virtue_concept_explanation"
        example_id = f"{config.dataset_name}.{task_type}.{anchor.tract}.{question_id}.{subject_id}"
        metadata = {
            "annotation_ids": [record.annotation_id for record in selected],
            "citation_labels": [record.source_passage_citation_label for record in selected],
            "group_keys": {"question_id": anchor.question_id},
            "part_id": anchor.part_id,
            "primary_question_id": anchor.question_id,
            "question_ids": [anchor.question_id],
            "question_title": anchor.question_title,
            "relation_type": None,
            "relation_types": [record.relation_type for record in selected],
            "source_files": [record.source_file for record in selected],
            "source_passage_ids": [record.source_passage_id for record in selected],
            "subject_id": anchor.subject_id,
            "subject_label": anchor.subject_label,
            "subject_type": anchor.subject_type,
            "support_types": sorted({record.support_type for record in selected}),
            "task_type": task_type,
            "tract": anchor.tract,
            "tract_display_label": anchor.tract_display_label,
        }
        examples.append(
            _make_example(
                example_id=example_id,
                task_type=task_type,
                system_prompt=config.system_prompt,
                user_prompt=render_concept_explanation_user_prompt(
                    anchor.subject_label,
                    anchor.tract_display_label,
                    anchor.question_title,
                    selected,
                ),
                assistant_response=render_concept_explanation_answer(
                    anchor.subject_label, selected
                ),
                metadata=metadata,
            )
        )
        counts[task_type] += 1

    counts.update({f"skipped.{key}": value for key, value in skipped.items()})
    return (examples, dict(sorted(counts.items())))


def _build_manifest(
    config: DatasetBuildConfig,
    source_annotation_count: int,
    filtered_annotations: list[JoinedAnnotationRecord],
    filter_drops: Mapping[str, int],
    examples: list[SFTExample],
    annotation_task_counts: Mapping[str, int],
    concept_task_counts: Mapping[str, int],
    split_result: SplitResult,
) -> dict[str, Any]:
    annotation_counts_by_tract = Counter(annotation.tract for annotation in filtered_annotations)
    relation_counts = Counter(annotation.relation_type for annotation in filtered_annotations)
    support_counts = Counter(annotation.support_type for annotation in filtered_annotations)
    split_sizes = {name: len(rows) for name, rows in split_result.split_examples.items()}
    task_counts = Counter(example.task_type for example in examples)

    return {
        "config_path": str(config.config_path) if config.config_path is not None else None,
        "dataset_name": config.dataset_name,
        "description": config.description,
        "source_annotation_count": source_annotation_count,
        "source_annotations_used": len(filtered_annotations),
        "dropped_rows": dict(sorted(filter_drops.items())),
        "annotation_counts_by_tract": dict(sorted(annotation_counts_by_tract.items())),
        "annotation_counts_by_relation_type": dict(sorted(relation_counts.items())),
        "annotation_counts_by_support_type": dict(sorted(support_counts.items())),
        "task_template_counts": dict(sorted(task_counts.items())),
        "task_generation_details": {
            "annotation_tasks": dict(sorted(annotation_task_counts.items())),
            "concept_tasks": dict(sorted(concept_task_counts.items())),
        },
        "split_sizes": split_sizes,
        "split_question_group_counts": split_result.split_group_counts,
        "split_tract_counts": split_result.split_tract_counts,
        "ood_holdout_tracts": list(config.ood_split.held_out_tracts),
        "grouping_key": config.splits.group_by,
    }


def build_dataset(config: DatasetBuildConfig) -> BuiltDataset:
    corpus = load_corpus_context(config.corpus)
    loaded_annotations = load_doctrinal_annotation_sources(config.sources)
    filter_result = apply_annotation_filters(loaded_annotations, config.filters)
    joined_annotations = _join_annotations_to_corpus(filter_result.annotations, corpus)
    annotation_examples, annotation_task_counts = _build_annotation_examples(
        joined_annotations, config
    )
    concept_examples, concept_task_counts = _build_concept_examples(joined_annotations, config)
    examples = sorted(
        [*annotation_examples, *concept_examples],
        key=lambda row: (row.task_type, row.example_id),
    )
    split_result = assign_dataset_splits(examples, config.splits, config.ood_split)
    manifest = _build_manifest(
        config=config,
        source_annotation_count=len(loaded_annotations),
        filtered_annotations=joined_annotations,
        filter_drops=filter_result.dropped_counts,
        examples=examples,
        annotation_task_counts=annotation_task_counts,
        concept_task_counts=concept_task_counts,
        split_result=split_result,
    )
    return BuiltDataset(
        config=config,
        annotations=joined_annotations,
        examples=examples,
        split_result=split_result,
        manifest=manifest,
    )
