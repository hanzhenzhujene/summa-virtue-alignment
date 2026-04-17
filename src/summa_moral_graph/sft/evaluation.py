from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .utils import extract_passage_ids


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _extract_reference_assistant_text(row: dict[str, Any]) -> str:
    messages = row.get("messages", [])
    for message in reversed(messages):
        if message.get("role") == "assistant":
            return str(message.get("content", ""))
    raise ValueError(f"Reference row {row.get('example_id')} is missing an assistant message")


def load_reference_examples(dataset_dir: Path) -> dict[str, dict[str, Any]]:
    path = dataset_dir / "all.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"Reference dataset not found: {path}")
    rows = _load_jsonl(path)
    return {str(row["example_id"]): row for row in rows}


def load_prediction_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows = _load_jsonl(path)
    return {str(row["example_id"]): row for row in rows}


def _extract_prediction_text(row: dict[str, Any]) -> str:
    if "assistant_text" in row:
        return str(row["assistant_text"])
    if "prediction" in row:
        return str(row["prediction"])
    if "messages" in row:
        return _extract_reference_assistant_text(row)
    raise ValueError(
        f"Prediction row {row.get('example_id')} does not expose assistant_text or messages"
    )


def _extract_predicted_relation_type(
    row: dict[str, Any], *, allow_metadata_fallback: bool
) -> str | None:
    if isinstance(row.get("predicted_relation_type"), str):
        return str(row["predicted_relation_type"])
    if allow_metadata_fallback:
        metadata = row.get("metadata")
        if isinstance(metadata, dict) and isinstance(metadata.get("relation_type"), str):
            return str(metadata["relation_type"])
    return None


def _metric_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(records)
    if not rows:
        return {
            "count": 0,
            "citation_exact_match": 0.0,
            "citation_partial_match": 0.0,
            "citation_overlap": 0.0,
            "relation_type_accuracy": None,
        }
    citation_exact = sum(1 for row in rows if row["citation_exact"])
    citation_partial = sum(1 for row in rows if row["citation_partial"])
    citation_overlap = sum(row["citation_overlap"] for row in rows)
    relation_rows = [row for row in rows if row["relation_type_correct"] is not None]
    relation_correct = sum(1 for row in relation_rows if row["relation_type_correct"])
    return {
        "count": len(rows),
        "citation_exact_match": citation_exact / len(rows),
        "citation_partial_match": citation_partial / len(rows),
        "citation_overlap": citation_overlap / len(rows),
        "relation_type_accuracy": (
            relation_correct / len(relation_rows) if relation_rows else None
        ),
    }


def evaluate_predictions(
    dataset_dir: Path,
    predictions_path: Path | None = None,
    reference_splits: list[str] | None = None,
) -> dict[str, Any]:
    references = load_reference_examples(dataset_dir)
    predictions = (
        load_prediction_rows(predictions_path) if predictions_path is not None else references
    )
    active_splits = reference_splits
    if active_splits is None and predictions_path is not None:
        predicted_split_names = sorted(
            {
                str(row["split"])
                for row in predictions.values()
                if isinstance(row.get("split"), str) and str(row.get("split"))
            }
        )
        if predicted_split_names:
            active_splits = predicted_split_names
    if active_splits is not None:
        active_split_set = set(active_splits)
        references = {
            example_id: row
            for example_id, row in references.items()
            if str(row.get("split")) in active_split_set
        }

    rows: list[dict[str, Any]] = []
    missing_predictions: list[str] = []
    for example_id, reference in references.items():
        prediction = predictions.get(example_id)
        if prediction is None:
            missing_predictions.append(example_id)
            continue
        reference_text = _extract_reference_assistant_text(reference)
        prediction_text = _extract_prediction_text(prediction)
        reference_ids = set(reference.get("metadata", {}).get("source_passage_ids", []))
        predicted_ids = set(extract_passage_ids(prediction_text))
        relation_type = reference.get("metadata", {}).get("relation_type")
        predicted_relation_type = _extract_predicted_relation_type(
            prediction,
            allow_metadata_fallback=predictions_path is None,
        )
        relation_type_correct: bool | None
        if isinstance(relation_type, str) and predicted_relation_type is not None:
            relation_type_correct = relation_type == predicted_relation_type
        else:
            relation_type_correct = None
        rows.append(
            {
                "example_id": example_id,
                "task_type": reference.get("task_type"),
                "tract": reference.get("metadata", {}).get("tract"),
                "support_types": reference.get("metadata", {}).get("support_types", []),
                "citation_exact": bool(reference_ids) and predicted_ids == reference_ids,
                "citation_partial": bool(reference_ids & predicted_ids),
                "citation_overlap": (
                    len(reference_ids & predicted_ids) / len(reference_ids)
                    if reference_ids
                    else 0.0
                ),
                "relation_type_correct": relation_type_correct,
                "reference_text": reference_text,
                "prediction_text": prediction_text,
            }
        )

    tract_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    support_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    task_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        tract_buckets[str(row["tract"])].append(row)
        task_buckets[str(row["task_type"])].append(row)
        for support_type in row["support_types"]:
            support_buckets[str(support_type)].append(row)

    qualitative_samples = sorted(
        rows,
        key=lambda row: (str(row["task_type"]), str(row["tract"]), str(row["example_id"])),
    )[:10]
    return {
        "overall": _metric_summary(rows),
        "evaluated_splits": active_splits,
        "by_tract": {key: _metric_summary(value) for key, value in sorted(tract_buckets.items())},
        "by_support_type": {
            key: _metric_summary(value) for key, value in sorted(support_buckets.items())
        },
        "by_task_type": {
            key: _metric_summary(value) for key, value in sorted(task_buckets.items())
        },
        "missing_prediction_count": len(missing_predictions),
        "missing_prediction_ids": missing_predictions[:25],
        "qualitative_samples": qualitative_samples,
    }


def write_markdown_report(metrics: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Christian Virtue SFT Evaluation",
        "",
        "## Overall",
        "",
        f"- Count: {metrics['overall']['count']}",
        f"- Citation exact match: {metrics['overall']['citation_exact_match']:.3f}",
        f"- Citation partial match: {metrics['overall']['citation_partial_match']:.3f}",
        f"- Citation overlap: {metrics['overall']['citation_overlap']:.3f}",
        f"- Relation type accuracy: {metrics['overall']['relation_type_accuracy']}",
        "",
        "## By Tract",
        "",
    ]
    for tract, summary in metrics["by_tract"].items():
        lines.append(
            f"- {tract}: exact={summary['citation_exact_match']:.3f}, "
            f"partial={summary['citation_partial_match']:.3f}, "
            f"overlap={summary['citation_overlap']:.3f}, "
            f"relation={summary['relation_type_accuracy']}"
        )
    lines.extend(["", "## By Support Type", ""])
    for support_type, summary in metrics["by_support_type"].items():
        lines.append(
            f"- {support_type}: exact={summary['citation_exact_match']:.3f}, "
            f"partial={summary['citation_partial_match']:.3f}, "
            f"overlap={summary['citation_overlap']:.3f}, "
            f"relation={summary['relation_type_accuracy']}"
        )
    lines.extend(["", "## Qualitative Sample", ""])
    for sample in metrics["qualitative_samples"]:
        lines.extend(
            [
                f"### {sample['example_id']}",
                "",
                f"- Task type: {sample['task_type']}",
                f"- Tract: {sample['tract']}",
                f"- Citation exact: {sample['citation_exact']}",
                f"- Citation partial: {sample['citation_partial']}",
                "",
                "Reference:",
                "",
                sample["reference_text"],
                "",
                "Prediction:",
                "",
                sample["prediction_text"],
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")
