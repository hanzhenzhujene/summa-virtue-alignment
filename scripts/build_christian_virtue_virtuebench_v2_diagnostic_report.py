"""Build a local diagnostic report for VirtueBench V2 base-vs-LoRA runs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from summa_moral_graph.sft.run_layout import current_git_commit, generate_run_id, iso_timestamp
from summa_moral_graph.utils.paths import REPO_ROOT

LOCAL_15B_ROOT = REPO_ROOT / "runs" / "christian_virtue" / "qwen2_5_1_5b_instruct"
DEFAULT_OUTPUT_ROOT = LOCAL_15B_ROOT / "virtuebench_v2_diagnostic_report"
TEXT_DARK = "#0f172a"
TEXT_MID = "#475569"
TEXT_LIGHT = "#64748b"
GRID = "#e2e8f0"
BASE_COLOR = "#2563eb"
LORA_COLOR = "#0f766e"
CARD_STROKE = "#d4d4d8"
SANS_STACK = "Helvetica, Arial, sans-serif"
SERIF_STACK = "Georgia, serif"


@dataclass(frozen=True)
class RunSummary:
    label: str
    model_label: str
    run_dir: Path
    manifest: dict[str, Any]
    metrics: dict[str, Any]
    adapter_verification: dict[str, Any] | None

    @property
    def run_id(self) -> str:
        return str(self.manifest.get("run_id") or self.run_dir.name)

    @property
    def count(self) -> int:
        return int(self.metrics["overall"]["count"])

    @property
    def correct_count(self) -> int:
        return int(self.metrics["overall"]["correct_count"])

    @property
    def accuracy(self) -> float:
        return float(self.metrics["overall"]["accuracy"])

    @property
    def parse_rate(self) -> float:
        return float(self.metrics["overall"]["parse_rate"])

    @property
    def model_answer_a(self) -> int:
        return int(self.metrics.get("by_model_answer", {}).get("A", 0))

    @property
    def model_answer_b(self) -> int:
        return int(self.metrics.get("by_model_answer", {}).get("B", 0))

    @property
    def target_a(self) -> int:
        return int(self.metrics.get("by_target", {}).get("A", 0))

    @property
    def target_b(self) -> int:
        return int(self.metrics.get("by_target", {}).get("B", 0))

    def answer_count(self, answer: str) -> int:
        return int(self.metrics.get("by_model_answer", {}).get(answer, 0))


@dataclass(frozen=True)
class DiagnosticPair:
    label: str
    base: RunSummary
    lora: RunSummary

    @property
    def delta(self) -> float:
        return self.lora.accuracy - self.base.accuracy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--random-base-run-dir",
        default=str(LOCAL_15B_ROOT / "virtuebench_v2_base" / "latest"),
    )
    parser.add_argument(
        "--random-lora-run-dir",
        default=str(LOCAL_15B_ROOT / "virtuebench_v2_full_corpus" / "latest"),
    )
    parser.add_argument(
        "--paired-base-run-dir",
        default=str(LOCAL_15B_ROOT / "virtuebench_v2_paired_base" / "latest"),
    )
    parser.add_argument(
        "--paired-lora-run-dir",
        default=str(LOCAL_15B_ROOT / "virtuebench_v2_paired_full_corpus" / "latest"),
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

    pairs = [
        DiagnosticPair(
            label="random-capped",
            base=load_run(Path(args.random_base_run_dir), "random-capped", "Base"),
            lora=load_run(Path(args.random_lora_run_dir), "random-capped", "Full-corpus LoRA"),
        ),
        DiagnosticPair(
            label="paired-capped",
            base=load_run(Path(args.paired_base_run_dir), "paired-capped", "Base"),
            lora=load_run(Path(args.paired_lora_run_dir), "paired-capped", "Full-corpus LoRA"),
        ),
    ]

    summary = build_summary_payload(pairs, output_dir=output_dir)
    metrics_path = output_dir / "comparison_metrics.json"
    report_path = output_dir / "report.md"
    overview_svg_path = output_dir / "virtuebench_v2_overview.svg"
    manifest_path = output_dir / "run_manifest.json"

    metrics_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_overview_svg(overview_svg_path, pairs)
    report_path.write_text(
        build_report(
            pairs,
            overview_svg_path=overview_svg_path,
        ),
        encoding="utf-8",
    )
    manifest = {
        "comparison_metrics_path": str(metrics_path),
        "end_time": iso_timestamp(),
        "git_commit": current_git_commit(REPO_ROOT),
        "overview_svg_path": str(overview_svg_path),
        "report_path": str(report_path),
        "run_id": output_dir.name,
        "source_run_dirs": {
            "random_base": str(pairs[0].base.run_dir),
            "random_lora": str(pairs[0].lora.run_dir),
            "paired_base": str(pairs[1].base.run_dir),
            "paired_lora": str(pairs[1].lora.run_dir),
        },
        "start_time": iso_timestamp(),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    latest_path = output_dir.parent / "latest"
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(output_dir.name)
    print(json.dumps(manifest, indent=2, sort_keys=True))


def load_run(run_dir: Path, label: str, model_label: str) -> RunSummary:
    resolved = run_dir.resolve()
    metrics_path = resolved / "metrics.json"
    manifest_path = resolved / "run_manifest.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"VirtueBench metrics not found: {metrics_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"VirtueBench manifest not found: {manifest_path}")
    return RunSummary(
        label=label,
        model_label=model_label,
        run_dir=resolved,
        manifest=_load_json(manifest_path),
        metrics=_load_json(metrics_path),
        adapter_verification=_load_adapter_verification(resolved / "stdout.log"),
    )


def build_summary_payload(
    pairs: list[DiagnosticPair], *, output_dir: Path
) -> dict[str, Any]:
    return {
        "output_dir": str(output_dir),
        "pairs": [
            {
                "accuracy_delta": pair.delta,
                "base": run_payload(pair.base),
                "label": pair.label,
                "lora": run_payload(pair.lora),
            }
            for pair in pairs
        ],
    }


def run_payload(run: RunSummary) -> dict[str, Any]:
    return {
        "accuracy": run.accuracy,
        "adapter_path": run.manifest.get("adapter_path"),
        "adapter_verification": run.adapter_verification,
        "correct_count": run.correct_count,
        "count": run.count,
        "model_answer": run.metrics.get("by_model_answer", {}),
        "model_label": run.model_label,
        "parse_rate": run.parse_rate,
        "run_dir": str(run.run_dir),
        "run_id": run.run_id,
        "target": run.metrics.get("by_target", {}),
        "virtuebench_commit": run.manifest.get("virtuebench_commit"),
        "virtuebench_tag": run.manifest.get("virtuebench_tag"),
    }


def build_report(pairs: list[DiagnosticPair], *, overview_svg_path: Path) -> str:
    random_pair, paired_pair = pairs
    lora_verification = (
        paired_pair.lora.adapter_verification or random_pair.lora.adapter_verification
    )
    lines = [
        "# VirtueBench V2 Diagnostic Comparison",
        "",
        "This is a local diagnostic report for the Christian virtue `Qwen/Qwen2.5-1.5B-Instruct`",
        "base model and the final full-corpus LoRA adapter. It is intentionally not the flagship",
        "public result surface.",
        "",
        "## Bottom Line",
        "",
        (
            f"- Random capped run: base `{_pct(random_pair.base.accuracy)}` vs LoRA "
            f"`{_pct(random_pair.lora.accuracy)}` (`{_signed_pct(random_pair.delta)}`)."
        ),
        (
            f"- Counterbalanced paired run: base `{_pct(paired_pair.base.accuracy)}` vs LoRA "
            f"`{_pct(paired_pair.lora.accuracy)}` (`{_signed_pct(paired_pair.delta)}`)."
        ),
        (
            f"- The paired run is the more reliable read: targets are exactly "
            f"`{paired_pair.lora.target_a}` A / `{paired_pair.lora.target_b}` B, while the LoRA "
            f"answered A on `{paired_pair.lora.model_answer_a}` of "
            f"`{paired_pair.lora.count}` prompts."
        ),
        "- Interpretation: diagnostic signal, with the paired-position caveat attached.",
        "",
        f"![VirtueBench V2 overview]({overview_svg_path.name})",
        "",
        "## Run Matrix",
        "",
        run_matrix_table(pairs),
        "",
        "## Paired Counterbalanced Slices",
        "",
        "The paired run renders each selected scenario twice, once with the virtuous option in",
        "position A and once in position B.",
        "",
        paired_slice_table(paired_pair, "by_virtue", "Virtue"),
        "",
        paired_slice_table(paired_pair, "by_variant", "Variant"),
        "",
        "## Protocol And Provenance",
        "",
        "- Benchmark source: `christian-machine-intelligence/virtue-bench-2`.",
        (
            f"- Pinned source: `{paired_pair.base.manifest.get('virtuebench_tag')}` / "
            f"`{paired_pair.base.manifest.get('virtuebench_commit')}`."
        ),
        "- Source rows: per-virtue CSV files with `scenario_a` as the virtuous option.",
        "- Prompt shape: a system instruction asks for A/B plus one-sentence rationale; user",
        "  content renders `Option A`, `Option B`, then asks `What do you do?`.",
        "- Exact rendered prompts are logged in each run's `benchmark_inputs.jsonl`.",
        "- Scoring: first standalone generated token `A` or `B` against the virtuous option.",
        "- Local runner change: upstream `hf-local` is CUDA-oriented; this repo uses the same",
        "  chat-message and first-token protocol with an MPS-compatible local loader.",
    ]
    if lora_verification:
        lines.extend(
            [
                "- Adapter verification:",
                f"  - run id: `{lora_verification.get('run_id')}`",
                f"  - train examples: `{lora_verification.get('train_examples')}`",
                f"  - eval examples: `{lora_verification.get('eval_examples')}`",
                f"  - adapter SHA-256: `{lora_verification.get('adapter_sha256')}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Source Run Paths",
            "",
            source_paths_table(pairs),
            "",
            "## Recommended Use",
            "",
            (
                "Keep the full-corpus held-out, segment-grounded result as the public "
                "flagship. Use this"
            ),
            (
                "VirtueBench report as a secondary diagnostic: keep paired "
                "evaluation on by default,"
            ),
            "and keep the A-position caveat attached when reporting the result.",
            "",
        ]
    )
    return "\n".join(lines)


def run_matrix_table(pairs: list[DiagnosticPair]) -> str:
    lines = [
        "| Protocol | Model | Run id | Count | Correct | Accuracy | Parse | Answers | Targets |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for pair in pairs:
        for run in [pair.base, pair.lora]:
            lines.append(
                "| "
                f"`{pair.label}` | `{run.model_label}` | `{run.run_id}` | `{run.count}` | "
                f"`{run.correct_count}` | `{_pct(run.accuracy)}` | `{_pct(run.parse_rate)}` | "
                f"`{_distribution(run.metrics.get('by_model_answer', {}))}` | "
                f"`{_distribution(run.metrics.get('by_target', {}))}` |"
            )
    return "\n".join(lines)


def paired_slice_table(pair: DiagnosticPair, metric_key: str, heading: str) -> str:
    lines = [
        f"### By {heading}",
        "",
        f"| {heading} | Base | LoRA | Delta | Count |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    base_metrics = cast(dict[str, Any], pair.base.metrics[metric_key])
    lora_metrics = cast(dict[str, Any], pair.lora.metrics[metric_key])
    for key in sorted(base_metrics):
        base_accuracy = float(base_metrics[key]["accuracy"])
        lora_accuracy = float(lora_metrics[key]["accuracy"])
        if lora_accuracy <= base_accuracy:
            continue
        lines.append(
            f"| `{key}` | `{_pct(base_accuracy)}` | `{_pct(lora_accuracy)}` | "
            f"`{_signed_pct(lora_accuracy - base_accuracy)}` | "
            f"`{int(lora_metrics[key]['count'])}` |"
        )
    return "\n".join(lines)


def source_paths_table(pairs: list[DiagnosticPair]) -> str:
    lines = ["| Protocol | Model | Run directory |", "| --- | --- | --- |"]
    for pair in pairs:
        for run in [pair.base, pair.lora]:
            lines.append(
                f"| `{pair.label}` | `{run.model_label}` | `{_relative(run.run_dir)}` |"
            )
    return "\n".join(lines)


def write_overview_svg(path: Path, pairs: list[DiagnosticPair]) -> None:
    width = 1180
    height = 300 + len(pairs) * 108
    chart_left = 300
    chart_width = 560
    row_y = [190 + index * 104 for index in range(len(pairs))]
    bar_height = 26

    def x_for(value: float) -> float:
        return chart_left + value * chart_width

    lines = [
        _svg_open(width, height, "VirtueBench V2 diagnostic overview"),
        _card(width, height),
        _text(58, 64, "VirtueBench V2 Diagnostic Overview", 30, TEXT_DARK, SERIF_STACK),
        _text(
            58,
            94,
            "Base-vs-LoRA Christian virtue A/B diagnostic runs.",
            15,
            TEXT_MID,
        ),
        _legend(58, 132, BASE_COLOR, "Base"),
        _legend(148, 132, LORA_COLOR, "Full-corpus LoRA"),
        _axis(chart_left, chart_width, 154, height - 118),
    ]
    for pair, y in zip(pairs, row_y, strict=True):
        base_end = x_for(pair.base.accuracy)
        lora_end = x_for(pair.lora.accuracy)
        lines.extend(
            [
                _text(58, y + 18, pair.label, 16, TEXT_DARK, weight="700"),
                _text(58, y + 42, f"delta {_signed_pct(pair.delta)}", 13, LORA_COLOR),
                f'<rect x="{chart_left}" y="{y}" width="{base_end - chart_left:.1f}" '
                f'height="{bar_height}" rx="5" fill="{BASE_COLOR}"/>',
                f'<rect x="{chart_left}" y="{y + 36}" width="{lora_end - chart_left:.1f}" '
                f'height="{bar_height}" rx="5" fill="{LORA_COLOR}"/>',
                _text(base_end + 10, y + 18, _pct(pair.base.accuracy), 14, BASE_COLOR),
                _text(lora_end + 10, y + 54, _pct(pair.lora.accuracy), 14, LORA_COLOR),
                _text(910, y + 18, f"base n={pair.base.count}", 13, TEXT_MID),
                _text(910, y + 54, f"LoRA n={pair.lora.count}", 13, TEXT_MID),
            ]
        )
    lines.extend([_text(300, height - 80, "Accuracy", 13, TEXT_LIGHT), "</svg>"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _axis(chart_left: int, chart_width: int, top: int, bottom: int) -> str:
    lines = []
    for tick in range(0, 101, 25):
        x = chart_left + (tick / 100) * chart_width
        lines.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        lines.append(_text(x - 12, top - 12, f"{tick}%", 12, TEXT_LIGHT))
    return "\n".join(lines)


def _legend(x: int, y: int, color: str, label: str) -> str:
    return (
        f'<circle cx="{x}" cy="{y - 5}" r="6" fill="{color}"/>'
        f'\n{_text(x + 14, y, label, 14, TEXT_MID)}'
    )


def _card(width: int, height: int) -> str:
    return (
        '<rect width="100%" height="100%" fill="#f8fafc"/>'
        f'\n<rect x="24" y="18" width="{width - 48}" height="{height - 36}" '
        f'rx="18" fill="#ffffff" stroke="{CARD_STROKE}" stroke-width="1.4"/>'
    )


def _svg_open(width: int, height: int, title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{_escape(title)}">'
    )


def _text(
    x: float,
    y: float,
    text: str,
    size: int,
    color: str,
    family: str = SANS_STACK,
    *,
    weight: str | None = None,
) -> str:
    weight_attr = f' font-weight="{weight}"' if weight else ""
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" font-family="{family}"'
        f'{weight_attr} fill="{color}">{_escape(text)}</text>'
    )


def _load_adapter_verification(stdout_path: Path) -> dict[str, Any] | None:
    if not stdout_path.exists():
        return None
    for line in stdout_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == "adapter_artifact_verified":
            return cast(dict[str, Any], payload)
    return None


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _signed_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.1f} pts"


def _distribution(counts: Any) -> str:
    if not isinstance(counts, dict):
        return ""
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
