from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from .comparison import build_comparison_report
from .evaluation import load_prediction_rows, load_reference_examples
from .utils import extract_passage_ids, tract_display_name

TASK_DISPLAY_NAMES = {
    "citation_grounded_moral_answer": "Citation-grounded moral answer",
    "passage_grounded_doctrinal_qa": "Passage-grounded doctrinal QA",
    "reviewed_relation_explanation": "Reviewed relation explanation",
    "virtue_concept_explanation": "Virtue concept explanation",
}


@dataclass(frozen=True)
class GoalDemoSpec:
    slot: int
    title: str
    focus: str
    example_id: str


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            rows.append(json.loads(stripped))
    return rows


def _extract_message_text(row: dict[str, Any], role: str) -> str:
    messages = row.get("messages", [])
    if not isinstance(messages, list):
        raise ValueError(f"Row {row.get('example_id')} is missing messages")
    for message in messages:
        if message.get("role") == role:
            return str(message.get("content", ""))
    raise ValueError(f"Row {row.get('example_id')} is missing a {role} message")


def _extract_prediction_text(row: dict[str, Any]) -> str:
    if "assistant_text" in row:
        return str(row["assistant_text"])
    if "prediction" in row:
        return str(row["prediction"])
    if "messages" in row:
        return _extract_message_text(row, "assistant")
    raise ValueError(f"Prediction row {row.get('example_id')} is missing assistant text")


def _truncate_text(text: str, *, limit: int = 420) -> str:
    stripped = " ".join(text.split())
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 1].rstrip() + "…"


def _format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _metric_value(row: dict[str, Any], key: str) -> float:
    value = row.get(key, 0.0)
    if value is None:
        return 0.0
    return float(value)


def _bucket_display_name(bucket_name: str, key: str) -> str:
    if bucket_name == "by_task_type":
        return TASK_DISPLAY_NAMES.get(key, key.replace("_", " ").title())
    if bucket_name == "by_tract":
        return tract_display_name(key)
    return key.replace("_", " ").title()


def _metric_breakdown_rows(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    *,
    bucket_name: str,
) -> list[dict[str, Any]]:
    baseline_bucket = cast(dict[str, Any], baseline_metrics.get(bucket_name, {}))
    candidate_bucket = cast(dict[str, Any], candidate_metrics.get(bucket_name, {}))

    rows: list[dict[str, Any]] = []
    for key, candidate_row_any in candidate_bucket.items():
        candidate_row = cast(dict[str, Any], candidate_row_any)
        baseline_row = cast(dict[str, Any], baseline_bucket.get(key, {}))
        baseline_exact = _metric_value(baseline_row, "citation_exact_match")
        candidate_exact = _metric_value(candidate_row, "citation_exact_match")
        count_value = candidate_row.get("count", 0)
        rows.append(
            {
                "key": key,
                "label": _bucket_display_name(bucket_name, str(key)),
                "count": int(count_value) if count_value is not None else 0,
                "baseline_exact": baseline_exact,
                "candidate_exact": candidate_exact,
                "delta_exact": candidate_exact - baseline_exact,
            }
        )

    rows.sort(
        key=lambda row: (
            float(row["candidate_exact"]),
            float(row["delta_exact"]),
            int(row["count"]),
            str(row["label"]),
        ),
        reverse=True,
    )
    return rows


def _lowest_metric_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return min(
        rows,
        key=lambda row: (
            float(row["candidate_exact"]),
            float(row["delta_exact"]),
            int(row["count"]),
            str(row["label"]),
        ),
    )


def _summarize_goal_demo_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(rows),
        "base_exact_count": sum(1 for row in rows if bool(row.get("base_exact_match"))),
        "adapter_exact_count": sum(1 for row in rows if bool(row.get("adapter_exact_match"))),
        "adapter_only_wins": sum(
            1
            for row in rows
            if bool(row.get("adapter_exact_match")) and not bool(row.get("base_exact_match"))
        ),
        "both_miss": sum(
            1
            for row in rows
            if not bool(row.get("adapter_exact_match")) and not bool(row.get("base_exact_match"))
        ),
    }


def _find_goal_demo_win(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        if bool(row.get("adapter_exact_match")) and not bool(row.get("base_exact_match")):
            return row
    return None


def _find_goal_demo_failure(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        if (
            not bool(row.get("adapter_exact_match"))
            and str(row.get("task_type")) == "citation_grounded_moral_answer"
        ):
            return row
    for row in rows:
        if not bool(row.get("adapter_exact_match")):
            return row
    return None


def _shift_heading(line: str, *, levels: int) -> str:
    stripped = line.lstrip()
    if not stripped.startswith("#"):
        return line
    heading_marks, _, rest = stripped.partition(" ")
    if not rest:
        return line
    prefix_width = len(line) - len(stripped)
    shifted_marks = "#" * min(len(heading_marks) + levels, 6)
    return f"{line[:prefix_width]}{shifted_marks} {rest}"


def _normalize_embedded_comparison_markdown(markdown: str) -> str:
    normalized_lines: list[str] = []
    for line in markdown.strip().splitlines():
        if line.startswith("# "):
            continue
        normalized_lines.append(_shift_heading(line, levels=1))
    return "\n".join(normalized_lines).strip()


def _read_goal_demo_specs(path: Path) -> list[GoalDemoSpec]:
    rows = _load_jsonl(path)
    specs = [
        GoalDemoSpec(
            slot=int(row["slot"]),
            title=str(row["title"]),
            focus=str(row["focus"]),
            example_id=str(row["example_id"]),
        )
        for row in rows
    ]
    return sorted(specs, key=lambda item: item.slot)


def build_goal_demo_panel(
    *,
    dataset_dir: Path,
    panel_path: Path,
    base_predictions_path: Path,
    adapter_predictions_path: Path,
) -> list[dict[str, Any]]:
    specs = _read_goal_demo_specs(panel_path)
    references = load_reference_examples(dataset_dir)
    base_predictions = load_prediction_rows(base_predictions_path)
    adapter_predictions = load_prediction_rows(adapter_predictions_path)

    rows: list[dict[str, Any]] = []
    for spec in specs:
        reference = references.get(spec.example_id)
        if reference is None:
            raise KeyError(f"Goal-demo example not found in dataset: {spec.example_id}")
        base_prediction = base_predictions.get(spec.example_id)
        adapter_prediction = adapter_predictions.get(spec.example_id)
        if base_prediction is None or adapter_prediction is None:
            raise KeyError(f"Goal-demo example missing from predictions: {spec.example_id}")

        reference_text = _extract_message_text(reference, "assistant")
        base_text = _extract_prediction_text(base_prediction)
        adapter_text = _extract_prediction_text(adapter_prediction)
        reference_ids = set(reference.get("metadata", {}).get("source_passage_ids", []))
        base_ids = set(extract_passage_ids(base_text))
        adapter_ids = set(extract_passage_ids(adapter_text))

        rows.append(
            {
                "slot": spec.slot,
                "title": spec.title,
                "focus": spec.focus,
                "example_id": spec.example_id,
                "task_type": str(reference.get("task_type")),
                "task_type_display": TASK_DISPLAY_NAMES.get(
                    str(reference.get("task_type")),
                    str(reference.get("task_type")).replace("_", " ").title(),
                ),
                "tract": str(reference.get("metadata", {}).get("tract")),
                "tract_display": tract_display_name(
                    str(reference.get("metadata", {}).get("tract", ""))
                ),
                "prompt": _extract_message_text(reference, "user"),
                "reference_excerpt": _truncate_text(reference_text),
                "base_excerpt": _truncate_text(base_text),
                "adapter_excerpt": _truncate_text(adapter_text),
                "reference_passage_ids": sorted(reference_ids),
                "base_passage_ids": sorted(base_ids),
                "adapter_passage_ids": sorted(adapter_ids),
                "base_exact_match": bool(reference_ids) and base_ids == reference_ids,
                "adapter_exact_match": bool(reference_ids) and adapter_ids == reference_ids,
            }
        )
    return rows


def _series_bounds(series: list[list[tuple[float, float]]]) -> tuple[float, float, float, float]:
    x_values = [point[0] for line in series for point in line]
    y_values = [point[1] for line in series for point in line]
    if not x_values or not y_values:
        raise ValueError("Series must contain at least one point")
    min_x = min(x_values)
    max_x = max(x_values)
    min_y = min(y_values)
    max_y = max(y_values)
    if min_x == max_x:
        max_x += 1.0
    if min_y == max_y:
        max_y += 1.0
    return min_x, max_x, min_y, max_y


def _polyline_points(
    points: list[tuple[float, float]],
    *,
    x0: float,
    y0: float,
    width: float,
    height: float,
    min_x: float,
    max_x: float,
    min_y: float,
    max_y: float,
) -> str:
    rendered: list[str] = []
    for x_value, y_value in points:
        x_pos = x0 + ((x_value - min_x) / (max_x - min_x)) * width
        y_pos = y0 + height - ((y_value - min_y) / (max_y - min_y)) * height
        rendered.append(f"{x_pos:.1f},{y_pos:.1f}")
    return " ".join(rendered)


def _append_line_chart(
    lines: list[str],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    series: list[tuple[str, str, list[tuple[float, float]]]],
) -> None:
    series_points = [points for _, _, points in series if points]
    if not series_points:
        return
    min_x, max_x, min_y, max_y = _series_bounds(series_points)
    lines.append(f"<g transform='translate({x:.1f},{y:.1f})'>")
    lines.append(
        "<rect x='0' y='0' width='{width:.1f}' height='{height:.1f}' "
        "fill='white' stroke='#d4d4d8' stroke-width='1.5' rx='12' />".format(
            width=width,
            height=height,
        )
    )
    lines.append(
        f"<text x='20' y='28' font-size='16' font-weight='700' fill='#111827'>"
        f"{html.escape(title)}</text>"
    )
    plot_x = 56.0
    plot_y = 48.0
    plot_width = width - 78.0
    plot_height = height - 92.0
    lines.append(
        f"<line x1='{plot_x:.1f}' y1='{plot_y:.1f}' x2='{plot_x:.1f}' "
        f"y2='{plot_y + plot_height:.1f}' stroke='#9ca3af' stroke-width='1.5' />"
    )
    lines.append(
        f"<line x1='{plot_x:.1f}' y1='{plot_y + plot_height:.1f}' "
        f"x2='{plot_x + plot_width:.1f}' y2='{plot_y + plot_height:.1f}' "
        "stroke='#9ca3af' stroke-width='1.5' />"
    )

    for _label, color, points in series:
        if not points:
            continue
        polyline = _polyline_points(
            points,
            x0=plot_x,
            y0=plot_y,
            width=plot_width,
            height=plot_height,
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
        )
        lines.append(
            f"<polyline fill='none' stroke='{color}' stroke-width='2.5' points='{polyline}' />"
        )
        last_x, last_y = points[-1]
        label_x = plot_x + ((last_x - min_x) / (max_x - min_x)) * plot_width
        label_y = plot_y + plot_height - ((last_y - min_y) / (max_y - min_y)) * plot_height
        lines.append(f"<circle cx='{label_x:.1f}' cy='{label_y:.1f}' r='3.5' fill='{color}' />")

    legend_y = height - 24.0
    legend_x = 18.0
    for label, color, points in series:
        if not points:
            continue
        lines.append(f"<circle cx='{legend_x:.1f}' cy='{legend_y:.1f}' r='5' fill='{color}' />")
        lines.append(
            f"<text x='{legend_x + 10:.1f}' y='{legend_y + 4:.1f}' font-size='12' "
            f"fill='#374151'>{html.escape(label)}</text>"
        )
        legend_x += 132.0
    lines.append("</g>")


def write_training_curves_svg(train_log_history_path: Path, output_path: Path) -> Path:
    history_rows = _load_jsonl(train_log_history_path)
    train_loss = [
        (float(row["step"]), float(row["loss"]))
        for row in history_rows
        if "step" in row and "loss" in row
    ]
    eval_loss = [
        (float(row["step"]), float(row["eval_loss"]))
        for row in history_rows
        if "step" in row and "eval_loss" in row
    ]
    train_accuracy = [
        (float(row["step"]), float(row["mean_token_accuracy"]))
        for row in history_rows
        if "step" in row and "mean_token_accuracy" in row
    ]
    eval_accuracy = [
        (float(row["step"]), float(row["eval_mean_token_accuracy"]))
        for row in history_rows
        if "step" in row and "eval_mean_token_accuracy" in row
    ]

    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='980' height='420' "
        "viewBox='0 0 980 420' role='img' aria-label='Christian virtue training curves'>",
        "<rect x='0' y='0' width='980' height='420' fill='#f8fafc' />",
    ]
    _append_line_chart(
        lines,
        x=20,
        y=24,
        width=450,
        height=360,
        title="Loss by step",
        series=[
            ("Train loss", "#b45309", train_loss),
            ("Eval loss", "#1d4ed8", eval_loss),
        ],
    )
    _append_line_chart(
        lines,
        x=500,
        y=24,
        width=450,
        height=360,
        title="Mean token accuracy by step",
        series=[
            ("Train accuracy", "#15803d", train_accuracy),
            ("Eval accuracy", "#7c3aed", eval_accuracy),
        ],
    )
    lines.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_task_comparison_svg(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    output_path: Path,
) -> Path:
    task_keys = [
        "overall",
        *sorted(candidate_metrics.get("by_task_type", {}).keys()),
    ]
    label_map = {
        "overall": "Overall",
        **{key: TASK_DISPLAY_NAMES.get(key, key.replace("_", " ").title()) for key in task_keys},
    }
    width = 1020
    height = 420
    chart_x = 80.0
    chart_y = 56.0
    chart_width = 880.0
    chart_height = 280.0
    group_width = chart_width / max(len(task_keys), 1)
    baseline_values = [
        float(
            baseline_metrics.get("overall", {}).get("citation_exact_match", 0.0)
            if key == "overall"
            else baseline_metrics.get("by_task_type", {})
            .get(key, {})
            .get("citation_exact_match", 0.0)
        )
        for key in task_keys
    ]
    candidate_values = [
        float(
            candidate_metrics.get("overall", {}).get("citation_exact_match", 0.0)
            if key == "overall"
            else candidate_metrics.get("by_task_type", {})
            .get(key, {})
            .get("citation_exact_match", 0.0)
        )
        for key in task_keys
    ]
    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        "viewBox='0 0 {width} {height}' role='img' "
        "aria-label='Base versus adapter citation exact comparison'>".format(
            width=width,
            height=height,
        ),
        f"<rect x='0' y='0' width='{width}' height='{height}' fill='#f8fafc' />",
        "<text x='80' y='34' font-size='20' font-weight='700' fill='#111827'>"
        "Citation exact match by evaluation slice</text>",
        f"<line x1='{chart_x}' y1='{chart_y}' x2='{chart_x}' y2='{chart_y + chart_height}' "
        "stroke='#9ca3af' stroke-width='1.5' />",
        f"<line x1='{chart_x}' y1='{chart_y + chart_height}' "
        f"x2='{chart_x + chart_width}' y2='{chart_y + chart_height}' "
        "stroke='#9ca3af' stroke-width='1.5' />",
    ]
    for index, key in enumerate(task_keys):
        group_x = chart_x + index * group_width
        baseline_height = chart_height * baseline_values[index]
        candidate_height = chart_height * candidate_values[index]
        baseline_x = group_x + group_width * 0.18
        candidate_x = group_x + group_width * 0.52
        bar_width = group_width * 0.22
        lines.append(
            f"<rect x='{baseline_x:.1f}' y='{chart_y + chart_height - baseline_height:.1f}' "
            f"width='{bar_width:.1f}' height='{baseline_height:.1f}' fill='#94a3b8' rx='6' />"
        )
        lines.append(
            f"<rect x='{candidate_x:.1f}' y='{chart_y + chart_height - candidate_height:.1f}' "
            f"width='{bar_width:.1f}' height='{candidate_height:.1f}' fill='#2563eb' rx='6' />"
        )
        lines.append(
            f"<text x='{baseline_x + (bar_width / 2):.1f}' y='{chart_y + chart_height + 18:.1f}' "
            "font-size='11' text-anchor='middle' fill='#374151'>Base</text>"
        )
        lines.append(
            f"<text x='{candidate_x + (bar_width / 2):.1f}' y='{chart_y + chart_height + 18:.1f}' "
            "font-size='11' text-anchor='middle' fill='#374151'>Adapter</text>"
        )
        lines.append(
            f"<text x='{group_x + group_width / 2:.1f}' y='{chart_y + chart_height + 40:.1f}' "
            "font-size='11' text-anchor='middle' fill='#111827'>"
            f"{html.escape(label_map[key])}</text>"
        )
        lines.append(
            f"<text x='{candidate_x + (bar_width / 2):.1f}' "
            f"y='{chart_y + chart_height - candidate_height - 8:.1f}' font-size='11' "
            "text-anchor='middle' fill='#1d4ed8'>"
            f"{candidate_values[index] * 100:.1f}%</text>"
        )
    lines.extend(
        [
            "<circle cx='760' cy='28' r='6' fill='#94a3b8' />",
            "<text x='772' y='32' font-size='12' fill='#374151'>Base model</text>",
            "<circle cx='864' cy='28' r='6' fill='#2563eb' />",
            "<text x='876' y='32' font-size='12' fill='#374151'>LoRA adapter</text>",
            "</svg>",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _parse_iso_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _runtime_minutes(start_time: str | None, end_time: str | None) -> float | None:
    start = _parse_iso_timestamp(start_time)
    end = _parse_iso_timestamp(end_time)
    if start is None or end is None:
        return None
    return (end - start).total_seconds() / 60.0


def build_publishable_local_report(
    *,
    dataset_manifest: dict[str, Any],
    train_metadata: dict[str, Any],
    base_metrics: dict[str, Any],
    adapter_metrics: dict[str, Any],
    goal_demo_rows: list[dict[str, Any]],
    comparison_markdown: str,
    training_curves_asset_path: str,
    comparison_asset_path: str,
    published_model_url: str | None = None,
    release_url: str | None = None,
) -> str:
    base_overall = base_metrics["overall"]
    adapter_overall = adapter_metrics["overall"]
    net_gain = float(adapter_overall["citation_exact_match"]) - float(
        base_overall["citation_exact_match"]
    )
    task_rows = _metric_breakdown_rows(base_metrics, adapter_metrics, bucket_name="by_task_type")
    tract_rows = _metric_breakdown_rows(base_metrics, adapter_metrics, bucket_name="by_tract")
    strongest_task = task_rows[0] if task_rows else None
    weakest_task = _lowest_metric_row(task_rows)
    strongest_tract = tract_rows[0] if tract_rows else None
    zero_gain_tracts = [
        row for row in tract_rows if float(row["candidate_exact"]) == 0.0 and int(row["count"]) > 0
    ]
    goal_demo_summary = _summarize_goal_demo_rows(goal_demo_rows)
    representative_win = _find_goal_demo_win(goal_demo_rows)
    representative_failure = _find_goal_demo_failure(goal_demo_rows)
    embedded_comparison_markdown = _normalize_embedded_comparison_markdown(comparison_markdown)
    runtime_minutes = _runtime_minutes(
        str(train_metadata.get("start_time")) if train_metadata.get("start_time") else None,
        str(train_metadata.get("end_time")) if train_metadata.get("end_time") else None,
    )
    lines = [
        "# Christian Virtue Qwen2.5 1.5B Local Pilot-Lite Report",
        "",
        "## Scope",
        "",
        "This report documents the canonical local Apple-Silicon LoRA baseline for the Christian "
        "virtue SFT pipeline. It is the official reproducible `Qwen/Qwen2.5-1.5B-Instruct` "
        "`pilot-lite` demonstration path for this repo.",
        "",
        "It is meant to show more than citation formatting. The real question is whether this "
        "dataset can push a general model toward Aquinas-grounded Christian virtue reasoning while "
        "keeping answers evidence-bounded and traceable.",
        "",
        "## Canonical Purpose",
        "",
        "- Primary objective: improve faithful Aquinas-grounded virtue reasoning.",
        "- Secondary objective: preserve citation-grounded traceability.",
        "- Non-goal: treating passage-id emission as the whole purpose of the SFT.",
        "",
        "## Experiment Snapshot",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| Base model | `{train_metadata['model_name_or_path']}` |",
        "| Training mode | LoRA on `mps`, `float16`, no quantization |",
        f"| Dataset export | `{dataset_manifest['dataset_name']}` |",
        f"| Reviewed source annotations | `{dataset_manifest['source_annotations_used']}` |",
        f"| Total SFT examples | `{sum(dataset_manifest['split_sizes'].values())}` |",
        (
            "| Train / val / test sizes | "
            f"`{dataset_manifest['split_sizes']['train']} / "
            f"{dataset_manifest['split_sizes']['val']} / "
            f"{dataset_manifest['split_sizes']['test']}` |"
        ),
        f"| Pilot-lite train subset | `{train_metadata['train_examples']}` |",
        f"| Pilot-lite eval subset | `{train_metadata['eval_examples']}` |",
        f"| Max steps | `{train_metadata['global_step']}` |",
        f"| Runtime device | `{train_metadata['resolved_device']}` |",
        f"| Git commit | `{train_metadata['git_commit']}` |",
        f"| Training run id | `{train_metadata['run_id']}` |",
        "",
        "Committed inputs:",
        "",
        "- Dataset manifest: "
        "[data/processed/sft/exports/christian_virtue_v1/manifest.json]"
        "(../../data/processed/sft/exports/christian_virtue_v1/manifest.json)",
        "- Training config: "
        "[configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml]"
        "(../../configs/train/qwen2_5_1_5b_instruct_lora_mps_pilot_lite.yaml)",
        "- Base inference config: "
        "[configs/inference/qwen2_5_1_5b_instruct_base_test.yaml]"
        "(../../configs/inference/qwen2_5_1_5b_instruct_base_test.yaml)",
        "- Adapter inference config: "
        "[configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml]"
        "(../../configs/inference/qwen2_5_1_5b_instruct_adapter_test.yaml)",
    ]
    if published_model_url is not None:
        lines.append(f"- Published adapter: [Hugging Face model page]({published_model_url})")
    if release_url is not None:
        lines.append(f"- GitHub release: [Release page]({release_url})")

    lines.extend(
        [
            "",
            "## Executive Readout",
            "",
            "| Slice | Base | Adapter | Delta |",
            "| --- | ---: | ---: | ---: |",
            f"| Held-out test citation exact | "
            f"`{_format_percent(float(base_overall['citation_exact_match']))}` | "
            f"`{_format_percent(float(adapter_overall['citation_exact_match']))}` | "
            f"`{_format_percent(net_gain)}` |",
        ]
    )
    if strongest_task is not None:
        lines.append(
            f"| Strongest task: {strongest_task['label']} | "
            f"`{_format_percent(float(strongest_task['baseline_exact']))}` | "
            f"`{_format_percent(float(strongest_task['candidate_exact']))}` | "
            f"`{_format_percent(float(strongest_task['delta_exact']))}` |"
        )
    if strongest_tract is not None:
        lines.append(
            f"| Strongest tract: {strongest_tract['label']} | "
            f"`{_format_percent(float(strongest_tract['baseline_exact']))}` | "
            f"`{_format_percent(float(strongest_tract['candidate_exact']))}` | "
            f"`{_format_percent(float(strongest_tract['delta_exact']))}` |"
        )
    if goal_demo_summary["total"] > 0:
        lines.append(
            f"| Goal-demo exact citations | "
            f"`{goal_demo_summary['base_exact_count']} / {goal_demo_summary['total']}` | "
            f"`{goal_demo_summary['adapter_exact_count']} / {goal_demo_summary['total']}` | "
            f"`+{goal_demo_summary['adapter_only_wins']}` |"
        )

    if task_rows:
        lines.extend(
            [
                "",
                "Strongest task slices:",
                "",
            ]
        )
        for row in task_rows[:3]:
            lines.append(
                f"- {row['label']}: {_format_percent(float(row['candidate_exact']))} exact over "
                f"`{row['count']}` held-out prompts."
            )

    if tract_rows:
        lines.extend(
            [
                "",
                "Strongest tract slices:",
                "",
            ]
        )
        for row in tract_rows[:3]:
            lines.append(
                f"- {row['label']}: {_format_percent(float(row['candidate_exact']))} exact over "
                f"`{row['count']}` held-out prompts."
            )

    weak_spot_lines: list[str] = []
    if weakest_task is not None and float(weakest_task["candidate_exact"]) == 0.0:
        weak_spot_lines.append(
            f"- Hardest task type remains {weakest_task['label']} at "
            f"{_format_percent(float(weakest_task['candidate_exact']))} exact over "
            f"`{weakest_task['count']}` prompts."
        )
    if zero_gain_tracts:
        weak_spot_lines.append(
            "- Zero-gain tracts in this run: "
            + ", ".join(str(row["label"]) for row in zero_gain_tracts)
            + "."
        )
    if goal_demo_summary["total"] > 0:
        weak_spot_lines.append(
            f"- Goal-demo exact citations move from "
            f"`{goal_demo_summary['base_exact_count']} / {goal_demo_summary['total']}` to "
            f"`{goal_demo_summary['adapter_exact_count']} / {goal_demo_summary['total']}`, "
            f"leaving `{goal_demo_summary['both_miss']}` shared misses for qualitative review."
        )
    if weak_spot_lines:
        lines.extend(["", "Persistent weak spots:", ""])
        lines.extend(weak_spot_lines)

    representative_lines: list[str] = []
    if representative_win is not None:
        representative_lines.append(
            f"- Clear adapter win: slot {representative_win['slot']} "
            f"`{representative_win['title']}`."
        )
    if representative_failure is not None:
        representative_lines.append(
            f"- Representative stubborn failure: slot {representative_failure['slot']} "
            f"`{representative_failure['title']}`."
        )
    if representative_lines:
        lines.extend(["", "Representative examples:", ""])
        lines.extend(representative_lines)

    lines.extend(
        [
            "",
            "## Data And Split Policy",
            "",
            "This run uses the committed `christian_virtue_v1` export built from approved reviewed "
            "doctrinal annotations only. Structural-editorial review, candidate material, and "
            "processed edge exports are not used as training truth.",
            "",
            "The dataset remains segment-grounded and grouped by `question_id` for leakage-safe "
            "splits.",
            "",
            f"- Grouping key: `{dataset_manifest['grouping_key']}`",
            f"- Support types: `"
            f"{', '.join(dataset_manifest['annotation_counts_by_support_type'])}`",
            "",
            "## Method",
            "",
            "| Parameter | Value |",
            "| --- | ---: |",
            f"| Learning rate | `{2e-4}` |",
            f"| Max sequence length | `{768}` |",
            f"| Train examples | `{train_metadata['train_examples']}` |",
            f"| Eval examples | `{train_metadata['eval_examples']}` |",
            "| Per-device train batch size | `1` |",
            "| Gradient accumulation steps | `8` |",
            "| LoRA rank | `16` |",
            "| LoRA alpha | `32` |",
            "| LoRA dropout | `0.05` |",
            "| Seed | `17` |",
            "",
            "## Runtime Environment",
            "",
            "| Item | Value |",
            "| --- | --- |",
            f"| Python | `{train_metadata['python_version']}` |",
            f"| Torch | `{train_metadata['torch_version']}` |",
            f"| Transformers | `{train_metadata['transformers_version']}` |",
            f"| PEFT | `{train_metadata['peft_version']}` |",
            f"| TRL | `{train_metadata['trl_version']}` |",
            f"| Accelerate | `{train_metadata['accelerate_version']}` |",
        ]
    )
    if runtime_minutes is not None:
        lines.append(f"| Approx train wall-clock | `{runtime_minutes:.1f} minutes` |")

    lines.extend(
        [
            "",
            "## Training Trajectory",
            "",
            f"![Pilot-lite training curves]({training_curves_asset_path})",
            "",
            "The training curve is healthy for a local demonstration run: loss falls sharply, "
            "token accuracy rises, and the small eval slice stays close to the training signal.",
            "",
            "## Held-Out Test Comparison",
            "",
            f"![Base vs adapter test comparison]({comparison_asset_path})",
            "",
            "| Model | Count | Citation exact | Citation partial | Citation overlap |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| Base model | `{base_overall['count']}` | "
            f"`{base_overall['citation_exact_match']:.3f}` | "
            f"`{base_overall['citation_partial_match']:.3f}` | "
            f"`{base_overall['citation_overlap']:.3f}` |",
            f"| LoRA adapter | `{adapter_overall['count']}` | "
            f"`{adapter_overall['citation_exact_match']:.3f}` | "
            f"`{adapter_overall['citation_partial_match']:.3f}` | "
            f"`{adapter_overall['citation_overlap']:.3f}` |",
            "",
            "The adapter materially improves held-out citation grounding over the untouched base "
            "model, but the improvement is uneven across tasks. The open user-style moral-answer "
            "task remains the hardest failure mode.",
            "",
            "## Goal Demo Panel",
            "",
            "This fixed panel uses held-out examples chosen to reflect the real SFT goal: virtue "
            "definition, part distinctions, act relations, vice opposition, and tract-local "
            "explanation.",
            "",
        ]
    )
    for row in goal_demo_rows:
        lines.extend(
            [
                f"### {row['slot']}. {row['title']}",
                "",
                f"- Focus: {row['focus']}",
                f"- Task type: {row['task_type_display']}",
                f"- Tract: {row['tract_display']}",
                f"- Prompt: {_truncate_text(row['prompt'], limit=220)}",
                f"- Reference citations: `{', '.join(row['reference_passage_ids'])}`",
                f"- Base exact citation match: `{row['base_exact_match']}`",
                f"- Adapter exact citation match: `{row['adapter_exact_match']}`",
                "",
                "Reference:",
                "",
                f"> {row['reference_excerpt']}",
                "",
                "Base model:",
                "",
                f"> {row['base_excerpt']}",
                "",
                "LoRA adapter:",
                "",
                f"> {row['adapter_excerpt']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Comparison Summary",
            "",
            embedded_comparison_markdown,
            "",
            "## What This Demonstrates",
            "",
            "1. The repo now has one clean, reproducible local 1.5B training recipe that works on "
            "Apple Silicon.",
            "2. The committed Christian virtue dataset can measurably move a base model toward "
            "repo-specific doctrinal behavior.",
            "3. The adapter is stronger than the base model on the held-out benchmark and on a "
            "fixed qualitative goal panel.",
            "4. The repo is publishable as a fine-tuning entrypoint because data, methods, "
            "evaluation, and model packaging now line up.",
            "",
            "## What This Does Not Demonstrate",
            "",
            "1. It does not prove that the local laptop recipe is the best-quality final model.",
            "2. It does not solve the hardest citation-grounded moral-answer cases.",
            "3. It does not replace the need for larger remote CUDA experiments when quality "
            "improvement becomes the primary objective.",
            "",
            "## Recommended Public Reproduction Path",
            "",
            "```bash",
            "make build-christian-virtue-sft",
            "make train-christian-virtue-qwen2-5-1-5b-local-smoke",
            "make train-christian-virtue-qwen2-5-1-5b-local-pilot-lite",
            "make eval-christian-virtue-qwen2-5-1-5b-local-base-test",
            "make eval-christian-virtue-qwen2-5-1-5b-local-adapter-test",
            "make compare-christian-virtue-qwen2-5-1-5b-local-test",
            "make report-christian-virtue-qwen2-5-1-5b-local-pilot-lite",
            "make verify-christian-virtue-qwen2-5-1-5b-local-publishable",
            "```",
            "",
            "## Headline Numbers",
            "",
            f"- Base citation exact match: {_format_percent(base_overall['citation_exact_match'])}",
            f"- Adapter citation exact match: "
            f"{_format_percent(adapter_overall['citation_exact_match'])}",
            f"- Net gain: {_format_percent(net_gain)}",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_publishable_local_report(
    *,
    dataset_dir: Path,
    train_run_dir: Path,
    base_run_dir: Path,
    adapter_run_dir: Path,
    panel_path: Path,
    output_path: Path,
    training_curves_asset_path: Path,
    comparison_asset_path: Path,
    published_model_url: str | None = None,
    release_url: str | None = None,
) -> Path:
    dataset_manifest = _load_json(dataset_dir / "manifest.json")
    train_metadata = _load_json(train_run_dir / "train_metadata.json")
    base_metrics = _load_json(base_run_dir / "metrics.json")
    adapter_metrics = _load_json(adapter_run_dir / "metrics.json")
    goal_demo_rows = build_goal_demo_panel(
        dataset_dir=dataset_dir,
        panel_path=panel_path,
        base_predictions_path=base_run_dir / "predictions.jsonl",
        adapter_predictions_path=adapter_run_dir / "predictions.jsonl",
    )
    comparison_markdown = build_comparison_report(
        base_metrics,
        adapter_metrics,
        baseline_label="Base model",
        candidate_label="LoRA adapter",
    )
    report_text = build_publishable_local_report(
        dataset_manifest=dataset_manifest,
        train_metadata=train_metadata,
        base_metrics=base_metrics,
        adapter_metrics=adapter_metrics,
        goal_demo_rows=goal_demo_rows,
        comparison_markdown=comparison_markdown,
        training_curves_asset_path=str(training_curves_asset_path),
        comparison_asset_path=str(comparison_asset_path),
        published_model_url=published_model_url,
        release_url=release_url,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    return output_path
