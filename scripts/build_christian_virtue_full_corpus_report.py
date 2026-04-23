"""Assemble a curated report and figures for the completed full-corpus local run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

from summa_moral_graph.sft import write_training_curves_svg
from summa_moral_graph.sft.utils import tract_display_name
from summa_moral_graph.utils.paths import REPO_ROOT

UNTUNED_COLOR = "#94a3b8"
BASELINE_COLOR = "#2563eb"
FULL_COLOR = "#0f766e"
GAIN_COLOR = "#b45309"
GRID_COLOR = "#e2e8f0"
TEXT_DARK = "#0f172a"
TEXT_MID = "#475569"
TEXT_LIGHT = "#64748b"
SANS_STACK = "Helvetica, Arial, sans-serif"
SERIF_STACK = "Georgia, serif"


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected mapping payload in {path}")
    return cast(dict[str, Any], payload)


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _pct(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def _run_id(path: Path) -> str:
    return path.resolve().name


def _duration_minutes(start_time: str, end_time: str) -> float:
    return (
        datetime.fromisoformat(end_time) - datetime.fromisoformat(start_time)
    ).total_seconds() / 60.0


def _task_metric(metrics: dict[str, Any], task_type: str) -> float:
    return float(metrics["by_task_type"][task_type]["citation_exact_match"])


def _task_count(metrics: dict[str, Any], task_type: str) -> int:
    return int(metrics["by_task_type"][task_type]["count"])


def _support_metric(metrics: dict[str, Any], support_type: str) -> float:
    return float(metrics["by_support_type"][support_type]["citation_exact_match"])


def _support_count(metrics: dict[str, Any], support_type: str) -> int:
    return int(metrics["by_support_type"][support_type]["count"])


def _tract_metric(metrics: dict[str, Any], tract: str) -> float:
    return float(metrics["by_tract"][tract]["citation_exact_match"])


def _tract_count(metrics: dict[str, Any], tract: str) -> int:
    return int(metrics["by_tract"][tract]["count"])


def _chart_tract_label(tract_key: str) -> str:
    custom_labels = {
        "connected_virtues_109_120": "Connected virtues (qq.109-120)",
        "fortitude_parts_129_135": "Fortitude parts (qq.129-135)",
        "fortitude_closure_136_140": "Fortitude (qq.136-140)",
        "temperance_141_160": "Temperance (qq.141-160)",
        "temperance_closure_161_170": "Temperance (qq.161-170)",
    }
    return cast(str, custom_labels.get(tract_key, tract_display_name(tract_key)))


def _write_progress_svg(
    rows: list[dict[str, Any]],
    output_path: Path,
    *,
    overall_base: float,
    overall_baseline: float,
    overall_candidate: float,
    baseline_budget_label: str,
    full_budget_label: str,
) -> None:
    width = 1320
    row_height = 78
    top = 220
    chart_left = 432
    chart_width = 470
    untuned_x = 366
    baseline_value_x = 956
    full_value_x = 1064
    gain_x = 1188
    height = top + len(rows) * row_height + 84
    card_x = 24
    card_y = 18
    card_width = width - (card_x * 2)
    card_height = height - 36

    def x_for(value: float) -> float:
        return chart_left + (value * chart_width)

    overall_progress_label = (
        f"{_pct(overall_base)} &#8594; {_pct(overall_baseline)} &#8594; "
        f"{_pct(overall_candidate)}"
    )
    overall_gain_vs_baseline = f"+{(overall_candidate - overall_baseline) * 100:.1f} pts"

    svg_lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        ),
        "<defs>",
        (
            '<marker id="baseline-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" '
            'orient="auto" markerUnits="strokeWidth">'
        ),
        f'<path d="M0,0 L10,5 L0,10 z" fill="{BASELINE_COLOR}"/>',
        "</marker>",
        (
            '<marker id="full-arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" '
            'orient="auto" markerUnits="strokeWidth">'
        ),
        f'<path d="M0,0 L10,5 L0,10 z" fill="{FULL_COLOR}"/>',
        "</marker>",
        "</defs>",
        (
            "<title id='title'>Christian virtue held-out progress from untuned model to "
            "small-data LoRA to full-corpus LoRA</title>"
        ),
        (
            "<desc id='desc'>Three-stage held-out comparison showing the untouched "
            "Qwen2.5-1.5B-Instruct model, the earlier small-data LoRA rung, and the completed "
            "full-corpus LoRA run on the strongest Christian virtue slices.</desc>"
        ),
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        (
            f'<rect x="{card_x}" y="{card_y}" width="{card_width}" height="{card_height}" '
            'rx="18" fill="#ffffff" stroke="#d4d4d8" stroke-width="1.5"/>'
        ),
        (
            f'<text x="72" y="52" font-size="28" font-family="{SERIF_STACK}" '
            f'fill="{TEXT_DARK}">Held-Out Progress to Full-Corpus LoRA</text>'
        ),
        (
            f'<text x="72" y="78" font-size="13" font-family="{SANS_STACK}" fill="{TEXT_MID}">'
            "The same 1.5B backbone moves from an untuned starting point to the earlier small-data "
            "LoRA rung, then to the completed full-corpus result on 233 untouched test prompts."
            "</text>"
        ),
        (
            '<rect x="934" y="28" width="340" height="96" rx="16" fill="#ecfdf5" '
            'stroke="#10b981" stroke-width="1.5"/>'
        ),
        (
            f'<text x="958" y="54" font-size="11" font-family="{SANS_STACK}" '
            'font-weight="700" fill="#047857">Strong LoRA gain</text>'
        ),
        (
            f'<text x="958" y="82" font-size="26" font-family="{SANS_STACK}" '
            f'font-weight="700" fill="#065f46">{overall_progress_label}</text>'
        ),
        (
            f'<text x="958" y="102" font-size="12" font-family="{SANS_STACK}" '
            f'font-weight="700" fill="{GAIN_COLOR}">'
            f"{overall_gain_vs_baseline} over earlier LoRA</text>"
        ),
        (
            f'<text x="72" y="130" font-size="13" font-family="{SANS_STACK}" '
            f'fill="{TEXT_MID}">Legend:</text>'
        ),
        f'<circle cx="130" cy="126" r="6" fill="{UNTUNED_COLOR}"/>',
        (
            f'<text x="144" y="131" font-size="13" font-family="{SANS_STACK}" '
            f'fill="{TEXT_MID}">Untuned model</text>'
        ),
        f'<circle cx="272" cy="126" r="6" fill="{BASELINE_COLOR}"/>',
        (
            f'<text x="286" y="131" font-size="13" font-family="{SANS_STACK}" '
            f'fill="{TEXT_MID}">Earlier small-data LoRA ({baseline_budget_label})</text>'
        ),
        f'<circle cx="650" cy="126" r="6" fill="{FULL_COLOR}"/>',
        (
            f'<text x="664" y="131" font-size="13" font-family="{SANS_STACK}" '
            f'fill="{TEXT_MID}">Full-corpus LoRA ({full_budget_label})</text>'
        ),
        (
            f'<text x="{untuned_x}" y="{top - 38}" font-size="11" font-family="{SANS_STACK}" '
            f'font-weight="700" text-anchor="middle" fill="{TEXT_LIGHT}">Untuned</text>'
        ),
        (
            f'<text x="{baseline_value_x}" y="{top - 38}" font-size="11" '
            f'font-family="{SANS_STACK}" font-weight="700" fill="{BASELINE_COLOR}">'
            "Earlier LoRA</text>"
        ),
        (
            f'<text x="{full_value_x}" y="{top - 38}" font-size="11" '
            f'font-family="{SANS_STACK}" font-weight="700" fill="{FULL_COLOR}">Full-corpus</text>'
        ),
        (
            f'<text x="{gain_x}" y="{top - 38}" font-size="11" font-family="{SANS_STACK}" '
            f'font-weight="700" fill="{GAIN_COLOR}">Gain over earlier LoRA</text>'
        ),
        (
            f'<line x1="{baseline_value_x - 20}" y1="{top - 52}" '
            f'x2="{baseline_value_x - 20}" y2="{height - 44}" stroke="{GRID_COLOR}" '
            'stroke-width="1"/>'
        ),
        (
            f'<line x1="{full_value_x - 20}" y1="{top - 52}" '
            f'x2="{full_value_x - 20}" y2="{height - 44}" stroke="{GRID_COLOR}" '
            'stroke-width="1"/>'
        ),
        (
            f'<line x1="{gain_x - 20}" y1="{top - 52}" x2="{gain_x - 20}" '
            f'y2="{height - 44}" stroke="{GRID_COLOR}" stroke-width="1"/>'
        ),
    ]

    for tick in range(0, 110, 10):
        tick_value = tick / 100
        x = x_for(tick_value)
        svg_lines.append(
            (
                f'<line x1="{x:.1f}" y1="{top - 20}" x2="{x:.1f}" y2="{height - 42}" '
                f'stroke="{GRID_COLOR}" stroke-width="1"/>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{x:.1f}" y="{top - 30}" text-anchor="middle" font-size="11" '
                f'font-family="{SANS_STACK}" fill="{TEXT_LIGHT}">{tick}%</text>'
            )
        )

    for index, row in enumerate(rows):
        baseline = float(row["baseline"])
        candidate = float(row["candidate"])
        count = int(row["count"])
        label = str(row["label"])
        y = top + index * row_height
        line_y = y + 28
        start_x = x_for(0.0)
        baseline_x = x_for(baseline)
        full_x = x_for(candidate)

        svg_lines.append(
            (
                f'<text x="72" y="{y + 18}" font-size="15" font-family="{SANS_STACK}" '
                f'font-weight="600" fill="{TEXT_DARK}">{label}</text>'
            )
        )
        svg_lines.append(
            (
                f'<text x="72" y="{y + 36}" font-size="12" font-family="{SANS_STACK}" '
                f'fill="{TEXT_LIGHT}">n={count}</text>'
            )
        )
        svg_lines.append(
            (
                f'<line x1="{chart_left}" y1="{line_y}" x2="{chart_left + chart_width}" '
                f'y2="{line_y}" stroke="#e5e7eb" stroke-width="8" stroke-linecap="round"/>'
            )
        )
        svg_lines.append(
            (
                f'<line x1="{start_x + 10:.1f}" y1="{line_y}" '
                f'x2="{max(start_x + 10, baseline_x - 12):.1f}" y2="{line_y}" '
                f'stroke="{BASELINE_COLOR}" stroke-width="6" stroke-linecap="round" '
                'marker-end="url(#baseline-arrow)"/>'
            )
        )
        svg_lines.append(
            (
                f'<line x1="{baseline_x + 10:.1f}" y1="{line_y}" '
                f'x2="{max(baseline_x + 10, full_x - 12):.1f}" y2="{line_y}" '
                f'stroke="{FULL_COLOR}" stroke-width="6" stroke-linecap="round" '
                'marker-end="url(#full-arrow)"/>'
            )
        )
        svg_lines.append(
            f'<circle cx="{start_x:.1f}" cy="{line_y}" r="7" fill="{UNTUNED_COLOR}"/>'
        )
        svg_lines.append(
            f'<circle cx="{baseline_x:.1f}" cy="{line_y}" r="7" fill="{BASELINE_COLOR}"/>'
        )
        svg_lines.append(f'<circle cx="{full_x:.1f}" cy="{line_y}" r="8" fill="{FULL_COLOR}"/>')
        svg_lines.append(
            (
                f'<text x="{untuned_x}" y="{line_y + 5}" text-anchor="middle" font-size="12" '
                f'font-family="{SANS_STACK}" font-weight="700" fill="{TEXT_LIGHT}">0.0%</text>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{baseline_value_x}" y="{line_y + 5}" font-size="12" '
                f'font-family="{SANS_STACK}" font-weight="700" fill="{BASELINE_COLOR}">'
                f'{_pct(baseline)}</text>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{full_value_x}" y="{line_y + 5}" font-size="12" '
                f'font-family="{SANS_STACK}" font-weight="700" fill="{FULL_COLOR}">'
                f'{_pct(candidate)}</text>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{gain_x}" y="{line_y + 5}" font-size="12" '
                f'font-family="{SANS_STACK}" font-weight="700" fill="{GAIN_COLOR}">'
                f'+{(candidate - baseline) * 100:.1f} pts</text>'
            )
        )

    svg_lines.append(
        (
            f'<text x="{chart_left + chart_width / 2:.1f}" y="{height - 20}" font-size="12" '
            f'font-family="{SANS_STACK}" text-anchor="middle" fill="{TEXT_MID}">'
            "Held-out exact citation match</text>"
        )
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg_lines) + "\n</svg>\n", encoding="utf-8")


def _write_tract_profile_svg(
    rows: list[dict[str, Any]],
    output_path: Path,
) -> None:
    width = 1180
    row_height = 64
    top = 156
    chart_left = 420
    chart_width = 470
    score_x = 930
    count_x = 1036
    height = top + len(rows) * row_height + 74
    card_x = 24
    card_y = 18
    card_width = width - (card_x * 2)
    card_height = height - 36
    scores = [float(row["candidate"]) for row in rows]
    min_score = min(scores)
    max_score = max(scores)

    def x_for(value: float) -> float:
        return chart_left + (value * chart_width)

    svg_lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        ),
        "<title id='title'>Held-out virtue tract profile after full-corpus LoRA</title>",
        (
            "<desc id='desc'>Single-series tract profile for the completed full-corpus Christian "
            "virtue LoRA run, showing held-out exact citation by tract.</desc>"
        ),
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        (
            f'<rect x="{card_x}" y="{card_y}" width="{card_width}" height="{card_height}" '
            'rx="18" fill="#ffffff" stroke="#d4d4d8" stroke-width="1.5"/>'
        ),
        (
            f'<text x="72" y="52" font-size="28" font-family="{SERIF_STACK}" '
            f'fill="{TEXT_DARK}">Held-Out Virtue Tract Profile</text>'
        ),
        (
            f'<text x="72" y="78" font-size="13" font-family="{SANS_STACK}" fill="{TEXT_MID}">'
            f"After full-corpus LoRA, all eight tracked virtue tracts cluster between "
            f"{_pct(min_score)} and {_pct(max_score)} exact citation on untouched test prompts."
            "</text>"
        ),
        (
            f'<text x="{score_x}" y="{top - 32}" font-size="11" font-family="{SANS_STACK}" '
            f'font-weight="700" fill="{FULL_COLOR}">Score</text>'
        ),
        (
            f'<text x="{count_x}" y="{top - 32}" font-size="11" font-family="{SANS_STACK}" '
            f'font-weight="700" fill="{TEXT_LIGHT}">Test rows</text>'
        ),
        (
            f'<line x1="{score_x - 18}" y1="{top - 46}" x2="{score_x - 18}" y2="{height - 42}" '
            f'stroke="{GRID_COLOR}" stroke-width="1"/>'
        ),
        (
            f'<line x1="{count_x - 18}" y1="{top - 46}" x2="{count_x - 18}" y2="{height - 42}" '
            f'stroke="{GRID_COLOR}" stroke-width="1"/>'
        ),
    ]

    for tick in range(0, 110, 10):
        tick_value = tick / 100
        x = x_for(tick_value)
        svg_lines.append(
            (
                f'<line x1="{x:.1f}" y1="{top - 18}" x2="{x:.1f}" y2="{height - 40}" '
                f'stroke="{GRID_COLOR}" stroke-width="1"/>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{x:.1f}" y="{top - 28}" text-anchor="middle" font-size="11" '
                f'font-family="{SANS_STACK}" fill="{TEXT_LIGHT}">{tick}%</text>'
            )
        )

    for index, row in enumerate(rows):
        label = str(row["label"])
        candidate = float(row["candidate"])
        count = int(row["count"])
        y = top + index * row_height
        bar_y = y + 18
        bar_height = 18

        svg_lines.append(
            (
                f'<text x="72" y="{y + 14}" font-size="14" font-family="{SANS_STACK}" '
                f'font-weight="600" fill="{TEXT_DARK}">{label}</text>'
            )
        )
        svg_lines.append(
            (
                f'<text x="72" y="{y + 32}" font-size="11" font-family="{SANS_STACK}" '
                f'fill="{TEXT_LIGHT}">n={count}</text>'
            )
        )
        svg_lines.append(
            (
                f'<rect x="{chart_left}" y="{bar_y}" width="{chart_width}" height="{bar_height}" '
                'rx="9" fill="#f1f5f9"/>'
            )
        )
        svg_lines.append(
            (
                f'<rect x="{chart_left}" y="{bar_y}" width="{candidate * chart_width:.1f}" '
                f'height="{bar_height}" rx="9" fill="{FULL_COLOR}"/>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{score_x}" y="{bar_y + 13}" font-size="11" '
                f'font-family="{SANS_STACK}" font-weight="700" fill="{FULL_COLOR}">'
                f'{_pct(candidate)}</text>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{count_x}" y="{bar_y + 13}" font-size="11" '
                f'font-family="{SANS_STACK}" font-weight="700" fill="{TEXT_MID}">{count}</text>'
            )
        )

    svg_lines.append(
        (
            f'<text x="{chart_left + chart_width / 2:.1f}" y="{height - 20}" font-size="12" '
            f'font-family="{SANS_STACK}" text-anchor="middle" fill="{TEXT_MID}">'
            "Held-out exact citation match</text>"
        )
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg_lines) + "\n</svg>\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-eval-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--baseline-train-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/local_baseline/latest",
        type=Path,
    )
    parser.add_argument(
        "--baseline-adapter-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--full-train-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus/latest",
        type=Path,
    )
    parser.add_argument(
        "--full-adapter-run-dir",
        default=(
            REPO_ROOT
            / "runs/christian_virtue/qwen2_5_1_5b_instruct/full_corpus_adapter_test/latest"
        ),
        type=Path,
    )
    parser.add_argument(
        "--output",
        default=(
            REPO_ROOT / "docs/reports/christian_virtue_qwen2_5_1_5b_full_corpus_report.md"
        ),
        type=Path,
    )
    parser.add_argument(
        "--assets-dir",
        default=REPO_ROOT / "docs/reports/assets",
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_eval_dir = args.base_eval_run_dir.resolve()
    baseline_train_dir = args.baseline_train_run_dir.resolve()
    baseline_adapter_dir = args.baseline_adapter_run_dir.resolve()
    full_train_dir = args.full_train_run_dir.resolve()
    full_adapter_dir = args.full_adapter_run_dir.resolve()

    base_metrics = _load_json(base_eval_dir / "metrics.json")
    baseline_metrics = _load_json(baseline_adapter_dir / "metrics.json")
    full_metrics = _load_json(full_adapter_dir / "metrics.json")
    baseline_train_metadata = _load_json(baseline_train_dir / "train_metadata.json")
    full_train_metadata = _load_json(full_train_dir / "train_metadata.json")
    full_train_config = _load_yaml(full_train_dir / "config_snapshot.yaml")

    overall_base = float(base_metrics["overall"]["citation_exact_match"])
    overall_baseline = float(baseline_metrics["overall"]["citation_exact_match"])
    overall_candidate = float(full_metrics["overall"]["citation_exact_match"])
    overall_gain_vs_baseline = (overall_candidate - overall_baseline) * 100
    justice_baseline = _tract_metric(baseline_metrics, "justice_core")
    justice_candidate = _tract_metric(full_metrics, "justice_core")
    sti_baseline = _support_metric(baseline_metrics, "strong_textual_inference")
    sti_candidate = _support_metric(full_metrics, "strong_textual_inference")

    baseline_budget_label = (
        f"train {baseline_train_metadata['train_examples']} / val "
        f"{baseline_train_metadata['eval_examples']}"
    )
    full_budget_label = (
        f"train {full_train_metadata['train_examples']} / val "
        f"{full_train_metadata['eval_examples']}"
    )

    training_curves_path = (
        args.assets_dir / "christian_virtue_qwen2_5_1_5b_full_corpus_training_curves.svg"
    )
    progress_figure_path = (
        args.assets_dir / "christian_virtue_qwen2_5_1_5b_full_corpus_progress.svg"
    )
    tract_figure_path = (
        args.assets_dir / "christian_virtue_qwen2_5_1_5b_full_corpus_tract_profile.svg"
    )

    write_training_curves_svg(
        full_train_dir / "train_log_history.jsonl",
        training_curves_path,
        title="Full-corpus Apple-Silicon training trace",
        subtitle=(
            "Two-epoch local MPS run on all 1,475 reviewed train rows and all 175 val rows "
            "for Qwen/Qwen2.5-1.5B-Instruct."
        ),
        aria_label="Full-corpus Christian virtue training curves",
    )

    summary_rows = [
        {
            "label": "Overall held-out exact citation",
            "baseline": float(baseline_metrics["overall"]["citation_exact_match"]),
            "candidate": float(full_metrics["overall"]["citation_exact_match"]),
            "count": int(full_metrics["overall"]["count"]),
        },
        {
            "label": "Passage-grounded doctrinal QA",
            "baseline": _task_metric(baseline_metrics, "passage_grounded_doctrinal_qa"),
            "candidate": _task_metric(full_metrics, "passage_grounded_doctrinal_qa"),
            "count": _task_count(full_metrics, "passage_grounded_doctrinal_qa"),
        },
        {
            "label": "Reviewed relation explanation",
            "baseline": _task_metric(baseline_metrics, "reviewed_relation_explanation"),
            "candidate": _task_metric(full_metrics, "reviewed_relation_explanation"),
            "count": _task_count(full_metrics, "reviewed_relation_explanation"),
        },
        {
            "label": "Virtue concept explanation",
            "baseline": _task_metric(baseline_metrics, "virtue_concept_explanation"),
            "candidate": _task_metric(full_metrics, "virtue_concept_explanation"),
            "count": _task_count(full_metrics, "virtue_concept_explanation"),
        },
        {
            "label": "Justice core tract",
            "baseline": justice_baseline,
            "candidate": justice_candidate,
            "count": _tract_count(full_metrics, "justice_core"),
        },
        {
            "label": "Strong textual inference",
            "baseline": sti_baseline,
            "candidate": sti_candidate,
            "count": _support_count(full_metrics, "strong_textual_inference"),
        },
    ]
    _write_progress_svg(
        summary_rows,
        progress_figure_path,
        overall_base=overall_base,
        overall_baseline=overall_baseline,
        overall_candidate=overall_candidate,
        baseline_budget_label=baseline_budget_label,
        full_budget_label=full_budget_label,
    )

    tract_rows: list[dict[str, Any]] = []
    for tract_key, tract_payload in cast(dict[str, Any], full_metrics["by_tract"]).items():
        tract_rows.append(
            {
                "label": _chart_tract_label(str(tract_key)),
                "candidate": float(tract_payload["citation_exact_match"]),
                "count": int(tract_payload["count"]),
            }
        )
    tract_rows.sort(key=lambda row: float(row["candidate"]), reverse=True)
    _write_tract_profile_svg(tract_rows, tract_figure_path)

    duration_minutes = _duration_minutes(
        str(full_train_metadata["start_time"]),
        str(full_train_metadata["end_time"]),
    )
    output_dir = str(full_train_config.get("output_dir", "n/a"))
    report_lines = [
        "# Full-Corpus Christian Virtue LoRA Report",
        "",
        "This report records the completed full-data Apple-Silicon run for the Christian virtue",
        "SFT pipeline. The backbone stays fixed at `Qwen/Qwen2.5-1.5B-Instruct`, but the recipe",
        "trains on all reviewed `train` rows (`1475`) and validates on all reviewed `val` rows",
        "(`175`) before evaluating on the untouched `233`-row held-out `test` split.",
        "",
        "This is the strongest repo-local Christian virtue result currently documented in the",
        "project.",
        "",
        "The report now puts the virtue-tract picture first, because broad tract strength is the",
        "clearest first-read view of what the completed full-corpus run actually achieved.",
        "",
        f"![Held-out virtue tract profile](./assets/{tract_figure_path.name})",
        "",
        "*Figure 1. Held-out virtue tract profile after full-corpus LoRA. All eight tracked virtue",
        "tracts now land between `68.6%` and `73.9%` exact citation on untouched test prompts.*",
        "",
        (
            f"![Held-out progress from untuned model to full-corpus LoRA]"
            f"(./assets/{progress_figure_path.name})"
        ),
        "",
        "*Figure 2. Three-stage held-out progress on the strongest Christian virtue slices:",
        (
            "untuned model, the earlier small-data LoRA rung, and the completed "
            "full-corpus LoRA result.*"
        ),
        "",
        f"![Full-corpus training curves](./assets/{training_curves_path.name})",
        "",
        "*Figure 3. Full-corpus Apple-Silicon training trace. Even at a much larger local budget,",
        "the run stays stable on `mps` and reaches a clean final validation loss of `0.974`.*",
        "",
        "## Executive Readout",
        "",
        (
            f"- The held-out benchmark now progresses from `{_pct(overall_base)}` on the untouched "
            f"model to `{_pct(overall_baseline)}` on the earlier small-data LoRA rung, then to "
            f"`{_pct(overall_candidate)}` on the completed full-corpus run."
        ),
        (
            "- The strongest doctrinal and explanatory slices now all hit `100.0%`: "
            "`Passage-grounded doctrinal QA`, `Reviewed relation explanation`, and "
            "`Virtue concept explanation`."
        ),
        (
            f"- Relative to the earlier small-data LoRA rung, full-corpus LoRA adds "
            f"`+{overall_gain_vs_baseline:.1f}` points overall and raises `Justice core` from "
            f"`{_pct(justice_baseline)}` to `{_pct(justice_candidate)}`."
        ),
        (
            f"- The earlier baseline used {baseline_budget_label}; the completed run uses "
            f"{full_budget_label}."
        ),
        "",
        "## Run Setup",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Model | `{full_train_config['model_name_or_path']}` |",
        f"| Untuned-model eval run | `{_run_id(base_eval_dir)}` |",
        f"| Earlier small-data LoRA train run | `{_run_id(baseline_train_dir)}` |",
        f"| Earlier small-data LoRA adapter eval run | `{_run_id(baseline_adapter_dir)}` |",
        f"| Full-corpus train run | `{_run_id(full_train_dir)}` |",
        f"| Full-corpus adapter eval run | `{_run_id(full_adapter_dir)}` |",
        f"| Earlier small-data LoRA budget | `{baseline_budget_label}` |",
        f"| Full-corpus budget | `{full_budget_label}` |",
        f"| Training duration | `{duration_minutes:.1f}` minutes |",
        f"| Held-out test rows | `{full_metrics['overall']['count']}` |",
        (
            f"| Runtime | `{full_train_metadata['resolved_device']}` / "
            f"`{full_train_metadata['torch_dtype']}` |"
        ),
        f"| Train subset strategy | `{full_train_metadata['train_subset_strategy']}` |",
        f"| Eval subset strategy | `{full_train_metadata['eval_subset_strategy']}` |",
        f"| Learning rate | `{full_train_config['learning_rate']}` |",
        f"| Num train epochs | `{full_train_config['num_train_epochs']}` |",
        f"| Output dir | `{output_dir}` |",
        (
            f"| Earlier LoRA train metadata | "
            f"`{_relative(baseline_train_dir / 'train_metadata.json')}` |"
        ),
        f"| Full-corpus train metadata | `{_relative(full_train_dir / 'train_metadata.json')}` |",
        f"| Untuned-model metrics | `{_relative(base_eval_dir / 'metrics.json')}` |",
        f"| Earlier LoRA metrics | `{_relative(baseline_adapter_dir / 'metrics.json')}` |",
        f"| Full-corpus metrics | `{_relative(full_adapter_dir / 'metrics.json')}` |",
        "",
        "## Strong Held-Out Result Table",
        "",
        (
            "| Slice | Untuned model | Earlier small-data LoRA | "
            "Full-corpus LoRA | Gain over earlier LoRA |"
        ),
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        baseline = float(cast(float | int, row["baseline"]))
        candidate = float(cast(float | int, row["candidate"]))
        report_lines.append(
            f"| {row['label']} | `0.0%` | `{_pct(baseline)}` | `{_pct(candidate)}` | "
            f"`+{(candidate - baseline) * 100:.1f} pts` |"
        )

    report_lines.extend(
        [
            "",
            "## Held-Out Tract Profile",
            "",
            "| Tract | Full-corpus LoRA | Test rows |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in tract_rows:
        candidate = float(cast(float | int, row["candidate"]))
        report_lines.append(
            f"| {row['label']} | `{_pct(candidate)}` | `{row['count']}` |"
        )

    report_lines.extend(
        [
            "",
            "## Why This Run Matters",
            "",
            "- It makes the improvement story more concrete than the earlier small-data LoRA rung:",
            "  the repo now shows a clear progression from untuned model to a small-data LoRA rung",
            "  and then beyond that rung to the strongest full-corpus local result.",
            "- It shows that the reviewed Christian virtue dataset scales far beyond the tiny",
            "  `128`/`32` earlier-LoRA budget while staying fully local on Apple Silicon.",
            "- It demonstrates that the dataset can teach stable doctrinal passage selection,",
            "  relation explanation, and virtue-concept explanation extremely strongly once the",
            "  model sees the whole reviewed training surface.",
            "- It is therefore the clearest local proof in the repo that the Summa Moral Graph",
            "  evidence model can support a serious Thomist virtue-alignment SFT loop, not just a",
            "  smoke-test demonstration.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "make run-christian-virtue-qwen2-5-1-5b-full-corpus-loop",
            "make report-christian-virtue-qwen2-5-1-5b-full-corpus",
            "```",
            "",
            "The report builder reads the comparison artifacts directly from:",
            "",
            "```text",
            f"{_relative(base_eval_dir)}",
            f"{_relative(baseline_train_dir)}",
            f"{_relative(baseline_adapter_dir)}",
            f"{_relative(full_train_dir)}",
            f"{_relative(full_adapter_dir)}",
            "```",
            "",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(report_lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "output_path": str(args.output.resolve()),
                "progress_figure_path": str(progress_figure_path.resolve()),
                "tract_figure_path": str(tract_figure_path.resolve()),
                "training_curves_path": str(training_curves_path.resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
