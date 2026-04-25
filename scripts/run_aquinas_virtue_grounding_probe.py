"""Run a position-neutral Aquinas grounding probe for the Christian virtue adapter."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from summa_moral_graph.sft.config import InferenceConfig
from summa_moral_graph.sft.inference import (
    _align_generation_config,
    _clean_assistant_text,
    _render_prompt,
    ensure_inference_dependencies,
    resolve_inference_runtime,
)
from summa_moral_graph.sft.run_layout import (
    build_environment_snapshot,
    iso_timestamp,
    run_artifacts_for_dir,
    write_config_snapshot,
    write_json,
    write_jsonl,
)
from summa_moral_graph.sft.runtime import detect_torch_availability
from summa_moral_graph.sft.utils import RELATION_FRAGMENTS, extract_passage_ids
from summa_moral_graph.utils.paths import REPO_ROOT

SYSTEM_PROMPT = (
    "You are answering a source-grounded Aquinas Christian virtue benchmark. "
    "Give a short answer in Aquinas's moral categories. Name the relevant subject, "
    "relation, and object when the question asks for them. Stay evidence-bounded, "
    "avoid generic self-help language, and end with exact Summa segment ids."
)
DEFAULT_DATASET_PATH = REPO_ROOT / "data/processed/sft/exports/christian_virtue_v1/test.jsonl"
GENERIC_DRIFT_PHRASES = [
    "authentic self",
    "boundaries",
    "follow your heart",
    "mental health",
    "mindfulness",
    "personal growth",
    "safe space",
    "self-care",
    "therapy",
    "toxic",
    "wellness",
    "your truth",
]
STIFF_TEMPLATE_PHRASES = [
    "according to the reviewed passage",
    "reviewed claim",
    "reviewed doctrinal",
    "support type",
]
AQUINAS_CATEGORY_TERMS = [
    "act",
    "appetite",
    "charity",
    "contrary",
    "deficiency",
    "end",
    "excess",
    "faith",
    "fortitude",
    "habit",
    "hope",
    "justice",
    "law",
    "object",
    "part",
    "passion",
    "prudence",
    "reason",
    "sin",
    "temperance",
    "vice",
    "virtue",
    "will",
]
RELATION_SIGNAL_PHRASES: dict[str, list[str]] = {
    "act_of": ["act of"],
    "annexed_to": ["annexed to"],
    "case_of": ["case of"],
    "caused_by": ["caused by"],
    "commands_act_of": ["commands", "act of"],
    "contrary_to": ["contrary to", "opposed to"],
    "deficiency_opposed_to": ["deficiency", "opposed to"],
    "directed_to": ["directed to"],
    "excess_opposed_to": ["excess", "opposed to"],
    "has_act": ["act", "has"],
    "has_object": ["object"],
    "integral_part_of": ["integral part", "part of"],
    "opposed_by": ["opposed by", "opposed"],
    "part_of": ["part of"],
    "part_of_fortitude": ["part of fortitude", "part of"],
    "potential_part_of": ["potential part", "part of"],
    "precept_of": ["precept of"],
    "regulated_by": ["regulated by"],
    "related_to_fortitude": ["fortitude", "related"],
    "requires": ["requires"],
    "requires_restitution": ["requires restitution", "restitution"],
    "resides_in": ["resides in", "will", "reason"],
    "species_of": ["species of"],
    "subjective_part_of": ["subjective part", "part of"],
    "tempted_by": ["tempted by", "temptation"],
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "for",
    "in",
    "is",
    "of",
    "or",
    "the",
    "through",
    "to",
    "with",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name-or-path", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--adapter-path")
    parser.add_argument(
        "--prompt-mode",
        choices=["canonical", "probe"],
        default="canonical",
        help=(
            "Use the held-out dataset's original system/user prompt, or a stricter "
            "probe-specific system prompt."
        ),
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=0,
        help="Maximum examples to run; 0 means the full held-out split.",
    )
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--runtime-backend", default="mps")
    parser.add_argument("--torch-dtype", default="float16")
    parser.add_argument("--max-new-tokens", type=int, default=192)
    parser.add_argument("--trust-remote-code", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_path = Path(args.dataset_path).resolve()
    output_dir = Path(args.output_dir).resolve()
    adapter_path = Path(args.adapter_path).resolve() if args.adapter_path else None
    rows = build_probe_inputs(
        dataset_path,
        max_examples=args.max_examples,
        prompt_mode=args.prompt_mode,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_inputs_path = output_dir / "benchmark_inputs.jsonl"
    write_jsonl(benchmark_inputs_path, rows)
    config_snapshot_path = write_config_snapshot(
        output_dir,
        config_path=None,
        payload={
            "adapter_path": str(adapter_path) if adapter_path is not None else None,
            "dataset_path": str(dataset_path),
            "max_examples": args.max_examples,
            "max_new_tokens": args.max_new_tokens,
            "model_name_or_path": args.model_name_or_path,
            "prompt_mode": args.prompt_mode,
            "probe_name": "aquinas_virtue_grounding_probe",
            "runtime_backend": args.runtime_backend,
            "seed": args.seed,
            "torch_dtype": args.torch_dtype,
            "trust_remote_code": args.trust_remote_code,
        },
    )
    manifest = run_generation(
        rows=rows,
        output_dir=output_dir,
        benchmark_inputs_path=benchmark_inputs_path,
        config_snapshot_path=config_snapshot_path,
        model_name_or_path=args.model_name_or_path,
        adapter_path=adapter_path,
        runtime_backend=args.runtime_backend,
        torch_dtype=args.torch_dtype,
        max_new_tokens=args.max_new_tokens,
        seed=args.seed,
        prompt_mode=args.prompt_mode,
        trust_remote_code=args.trust_remote_code,
        dataset_path=dataset_path,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


def build_probe_inputs(
    dataset_path: Path,
    *,
    max_examples: int = 0,
    prompt_mode: str = "canonical",
) -> list[dict[str, Any]]:
    rows = _load_jsonl(dataset_path)
    if max_examples > 0:
        rows = rows[:max_examples]
    probe_rows: list[dict[str, Any]] = []
    for row in rows:
        user_prompt = _extract_user_prompt(row)
        metadata = row["metadata"]
        source_passage_ids = list(metadata.get("source_passage_ids") or [])
        messages = _build_probe_messages(row, user_prompt=user_prompt, prompt_mode=prompt_mode)
        probe_rows.append(
            {
                "citation_labels": list(metadata.get("citation_labels") or []),
                "example_id": str(row["example_id"]),
                "expected_object_label": str(metadata.get("object_label") or ""),
                "expected_relation_type": str(metadata.get("relation_type") or ""),
                "expected_source_passage_ids": source_passage_ids,
                "expected_subject_label": str(metadata.get("subject_label") or ""),
                "messages": messages,
                "metadata": metadata,
                "prompt_mode": prompt_mode,
                "split": str(row.get("split") or "test"),
                "task_type": str(row.get("task_type") or metadata.get("task_type") or ""),
                "tract": str(metadata.get("tract") or ""),
                "user_prompt": user_prompt,
            }
        )
    return probe_rows


def run_generation(
    *,
    rows: list[dict[str, Any]],
    output_dir: Path,
    benchmark_inputs_path: Path,
    config_snapshot_path: Path,
    model_name_or_path: str,
    adapter_path: Path | None,
    runtime_backend: str,
    torch_dtype: str,
    max_new_tokens: int,
    seed: int,
    prompt_mode: str,
    trust_remote_code: bool,
    dataset_path: Path,
) -> dict[str, Any]:
    config = InferenceConfig.model_validate(
        {
            "run_name": "aquinas-virtue-grounding-probe",
            "model_name_or_path": model_name_or_path,
            "dataset_dir": str(output_dir),
            "split_names": ["test"],
            "output_dir": str(output_dir),
            "adapter_path": str(adapter_path) if adapter_path is not None else None,
            "trust_remote_code": trust_remote_code,
            "runtime_backend": runtime_backend,
            "torch_dtype": torch_dtype,
            "load_in_4bit": False,
            "max_new_tokens": max_new_tokens,
            "do_sample": False,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": seed,
        }
    )
    ensure_inference_dependencies(config)
    runtime = _resolve_runtime(config)
    artifacts = run_artifacts_for_dir(output_dir)
    start_time = iso_timestamp()
    environment = build_environment_snapshot(
        workspace_root=REPO_ROOT,
        resolved_device=runtime.device_type,
        torch_dtype=runtime.torch_dtype_name,
    )
    environment["benchmark"] = {
        "dataset_path": str(dataset_path),
        "name": "aquinas_virtue_grounding_probe",
        "prompt_mode": prompt_mode,
        "scoring": "deterministic citation and lexical grounding checks",
    }
    write_json(artifacts.environment_path, environment)

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    prediction_rows = _load_jsonl(artifacts.partial_predictions_path)
    completed_ids = {str(row["example_id"]) for row in prediction_rows}
    remaining_rows = [row for row in rows if str(row["example_id"]) not in completed_ids]

    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path,
        trust_remote_code=trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token or tokenizer.unk_token

    model: Any = AutoModelForCausalLM.from_pretrained(
        model_name_or_path,
        trust_remote_code=trust_remote_code,
        torch_dtype=getattr(torch, runtime.torch_dtype_name),
        low_cpu_mem_usage=True,
    )
    if adapter_path is not None:
        if not adapter_path.exists():
            raise FileNotFoundError(f"Adapter path not found: {adapter_path}")
        model = PeftModel.from_pretrained(model, str(adapter_path))
    model = model.to(runtime.device_type)
    _align_generation_config(model, config)
    model.eval()
    set_seed(seed)

    total_rows = len(rows)
    if prediction_rows:
        _log_event("resume_loaded", completed=len(prediction_rows), total=total_rows)
    device = next(model.parameters()).device
    for index, row in enumerate(remaining_rows, start=len(prediction_rows) + 1):
        prompt_text = _render_prompt(tokenizer, row["messages"])
        tokenized = tokenizer(prompt_text, return_tensors="pt")
        tokenized = {key: value.to(device) for key, value in tokenized.items()}
        with torch.no_grad():
            generated = model.generate(
                **tokenized,
                do_sample=False,
                eos_token_id=tokenizer.eos_token_id,
                max_new_tokens=max_new_tokens,
                pad_token_id=tokenizer.pad_token_id,
                repetition_penalty=1.0,
            )
        input_length = int(tokenized["input_ids"].shape[-1])
        assistant_text = _clean_assistant_text(
            tokenizer.decode(generated[0][input_length:], skip_special_tokens=True)
        )
        prediction = score_prediction(
            {
                "adapter_path": str(adapter_path) if adapter_path is not None else None,
                "assistant_text": assistant_text,
                "example_id": row["example_id"],
                "expected_object_label": row["expected_object_label"],
                "expected_relation_type": row["expected_relation_type"],
                "expected_source_passage_ids": row["expected_source_passage_ids"],
                "expected_subject_label": row["expected_subject_label"],
                "metadata": row["metadata"],
                "model_name_or_path": model_name_or_path,
                "split": row["split"],
                "task_type": row["task_type"],
                "tract": row["tract"],
                "user_prompt": row["user_prompt"],
            }
        )
        prediction_rows.append(prediction)
        with artifacts.partial_predictions_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(prediction, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        if index == total_rows or index % 10 == 0:
            _log_event(
                "aquinas_grounding_probe_progress",
                completed=index,
                remaining=total_rows - index,
                total=total_rows,
            )

    write_jsonl(artifacts.predictions_path, prediction_rows)
    if artifacts.partial_predictions_path.exists():
        artifacts.partial_predictions_path.unlink()
    metrics = build_metrics(prediction_rows)
    write_json(artifacts.metrics_path, metrics)
    write_report(
        artifacts.report_path,
        metrics,
        adapter_path=adapter_path,
        dataset_path=dataset_path,
    )
    end_time = iso_timestamp()
    versions = environment["versions"]
    manifest = {
        "adapter_path": str(adapter_path) if adapter_path is not None else None,
        "benchmark_count": len(rows),
        "benchmark_inputs_path": str(benchmark_inputs_path),
        "config_snapshot_path": str(config_snapshot_path),
        "dataset_path": str(dataset_path),
        "end_time": end_time,
        "environment_path": str(artifacts.environment_path),
        "git_commit": environment["git_commit"],
        "max_new_tokens": max_new_tokens,
        "metrics_path": str(artifacts.metrics_path),
        "model_name_or_path": model_name_or_path,
        "peft_version": versions["peft"],
        "prompt_mode": prompt_mode,
        "predictions_path": str(artifacts.predictions_path),
        "python_version": environment["platform"]["python_version"],
        "report_path": str(artifacts.report_path),
        "resolved_device": runtime.device_type,
        "run_id": output_dir.name,
        "start_time": start_time,
        "torch_dtype": runtime.torch_dtype_name,
        "torch_version": versions["torch"],
        "transformers_version": versions["transformers"],
    }
    write_json(artifacts.run_manifest_path, manifest)
    return manifest


def score_prediction(row: dict[str, Any]) -> dict[str, Any]:
    assistant_text = str(row["assistant_text"])
    expected_ids = list(row.get("expected_source_passage_ids") or [])
    expected_id_set = set(expected_ids)
    predicted_ids = extract_passage_ids(assistant_text)
    predicted_id_set = set(predicted_ids)
    citation_overlap_count = len(expected_id_set & predicted_id_set)
    citation_overlap = citation_overlap_count / len(expected_id_set) if expected_id_set else 0.0
    subject_present = label_present(str(row.get("expected_subject_label") or ""), assistant_text)
    object_present = label_present(str(row.get("expected_object_label") or ""), assistant_text)
    relation_present = relation_signal_present(
        str(row.get("expected_relation_type") or ""),
        assistant_text,
    )
    category_signal = aquinas_category_signal_present(assistant_text)
    generic_drift = contains_any_phrase(assistant_text, GENERIC_DRIFT_PHRASES)
    stiff_template_phrase = contains_any_phrase(assistant_text, STIFF_TEMPLATE_PHRASES)
    citation_exact = bool(expected_id_set) and predicted_id_set == expected_id_set
    citation_partial = bool(expected_id_set & predicted_id_set)
    scores = {
        "aquinas_category_signal": category_signal,
        "citation_exact": citation_exact,
        "citation_partial": citation_partial,
        "citation_present": bool(predicted_ids),
        "no_generic_drift": not generic_drift,
        "object_label_present": object_present,
        "relation_signal_present": relation_present,
        "subject_label_present": subject_present,
    }
    grounding_score = (
        (0.40 if citation_exact else 0.0)
        + (0.10 if citation_partial else 0.0)
        + (0.15 if subject_present else 0.0)
        + (0.15 if object_present else 0.0)
        + (0.10 if relation_present else 0.0)
        + (0.05 if category_signal else 0.0)
        + (0.05 if not generic_drift else 0.0)
    )
    return {
        **row,
        "aquinas_category_signal": category_signal,
        "citation_exact": citation_exact,
        "citation_overlap": citation_overlap,
        "citation_overlap_count": citation_overlap_count,
        "citation_partial": citation_partial,
        "citation_present": bool(predicted_ids),
        "generic_drift": generic_drift,
        "grounding_score": grounding_score,
        "object_label_present": object_present,
        "predicted_source_passage_ids": predicted_ids,
        "relation_signal_present": relation_present,
        "scoring_flags": scores,
        "stiff_template_phrase": stiff_template_phrase,
        "subject_label_present": subject_present,
    }


def build_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "by_relation_type": _summary_by(rows, "expected_relation_type"),
        "by_support_type": _summary_by_support_type(rows),
        "by_task_type": _summary_by(rows, "task_type"),
        "by_tract": _summary_by(rows, "tract"),
        "overall": _summary(rows),
    }


def write_report(
    path: Path,
    metrics: dict[str, Any],
    *,
    adapter_path: Path | None,
    dataset_path: Path,
) -> Path:
    lines = [
        "# Aquinas Virtue Grounding Probe",
        "",
        f"- Dataset: `{dataset_path}`.",
        f"- Adapter: `{adapter_path}`." if adapter_path is not None else "- Adapter: none.",
        "- Protocol: deterministic generation over held-out Aquinas relation prompts.",
        "- Scoring: exact segment ids plus lexical checks for subject, object, relation, "
        "Aquinas category language, and generic drift.",
        "",
        "## Overall",
        "",
        _summary_bullets(metrics["overall"]),
        "",
        "## By Task Type",
        "",
        _summary_table(metrics["by_task_type"]),
        "",
        "## By Tract",
        "",
        _summary_table(metrics["by_tract"]),
        "",
        "## By Relation Type",
        "",
        _summary_table(metrics["by_relation_type"]),
        "",
        "## By Support Type",
        "",
        _summary_table(metrics["by_support_type"]),
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def label_present(label: str, text: str) -> bool:
    label_normalized = normalize_text(label)
    text_normalized = normalize_text(text)
    if not label_normalized:
        return False
    if label_normalized in text_normalized:
        return True
    label_tokens = content_tokens(label)
    text_tokens = set(content_tokens(text))
    if not label_tokens:
        return False
    min_required = 1 if len(label_tokens) == 1 else max(2, len(label_tokens) - 1)
    return sum(1 for token in label_tokens if token in text_tokens) >= min_required


def relation_signal_present(relation_type: str, text: str) -> bool:
    if not relation_type:
        return False
    text_normalized = normalize_text(text)
    phrases = list(RELATION_SIGNAL_PHRASES.get(relation_type, []))
    fragment = RELATION_FRAGMENTS.get(relation_type)
    if fragment:
        phrases.append(re.sub(r"\{object\}", "", fragment))
    if any(normalize_text(phrase) in text_normalized for phrase in phrases if phrase.strip()):
        return True
    relation_tokens = [token for token in relation_type.split("_") if token not in STOPWORDS]
    text_tokens = set(content_tokens(text))
    if not relation_tokens:
        return False
    return sum(1 for token in relation_tokens if token in text_tokens) >= min(
        2,
        len(relation_tokens),
    )


def aquinas_category_signal_present(text: str) -> bool:
    text_tokens = set(content_tokens(text))
    return any(term in text_tokens for term in AQUINAS_CATEGORY_TERMS)


def contains_any_phrase(text: str, phrases: Sequence[str]) -> bool:
    text_normalized = normalize_text(text)
    return any(normalize_text(phrase) in text_normalized for phrase in phrases)


def normalize_text(value: str) -> str:
    return " ".join(content_tokens(value))


def content_tokens(value: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", value.lower().replace("'", ""))
        if token not in STOPWORDS
    ]


def _summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    count = len(materialized)
    if count == 0:
        return {
            "aquinas_category_signal_rate": 0.0,
            "citation_exact_match": 0.0,
            "citation_partial_match": 0.0,
            "citation_presence": 0.0,
            "citation_overlap": 0.0,
            "count": 0,
            "generic_drift_rate": 0.0,
            "grounding_score": 0.0,
            "object_label_presence": 0.0,
            "relation_signal_presence": 0.0,
            "stiff_template_phrase_rate": 0.0,
            "subject_label_presence": 0.0,
        }
    return {
        "aquinas_category_signal_rate": _rate(materialized, "aquinas_category_signal"),
        "citation_exact_match": _rate(materialized, "citation_exact"),
        "citation_partial_match": _rate(materialized, "citation_partial"),
        "citation_presence": _rate(materialized, "citation_present"),
        "citation_overlap": _mean_float(materialized, "citation_overlap"),
        "count": count,
        "generic_drift_rate": _rate(materialized, "generic_drift"),
        "grounding_score": _mean_float(materialized, "grounding_score"),
        "object_label_presence": _rate(materialized, "object_label_present"),
        "relation_signal_presence": _rate(materialized, "relation_signal_present"),
        "stiff_template_phrase_rate": _rate(materialized, "stiff_template_phrase"),
        "subject_label_presence": _rate(materialized, "subject_label_present"),
    }


def _summary_by(rows: Sequence[dict[str, Any]], field_name: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field_name) or "unknown")].append(row)
    return {key: _summary(value) for key, value in sorted(grouped.items())}


def _summary_by_support_type(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        support_types = row.get("metadata", {}).get("support_types") or ["unknown"]
        for support_type in support_types:
            grouped[str(support_type)].append(row)
    return {key: _summary(value) for key, value in sorted(grouped.items())}


def _rate(rows: Sequence[dict[str, Any]], field_name: str) -> float:
    return sum(1 for row in rows if row[field_name]) / len(rows)


def _mean_float(rows: Sequence[dict[str, Any]], field_name: str) -> float:
    return sum(float(row[field_name]) for row in rows) / len(rows)


def _summary_bullets(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- Count: {summary['count']}",
            f"- Grounding score: `{summary['grounding_score']:.3f}`",
            f"- Citation exact match: `{summary['citation_exact_match']:.3f}`",
            f"- Citation partial match: `{summary['citation_partial_match']:.3f}`",
            f"- Citation presence: `{summary['citation_presence']:.3f}`",
            f"- Citation overlap: `{summary['citation_overlap']:.3f}`",
            f"- Subject label presence: `{summary['subject_label_presence']:.3f}`",
            f"- Object label presence: `{summary['object_label_presence']:.3f}`",
            f"- Relation signal presence: `{summary['relation_signal_presence']:.3f}`",
            f"- Aquinas category signal: `{summary['aquinas_category_signal_rate']:.3f}`",
            f"- Generic drift rate: `{summary['generic_drift_rate']:.3f}`",
            f"- Stiff template phrase rate: `{summary['stiff_template_phrase_rate']:.3f}`",
        ]
    )


def _summary_table(grouped: dict[str, dict[str, Any]]) -> str:
    if not grouped:
        return "_No rows._"
    lines = [
        "| group | n | score | exact | partial | cite | subj | obj | rel | cat | generic "
        "| template |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, summary in grouped.items():
        lines.append(
            "| "
            f"{key} | "
            f"{summary['count']} | "
            f"{summary['grounding_score']:.3f} | "
            f"{summary['citation_exact_match']:.3f} | "
            f"{summary['citation_partial_match']:.3f} | "
            f"{summary['citation_presence']:.3f} | "
            f"{summary['subject_label_presence']:.3f} | "
            f"{summary['object_label_presence']:.3f} | "
            f"{summary['relation_signal_presence']:.3f} | "
            f"{summary['aquinas_category_signal_rate']:.3f} | "
            f"{summary['generic_drift_rate']:.3f} | "
            f"{summary['stiff_template_phrase_rate']:.3f} |"
        )
    return "\n".join(lines)


def _extract_user_prompt(row: dict[str, Any]) -> str:
    for message in row.get("messages", []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    raise ValueError(f"Row {row.get('example_id')} is missing a user message")


def _build_probe_messages(
    row: dict[str, Any],
    *,
    user_prompt: str,
    prompt_mode: str,
) -> list[dict[str, str]]:
    if prompt_mode == "probe":
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    if prompt_mode != "canonical":
        raise ValueError(f"Unsupported prompt mode: {prompt_mode}")
    messages: list[dict[str, str]] = []
    for message in row.get("messages", []):
        role = message.get("role")
        if role == "assistant":
            break
        if role in {"system", "user"}:
            messages.append(
                {
                    "content": str(message.get("content") or ""),
                    "role": str(role),
                }
            )
    if not any(message["role"] == "user" for message in messages):
        messages.append({"role": "user", "content": user_prompt})
    return messages


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows


def _resolve_runtime(config: InferenceConfig) -> Any:
    availability = detect_torch_availability()
    if availability is None:
        raise RuntimeError("Torch is required for inference runtime detection.")
    return resolve_inference_runtime(
        config,
        cuda_available=availability.cuda_available,
        mps_available=availability.mps_available,
        bf16_supported=availability.bf16_supported,
    )


def _log_event(event: str, **payload: Any) -> None:
    print(json.dumps({"event": event, **payload}, sort_keys=True))


if __name__ == "__main__":
    main()
