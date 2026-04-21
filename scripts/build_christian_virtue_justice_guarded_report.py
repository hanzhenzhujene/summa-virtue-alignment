"""Assemble a curated report for the justice-guarded citation-repair follow-up run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

from summa_moral_graph.utils.paths import REPO_ROOT

BAR_COLORS = {
    "Baseline": "#2563eb",
    "Citation-frontier": "#d97706",
    "Justice-guarded": "#0f766e",
}
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


def _relative_from(base_dir: Path, target: Path) -> str:
    return str(target.resolve().relative_to(base_dir.resolve()))


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


def _support_metric(metrics: dict[str, Any], support_type: str) -> float:
    return float(metrics["by_support_type"][support_type]["citation_exact_match"])


def _tract_metric(metrics: dict[str, Any], tract: str) -> float:
    return float(metrics["by_tract"][tract]["citation_exact_match"])


def _write_triptych_svg(
    rows: list[tuple[str, float, float, float]],
    output_path: Path,
) -> None:
    width = 1040
    row_height = 74
    top = 140
    left = 290
    chart_width = 660
    height = top + len(rows) * row_height + 60
    max_value = max(
        max(baseline, frontier, guarded)
        for _, baseline, frontier, guarded in rows
    )
    if max_value <= 0:
        max_value = 1.0

    def bar_width(value: float) -> float:
        return (value / max_value) * chart_width

    def bar_y(row_index: int, offset: int) -> int:
        return top + row_index * row_height + offset * 18

    svg_open = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
    )
    subtitle = (
        "Qwen/Qwen2.5-1.5B-Instruct local LoRA on Christian virtue supervision. "
        "Same 128-example / 20-step budget."
    )
    svg_lines = [
        svg_open,
        '<title id="title">Justice-guarded same-budget follow-up comparison</title>',
        (
            '<desc id="desc">Baseline, citation-frontier, and justice-guarded exact '
            "citation scores across key held-out Christian virtue slices.</desc>"
        ),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        (
            f'<text x="56" y="52" font-size="28" font-family="{SERIF_STACK}" '
            'fill="#0f172a">Justice-Guarded Same-Budget Follow-Up</text>'
        ),
        (
            f'<text x="56" y="84" font-size="16" font-family="{SANS_STACK}" '
            f'fill="#475569">{subtitle}</text>'
        ),
    ]

    legend_y = 108
    legend_x = 56
    for label, color in BAR_COLORS.items():
        svg_lines.append(
            f'<circle cx="{legend_x}" cy="{legend_y}" r="6" fill="{color}"/>'
        )
        svg_lines.append(
            (
                f'<text x="{legend_x + 14}" y="{legend_y + 5}" font-size="14" '
                f'font-family="{SANS_STACK}" fill="#334155">{label}</text>'
            )
        )
        legend_x += 180

    for tick in range(0, int(max_value * 100) + 10, 10):
        tick_value = tick / 100
        x = left + bar_width(tick_value)
        svg_lines.append(
            (
                f'<line x1="{x:.1f}" y1="{top - 18}" x2="{x:.1f}" '
                f'y2="{height - 36}" stroke="#e2e8f0" stroke-width="1"/>'
            )
        )
        svg_lines.append(
            (
                f'<text x="{x:.1f}" y="{top - 28}" text-anchor="middle" '
                f'font-size="12" font-family="{SANS_STACK}" '
                f'fill="#64748b">{tick}%</text>'
            )
        )

    for row_index, (label, baseline, frontier, guarded) in enumerate(rows):
        label_y = top + row_index * row_height + 28
        svg_lines.append(
            (
                f'<text x="{left - 18}" y="{label_y}" text-anchor="end" '
                f'font-size="15" font-family="{SANS_STACK}" '
                f'fill="#0f172a">{label}</text>'
            )
        )
        for offset, (series_label, value) in enumerate(
            [
                ("Baseline", baseline),
                ("Citation-frontier", frontier),
                ("Justice-guarded", guarded),
            ]
        ):
            y = bar_y(row_index, offset)
            width_value = bar_width(value)
            svg_lines.append(
                (
                    f'<rect x="{left}" y="{y}" width="{chart_width}" '
                    'height="12" rx="6" fill="#f8fafc"/>'
                )
            )
            svg_lines.append(
                (
                    f'<rect x="{left}" y="{y}" width="{width_value:.1f}" '
                    f'height="12" rx="6" fill="{BAR_COLORS[series_label]}"/>'
                )
            )
            svg_lines.append(
                (
                    f'<text x="{left + width_value + 8:.1f}" y="{y + 10}" '
                    f'font-size="12" font-family="{SANS_STACK}" '
                    f'fill="#334155">{series_label} {_pct(value)}</text>'
                )
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg_lines) + "\n</svg>\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline-adapter-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--frontier-adapter-run-dir",
        default=(
            REPO_ROOT
            / "runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier_adapter_test/latest"
        ),
        type=Path,
    )
    parser.add_argument(
        "--guarded-train-run-dir",
        default=(
            REPO_ROOT
            / "runs/christian_virtue/qwen2_5_1_5b_instruct/justice_guarded_citation_repair/latest"
        ),
        type=Path,
    )
    parser.add_argument(
        "--guarded-adapter-run-dir",
        default=(
            REPO_ROOT
            / (
                "runs/christian_virtue/qwen2_5_1_5b_instruct/"
                "justice_guarded_citation_repair_adapter_test/latest"
            )
        ),
        type=Path,
    )
    parser.add_argument(
        "--output",
        default=(
            REPO_ROOT
            / (
                "docs/reports/"
                "christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md"
            )
        ),
        type=Path,
    )
    parser.add_argument(
        "--figure-path",
        default=(
            REPO_ROOT
            / (
                "docs/reports/assets/"
                "christian_virtue_qwen2_5_1_5b_justice_guarded_tradeoffs.svg"
            )
        ),
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    baseline_adapter_dir = args.baseline_adapter_run_dir.resolve()
    frontier_adapter_dir = args.frontier_adapter_run_dir.resolve()
    guarded_train_dir = args.guarded_train_run_dir.resolve()
    guarded_adapter_dir = args.guarded_adapter_run_dir.resolve()

    baseline_metrics = _load_json(baseline_adapter_dir / "metrics.json")
    frontier_metrics = _load_json(frontier_adapter_dir / "metrics.json")
    guarded_metrics = _load_json(guarded_adapter_dir / "metrics.json")
    train_metadata = _load_json(guarded_train_dir / "train_metadata.json")
    train_config = _load_yaml(guarded_train_dir / "config_snapshot.yaml")
    figure_path = _relative_from(args.output.parent, args.figure_path)
    train_quota_json = json.dumps(
        train_metadata["train_task_type_quotas"],
        sort_keys=True,
    )
    protected_bucket_count = len(
        cast(list[dict[str, Any]], train_metadata["train_protected_buckets"])
    )

    comparison_rows = [
        (
            "Overall held-out exact citation",
            float(baseline_metrics["overall"]["citation_exact_match"]),
            float(frontier_metrics["overall"]["citation_exact_match"]),
            float(guarded_metrics["overall"]["citation_exact_match"]),
        ),
        (
            "Justice core",
            _tract_metric(baseline_metrics, "justice_core"),
            _tract_metric(frontier_metrics, "justice_core"),
            _tract_metric(guarded_metrics, "justice_core"),
        ),
        (
            "Strong textual inference",
            _support_metric(baseline_metrics, "strong_textual_inference"),
            _support_metric(frontier_metrics, "strong_textual_inference"),
            _support_metric(guarded_metrics, "strong_textual_inference"),
        ),
        (
            "Passage-grounded doctrinal QA",
            _task_metric(baseline_metrics, "passage_grounded_doctrinal_qa"),
            _task_metric(frontier_metrics, "passage_grounded_doctrinal_qa"),
            _task_metric(guarded_metrics, "passage_grounded_doctrinal_qa"),
        ),
        (
            "Reviewed relation explanation",
            _task_metric(baseline_metrics, "reviewed_relation_explanation"),
            _task_metric(frontier_metrics, "reviewed_relation_explanation"),
            _task_metric(guarded_metrics, "reviewed_relation_explanation"),
        ),
        (
            "Virtue concept explanation",
            _task_metric(baseline_metrics, "virtue_concept_explanation"),
            _task_metric(frontier_metrics, "virtue_concept_explanation"),
            _task_metric(guarded_metrics, "virtue_concept_explanation"),
        ),
        (
            "Citation-grounded moral answer",
            _task_metric(baseline_metrics, "citation_grounded_moral_answer"),
            _task_metric(frontier_metrics, "citation_grounded_moral_answer"),
            _task_metric(guarded_metrics, "citation_grounded_moral_answer"),
        ),
    ]
    _write_triptych_svg(comparison_rows, args.figure_path.resolve())

    duration_minutes = _duration_minutes(
        str(train_metadata["start_time"]),
        str(train_metadata["end_time"]),
    )
    lines = [
        "# Justice-Guarded Citation-Repair Report",
        "",
        "This follow-up keeps the same tiny local `Qwen/Qwen2.5-1.5B-Instruct` budget as the",
        "canonical baseline and the citation-frontier run, but adds four protected justice buckets",
        "inside the deterministic subset selector. The result is the strongest same-budget overall",
        "held-out exact citation score so far, while recovering most of the `justice_core` and",
        "`strong_textual_inference` damage from the citation-frontier recipe.",
        "",
        f"![Justice-guarded tradeoff summary]({figure_path})",
        "",
        "*Figure 1. Same-budget comparison across the canonical baseline, the citation-frontier",
        "follow-up, and the justice-guarded recipe. The justice-guarded run is the best overall",
        "exact-citation configuration in this local 1.5B family, but it gives back the frontier's",
        "small gain on `citation_grounded_moral_answer`.*",
        "",
        "## Setup",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Model | `{train_config['model_name_or_path']}` |",
        f"| Train run | `{_run_id(guarded_train_dir)}` |",
        f"| Adapter eval run | `{_run_id(guarded_adapter_dir)}` |",
        f"| Training duration | `{duration_minutes:.1f}` minutes |",
        f"| Train subset strategy | `{train_metadata['train_subset_strategy']}` |",
        f"| Eval subset strategy | `{train_metadata['eval_subset_strategy']}` |",
        f"| Train quotas | `{train_quota_json}` |",
        (
            f"| Protected buckets | `{protected_bucket_count}` justice-specific "
            "reservations |"
        ),
        f"| Config snapshot | `{_relative(guarded_train_dir / 'config_snapshot.yaml')}` |",
        f"| Train metadata | `{_relative(guarded_train_dir / 'train_metadata.json')}` |",
        f"| Adapter metrics | `{_relative(guarded_adapter_dir / 'metrics.json')}` |",
        "",
        "## Result Table",
        "",
        "| Slice | Baseline | Citation-frontier | Justice-guarded |",
        "| --- | ---: | ---: | ---: |",
    ]
    for label, baseline, frontier, guarded in comparison_rows:
        lines.append(
            f"| {label} | `{_pct(baseline)}` | `{_pct(frontier)}` | `{_pct(guarded)}` |"
        )

    lines.extend(
        [
            "",
            "## What Changed",
            "",
            "- Overall held-out exact citation improved from `36.5%` on the canonical baseline and",
            "  `38.6%` on citation-frontier to `39.1%` here.",
            (
                "- `justice_core` recovered from the frontier collapse "
                "(`19.0%`) to `42.9%`, which is much"
            ),
            "  closer to the canonical baseline (`50.0%`).",
            (
                "- `strong_textual_inference` recovered from `20.0%` on "
                "citation-frontier to `42.9%`, again"
            ),
            "  much closer to the canonical baseline (`48.6%`).",
            (
                "- The biggest new gain is `passage_grounded_doctrinal_qa`, "
                "which reached `46.3%` exact"
            ),
            "  citation compared with `32.8%` on the baseline and `37.3%` on citation-frontier.",
            (
                "- `virtue_concept_explanation` also improved to `71.9%`, "
                "the strongest same-budget result"
            ),
            "  in this local 1.5B series.",
            "",
            "## What It Did Not Fix",
            "",
            (
                "- `citation_grounded_moral_answer` fell back to `0.0%` "
                "exact stable-id recovery after the"
            ),
            "  frontier recipe's small `3.0%` gain.",
            (
                "- `reviewed_relation_explanation` dropped from the canonical "
                "baseline's `62.7%` to `55.2%`."
            ),
            "- The successful rerun used explicit MPS env overrides",
            (
                "  (`PYTORCH_ENABLE_MPS_FALLBACK=1`, "
                "`PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`) after an earlier"
            ),
            (
                "  MPS kernel stall, so this result is reproducible but not "
                "yet a cleaner public default than"
            ),
            "  `local-baseline`.",
            "",
            "## Interpretation",
            "",
            (
                "This justice-guarded recipe is a meaningful same-budget "
                "follow-up, not just a safer frontier"
            ),
            (
                "variant. It demonstrates that the subset selector can be "
                "taught to protect doctrinally"
            ),
            (
                "important justice/STI slices while still moving the overall "
                "held-out benchmark upward."
            ),
            (
                "But it also shows that the repo's hardest remaining problem "
                "is still user-style moral QA with"
            ),
            (
                "stable passage-id recovery. The next research step is "
                "therefore an accuracy-first hybrid recipe that keeps"
            ),
            (
                "the justice guard while restoring at least some of the "
                "frontier's `citation_grounded_moral_answer` gain."
            ),
            "",
            "## Reproduce",
            "",
            "```bash",
            "make run-christian-virtue-qwen2-5-1-5b-justice-guarded-loop",
            "```",
            "",
            "The official justice-guarded wrapper now exports the required MPS safety env",
            "overrides automatically before training and adapter evaluation.",
            "",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(
        json.dumps(
            {
                "figure_path": str(args.figure_path.resolve()),
                "output_path": str(args.output.resolve()),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
