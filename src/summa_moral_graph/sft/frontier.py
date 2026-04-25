"""Fast frontier audits for identifying the next Christian virtue SFT optimization target."""

from __future__ import annotations

import html
import json
from collections import Counter, defaultdict
from pathlib import Path
from textwrap import wrap
from typing import Any, Literal, cast

from ..utils.paths import REPO_ROOT
from .evaluation import load_prediction_rows, load_reference_examples
from .run_layout import write_json
from .utils import extract_passage_ids, tract_display_name

CitationCategory = Literal[
    "exact_stable_id_match",
    "partial_stable_id_match",
    "label_only_citation",
    "wrong_stable_id",
    "no_citation_signal",
]

CATEGORY_DISPLAY_NAMES: dict[CitationCategory, str] = {
    "exact_stable_id_match": "Exact stable-id match",
    "partial_stable_id_match": "Partial stable-id match",
    "label_only_citation": "Label-only citation",
    "wrong_stable_id": "Wrong stable id",
    "no_citation_signal": "No citation signal",
}

CATEGORY_COLORS: dict[CitationCategory, str] = {
    "exact_stable_id_match": "#2563eb",
    "partial_stable_id_match": "#0f766e",
    "label_only_citation": "#d97706",
    "wrong_stable_id": "#b91c1c",
    "no_citation_signal": "#94a3b8",
}

CATEGORY_ORDER: tuple[CitationCategory, ...] = (
    "exact_stable_id_match",
    "partial_stable_id_match",
    "label_only_citation",
    "wrong_stable_id",
    "no_citation_signal",
)


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _display_path(path: Path) -> str:
    absolute_path = path if path.is_absolute() else REPO_ROOT / path
    try:
        return str(absolute_path.absolute().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _extract_reference_text(row: dict[str, Any]) -> str:
    for message in reversed(cast(list[dict[str, Any]], row.get("messages", []))):
        if message.get("role") == "assistant":
            return str(message.get("content", ""))
    raise ValueError(f"Reference row {row.get('example_id')} is missing an assistant message")


def _extract_user_text(row: dict[str, Any]) -> str:
    for message in reversed(cast(list[dict[str, Any]], row.get("messages", []))):
        if message.get("role") == "user":
            return str(message.get("content", ""))
    raise ValueError(f"Reference row {row.get('example_id')} is missing a user message")


def _normalize_labels(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(value) for value in values if str(value).strip()]
    if isinstance(values, str) and values.strip():
        return [values]
    return []


def _contains_reference_label(text: str, labels: list[str]) -> bool:
    lowered = text.lower()
    return any(label.lower() in lowered for label in labels if label.strip())


def classify_citation_signal(
    prediction_text: str,
    *,
    reference_ids: list[str],
    reference_labels: list[str],
) -> dict[str, Any]:
    predicted_ids = extract_passage_ids(prediction_text)
    reference_id_set = set(reference_ids)
    predicted_id_set = set(predicted_ids)
    overlap_ids = sorted(reference_id_set & predicted_id_set)
    label_hit = _contains_reference_label(prediction_text, reference_labels)
    exact = bool(reference_id_set) and predicted_id_set == reference_id_set
    partial = bool(overlap_ids) and not exact
    if exact:
        category: CitationCategory = "exact_stable_id_match"
    elif partial:
        category = "partial_stable_id_match"
    elif not predicted_ids and label_hit:
        category = "label_only_citation"
    elif predicted_ids:
        category = "wrong_stable_id"
    else:
        category = "no_citation_signal"
    return {
        "category": category,
        "predicted_ids": predicted_ids,
        "overlap_ids": overlap_ids,
        "reference_ids": reference_ids,
        "reference_labels": reference_labels,
        "has_any_stable_id": bool(predicted_ids),
        "has_reference_label": label_hit,
        "has_any_citation_signal": bool(predicted_ids) or label_hit,
        "exact_stable_id_match": exact,
        "partial_stable_id_match": partial,
    }


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _summary_from_rows(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    total = len(rows)
    counts = Counter(cast(CitationCategory, row[key]["category"]) for row in rows)
    exact = sum(1 for row in rows if row[key]["exact_stable_id_match"])
    partial = sum(1 for row in rows if row[key]["partial_stable_id_match"])
    signal = sum(1 for row in rows if row[key]["has_any_citation_signal"])
    wrong_id = counts["wrong_stable_id"]
    label_only = counts["label_only_citation"]
    no_signal = counts["no_citation_signal"]
    return {
        "count": total,
        "exact_stable_id_match_rate": _rate(exact, total),
        "partial_stable_id_match_rate": _rate(partial, total),
        "any_citation_signal_rate": _rate(signal, total),
        "wrong_stable_id_rate": _rate(wrong_id, total),
        "label_only_citation_rate": _rate(label_only, total),
        "no_citation_signal_rate": _rate(no_signal, total),
        "category_counts": {category: counts.get(category, 0) for category in CATEGORY_ORDER},
        "category_rates": {
            category: _rate(counts.get(category, 0), total) for category in CATEGORY_ORDER
        },
    }


def _by_bucket(rows: list[dict[str, Any]], bucket_key: str, analysis_key: str) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[str(row[bucket_key])].append(row)
    return {
        bucket: _summary_from_rows(bucket_rows, analysis_key)
        for bucket, bucket_rows in sorted(
            buckets.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )
    }


def _trim_text(value: str, limit: int = 420) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def _select_examples(
    rows: list[dict[str, Any]],
    *,
    adapter_category: CitationCategory,
    limit: int = 2,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        if row["adapter"]["category"] != adapter_category:
            continue
        selected.append(
            {
                "example_id": row["example_id"],
                "tract": row["tract"],
                "relation_type": row["relation_type"],
                "question": row["question"],
                "reference_ids": row["reference_ids"],
                "reference_labels": row["reference_labels"],
                "base_category": row["base"]["category"],
                "adapter_category": row["adapter"]["category"],
                "base_prediction_text": _trim_text(row["base_prediction_text"]),
                "adapter_prediction_text": _trim_text(row["adapter_prediction_text"]),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def _build_representative_examples(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "wrong_stable_id": _select_examples(rows, adapter_category="wrong_stable_id"),
        "label_only_citation": _select_examples(rows, adapter_category="label_only_citation"),
        "no_citation_signal": _select_examples(rows, adapter_category="no_citation_signal"),
    }


def analyze_citation_frontier(
    *,
    dataset_dir: Path,
    base_predictions_path: Path,
    adapter_predictions_path: Path,
    split_name: str = "test",
    task_type: str = "citation_grounded_moral_answer",
) -> dict[str, Any]:
    references = load_reference_examples(dataset_dir)
    base_predictions = load_prediction_rows(base_predictions_path)
    adapter_predictions = load_prediction_rows(adapter_predictions_path)

    rows: list[dict[str, Any]] = []
    for example_id, reference in sorted(references.items()):
        if str(reference.get("split")) != split_name:
            continue
        if str(reference.get("task_type")) != task_type:
            continue
        base_prediction = base_predictions.get(example_id)
        adapter_prediction = adapter_predictions.get(example_id)
        if base_prediction is None or adapter_prediction is None:
            raise KeyError(f"Missing prediction row for {example_id}")
        metadata = cast(dict[str, Any], reference.get("metadata", {}))
        reference_ids = [str(value) for value in metadata.get("source_passage_ids", [])]
        reference_labels = _normalize_labels(metadata.get("citation_labels"))
        base_prediction_text = str(base_prediction.get("assistant_text", ""))
        adapter_prediction_text = str(adapter_prediction.get("assistant_text", ""))
        rows.append(
            {
                "example_id": example_id,
                "tract": str(metadata.get("tract", "")),
                "tract_display_label": tract_display_name(str(metadata.get("tract", ""))),
                "relation_type": str(metadata.get("relation_type", "")),
                "question": _extract_user_text(reference),
                "reference_text": _extract_reference_text(reference),
                "reference_ids": reference_ids,
                "reference_labels": reference_labels,
                "base_prediction_text": base_prediction_text,
                "adapter_prediction_text": adapter_prediction_text,
                "base": classify_citation_signal(
                    base_prediction_text,
                    reference_ids=reference_ids,
                    reference_labels=reference_labels,
                ),
                "adapter": classify_citation_signal(
                    adapter_prediction_text,
                    reference_ids=reference_ids,
                    reference_labels=reference_labels,
                ),
            }
        )

    overall = {
        "base": _summary_from_rows(rows, "base"),
        "adapter": _summary_from_rows(rows, "adapter"),
    }
    by_tract = {
        "base": _by_bucket(rows, "tract", "base"),
        "adapter": _by_bucket(rows, "tract", "adapter"),
    }
    by_relation_type = {
        "base": _by_bucket(rows, "relation_type", "base"),
        "adapter": _by_bucket(rows, "relation_type", "adapter"),
    }

    recommendation = {
        "next_frontier": task_type,
        "thesis": (
            "The next expansion should target citation-grounded moral answers rather than "
            "widening doctrinal scope, because the current local baseline already shows strong "
            "virtue-concept and reviewed-relation gains while this user-style task remains the "
            "main unresolved traceability bottleneck."
        ),
        "under_five_hour_experiment": [
            "keep the current local-baseline as the public virtue-reasoning demo",
            "rerun this frontier audit after any focused mixture change",
            (
                "treat stable-id recovery on citation_grounded_moral_answer "
                "as the next local success criterion"
            ),
        ],
        "citation_frontier_recipe": {
            "config_path": (
                "configs/train/qwen2_5_1_5b_instruct_lora_mps_citation_frontier.yaml"
            ),
            "inference_config_path": (
                "configs/inference/qwen2_5_1_5b_instruct_citation_frontier_adapter_test.yaml"
            ),
            "max_steps": 20,
            "max_train_examples": 128,
            "max_eval_examples": 32,
            "train_task_type_quotas": {
                "citation_grounded_moral_answer": 64,
                "reviewed_relation_explanation": 24,
                "virtue_concept_explanation": 24,
                "passage_grounded_doctrinal_qa": 16,
            },
            "eval_task_type_quotas": {
                "citation_grounded_moral_answer": 16,
                "reviewed_relation_explanation": 8,
                "virtue_concept_explanation": 4,
                "passage_grounded_doctrinal_qa": 4,
            },
            "commands": [
                "make train-christian-virtue-qwen2-5-1-5b-citation-frontier",
                "make eval-christian-virtue-qwen2-5-1-5b-citation-frontier-test",
                "make compare-christian-virtue-qwen2-5-1-5b-citation-frontier",
                "make audit-christian-virtue-qwen2-5-1-5b-citation-frontier",
            ],
        },
    }

    return {
        "dataset_dir": _display_path(dataset_dir),
        "base_predictions_path": _display_path(base_predictions_path),
        "adapter_predictions_path": _display_path(adapter_predictions_path),
        "split_name": split_name,
        "task_type": task_type,
        "overall": overall,
        "by_tract": by_tract,
        "by_relation_type": by_relation_type,
        "representative_examples": _build_representative_examples(rows),
        "recommendation": recommendation,
    }


def write_citation_frontier_svg(
    analysis: dict[str, Any],
    output_path: Path,
    *,
    subtitle: str = (
        "Fast next-step audit for `citation_grounded_moral_answer` "
        "on the held-out test split"
    ),
    summary_text: str | None = None,
) -> Path:
    """Render a compact stacked-bar SVG for base vs adapter frontier failure modes."""

    return _write_citation_frontier_svg(
        analysis,
        output_path,
        subtitle=subtitle,
        summary_text=summary_text,
    )


def _write_citation_frontier_svg(
    analysis: dict[str, Any],
    output_path: Path,
    *,
    subtitle: str,
    summary_text: str | None = None,
) -> Path:
    """Render a compact stacked-bar SVG for base vs adapter frontier failure modes."""

    base_summary = cast(dict[str, Any], analysis["overall"]["base"])
    adapter_summary = cast(dict[str, Any], analysis["overall"]["adapter"])
    width = 1280
    height = 560
    card_x = 24.0
    card_y = 18.0
    card_width = width - (card_x * 2)
    card_height = height - 36.0
    chart_x = 330.0
    chart_width = 640.0
    bar_height = 28.0
    top_y = 286.0
    gap = 108.0
    exact_x = 1030.0
    signal_x = 1140.0
    base_signal = _format_percent(float(base_summary["any_citation_signal_rate"]))
    adapter_signal = _format_percent(float(adapter_summary["any_citation_signal_rate"]))
    adapter_exact = _format_percent(float(adapter_summary["exact_stable_id_match_rate"]))
    if summary_text is None:
        summary_text = (
            f"Adapter citation signal rises from {base_signal} to {adapter_signal} on the hardest "
            "held-out moral QA slice, while exact stable-id recovery remains "
            f"{adapter_exact}."
        )
    signal_progress = f"{base_signal} -> {adapter_signal}"
    summary_lines = _wrap_svg_text(summary_text, line_width=82)[:3]
    lines = [
        "<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
        "viewBox='0 0 {width} {height}' role='img' "
        "aria-label='Citation frontier failure-mode breakdown for base and adapter'>".format(
            width=width, height=height
        ),
        f"<rect x='0' y='0' width='{width}' height='{height}' fill='#f8fafc' />",
        f"<rect x='{card_x:.1f}' y='{card_y:.1f}' width='{card_width:.1f}' "
        f"height='{card_height:.1f}' fill='white' stroke='#d4d4d8' stroke-width='1.5' rx='18' />",
        "<text x='56' y='52' font-size='28' font-family='Georgia, serif' "
        "fill='#0f172a'>"
        "Citation frontier on user-style moral QA</text>",
        "<text x='56' y='78' font-size='13' font-family='Helvetica, Arial, sans-serif' "
        "fill='#475569'>"
        f"{html.escape(subtitle)}</text>",
        "<text x='56' y='100' font-size='12' font-family='Helvetica, Arial, sans-serif' "
        "font-weight='700' fill='#1d4ed8'>"
        "Small-model demo: Qwen/Qwen2.5-1.5B-Instruct (1.5B)</text>",
        "<rect x='56' y='120' width='672' height='78' fill='#f8fafc' stroke='#e2e8f0' "
        "stroke-width='1' rx='12' />",
        "<text x='74' y='142' font-size='11' font-family='Helvetica, Arial, sans-serif' "
        "font-weight='700' fill='#334155'>What this figure isolates</text>",
        "<rect x='760' y='120' width='448' height='78' rx='14' fill='#ecfdf5' "
        "stroke='#10b981' stroke-width='1.5' />",
        "<text x='784' y='144' font-size='11' font-family='Helvetica, Arial, sans-serif' "
        "font-weight='700' fill='#047857'>Headline shift</text>",
        "<text x='784' y='168' font-size='26' font-family='Helvetica, Arial, sans-serif' "
        "font-weight='700' fill='#065f46'>"
        f"{signal_progress}</text>",
        f"<text x='784' y='186' font-size='12' font-family='Helvetica, Arial, sans-serif' "
        "fill='#334155'>Any citation signal; exact stable-id recovery remains "
        f"{adapter_exact}.</text>",
        "<text x='56' y='228' font-size='13' font-family='Helvetica, Arial, sans-serif' "
        "fill='#475569'>Failure-mode legend:</text>",
    ]
    for line_index, line_text in enumerate(summary_lines):
        lines.append(
            f"<text x='74' y='{162 + (line_index * 16)}' font-size='12' "
            "font-family='Helvetica, Arial, sans-serif' fill='#334155'>"
            f"{html.escape(line_text)}</text>"
        )
    legend_x = 176.0
    legend_y = 224.0
    for index, category in enumerate(CATEGORY_ORDER):
        x = legend_x + index * 190.0
        lines.append(
            f"<rect x='{x:.1f}' y='{legend_y - 11:.1f}' width='16' height='16' "
            f"fill='{CATEGORY_COLORS[category]}' rx='4' />"
        )
        lines.append(
            f"<text x='{x + 24:.1f}' y='{legend_y + 2:.1f}' font-size='12' "
            "font-family='Helvetica, Arial, sans-serif' fill='#374151'>"
            f"{html.escape(CATEGORY_DISPLAY_NAMES[category])}</text>"
        )
    lines.extend(
        [
            f"<text x='{exact_x:.1f}' y='{top_y - 34:.1f}' font-size='11' "
            "font-family='Helvetica, Arial, sans-serif' font-weight='700' "
            "fill='#334155'>exact stable id</text>",
            f"<text x='{signal_x:.1f}' y='{top_y - 34:.1f}' font-size='11' "
            "font-family='Helvetica, Arial, sans-serif' font-weight='700' "
            "fill='#334155'>Any citation signal</text>",
            f"<line x1='{exact_x - 18:.1f}' y1='{top_y - 46:.1f}' "
            f"x2='{exact_x - 18:.1f}' y2='{height - 54:.1f}' stroke='#e2e8f0' stroke-width='1' />",
            f"<line x1='{signal_x - 18:.1f}' y1='{top_y - 46:.1f}' "
            f"x2='{signal_x - 18:.1f}' y2='{height - 54:.1f}' stroke='#e2e8f0' stroke-width='1' />",
            f"<line x1='{chart_x:.1f}' y1='{top_y - 22:.1f}' "
            f"x2='{chart_x + chart_width:.1f}' y2='{top_y - 22:.1f}' "
            "stroke='#cbd5e1' stroke-width='1.5' />",
        ]
    )
    for tick_ratio in [0.0, 0.25, 0.5, 0.75, 1.0]:
        tick_x = chart_x + chart_width * tick_ratio
        lines.append(
            f"<line x1='{tick_x:.1f}' y1='{top_y - 22:.1f}' x2='{tick_x:.1f}' "
            f"y2='{top_y + gap + bar_height + 32:.1f}' "
            "stroke='#eef2f7' stroke-width='1' />"
        )
        lines.append(
            f"<text x='{tick_x:.1f}' y='{top_y + gap + bar_height + 52:.1f}' font-size='11' "
            "font-family='Helvetica, Arial, sans-serif' text-anchor='middle' fill='#64748b'>"
            f"{tick_ratio * 100:.0f}%</text>"
        )
    for index, model_key in enumerate(["base", "adapter"]):
        summary = cast(dict[str, Any], analysis["overall"][model_key])
        y = top_y + index * gap
        model_name = "Untuned model" if model_key == "base" else "Citation-frontier adapter"
        exact_rate = _format_percent(float(summary["exact_stable_id_match_rate"]))
        signal_rate = _format_percent(float(summary["any_citation_signal_rate"]))
        count = int(summary["count"])
        lines.append(
            f"<text x='56' y='{y + 6:.1f}' font-size='15' "
            "font-family='Helvetica, Arial, sans-serif' "
            "font-weight='700' fill='#111827'>"
            f"{model_name}</text>"
        )
        lines.append(
            f"<text x='56' y='{y + 26:.1f}' font-size='12' "
            "font-family='Helvetica, Arial, sans-serif' "
            "fill='#64748b'>"
            f"n={count} held-out moral-QA prompts</text>"
        )
        lines.append(
            f"<rect x='{chart_x:.1f}' y='{y:.1f}' width='{chart_width:.1f}' "
            f"height='{bar_height:.1f}' fill='#e5e7eb' rx='14' />"
        )
        cursor_x = chart_x
        for category in CATEGORY_ORDER:
            fraction = float(summary["category_rates"][category])
            segment_width = chart_width * fraction
            if segment_width <= 0:
                continue
            lines.append(
                f"<rect x='{cursor_x:.1f}' y='{y:.1f}' width='{segment_width:.1f}' "
                f"height='{bar_height:.1f}' fill='{CATEGORY_COLORS[category]}' rx='0' />"
            )
            if segment_width >= 70.0:
                lines.append(
                    f"<text x='{cursor_x + segment_width / 2:.1f}' y='{y + 18:.1f}' "
                    "font-size='11' font-family='Helvetica, Arial, sans-serif' "
                    "text-anchor='middle' fill='white' font-weight='700'>"
                    f"{fraction * 100:.1f}%</text>"
                )
            cursor_x += segment_width
        lines.append(
            f"<text x='{exact_x:.1f}' y='{y + 18:.1f}' font-size='12' "
            "font-family='Helvetica, Arial, sans-serif' font-weight='700' fill='#2563eb'>"
            f"{exact_rate}</text>"
        )
        lines.append(
            f"<text x='{signal_x:.1f}' y='{y + 18:.1f}' font-size='12' "
            "font-family='Helvetica, Arial, sans-serif' font-weight='700' fill='#0f766e'>"
            f"{signal_rate}</text>"
        )
    lines.append("</svg>")
    lines.insert(
        len(lines) - 1,
        f"<text x='{chart_x + chart_width / 2:.1f}' y='{height - 26:.1f}' font-size='12' "
        "font-family='Helvetica, Arial, sans-serif' text-anchor='middle' fill='#475569'>"
        "Share of held-out `citation_grounded_moral_answer` prompts</text>",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _wrap_svg_text(value: str, *, line_width: int) -> list[str]:
    normalized = " ".join(value.split())
    if not normalized:
        return []
    return wrap(normalized, width=line_width, break_long_words=False, break_on_hyphens=False)


def write_citation_frontier_report(
    analysis: dict[str, Any],
    output_path: Path,
    *,
    figure_path: Path | None = None,
) -> Path:
    """Write a maintainer-facing markdown report for the current citation frontier."""

    base_overall = cast(dict[str, Any], analysis["overall"]["base"])
    adapter_overall = cast(dict[str, Any], analysis["overall"]["adapter"])
    lines = [
        "# Christian Virtue Citation Frontier Audit",
        "",
        "## Why This Is The Next Step",
        "",
        "The current local 1.5B baseline already demonstrates real Thomist virtue alignment on "
        "virtue-concept and reviewed-relation tasks. The next logical expansion is therefore not "
        "more doctrinal scope. It is the narrow frontier that still blocks the assistant from "
        "feeling complete: `citation_grounded_moral_answer` on held-out user-style prompts.",
        "",
        "This audit is intentionally fast. It reuses the canonical base and adapter predictions, "
        "runs in seconds, and tells us where the next under-five-hour local experiment should "
        "focus.",
        "",
        "## Canonical Scope",
        "",
        f"- Split: `{analysis['split_name']}`",
        f"- Target task family: `{analysis['task_type']}`",
        f"- Dataset: `{analysis['dataset_dir']}`",
        f"- Base predictions: `{analysis['base_predictions_path']}`",
        f"- Adapter predictions: `{analysis['adapter_predictions_path']}`",
        "",
        "## Core Readout",
        "",
        (
            "| Model | Count | Exact stable id | Any citation signal | "
            "Label-only citation | Wrong stable id | No citation signal |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| Base | `{base_overall['count']}` | "
            f"`{float(base_overall['exact_stable_id_match_rate']) * 100:.1f}%` | "
            f"`{float(base_overall['any_citation_signal_rate']) * 100:.1f}%` | "
            f"`{float(base_overall['label_only_citation_rate']) * 100:.1f}%` | "
            f"`{float(base_overall['wrong_stable_id_rate']) * 100:.1f}%` | "
            f"`{float(base_overall['no_citation_signal_rate']) * 100:.1f}%` |"
        ),
        (
            f"| Adapter | `{adapter_overall['count']}` | "
            f"`{float(adapter_overall['exact_stable_id_match_rate']) * 100:.1f}%` | "
            f"`{float(adapter_overall['any_citation_signal_rate']) * 100:.1f}%` | "
            f"`{float(adapter_overall['label_only_citation_rate']) * 100:.1f}%` | "
            f"`{float(adapter_overall['wrong_stable_id_rate']) * 100:.1f}%` | "
            f"`{float(adapter_overall['no_citation_signal_rate']) * 100:.1f}%` |"
        ),
        "",
    ]
    if figure_path is not None:
        lines.extend(
            [
                f"![Citation frontier failure modes]({figure_path})",
                "",
                "*Figure. Base-vs-adapter citation behavior on the hardest user-style moral QA "
                "slice. The key question is not whether the model can sound Thomistic; it is "
                "whether it can recover the right stable passage id when asked in natural "
                "language.*",
                "",
            ]
        )
    lines.extend(
        [
        "Key takeaway:",
            "",
            (
                "- The adapter has already learned a meaningful amount of "
                "citation-seeking behavior on this hard slice."
            ),
            (
                "- But the remaining failures are mostly retrieval and "
                "citation-format failures, not evidence-scope failures."
            ),
            (
                "- So the next experiment should target citation recovery "
                "within the same virtue dataset, not broader corpus expansion."
            ),
            "",
            "## Adapter By Tract",
            "",
            "| Tract | Count | Exact stable id | Any citation signal | No citation signal |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for tract, summary in cast(dict[str, Any], analysis["by_tract"]["adapter"]).items():
        lines.append(
            f"| {tract_display_name(tract)} | `{summary['count']}` | "
            f"`{float(summary['exact_stable_id_match_rate']) * 100:.1f}%` | "
            f"`{float(summary['any_citation_signal_rate']) * 100:.1f}%` | "
            f"`{float(summary['no_citation_signal_rate']) * 100:.1f}%` |"
        )
    lines.extend(
        [
            "",
            "## Adapter By Relation Type",
            "",
            (
                "| Relation type | Count | Any citation signal | "
                "Wrong stable id | No citation signal |"
            ),
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    relation_rows = list(cast(dict[str, Any], analysis["by_relation_type"]["adapter"]).items())[:10]
    for relation_type, summary in relation_rows:
        lines.append(
            f"| `{relation_type}` | `{summary['count']}` | "
            f"`{float(summary['any_citation_signal_rate']) * 100:.1f}%` | "
            f"`{float(summary['wrong_stable_id_rate']) * 100:.1f}%` | "
            f"`{float(summary['no_citation_signal_rate']) * 100:.1f}%` |"
        )
    lines.extend(["", "## Representative Failure Modes", ""])
    for section_key, section_title in [
        ("wrong_stable_id", "Wrong Stable Id"),
        ("label_only_citation", "Label-Only Citation"),
        ("no_citation_signal", "No Citation Signal"),
    ]:
        examples = cast(list[dict[str, Any]], analysis["representative_examples"][section_key])
        lines.extend([f"### {section_title}", ""])
        if not examples:
            lines.extend(["- None in this run.", ""])
            continue
        for example in examples:
            lines.extend(
                [
                    f"#### {example['example_id']}",
                    "",
                    f"- Tract: {tract_display_name(str(example['tract']))}",
                    f"- Relation type: `{example['relation_type']}`",
                    f"- User question: {example['question']}",
                    f"- Reference ids: `{', '.join(example['reference_ids'])}`",
                    f"- Base category: `{example['base_category']}`",
                    f"- Adapter category: `{example['adapter_category']}`",
                    "",
                    "Base prediction:",
                    "",
                    f"> {example['base_prediction_text']}",
                    "",
                    "Adapter prediction:",
                    "",
                    f"> {example['adapter_prediction_text']}",
                    "",
                ]
            )
    recommendation = cast(dict[str, Any], analysis["recommendation"])
    lines.extend(
        [
            "## Final Next-Step Thesis",
            "",
            recommendation["thesis"],
            "",
            "The concrete next local expansion should therefore be:",
            "",
        ]
    )
    for step in cast(list[str], recommendation["under_five_hour_experiment"]):
        lines.append(f"- {step}")
    recipe = cast(dict[str, Any], recommendation["citation_frontier_recipe"])
    lines.extend(
        [
            "",
            "## Recommended Citation-Frontier Recipe",
            "",
            "Keep the Christian virtue dataset fixed and strengthen the local recipe only through "
            "a more citation-heavy but still mixed small-run subset.",
            "",
            f"- Training config: `{recipe['config_path']}`",
            f"- Adapter inference config: `{recipe['inference_config_path']}`",
            f"- Max steps: `{recipe['max_steps']}`",
            f"- Max train examples: `{recipe['max_train_examples']}`",
            f"- Max eval examples: `{recipe['max_eval_examples']}`",
            (
                "- Train task quotas: "
                + ", ".join(
                    f"`{task}={count}`"
                    for task, count in cast(
                        dict[str, int], recipe["train_task_type_quotas"]
                    ).items()
                )
            ),
            (
                "- Eval task quotas: "
                + ", ".join(
                    f"`{task}={count}`"
                    for task, count in cast(
                        dict[str, int], recipe["eval_task_type_quotas"]
                    ).items()
                )
            ),
            "",
            "Suggested command sequence:",
            "",
        ]
    )
    for command in cast(list[str], recipe["commands"]):
        lines.append(f"- `{command}`")
    lines.extend(
        [
            "",
            "This recipe keeps the same small-model local budget as the canonical baseline, but it "
            "puts half of the train subset on citation-grounded moral answers while preserving "
            "relation, concept, and passage-grounded anchors. That makes it the cleanest next "
            "experiment if the goal is better Thomist virtue behavior with stronger stable-id "
            "traceability.",
            "",
            "That is the cleanest expansion of this research program: keep the dataset fixed, "
            "keep the Thomist virtue target fixed, and push the next fast loop directly at the "
            "remaining citation-retrieval bottleneck.",
            "",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def write_citation_frontier_artifacts(
    *,
    analysis: dict[str, Any],
    report_path: Path,
    metrics_path: Path,
    figure_path: Path | None = None,
) -> dict[str, str]:
    """Write the full fast frontier-audit artifact set."""

    if figure_path is not None:
        write_citation_frontier_svg(analysis, figure_path)
        figure_reference = str(figure_path.relative_to(report_path.parent))
    else:
        figure_reference = None
    write_json(metrics_path, analysis)
    write_citation_frontier_report(
        analysis,
        report_path,
        figure_path=(Path(figure_reference) if figure_reference is not None else None),
    )
    return {
        "metrics_path": str(metrics_path),
        "report_path": str(report_path),
        "figure_path": str(figure_path) if figure_path is not None else "",
    }
