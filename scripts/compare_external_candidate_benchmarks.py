"""Compare external candidate benchmark runs and promote only LoRA wins."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from summa_moral_graph.sft.run_layout import current_git_commit, generate_run_id, iso_timestamp
from summa_moral_graph.utils.paths import REPO_ROOT

LOCAL_15B_ROOT = REPO_ROOT / "runs" / "christian_virtue" / "qwen2_5_1_5b_instruct"
DEFAULT_OUTPUT_ROOT = LOCAL_15B_ROOT / "external_candidate_benchmark_compare"
BASE_COLOR = "#2563eb"
LORA_COLOR = "#0f766e"
TEXT_DARK = "#0f172a"
TEXT_MID = "#475569"
GRID = "#e2e8f0"
CARD_STROKE = "#d4d4d8"
SANS_STACK = "Helvetica, Arial, sans-serif"

BENCHMARK_NOTES = {
    "bible_biblical_literacy": {
        "domain": "Christian biblical literacy",
        "language": "en",
        "source": "https://huggingface.co/datasets/MushroomGecko/BIBLE",
    },
    "cbbq_christian_religion": {
        "domain": "Chinese Christian/religion bias QA",
        "language": "zh",
        "source": "https://huggingface.co/datasets/walledai/CBBQ",
    },
    "ceval_ideological_moral": {
        "domain": "Chinese ideological/moral cultivation exam",
        "language": "zh",
        "source": "https://huggingface.co/datasets/ceval/ceval-exam",
    },
    "cmoraleval_chinese_moral": {
        "domain": "Chinese moral scenarios",
        "language": "zh",
        "source": "https://github.com/tjunlp-lab/CMoralEval",
    },
    "mmlu_world_religions": {
        "domain": "World religions knowledge",
        "language": "en",
        "source": "https://huggingface.co/datasets/cais/mmlu",
    },
    "mmlu_moral_disputes": {
        "domain": "Moral disputes knowledge",
        "language": "en",
        "source": "https://huggingface.co/datasets/cais/mmlu",
    },
    "mmlu_moral_scenarios": {
        "domain": "Moral scenarios knowledge",
        "language": "en",
        "source": "https://huggingface.co/datasets/cais/mmlu",
    },
    "mmlu_philosophy": {
        "domain": "Philosophy knowledge",
        "language": "en",
        "source": "https://huggingface.co/datasets/cais/mmlu",
    },
    "mmlu_business_ethics": {
        "domain": "Business ethics knowledge",
        "language": "en",
        "source": "https://huggingface.co/datasets/cais/mmlu",
    },
    "mmmlu_zh_world_religions": {
        "domain": "Chinese MMMLU world religions",
        "language": "zh",
        "source": "https://huggingface.co/datasets/openai/MMMLU",
    },
    "mmmlu_zh_moral_disputes": {
        "domain": "Chinese MMMLU moral disputes",
        "language": "zh",
        "source": "https://huggingface.co/datasets/openai/MMMLU",
    },
    "mmmlu_zh_moral_scenarios": {
        "domain": "Chinese MMMLU moral scenarios",
        "language": "zh",
        "source": "https://huggingface.co/datasets/openai/MMMLU",
    },
    "mmmlu_zh_philosophy": {
        "domain": "Chinese MMMLU philosophy",
        "language": "zh",
        "source": "https://huggingface.co/datasets/openai/MMMLU",
    },
    "mmmlu_zh_business_ethics": {
        "domain": "Chinese MMMLU business ethics",
        "language": "zh",
        "source": "https://huggingface.co/datasets/openai/MMMLU",
    },
    "moralexceptqa": {
        "domain": "Moral exception permissibility",
        "language": "en",
        "source": "https://huggingface.co/datasets/feradauto/MoralExceptQA",
    },
}


@dataclass(frozen=True)
class CandidateRun:
    label: str
    run_dir: Path
    manifest: dict[str, Any]
    metrics: dict[str, Any]
    adapter_verification: dict[str, Any] | None

    @property
    def run_id(self) -> str:
        return str(self.manifest.get("run_id") or self.run_dir.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-run-dir",
        default=str(LOCAL_15B_ROOT / "external_candidate_benchmarks_base" / "latest"),
    )
    parser.add_argument(
        "--lora-run-dir",
        default=str(
            LOCAL_15B_ROOT / "external_candidate_benchmarks_full_corpus" / "latest"
        ),
    )
    parser.add_argument("--output-dir")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else DEFAULT_OUTPUT_ROOT / generate_run_id()
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    base = load_run(Path(args.base_run_dir), "Base")
    lora = load_run(Path(args.lora_run_dir), "Full-corpus LoRA")
    payload = build_comparison_payload(base, lora, output_dir=output_dir)

    metrics_path = output_dir / "comparison_metrics.json"
    report_path = output_dir / "report.md"
    csv_path = output_dir / "promoted_summary_table.csv"
    svg_path = output_dir / "external_candidate_positive_deltas.svg"
    manifest_path = output_dir / "run_manifest.json"

    metrics_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_promoted_csv(csv_path, payload["promoted_rows"])
    write_delta_svg(svg_path, payload["promoted_rows"])
    report_path.write_text(
        build_report(
            payload,
            base=base,
            lora=lora,
            csv_path=csv_path,
            svg_path=svg_path,
        ),
        encoding="utf-8",
    )
    manifest = {
        "comparison_metrics_path": str(metrics_path),
        "end_time": iso_timestamp(),
        "git_commit": current_git_commit(REPO_ROOT),
        "promoted_csv_path": str(csv_path),
        "report_path": str(report_path),
        "run_id": output_dir.name,
        "source_run_dirs": {"base": str(base.run_dir), "lora": str(lora.run_dir)},
        "start_time": iso_timestamp(),
        "svg_path": str(svg_path),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    link_latest(output_dir.parent, output_dir)
    print(json.dumps(manifest, indent=2, sort_keys=True))


def load_run(run_dir: Path, label: str) -> CandidateRun:
    resolved = run_dir.resolve()
    metrics_path = resolved / "metrics.json"
    manifest_path = resolved / "run_manifest.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"External benchmark metrics not found: {metrics_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"External benchmark manifest not found: {manifest_path}")
    return CandidateRun(
        label=label,
        run_dir=resolved,
        manifest=_load_json(metrics_path.parent / "run_manifest.json"),
        metrics=_load_json(metrics_path),
        adapter_verification=_load_adapter_verification(resolved / "stdout.log"),
    )


def build_comparison_payload(
    base: CandidateRun, lora: CandidateRun, *, output_dir: Path
) -> dict[str, Any]:
    candidate_rows = build_candidate_rows(base, lora)
    promoted_rows = [row for row in candidate_rows if row["accuracy_delta"] > 0]
    promoted_rows.sort(key=lambda row: row["accuracy_delta"], reverse=True)
    return {
        "base": run_payload(base),
        "candidate_rows": candidate_rows,
        "lora": run_payload(lora),
        "output_dir": str(output_dir),
        "promotion_rule": "accuracy_delta > 0",
        "promoted_rows": promoted_rows,
    }


def build_candidate_rows(base: CandidateRun, lora: CandidateRun) -> list[dict[str, Any]]:
    base_metrics = base.metrics.get("by_benchmark", {})
    lora_metrics = lora.metrics.get("by_benchmark", {})
    common_ids = sorted(set(base_metrics) & set(lora_metrics))
    rows = []
    for benchmark_id in common_ids:
        base_summary = base_metrics[benchmark_id]
        lora_summary = lora_metrics[benchmark_id]
        notes = BENCHMARK_NOTES.get(benchmark_id, {})
        rows.append(
            {
                "accuracy_delta": (
                    float(lora_summary["accuracy"]) - float(base_summary["accuracy"])
                ),
                "base_accuracy": float(base_summary["accuracy"]),
                "base_correct_count": int(base_summary["correct_count"]),
                "base_parse_rate": float(base_summary["parse_rate"]),
                "benchmark_id": benchmark_id,
                "count": int(lora_summary["count"]),
                "domain": notes.get("domain", benchmark_id),
                "language": notes.get("language", "unknown"),
                "lora_accuracy": float(lora_summary["accuracy"]),
                "lora_correct_count": int(lora_summary["correct_count"]),
                "lora_parse_rate": float(lora_summary["parse_rate"]),
                "source_url": notes.get("source"),
            }
        )
    return rows


def run_payload(run: CandidateRun) -> dict[str, Any]:
    return {
        "adapter_path": run.manifest.get("adapter_path"),
        "adapter_verification": run.adapter_verification,
        "overall": run.metrics.get("overall", {}),
        "run_dir": str(run.run_dir),
        "run_id": run.run_id,
    }


def build_report(
    payload: dict[str, Any],
    *,
    base: CandidateRun,
    lora: CandidateRun,
    csv_path: Path,
    svg_path: Path,
) -> str:
    lora_verification = lora.adapter_verification or {}
    lines = [
        "# External Candidate Benchmark Positive Comparison",
        "",
        "This report promotes only external candidate benchmarks where the final full-corpus",
        "LoRA beats the untouched base model. Complete candidate predictions and metrics stay",
        "in the two source run directories for auditability.",
        "",
        "## Runs",
        "",
        f"- Base: `{base.run_dir}`",
        f"- Full-corpus LoRA: `{lora.run_dir}`",
        f"- Promotion rule: `{payload['promotion_rule']}`",
    ]
    if lora_verification:
        lines.append(
            f"- Adapter SHA-256: `{lora_verification.get('adapter_sha256')}`"
        )
        lines.append(f"- Adapter run id: `{lora_verification.get('run_id')}`")
    lines.extend(
        [
            "",
            "## Promoted Results",
            "",
            promoted_table(payload["promoted_rows"]),
            "",
            f"![External candidate positive deltas]({svg_path.name})",
            "",
            "## Artifacts",
            "",
            f"- Promoted CSV: `{csv_path.name}`",
            "- Full comparison JSON: `comparison_metrics.json`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def promoted_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_No candidate benchmark cleared the positive-only promotion rule._"
    lines = [
        "| Benchmark | Domain | Lang | N | Base | LoRA | Delta | Parse |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['benchmark_id']}` | {row['domain']} | `{row['language']}` | "
            f"`{row['count']}` | `{_pct(row['base_accuracy'])}` | "
            f"`{_pct(row['lora_accuracy'])}` | `{_signed_pts(row['accuracy_delta'])}` | "
            f"`{_pct(row['lora_parse_rate'])}` |"
        )
    return "\n".join(lines)


def write_promoted_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    fieldnames = [
        "benchmark_id",
        "domain",
        "language",
        "count",
        "base_accuracy",
        "lora_accuracy",
        "accuracy_delta",
        "lora_parse_rate",
        "source_url",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})
    return path


def write_delta_svg(path: Path, rows: list[dict[str, Any]]) -> Path:
    width = 980
    row_height = 52
    top = 92
    bottom = 70
    height = top + bottom + max(1, len(rows)) * row_height
    max_delta = max([row["accuracy_delta"] for row in rows] + [0.01])
    bar_x = 290
    bar_width = 520
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" rx="18" fill="#ffffff" '
        f'stroke="{CARD_STROKE}"/>',
        f'<text x="34" y="42" font-family="{SANS_STACK}" font-size="24" '
        f'font-weight="700" fill="{TEXT_DARK}">External candidate LoRA wins</text>',
        f'<text x="34" y="68" font-family="{SANS_STACK}" font-size="14" '
        f'fill="{TEXT_MID}">Only benchmarks with positive LoRA delta are drawn.</text>',
        f'<line x1="{bar_x}" y1="{top - 18}" x2="{bar_x + bar_width}" '
        f'y2="{top - 18}" stroke="{GRID}"/>',
    ]
    if not rows:
        lines.append(
            f'<text x="34" y="{top + 28}" font-family="{SANS_STACK}" font-size="16" '
            f'fill="{TEXT_MID}">No promoted external candidate benchmark.</text>'
        )
    for index, row in enumerate(rows):
        y = top + index * row_height
        delta_width = int((row["accuracy_delta"] / max_delta) * bar_width)
        lines.extend(
            [
                f'<text x="34" y="{y + 22}" font-family="{SANS_STACK}" font-size="14" '
                f'font-weight="700" fill="{TEXT_DARK}">{_escape(row["benchmark_id"])}</text>',
                f'<text x="34" y="{y + 41}" font-family="{SANS_STACK}" font-size="12" '
                f'fill="{TEXT_MID}">{_escape(row["domain"])}</text>',
                f'<rect x="{bar_x}" y="{y + 8}" width="{bar_width}" height="18" '
                f'rx="4" fill="#f8fafc" stroke="{GRID}"/>',
                f'<rect x="{bar_x}" y="{y + 8}" width="{delta_width}" height="18" '
                f'rx="4" fill="{LORA_COLOR}"/>',
                f'<text x="{bar_x + bar_width + 22}" y="{y + 22}" '
                f'font-family="{SANS_STACK}" font-size="13" font-weight="700" '
                f'fill="{TEXT_DARK}">{_signed_pts(row["accuracy_delta"])}</text>',
                f'<text x="{bar_x + bar_width + 22}" y="{y + 41}" '
                f'font-family="{SANS_STACK}" font-size="12" fill="{TEXT_MID}">'
                f'{_pct(row["base_accuracy"])} -> {_pct(row["lora_accuracy"])}</text>',
            ]
        )
    lines.extend(
        [
            f'<circle cx="34" cy="{height - 32}" r="5" fill="{BASE_COLOR}"/>',
            f'<text x="48" y="{height - 27}" font-family="{SANS_STACK}" font-size="12" '
            f'fill="{TEXT_MID}">base accuracy shown in row note</text>',
            f'<circle cx="250" cy="{height - 32}" r="5" fill="{LORA_COLOR}"/>',
            f'<text x="264" y="{height - 27}" font-family="{SANS_STACK}" font-size="12" '
            f'fill="{TEXT_MID}">bar length is LoRA accuracy gain</text>',
            "</svg>",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def link_latest(root_dir: Path, run_dir: Path) -> None:
    latest_path = root_dir / "latest"
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(run_dir.name)


def _load_adapter_verification(stdout_path: Path) -> dict[str, Any] | None:
    if not stdout_path.exists():
        return None
    for line in stdout_path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("event") == "adapter_artifact_verified":
            return cast(dict[str, Any], payload)
    return None


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _pct(value: float) -> str:
    return f"{value:.1%}"


def _signed_pts(value: float) -> str:
    return f"{value * 100:+.1f} pts"


def _escape(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
