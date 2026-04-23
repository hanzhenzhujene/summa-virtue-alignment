"""Assemble a curated report for the completed local citation-frontier follow-up run."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

from summa_moral_graph.sft.frontier import analyze_citation_frontier, write_citation_frontier_svg
from summa_moral_graph.sft.utils import tract_display_name
from summa_moral_graph.utils.paths import REPO_ROOT


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


def _metric(metrics: dict[str, Any], bucket: str, key: str, metric_name: str) -> float:
    bucket_payload = cast(dict[str, Any], metrics[bucket])
    row = cast(dict[str, Any], bucket_payload[key])
    return float(row[metric_name])


def _support_type_label(value: str) -> str:
    return value.replace("_", " ").title()


def _bucket_label(bucket: str, key: str) -> str:
    if bucket == "by_tract":
        return tract_display_name(key)
    if bucket == "by_support_type":
        return _support_type_label(key)
    return key.replace("_", " ").title()


def _regression_label(key: str) -> str:
    if key in {"explicit_textual", "strong_textual_inference"}:
        return _bucket_label("by_support_type", key)
    return _bucket_label("by_tract", key)


def _top_delta_rows(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    *,
    bucket: str,
    positive: bool,
    limit: int,
) -> list[tuple[str, float, float, float]]:
    baseline_bucket = cast(dict[str, Any], baseline_metrics.get(bucket, {}))
    candidate_bucket = cast(dict[str, Any], candidate_metrics.get(bucket, {}))
    rows: list[tuple[str, float, float, float]] = []
    for key in sorted(set(baseline_bucket) | set(candidate_bucket)):
        baseline_exact = float(
            cast(dict[str, Any], baseline_bucket.get(key, {})).get("citation_exact_match", 0.0)
            or 0.0
        )
        candidate_exact = float(
            cast(dict[str, Any], candidate_bucket.get(key, {})).get("citation_exact_match", 0.0)
            or 0.0
        )
        delta = candidate_exact - baseline_exact
        if positive and delta <= 0:
            continue
        if not positive and delta >= 0:
            continue
        rows.append((str(key), baseline_exact, candidate_exact, delta))
    rows.sort(key=lambda row: row[3], reverse=positive)
    return rows[:limit]


def _frontier_delta_row(
    label: str,
    baseline_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    metric_name: str,
) -> str:
    baseline_value = float(baseline_summary[metric_name])
    candidate_value = float(candidate_summary[metric_name])
    return (
        f"| {label} | `{_pct(baseline_value)}` | `{_pct(candidate_value)}` | "
        f"`{_pct(candidate_value - baseline_value)}` |"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-dir",
        default=REPO_ROOT / "data/processed/sft/exports/christian_virtue_v1",
        type=Path,
    )
    parser.add_argument(
        "--base-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/base_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--baseline-adapter-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/adapter_test/latest",
        type=Path,
    )
    parser.add_argument(
        "--frontier-train-run-dir",
        default=REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct/citation_frontier/latest",
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
        "--output",
        default=(
            REPO_ROOT / "docs/reports/christian_virtue_qwen2_5_1_5b_citation_frontier_report.md"
        ),
        type=Path,
    )
    parser.add_argument(
        "--figure-path",
        default=(
            REPO_ROOT
            / (
                "docs/reports/assets/"
                "christian_virtue_qwen2_5_1_5b_citation_frontier_followup_modes.svg"
            )
        ),
        type=Path,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frontier_train_dir = args.frontier_train_run_dir.resolve()
    frontier_adapter_dir = args.frontier_adapter_run_dir.resolve()
    baseline_adapter_dir = args.baseline_adapter_run_dir.resolve()
    base_run_dir = args.base_run_dir.resolve()

    train_config = _load_yaml(frontier_train_dir / "config_snapshot.yaml")
    train_metadata = _load_json(frontier_train_dir / "train_metadata.json")
    baseline_metrics = _load_json(baseline_adapter_dir / "metrics.json")
    frontier_metrics = _load_json(frontier_adapter_dir / "metrics.json")

    baseline_frontier = analyze_citation_frontier(
        dataset_dir=args.dataset_dir.resolve(),
        base_predictions_path=(base_run_dir / "predictions.jsonl").resolve(),
        adapter_predictions_path=(baseline_adapter_dir / "predictions.jsonl").resolve(),
    )
    frontier_audit = analyze_citation_frontier(
        dataset_dir=args.dataset_dir.resolve(),
        base_predictions_path=(base_run_dir / "predictions.jsonl").resolve(),
        adapter_predictions_path=(frontier_adapter_dir / "predictions.jsonl").resolve(),
    )

    duration_minutes = _duration_minutes(
        str(train_metadata["start_time"]),
        str(train_metadata["end_time"]),
    )
    task_rows = [
        (
            "Held-out benchmark exact citation",
            float(baseline_metrics["overall"]["citation_exact_match"]),
            float(frontier_metrics["overall"]["citation_exact_match"]),
        ),
        (
            "Citation-grounded moral answer",
            _metric(
                baseline_metrics,
                "by_task_type",
                "citation_grounded_moral_answer",
                "citation_exact_match",
            ),
            _metric(
                frontier_metrics,
                "by_task_type",
                "citation_grounded_moral_answer",
                "citation_exact_match",
            ),
        ),
        (
            "Passage-grounded doctrinal QA",
            _metric(
                baseline_metrics,
                "by_task_type",
                "passage_grounded_doctrinal_qa",
                "citation_exact_match",
            ),
            _metric(
                frontier_metrics,
                "by_task_type",
                "passage_grounded_doctrinal_qa",
                "citation_exact_match",
            ),
        ),
        (
            "Reviewed relation explanation",
            _metric(
                baseline_metrics,
                "by_task_type",
                "reviewed_relation_explanation",
                "citation_exact_match",
            ),
            _metric(
                frontier_metrics,
                "by_task_type",
                "reviewed_relation_explanation",
                "citation_exact_match",
            ),
        ),
        (
            "Virtue concept explanation",
            _metric(
                baseline_metrics,
                "by_task_type",
                "virtue_concept_explanation",
                "citation_exact_match",
            ),
            _metric(
                frontier_metrics,
                "by_task_type",
                "virtue_concept_explanation",
                "citation_exact_match",
            ),
        ),
    ]
    strongest_gains = _top_delta_rows(
        baseline_metrics,
        frontier_metrics,
        bucket="by_tract",
        positive=True,
        limit=4,
    )
    regressions = (
        _top_delta_rows(
            baseline_metrics,
            frontier_metrics,
            bucket="by_support_type",
            positive=False,
            limit=2,
        )
        + _top_delta_rows(
            baseline_metrics,
            frontier_metrics,
            bucket="by_tract",
            positive=False,
            limit=2,
        )
    )
    frontier_base_summary = cast(dict[str, Any], baseline_frontier["overall"]["adapter"])
    frontier_candidate_summary = cast(dict[str, Any], frontier_audit["overall"]["adapter"])
    figure_path = args.figure_path.resolve()
    figure_asset_path = Path(f"./assets/{figure_path.name}")

    write_citation_frontier_svg(
        frontier_audit,
        figure_path,
        subtitle="Completed same-budget citation-frontier follow-up on the held-out test split",
        summary_text=(
            "Citation-frontier training raises citation signal sharply on the hardest held-out "
            "moral QA slice, while exact stable-id recovery reaches a first non-zero result."
        ),
    )

    lines = [
        "# Christian Virtue Citation-Frontier Follow-Up",
        "",
        "## Why This Run Exists",
        "",
        "The canonical `local-baseline` proved that the Christian virtue dataset can move a small "
        "model toward better Thomist moral virtue behavior, but it left one conspicuous gap: "
        "`citation_grounded_moral_answer` stayed at `0.0%` exact stable-id recovery on held-out "
        "user-style moral prompts.",
        "",
        "This follow-up keeps the same small Apple-Silicon local budget and the same dataset, but "
        "shifts more of the tiny train subset toward citation-grounded moral answers. The point "
        "is not bigger compute. The point is to test whether same-budget mixture steering can "
        "improve traceable moral QA without changing the theological scope.",
        "",
        "## Canonical Scope",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Dataset | `{_relative(args.dataset_dir)}` |",
        f"| Base model | `{train_metadata['model_name_or_path']}` |",
        f"| Runtime | `{train_metadata['resolved_device']}` / `{train_metadata['torch_dtype']}` |",
        f"| Train run id | `{train_metadata['run_id']}` |",
        f"| Base test run id | `{_run_id(base_run_dir)}` |",
        f"| Local-baseline adapter run id | `{_run_id(baseline_adapter_dir)}` |",
        f"| Citation-frontier adapter run id | `{_run_id(frontier_adapter_dir)}` |",
        f"| Git commit | `{train_metadata['git_commit']}` |",
        f"| Wall time | `{duration_minutes:.1f}` minutes |",
        f"| Max steps | `{train_config['max_steps']}` |",
        f"| Train examples | `{train_metadata['train_examples']}` |",
        f"| Eval examples | `{train_metadata['eval_examples']}` |",
        f"| Train subset strategy | `{train_metadata['train_subset_strategy']}` |",
        "",
        "### Citation-Frontier Train Mixture",
        "",
        "| Task family | Quota |",
        "| --- | ---: |",
    ]
    for task_name, quota in cast(dict[str, int], train_metadata["train_task_type_quotas"]).items():
        lines.append(f"| `{task_name}` | `{quota}` |")
    lines.extend(
        [
            "",
            "This same-budget run kept the deterministic tract balancing intact: the selected "
            "train subset remained evenly distributed across the eight virtue tracts, while half "
            "of the tiny local budget moved onto `citation_grounded_moral_answer`.",
            "",
            "## Headline Outcome",
            "",
            "| Slice | Local-baseline adapter | Citation-frontier adapter | Delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for label, baseline_value, candidate_value in task_rows:
        lines.append(
            f"| {label} | `{_pct(baseline_value)}` | `{_pct(candidate_value)}` | "
            f"`{_pct(candidate_value - baseline_value)}` |"
        )
    lines.extend(
        [
            "",
            "Three of the four held-out task families moved upward, while `reviewed_relation_"
            "explanation` slipped only slightly. That pattern still supports the main point: the "
            "mixture change did more than merely overfit the target task.",
            "",
            "## Strongest Gains",
            "",
            "| Slice | Local-baseline adapter | Citation-frontier adapter | Delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for key, baseline_value, candidate_value, delta in strongest_gains:
        lines.append(
            f"| {_bucket_label('by_tract', key)} | `{_pct(baseline_value)}` | "
            f"`{_pct(candidate_value)}` | "
            f"`{_pct(delta)}` |"
        )
    lines.extend(
        [
            "",
            "## Important Tradeoffs",
            "",
            "| Slice | Local-baseline adapter | Citation-frontier adapter | Delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    seen_regressions: set[str] = set()
    for key, baseline_value, candidate_value, delta in regressions:
        if key in seen_regressions:
            continue
        seen_regressions.add(key)
        lines.append(
            f"| {_regression_label(key)} | "
            f"`{_pct(baseline_value)}` | `{_pct(candidate_value)}` | "
            f"`{_pct(delta)}` |"
        )
    lines.extend(
        [
            "",
            "The important caution is that the run is better overall but not uniformly better. "
            "The citation-heavy mixture helps the main bottleneck, yet it clearly harms "
            "`justice_core` and `strong_textual_inference`. So this is a real follow-up result, "
            "not an automatic replacement for the public baseline.",
            "",
            "## Hardest User-Style Moral QA After The Follow-Up",
            "",
            (
                "| Citation-grounded moral answer frontier | Local-baseline adapter | "
                "Citation-frontier adapter | Delta |"
            ),
            "| --- | ---: | ---: | ---: |",
            _frontier_delta_row(
                "Exact stable id",
                frontier_base_summary,
                frontier_candidate_summary,
                "exact_stable_id_match_rate",
            ),
            _frontier_delta_row(
                "Any citation signal",
                frontier_base_summary,
                frontier_candidate_summary,
                "any_citation_signal_rate",
            ),
            _frontier_delta_row(
                "Wrong stable id",
                frontier_base_summary,
                frontier_candidate_summary,
                "wrong_stable_id_rate",
            ),
            _frontier_delta_row(
                "No citation signal",
                frontier_base_summary,
                frontier_candidate_summary,
                "no_citation_signal_rate",
            ),
            "",
            f"![Citation frontier failure modes]({figure_asset_path.as_posix()})",
            "",
            "*Figure 1. Failure-mode breakdown from the untuned model to the completed same-budget "
            "`citation-frontier` adapter on the hardest held-out moral-QA slice. The gain is "
            "mostly citation-seeking behavior; the main remaining error is wrong-id selection "
            "rather than total citation silence.*",
            "",
            "The headline tables above compare `local-baseline` against `citation-frontier`. "
            "Figure 1 isolates the narrower shift from the untouched model to the "
            "`citation-frontier` adapter so the failure-mode story is visually easier to read.",
            "",
            "The follow-up did achieve the first non-zero exact stable-id recovery on this hard "
            "slice. But the dominant remaining error is now clear: the model usually tries to "
            "cite, yet most cited ids are still the wrong ones.",
            "",
            "## Interpretation",
            "",
            "1. The same-budget local recipe is steerable: changing only the train mixture moved "
            f"the held-out test set from `{_pct(task_rows[0][1])}` to `{_pct(task_rows[0][2])}` "
            "exact citation overall.",
            "2. The hardest user-style task is no longer completely flat: exact stable-id recovery "
            "on `citation_grounded_moral_answer` rose from `0.0%` to `3.0%`.",
            "3. The run is not yet a better public baseline, because the gains came with a severe "
            "drop on `justice_core` and `strong_textual_inference`.",
            "4. That means the next research step should preserve the new citation-seeking "
            "behavior while reintroducing protection for the slices that regressed.",
            "",
            "## Next Step After Citation-Frontier",
            "",
            "That follow-up has now been completed in "
            "[`christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md`]"
            "(./christian_virtue_qwen2_5_1_5b_justice_guarded_citation_repair_report.md).",
            "From the perspective of this frontier report, the next experiment was a "
            "justice-guarded citation-repair recipe:",
            "",
            "- keep the Christian virtue dataset fixed",
            "- keep the same small Apple-Silicon budget",
            "- preserve the citation-heavy train emphasis",
            "- explicitly protect `justice_core` and `strong_textual_inference` so the model does "
            "not trade away doctrinal precision for citation activity",
            "- treat success as a dual condition: improve `citation_grounded_moral_answer` further "
            "while recovering the baseline-level strength of the regressed slices",
            "",
            "For now, the correct public reading is modest and strong: the dataset is rich enough "
            "that even a tiny same-budget mixture change can move a small model in a measurable, "
            "theologically relevant direction.",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output_path": str(args.output),
                "frontier_train_run_id": train_metadata["run_id"],
                "frontier_adapter_run_id": _run_id(frontier_adapter_dir),
                "figure_path": str(figure_path),
                "overall_exact_delta": (
                    float(frontier_metrics["overall"]["citation_exact_match"])
                    - float(baseline_metrics["overall"]["citation_exact_match"])
                ),
                "frontier_exact_stable_id_rate": float(
                    frontier_candidate_summary["exact_stable_id_match_rate"]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
