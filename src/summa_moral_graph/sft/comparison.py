"""Compare baseline and candidate evaluation bundles and render markdown deltas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

SUMMARY_KEYS = [
    "count",
    "citation_exact_match",
    "citation_partial_match",
    "citation_overlap",
    "relation_type_accuracy",
]


def load_metrics_file(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _metric_delta(baseline_value: Any, candidate_value: Any) -> float | int | None:
    if baseline_value is None or candidate_value is None:
        return None
    if isinstance(baseline_value, int) and isinstance(candidate_value, int):
        return candidate_value - baseline_value
    return float(candidate_value) - float(baseline_value)


def _comparison_rows(
    baseline_summary: dict[str, Any], candidate_summary: dict[str, Any]
) -> list[tuple[str, Any, Any, float | int | None]]:
    rows: list[tuple[str, Any, Any, float | int | None]] = []
    for key in SUMMARY_KEYS:
        baseline_value = baseline_summary.get(key)
        candidate_value = candidate_summary.get(key)
        rows.append(
            (
                key,
                baseline_value,
                candidate_value,
                _metric_delta(baseline_value, candidate_value),
            )
        )
    return rows


def _bucket_keys(
    baseline_metrics: dict[str, Any], candidate_metrics: dict[str, Any], bucket_name: str
) -> list[str]:
    baseline_bucket = baseline_metrics.get(bucket_name, {})
    candidate_bucket = candidate_metrics.get(bucket_name, {})
    keys = {str(key) for key in baseline_bucket} | {str(key) for key in candidate_bucket}
    return sorted(keys)


def build_comparison_report(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    *,
    baseline_label: str,
    candidate_label: str,
) -> str:
    def format_value(value: Any) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return f"{value:.3f}"
        return str(value)

    def format_delta(value: float | int | None) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, int):
            return f"{value:+d}"
        return f"{value:+.3f}"

    def append_metric_table(
        lines: list[str],
        summary_rows: list[tuple[str, Any, Any, float | int | None]],
    ) -> None:
        lines.extend(
            [
                "| Metric | Baseline | Candidate | Delta |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for metric_name, baseline_value, candidate_value, delta in summary_rows:
            lines.append(
                f"| {metric_name} | {format_value(baseline_value)} | "
                f"{format_value(candidate_value)} | {format_delta(delta)} |"
            )

    lines = [
        "# Christian Virtue Run Comparison",
        "",
        f"- Baseline: {baseline_label}",
        f"- Candidate: {candidate_label}",
        "",
        "## Overall",
        "",
    ]
    append_metric_table(
        lines,
        _comparison_rows(baseline_metrics["overall"], candidate_metrics["overall"]),
    )

    for bucket_name, title in [
        ("by_split", "By Split"),
        ("by_tract", "By Tract"),
        ("by_support_type", "By Support Type"),
        ("by_task_type", "By Task Type"),
    ]:
        lines.extend(["", f"## {title}", ""])
        keys = _bucket_keys(baseline_metrics, candidate_metrics, bucket_name)
        if not keys:
            lines.append("- No data.")
            continue
        for key in keys:
            baseline_summary = baseline_metrics.get(bucket_name, {}).get(
                key,
                {metric: None for metric in SUMMARY_KEYS},
            )
            candidate_summary = candidate_metrics.get(bucket_name, {}).get(
                key,
                {metric: None for metric in SUMMARY_KEYS},
            )
            lines.append(f"### {key}")
            lines.append("")
            append_metric_table(
                lines,
                _comparison_rows(
                    baseline_summary,
                    candidate_summary,
                ),
            )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_comparison_report(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    output_path: Path,
    *,
    baseline_label: str,
    candidate_label: str,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_comparison_report(
            baseline_metrics,
            candidate_metrics,
            baseline_label=baseline_label,
            candidate_label=candidate_label,
        ),
        encoding="utf-8",
    )
    return output_path
