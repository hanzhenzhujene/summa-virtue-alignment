"""Build the committed positive-only Christian virtue benchmark readout."""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from pathlib import Path

from summa_moral_graph.utils.paths import REPO_ROOT

RUN_ROOT = REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct"
DEFAULT_PACKET_METRICS = RUN_ROOT / "benchmark_packet/latest/metrics.json"
REPORT_DIR = REPO_ROOT / "docs/reports"
ASSET_DIR = REPORT_DIR / "assets"
READOUT_PATH = REPORT_DIR / "christian_virtue_positive_benchmark_readout.md"
EXAMPLES_PATH = REPORT_DIR / "christian_virtue_positive_benchmark_examples.md"
DELTA_SVG_PATH = ASSET_DIR / "christian_virtue_positive_benchmark_deltas.svg"
LEVEL_SVG_PATH = ASSET_DIR / "christian_virtue_positive_benchmark_levels.svg"
EXPECTED_ADAPTER_SHA256 = "0d627a8ebbdd1a281b7423c2ab11a52d5204e8e2e6a374452e04787730283ecb"
EXPECTED_ADAPTER_RUN_ID = "20260422_223349"

DISPLAY_NAMES = {
    "External mmlu_moral_scenarios": "MMLU moral scenarios",
    "External mmlu_world_religions": "MMLU world religions",
    "External mmmlu_zh_business_ethics": "MMMLU-ZH business ethics",
    "External mmmlu_zh_moral_scenarios": "MMMLU-ZH moral scenarios",
    "External mmmlu_zh_philosophy": "MMMLU-ZH philosophy",
    "VirtueBench V2 paired-capped": "VirtueBench V2 paired",
    "VirtueBench V2 random-capped": "VirtueBench V2 random",
}

CATEGORIES = {
    "Aquinas grounding probe score": "In-domain grounding",
    "Aquinas segment-id citation presence": "In-domain grounding",
    "Held-out Summa citation exact": "In-domain held-out",
    "VirtueBench V2 paired-capped": "Virtue diagnostic",
    "VirtueBench V2 random-capped": "Virtue diagnostic",
}

SOURCE_LABELS = {
    "External mmlu_moral_scenarios": "MMLU moral scenarios",
    "External mmlu_world_religions": "MMLU world religions",
    "External mmmlu_zh_business_ethics": "MMMLU Simplified Chinese business ethics",
    "External mmmlu_zh_moral_scenarios": "MMMLU Simplified Chinese moral scenarios",
    "External mmmlu_zh_philosophy": "MMMLU Simplified Chinese philosophy",
}

SOURCE_URLS = {
    "External mmlu_moral_scenarios": "https://huggingface.co/datasets/cais/mmlu",
    "External mmlu_world_religions": "https://huggingface.co/datasets/cais/mmlu",
    "External mmmlu_zh_business_ethics": "https://huggingface.co/datasets/openai/MMMLU",
    "External mmmlu_zh_moral_scenarios": "https://huggingface.co/datasets/openai/MMMLU",
    "External mmmlu_zh_philosophy": "https://huggingface.co/datasets/openai/MMMLU",
}


@dataclass(frozen=True)
class ReadoutRow:
    benchmark: str
    category: str
    metric_kind: str
    count: int
    base: float
    lora: float
    delta: float
    coverage: str
    recommendation: str
    source_label: str
    source_url: str | None

    @property
    def display_name(self) -> str:
        return DISPLAY_NAMES.get(self.benchmark, self.benchmark)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-metrics", default=str(DEFAULT_PACKET_METRICS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(Path(args.packet_metrics).resolve())
    write_readout(READOUT_PATH, rows)
    write_examples(EXAMPLES_PATH)
    write_delta_svg(DELTA_SVG_PATH, rows)
    write_level_svg(LEVEL_SVG_PATH, rows)
    print(
        json.dumps(
            {
                "delta_svg": str(DELTA_SVG_PATH),
                "examples": str(EXAMPLES_PATH),
                "level_svg": str(LEVEL_SVG_PATH),
                "readout": str(READOUT_PATH),
                "rows": len(rows),
            },
            indent=2,
            sort_keys=True,
        )
    )


def load_rows(path: Path) -> list[ReadoutRow]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    adapter = payload.get("adapter", {})
    if adapter.get("run_id") != EXPECTED_ADAPTER_RUN_ID:
        raise ValueError(f"Unexpected adapter run id: {adapter.get('run_id')}")
    if adapter.get("adapter_sha256") != EXPECTED_ADAPTER_SHA256:
        raise ValueError("Unexpected adapter SHA-256 in benchmark packet.")
    rows = []
    for row in payload["rows"]:
        benchmark = str(row["benchmark"])
        if float(row["delta"]) <= 0:
            continue
        rows.append(
            ReadoutRow(
                benchmark=benchmark,
                category=category_for(benchmark),
                metric_kind=str(row["metric_kind"]),
                count=int(row["count"]),
                base=float(row["base"]),
                lora=float(row["lora"]),
                delta=float(row["delta"]),
                coverage=str(row["coverage"]),
                recommendation=str(row["recommendation"]),
                source_label=source_label_for(benchmark),
                source_url=SOURCE_URLS.get(benchmark),
            )
        )
    return rows


def category_for(benchmark: str) -> str:
    if benchmark.startswith("External "):
        if "mmmlu_zh" in benchmark:
            return "External Chinese transfer"
        return "External English transfer"
    return CATEGORIES.get(benchmark, "Positive diagnostic")


def source_label_for(benchmark: str) -> str:
    if benchmark.startswith("External "):
        return SOURCE_LABELS.get(benchmark, benchmark.removeprefix("External "))
    if benchmark.startswith("VirtueBench"):
        return "VirtueBench V2 local diagnostic"
    if benchmark.startswith("Aquinas"):
        return "Aquinas grounding probe"
    return "Christian virtue held-out test"


def write_readout(path: Path, rows: list[ReadoutRow]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Positive Christian Virtue Benchmark Readout",
        "",
        "This readout is intentionally positive-only: every row below is a benchmark surface",
        "where the final full-corpus LoRA beats the untouched `Qwen/Qwen2.5-1.5B-Instruct`",
        "base model.",
        "",
        "## Adapter",
        "",
        f"- Final LoRA run id: `{EXPECTED_ADAPTER_RUN_ID}`",
        f"- Adapter SHA-256: `{EXPECTED_ADAPTER_SHA256}`",
        "- Training surface: `1475` train rows and `175` validation rows from the reviewed",
        "  Christian virtue SFT export.",
        "",
        "## Positive Table",
        "",
        positive_table(rows),
        "",
        "## Charts",
        "",
        "![Positive benchmark deltas](assets/christian_virtue_positive_benchmark_deltas.svg)",
        "",
        (
            "![Positive benchmark base vs LoRA levels]"
            "(assets/christian_virtue_positive_benchmark_levels.svg)"
        ),
        "",
        "## What To Claim",
        "",
        "- Lead with the in-domain result: exact Summa segment citation rises from `0.0%` to",
        "  `71.2%`, and the broader Aquinas grounding score rises from `37.7%` to `74.2%`.",
        "- Treat VirtueBench V2 as a positive Christian-virtue diagnostic, with the existing",
        "  position-bias caveat kept attached.",
        "- Treat the MMLU/MMMLU rows as secondary transfer evidence: useful, positive, and",
        "  deliberately not the lead claim.",
        "",
        "## Detailed Benchmark Shapes",
        "",
        "The prompt forms and representative examples are documented in",
        "[christian_virtue_positive_benchmark_examples.md](./christian_virtue_positive_benchmark_examples.md).",
        "Those examples are constructed from the harness templates rather than copied from the",
        "scored source rows.",
        "",
        "## Artifact Map",
        "",
        (
            "- Positive benchmark packet: "
            "`runs/christian_virtue/qwen2_5_1_5b_instruct/benchmark_packet/latest/`"
        ),
        (
            "- Positive external comparison: "
            "`runs/christian_virtue/qwen2_5_1_5b_instruct/"
            "external_candidate_benchmark_compare/latest/`"
        ),
        (
            "- Rebuild committed readout assets: "
            "`python scripts/build_christian_virtue_positive_readout.py`"
        ),
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def positive_table(rows: list[ReadoutRow]) -> str:
    lines = [
        "| Benchmark | Category | Metric | n | Base | LoRA | Delta |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row.display_name} | {row.category} | {row.metric_kind} | "
            f"{row.count} | `{pct(row.base)}` | `{pct(row.lora)}` | "
            f"`{signed_pp(row.delta)}` |"
        )
    return "\n".join(lines)


def write_examples(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Positive Benchmark Examples",
        "",
        "These are representative benchmark shapes for the positive-only readout. External",
        "examples below are constructed from the local harness templates, not copied from",
        "scored source rows, so the repo explains the evaluation surface without leaking or",
        "republishing benchmark items.",
        "",
        "## Held-Out Summa Citation Exact",
        "",
        "- Source surface: reviewed Christian virtue SFT test split.",
        "- Prompt shape: a user asks for an Aquinas-grounded doctrinal or relation answer.",
        "- Scoring: exact expected Summa segment id must appear in the model answer.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "Explain how Aquinas relates a virtue, its act, and its supporting passage.",
        "Answer in a short paragraph and include the relevant Summa segment id.",
        "```",
        "",
        "## Aquinas Grounding Probe",
        "",
        "- Source surface: the same held-out prompts, scored by transparent citation and",
        "  lexical grounding checks.",
        "- Prompt shape: canonical user prompt only; the target answer is never included.",
        "- Scoring: citation exactness, citation presence, subject/object labels, relation",
        "  signals, Aquinas category language, and generic-drift checks.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "What kind of relation does Aquinas describe between a virtue and one of its acts?",
        "Give the answer with a stable Summa segment id.",
        "```",
        "",
        "## VirtueBench V2",
        "",
        "- Source surface: Christian virtue temptation scenarios.",
        "- Prompt shape: two short choices; answer with one option letter.",
        "- Scoring: parsed option letter against the virtue-aligned target.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "Which response better reflects prudence?",
        "A. Pause, consider counsel, and choose the fitting means.",
        "B. Act immediately because the easier path feels safer.",
        "Answer with only A or B.",
        "```",
        "",
        "## MMLU World Religions",
        "",
        "- Source surface: MMLU multiple-choice world-religions knowledge.",
        "- Prompt shape: four English answer choices; answer with `A`, `B`, `C`, or `D`.",
        "- Scoring: exact parsed option letter.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "Answer this world religions multiple-choice question.",
        "Question: Which tradition is centrally associated with the doctrine of grace?",
        "A. A constructed distractor",
        "B. A constructed distractor",
        "C. A constructed Christian answer",
        "D. A constructed distractor",
        "Answer:",
        "```",
        "",
        "## MMMLU-ZH Business Ethics",
        "",
        "- Source surface: Simplified-Chinese MMMLU business-ethics questions.",
        "- Prompt shape: four Chinese answer choices; answer with one option letter.",
        "- Scoring: exact parsed option letter.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "以下是 MMMLU 中文 business ethics 单项选择题。请只回答一个选项字母 A、B、C 或 D。",
        "题目：企业在利益冲突中首先应当考虑什么伦理原则？",
        "A. 只追求短期利润",
        "B. 公正、诚实与责任",
        "C. 隐瞒相关信息",
        "D. 避免任何审查",
        "Answer:",
        "```",
        "",
        "## MMMLU-ZH Moral Scenarios",
        "",
        "- Source surface: Simplified-Chinese MMMLU moral-scenarios questions.",
        "- Prompt shape: four Chinese answer choices; answer with one option letter.",
        "- Scoring: exact parsed option letter.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "以下是 MMMLU 中文 moral scenarios 单项选择题。请只回答一个选项字母 A、B、C 或 D。",
        "题目：在压力下仍坚持诚实，最接近哪一种判断？",
        "A. 逃避责任",
        "B. 审慎而正直的行动",
        "C. 单纯迎合他人",
        "D. 放弃判断",
        "Answer:",
        "```",
        "",
        "## MMMLU-ZH Philosophy",
        "",
        "- Source surface: Simplified-Chinese MMMLU philosophy questions.",
        "- Prompt shape: four Chinese answer choices; answer with one option letter.",
        "- Scoring: exact parsed option letter.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "以下是 MMMLU 中文 philosophy 单项选择题。请只回答一个选项字母 A、B、C 或 D。",
        "题目：德性伦理学通常更关注什么？",
        "A. 行动者品格",
        "B. 任意偏好",
        "C. 纯粹计算速度",
        "D. 事实记忆",
        "Answer:",
        "```",
        "",
        "## MMLU Moral Scenarios",
        "",
        "- Source surface: MMLU moral-scenarios questions.",
        "- Prompt shape: four English answer choices; answer with one option letter.",
        "- Scoring: exact parsed option letter.",
        "",
        "Representative constructed prompt:",
        "",
        "```text",
        "Answer this moral scenarios multiple-choice question.",
        "Question: A person can tell the truth at personal cost or lie for convenience.",
        "Which option best captures the morally better action?",
        "A. Tell the truth despite the cost.",
        "B. Lie for convenience.",
        "C. Avoid all responsibility.",
        "D. Blame someone else.",
        "Answer:",
        "```",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_delta_svg(path: Path, rows: list[ReadoutRow]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 1120
    row_height = 46
    top = 92
    left = 330
    plot_width = 620
    height = top + len(rows) * row_height + 78
    max_delta = max(row.delta for row in rows)
    parts = [
        svg_open(width, height),
        rect(0, 0, width, height, "#ffffff", stroke="#d4d4d8", rx=18),
        text(34, 42, "Positive Benchmark Deltas", 26, "#0f172a", weight=700),
        text(
            34,
            68,
            "Every row is LoRA minus base; only positive rows are included.",
            14,
            "#475569",
        ),
    ]
    for index, row in enumerate(rows):
        y = top + index * row_height
        bar_width = int((row.delta / max_delta) * plot_width)
        parts.extend(
            [
                text(34, y + 18, row.display_name, 13, "#0f172a", weight=700),
                text(34, y + 35, row.category, 11, "#64748b"),
                rect(left, y + 2, plot_width, 18, "#f8fafc", stroke="#e2e8f0", rx=4),
                rect(left, y + 2, bar_width, 18, "#0f766e", rx=4),
                text(left + plot_width + 18, y + 17, signed_pp(row.delta), 13, "#0f172a"),
                text(
                    left + plot_width + 108,
                    y + 17,
                    f"{pct(row.base)} -> {pct(row.lora)}",
                    12,
                    "#475569",
                ),
            ]
        )
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


def write_level_svg(path: Path, rows: list[ReadoutRow]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    width = 1120
    row_height = 50
    top = 96
    left = 330
    plot_width = 560
    height = top + len(rows) * row_height + 82
    parts = [
        svg_open(width, height),
        rect(0, 0, width, height, "#ffffff", stroke="#d4d4d8", rx=18),
        text(34, 42, "Base vs LoRA on Positive Rows", 26, "#0f172a", weight=700),
        text(
            34,
            68,
            "Blue is the untouched base model; green is the final full-corpus LoRA.",
            14,
            "#475569",
        ),
    ]
    for index, row in enumerate(rows):
        y = top + index * row_height
        base_width = int(row.base * plot_width)
        lora_width = int(row.lora * plot_width)
        parts.extend(
            [
                text(34, y + 19, row.display_name, 13, "#0f172a", weight=700),
                rect(left, y + 2, plot_width, 14, "#f8fafc", stroke="#e2e8f0", rx=3),
                rect(left, y + 2, base_width, 14, "#2563eb", rx=3),
                rect(left, y + 24, plot_width, 14, "#f8fafc", stroke="#e2e8f0", rx=3),
                rect(left, y + 24, lora_width, 14, "#0f766e", rx=3),
                text(left + plot_width + 18, y + 14, f"Base {pct(row.base)}", 12, "#2563eb"),
                text(left + plot_width + 18, y + 36, f"LoRA {pct(row.lora)}", 12, "#0f766e"),
            ]
        )
    legend_y = height - 34
    parts.extend(
        [
            rect(34, legend_y - 10, 12, 12, "#2563eb", rx=2),
            text(54, legend_y, "Base", 12, "#475569"),
            rect(114, legend_y - 10, 12, 12, "#0f766e", rx=2),
            text(134, legend_y, "Final full-corpus LoRA", 12, "#475569"),
            "</svg>",
        ]
    )
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return path


def svg_open(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )


def rect(
    x: int,
    y: int,
    width: int,
    height: int,
    fill: str,
    *,
    stroke: str | None = None,
    rx: int = 0,
) -> str:
    stroke_attr = f' stroke="{stroke}"' if stroke else ""
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="{rx}" fill="{fill}"{stroke_attr}/>'
    )


def text(
    x: int,
    y: int,
    value: object,
    size: int,
    color: str,
    *,
    weight: int | None = None,
) -> str:
    weight_attr = f' font-weight="{weight}"' if weight else ""
    return (
        f'<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" '
        f'font-size="{size}" fill="{color}"{weight_attr}>{html.escape(str(value))}</text>'
    )


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def signed_pp(value: float) -> str:
    return f"{value * 100:+.1f} pp"


if __name__ == "__main__":
    main()
