"""Filter reviewed doctrinal annotations into the default SFT supervision set."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .config import AnnotationFilterConfig
from .loaders import LoadedAnnotationRecord


@dataclass(frozen=True)
class AnnotationFilterResult:
    annotations: list[LoadedAnnotationRecord]
    dropped_counts: dict[str, int]


def apply_annotation_filters(
    annotations: list[LoadedAnnotationRecord],
    config: AnnotationFilterConfig,
) -> AnnotationFilterResult:
    kept: list[LoadedAnnotationRecord] = []
    dropped = Counter[str]()
    seen_annotation_ids: set[str] = set()

    for annotation in annotations:
        if annotation.edge_layer != config.required_edge_layer:
            dropped["wrong_edge_layer"] += 1
            continue
        if annotation.review_status not in config.allowed_review_statuses:
            dropped["review_status_filtered"] += 1
            continue
        if annotation.support_type not in config.allowed_support_types:
            dropped["support_type_filtered"] += 1
            continue
        if annotation.annotation_id in seen_annotation_ids:
            dropped["duplicate_annotation_id"] += 1
            continue
        seen_annotation_ids.add(annotation.annotation_id)
        kept.append(annotation)

    return AnnotationFilterResult(annotations=kept, dropped_counts=dict(sorted(dropped.items())))
