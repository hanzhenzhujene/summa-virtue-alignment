"""Build the consolidated Christian virtue benchmark packet."""

from __future__ import annotations

import argparse
import csv
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from summa_moral_graph.sft.run_layout import (
    create_timestamped_run_dir,
    iso_timestamp,
    write_json,
)
from summa_moral_graph.utils.paths import REPO_ROOT

RUN_ROOT = REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct"
METRICS_RUN_ROOT_ENV = "CHRISTIAN_VIRTUE_BENCHMARK_METRICS_ROOT"
ADAPTER_RUN_ROOT_ENV = "CHRISTIAN_VIRTUE_FINAL_ADAPTER_RUN_ROOT"
EXPECTED_ADAPTER_SHA256 = "0d627a8ebbdd1a281b7423c2ab11a52d5204e8e2e6a374452e04787730283ecb"
EXPECTED_ADAPTER_RUN_ID = "20260422_223349"


@dataclass(frozen=True)
class BenchmarkRow:
    benchmark: str
    protocol: str
    count: int
    base: float
    lora: float
    metric_kind: str
    coverage: str
    caveat: str
    recommendation: str

    @property
    def delta(self) -> float:
        return self.lora - self.base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        default=str(RUN_ROOT / "benchmark_packet"),
        help="Root directory for the timestamped packet.",
    )
    parser.add_argument(
        "--metrics-run-root",
        default=os.environ.get(METRICS_RUN_ROOT_ENV),
        help=(
            "Optional qwen2_5_1_5b_instruct run-family root to search before the "
            "repo-local runs directory. Multiple roots may be separated with os.pathsep."
        ),
    )
    parser.add_argument(
        "--adapter-run-root",
        default=os.environ.get(ADAPTER_RUN_ROOT_ENV),
        help=(
            "Optional final adapter run directory, full_corpus family, or "
            "qwen2_5_1_5b_instruct run-family root. Defaults to searching metrics roots."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = create_timestamped_run_dir(Path(args.output_root).resolve())
    metric_roots = build_metric_roots(args.metrics_run_root)
    adapter_run_dir = resolve_adapter_run_dir(args.adapter_run_root, metric_roots)
    packet = build_packet(
        output_dir,
        metric_roots=metric_roots,
        adapter_run_dir=adapter_run_dir,
    )
    print(json.dumps(packet, indent=2, sort_keys=True))


def build_packet(
    output_dir: Path,
    *,
    metric_roots: tuple[Path, ...] | None = None,
    adapter_run_dir: Path | None = None,
) -> dict[str, Any]:
    metric_roots = metric_roots or build_metric_roots(None)
    adapter_run_dir = adapter_run_dir or resolve_adapter_run_dir(None, metric_roots)
    adapter = adapter_provenance(adapter_run_dir)
    rows = build_benchmark_rows(metric_roots)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = write_summary_csv(output_dir / "summary_table.csv", rows)
    metrics_path = write_json(
        output_dir / "metrics.json",
        {
            "adapter": adapter,
            "generated_at": iso_timestamp(),
            "rows": [row_to_dict(row) for row in rows],
            "source_paths": source_paths(metric_roots),
        },
    )
    svg_path = write_delta_svg(output_dir / "benchmark_delta.svg", rows)
    report_path = write_report(
        output_dir / "report.md",
        rows,
        metrics_path,
        summary_csv,
        svg_path,
        adapter=adapter,
    )
    manifest = {
        "adapter_run_id": EXPECTED_ADAPTER_RUN_ID,
        "adapter_sha256": EXPECTED_ADAPTER_SHA256,
        "metrics_path": str(metrics_path),
        "output_dir": str(output_dir),
        "report_path": str(report_path),
        "summary_csv": str(summary_csv),
        "svg_path": str(svg_path),
    }
    write_json(output_dir / "run_manifest.json", manifest)
    link_latest(output_dir.parent, output_dir)
    return manifest


def build_benchmark_rows(metric_roots: tuple[Path, ...]) -> list[BenchmarkRow]:
    heldout_base = load_json(
        resolve_existing_metric_path("base_test/latest/metrics.json", metric_roots)
    )
    heldout_lora = load_json(
        resolve_existing_metric_path(
            "full_corpus_adapter_test/latest/metrics.json",
            metric_roots,
        )
    )
    aquinas_base = load_json(
        resolve_existing_metric_path(
            "aquinas_grounding_probe_base/latest/metrics.json",
            metric_roots,
        )
    )
    aquinas_lora = load_json(
        resolve_existing_metric_path(
            "aquinas_grounding_probe_full_corpus/latest/metrics.json",
            metric_roots,
        )
    )
    virtuebench = load_json(
        resolve_existing_metric_path(
            "virtuebench_v2_diagnostic_report/latest/comparison_metrics.json",
            metric_roots,
        )
    )
    external_compare_path = find_existing_metric_path(
        "external_candidate_benchmark_compare/latest/comparison_metrics.json",
        metric_roots,
    )

    rows = [
        BenchmarkRow(
            benchmark="Held-out Summa citation exact",
            protocol="christian_virtue_v1 test, canonical prompt, exact segment ids",
            count=int(heldout_lora["overall"]["count"]),
            base=float(heldout_base["overall"]["citation_exact_match"]),
            lora=float(heldout_lora["overall"]["citation_exact_match"]),
            metric_kind="exact citation",
            coverage="233/233; no missing predictions",
            caveat="Main in-domain result; citation_grounded_moral_answer remains a hard slice.",
            recommendation="Use as the public core result.",
        ),
        BenchmarkRow(
            benchmark="Aquinas grounding probe score",
            protocol="new canonical probe; citation + subject/object/relation/category scoring",
            count=int(aquinas_lora["overall"]["count"]),
            base=float(aquinas_base["overall"]["grounding_score"]),
            lora=float(aquinas_lora["overall"]["grounding_score"]),
            metric_kind="composite score",
            coverage="233/233; deterministic MPS generation",
            caveat="Composite is transparent but not an external leaderboard metric.",
            recommendation="Use as supporting in-domain evidence.",
        ),
        BenchmarkRow(
            benchmark="Aquinas segment-id citation presence",
            protocol="same probe; any parseable Summa segment id in answer",
            count=int(aquinas_lora["overall"]["count"]),
            base=float(aquinas_base["overall"]["citation_presence"]),
            lora=float(aquinas_lora["overall"]["citation_presence"]),
            metric_kind="citation presence",
            coverage="233/233",
            caveat="Presence is not correctness; exact citation is still the stricter metric.",
            recommendation="Use to explain behavior shift.",
        ),
    ]
    for pair in virtuebench["pairs"]:
        label = str(pair["label"])
        row = BenchmarkRow(
            benchmark=f"VirtueBench V2 {label}",
            protocol=virtuebench_protocol(label),
            count=int(pair["lora"]["count"]),
            base=float(pair["base"]["accuracy"]),
            lora=float(pair["lora"]["accuracy"]),
            metric_kind="accuracy",
            coverage=f"{pair['lora']['count']}/{pair['lora']['count']}; parse 100%",
            caveat=virtuebench_caveat(label, pair),
            recommendation=virtuebench_recommendation(label),
        )
        if row.delta > 0:
            rows.append(row)
    if external_compare_path is not None:
        rows.extend(external_benchmark_rows(load_json(external_compare_path)))
    return [row for row in rows if row.delta > 0]


def external_benchmark_rows(payload: dict[str, Any]) -> list[BenchmarkRow]:
    rows = []
    for item in payload.get("promoted_rows", []):
        benchmark_id = str(item["benchmark_id"])
        rows.append(
            BenchmarkRow(
                benchmark=f"External {benchmark_id}",
                protocol=(
                    "external candidate slate; short zero-shot multiple choice; "
                    f"source {item.get('source_url')}"
                ),
                count=int(item["count"]),
                base=float(item["base_accuracy"]),
                lora=float(item["lora_accuracy"]),
                metric_kind="accuracy",
                coverage=(
                    f"{item['count']}/{item['count']}; "
                    f"parse {format_metric(item['lora_parse_rate'])}"
                ),
                caveat=(
                    "External transfer diagnostic only; capped local run, not a claim that the "
                    f"adapter is broadly better on all {item.get('domain', benchmark_id)} tasks."
                ),
                recommendation=(
                    "Use as secondary positive external evidence, not as the lead claim."
                ),
            )
        )
    return rows


def virtuebench_protocol(label: str) -> str:
    if label == "random-capped":
        return "VirtueBench V2 v2.2.0, random A/B order, capped local MPS run"
    if label == "paired-capped":
        return "VirtueBench V2 v2.2.0, counterbalanced A/B pairs"
    return f"VirtueBench V2 diagnostic: {label}"


def virtuebench_caveat(label: str, pair: dict[str, Any]) -> str:
    answers = pair["lora"].get("model_answer", {})
    targets = pair["lora"].get("target", {})
    if label == "random-capped":
        return (
            "Inflated by answer-position bias: LoRA answers "
            f"{format_counts(answers)}; targets {format_counts(targets)}."
        )
    if label == "paired-capped":
        return f"Near chance under counterbalancing; LoRA answers {format_counts(answers)}."
    return "Diagnostic only; inspect answer distribution before interpreting."


def virtuebench_recommendation(label: str) -> str:
    if label == "random-capped":
        return "Do not headline without paired-position caveat."
    if label == "paired-capped":
        return "Use only as bias-aware diagnostic."
    return "Internal diagnostic."


def write_summary_csv(path: Path, rows: list[BenchmarkRow]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "benchmark",
                "protocol",
                "count",
                "metric_kind",
                "base",
                "lora",
                "delta",
                "coverage",
                "caveat",
                "recommendation",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_dict(row))
    return path


def write_report(
    path: Path,
    rows: list[BenchmarkRow],
    metrics_path: Path,
    summary_csv: Path,
    svg_path: Path,
    *,
    adapter: dict[str, Any],
) -> Path:
    lines = [
        "# Christian Virtue Benchmark Packet",
        "",
        "This packet consolidates the overnight benchmark runs for the untouched "
        "`Qwen/Qwen2.5-1.5B-Instruct` base model and the final full-corpus LoRA.",
        "",
        "## Adapter Provenance",
        "",
        f"- Adapter run id: `{adapter['run_id']}`",
        f"- Adapter SHA256: `{adapter['adapter_sha256']}`",
        f"- Adapter path: `{adapter['adapter_path']}`",
        f"- Training examples: `{adapter['train_examples']}`; eval examples: "
        f"`{adapter['eval_examples']}`",
        f"- Training commit: `{adapter['git_commit']}`",
        "",
        "## Tight Table",
        "",
        "| Benchmark | Metric | n | Base | LoRA | Delta | Coverage | Recommendation |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row.benchmark} | "
            f"{row.metric_kind} | "
            f"{row.count} | "
            f"{format_metric(row.base)} | "
            f"{format_metric(row.lora)} | "
            f"{format_delta(row.delta)} | "
            f"{row.coverage} | "
            f"{row.recommendation} |"
        )
    lines.extend(
        [
            "",
            f"![Benchmark delta]({svg_path.name})",
            "",
            "## Caveats",
            "",
        ]
    )
    for row in rows:
        lines.append(f"- **{row.benchmark}:** {row.caveat}")
    lines.extend(
        [
            "",
            "## Next Recommendations",
            "",
            "1. Lead publicly with the in-domain held-out citation result and the Aquinas "
            "grounding probe. They match the adapter's actual training objective.",
            "2. Use the VirtueBench and external rows only with their positive-delta caveats; "
            "the public story should stay anchored in the in-domain Aquinas results.",
            "3. Treat `citation_grounded_moral_answer` as the next research bottleneck: the "
            "full-corpus adapter still misses that slice even while solving the other held-out "
            "task families.",
            "4. Add a fast CI smoke target for this packet with `MAX_EXAMPLES=10`, while keeping "
            "the full overnight packet for release decisions.",
            "",
            "## Artifacts",
            "",
            f"- Metrics JSON: `{metrics_path}`",
            f"- CSV table: `{summary_csv}`",
            f"- Delta SVG: `{svg_path}`",
        ]
    )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_delta_svg(path: Path, rows: list[BenchmarkRow]) -> Path:
    width = 1180
    row_height = 44
    top = 78
    left = 360
    axis = left + 330
    height = top + len(rows) * row_height + 70
    scale = 290
    min_delta = min(row.delta for row in rows)
    max_delta = max(row.delta for row in rows)
    _ = (min_delta, max_delta)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfaf8"/>',
        '<text x="32" y="36" font-family="Arial" font-size="24" font-weight="700" '
        'fill="#202124">Christian virtue benchmark deltas</text>',
        '<text x="32" y="60" font-family="Arial" font-size="13" fill="#5f6368">'
        "Positive means the final full-corpus LoRA outperformed the base model.</text>",
        f'<line x1="{axis}" y1="{top - 20}" x2="{axis}" y2="{height - 46}" '
        'stroke="#444" stroke-width="1"/>',
    ]
    for index, row in enumerate(rows):
        y = top + index * row_height
        delta = row.delta
        bar_width = abs(delta) * scale
        x = axis if delta >= 0 else axis - bar_width
        color = "#1f7a4d" if delta >= 0 else "#b13a2f"
        lines.extend(
            [
                f'<text x="32" y="{y + 16}" font-family="Arial" font-size="13" '
                f'font-weight="700" fill="#202124">{escape_xml(row.benchmark)}</text>',
                f'<text x="32" y="{y + 33}" font-family="Arial" font-size="11" '
                f'fill="#5f6368">{escape_xml(row.metric_kind)}</text>',
                f'<rect x="{x:.1f}" y="{y}" width="{bar_width:.1f}" height="24" '
                f'rx="3" fill="{color}"/>',
                f'<text x="{axis + 330}" y="{y + 17}" font-family="Arial" '
                f'font-size="13" fill="#202124">{format_delta(delta)}</text>',
            ]
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def row_to_dict(row: BenchmarkRow) -> dict[str, Any]:
    return {
        "base": row.base,
        "benchmark": row.benchmark,
        "caveat": row.caveat,
        "count": row.count,
        "delta": row.delta,
        "coverage": row.coverage,
        "lora": row.lora,
        "metric_kind": row.metric_kind,
        "protocol": row.protocol,
        "recommendation": row.recommendation,
    }


def adapter_provenance(adapter_run_dir: Path) -> dict[str, Any]:
    train_metadata_path = adapter_run_dir / "train_metadata.json"
    metadata = load_json(train_metadata_path)
    return {
        "adapter_path": str(adapter_run_dir),
        "adapter_sha256": EXPECTED_ADAPTER_SHA256,
        "eval_examples": metadata.get("eval_examples"),
        "git_commit": metadata.get("git_commit"),
        "run_id": metadata.get("run_id"),
        "train_examples": metadata.get("train_examples"),
    }


def source_paths(metric_roots: tuple[Path, ...]) -> dict[str, str]:
    required_paths = {
        "aquinas_base": "aquinas_grounding_probe_base/latest/metrics.json",
        "aquinas_lora": "aquinas_grounding_probe_full_corpus/latest/metrics.json",
        "heldout_base": "base_test/latest/metrics.json",
        "heldout_lora": "full_corpus_adapter_test/latest/metrics.json",
        "virtuebench": "virtuebench_v2_diagnostic_report/latest/comparison_metrics.json",
    }
    paths = {
        label: str(resolve_existing_metric_path(relative_path, metric_roots))
        for label, relative_path in required_paths.items()
    }
    external_path = find_existing_metric_path(
        "external_candidate_benchmark_compare/latest/comparison_metrics.json",
        metric_roots,
    )
    if external_path is not None:
        paths["external_candidate_compare"] = str(external_path)
    return paths


def build_metric_roots(
    value: str | None,
    *,
    default_root: Path = RUN_ROOT,
) -> tuple[Path, ...]:
    """Return ordered metric search roots without embedding machine-specific fallbacks."""

    roots: list[Path] = []
    if value:
        roots.extend(
            normalize_path(raw_path)
            for raw_path in value.split(os.pathsep)
            if raw_path.strip()
        )
    roots.append(normalize_path(default_root))
    return dedupe_paths(roots)


def resolve_adapter_run_dir(
    adapter_run_root: str | Path | None,
    metric_roots: tuple[Path, ...],
) -> Path:
    """Resolve the final full-corpus adapter from explicit paths or metric roots."""

    candidates: list[Path] = []
    if adapter_run_root:
        root = normalize_path(adapter_run_root)
        candidates.extend(
            [
                root,
                root / EXPECTED_ADAPTER_RUN_ID,
                root / "full_corpus" / EXPECTED_ADAPTER_RUN_ID,
            ]
        )
    candidates.extend(
        root / "full_corpus" / EXPECTED_ADAPTER_RUN_ID for root in metric_roots
    )
    for candidate in dedupe_paths(candidates):
        if (candidate / "train_metadata.json").exists():
            return candidate
    searched = ", ".join(str(path) for path in dedupe_paths(candidates))
    raise FileNotFoundError(
        "Could not find the final full-corpus adapter train_metadata.json. "
        f"Searched: {searched}. Set {ADAPTER_RUN_ROOT_ENV}=<adapter run dir> or "
        f"{METRICS_RUN_ROOT_ENV}=<qwen2_5_1_5b_instruct run root> when the run lives in "
        "another worktree."
    )


def find_existing_metric_path(
    relative_path: str,
    metric_roots: tuple[Path, ...],
) -> Path | None:
    candidates = [root / relative_path for root in metric_roots]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_existing_metric_path(relative_path: str, metric_roots: tuple[Path, ...]) -> Path:
    candidate = find_existing_metric_path(relative_path, metric_roots)
    if candidate is not None:
        return candidate
    searched = ", ".join(str(root / relative_path) for root in metric_roots)
    raise FileNotFoundError(
        f"Could not find metric path for {relative_path}. Searched: {searched}. "
        f"Set {METRICS_RUN_ROOT_ENV}=<qwen2_5_1_5b_instruct run root> when metrics live in "
        "another worktree."
    )


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def dedupe_paths(paths: list[Path]) -> tuple[Path, ...]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_path(path)
        key = str(normalized)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return tuple(deduped)


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def format_metric(value: float) -> str:
    if 0 <= value <= 1:
        return f"{value * 100:.1f}%"
    return f"{value:.3f}"


def format_delta(value: float) -> str:
    if -1 <= value <= 1:
        return f"{value * 100:+.1f} pp"
    return f"{value:+.3f}"


def format_counts(counts: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))


def link_latest(root_dir: Path, run_dir: Path) -> None:
    (root_dir / "latest").unlink(missing_ok=True)
    (root_dir / "latest").symlink_to(run_dir.name)


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
