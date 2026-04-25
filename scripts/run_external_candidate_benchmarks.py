"""Run compact external candidate benchmarks for the Christian virtue LoRA."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
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
from summa_moral_graph.utils.paths import REPO_ROOT

RUN_ROOT = REPO_ROOT / "runs/christian_virtue/qwen2_5_1_5b_instruct"
DEFAULT_BENCHMARKS = [
    "cmoraleval_chinese_moral",
    "ceval_ideological_moral",
    "cbbq_christian_religion",
    "bible_biblical_literacy",
    "mmlu_world_religions",
    "mmlu_moral_disputes",
    "mmlu_moral_scenarios",
    "mmlu_philosophy",
    "mmlu_business_ethics",
    "mmmlu_zh_world_religions",
    "mmmlu_zh_moral_disputes",
    "mmmlu_zh_moral_scenarios",
    "mmmlu_zh_philosophy",
    "mmmlu_zh_business_ethics",
    "moralexceptqa",
]
CHOICE_LABELS = ["A", "B", "C", "D"]
CMORALEVAL_FILES = [
    "cmoraleval_c1_party_moral_val_data",
    "cmoraleval_c1_party_unmoral_val_data",
    "cmoraleval_c2_party_moral_val_data",
    "cmoraleval_c2_party_unmoral_val_data",
    "cmoraleval_d1_party_moral_val_data",
    "cmoraleval_d1_party_unmoral_val_data",
    "cmoraleval_d2_party_moral_val_data",
    "cmoraleval_d2_party_unmoral_val_data",
]
CMORALEVAL_RAW_ROOT = (
    "https://raw.githubusercontent.com/tjunlp-lab/CMoralEval/main/data/val_data"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model-name-or-path", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--adapter-path")
    parser.add_argument("--benchmarks", nargs="+", default=DEFAULT_BENCHMARKS)
    parser.add_argument("--max-examples-per-benchmark", type=int, default=60)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--runtime-backend", default="mps")
    parser.add_argument("--torch-dtype", default="float16")
    parser.add_argument("--max-new-tokens", type=int, default=8)
    parser.add_argument("--trust-remote-code", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    adapter_path = Path(args.adapter_path).resolve() if args.adapter_path else None
    samples = build_samples(
        benchmark_ids=args.benchmarks,
        max_examples_per_benchmark=args.max_examples_per_benchmark,
        seed=args.seed,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_inputs_path = output_dir / "benchmark_inputs.jsonl"
    write_jsonl(benchmark_inputs_path, samples)
    config_snapshot_path = write_config_snapshot(
        output_dir,
        config_path=None,
        payload={
            "adapter_path": str(adapter_path) if adapter_path is not None else None,
            "benchmarks": args.benchmarks,
            "max_examples_per_benchmark": args.max_examples_per_benchmark,
            "max_new_tokens": args.max_new_tokens,
            "model_name_or_path": args.model_name_or_path,
            "runner": "external_candidate_benchmarks",
            "runtime_backend": args.runtime_backend,
            "seed": args.seed,
            "torch_dtype": args.torch_dtype,
            "trust_remote_code": args.trust_remote_code,
        },
    )
    manifest = run_generation(
        rows=samples,
        output_dir=output_dir,
        benchmark_inputs_path=benchmark_inputs_path,
        config_snapshot_path=config_snapshot_path,
        model_name_or_path=args.model_name_or_path,
        adapter_path=adapter_path,
        runtime_backend=args.runtime_backend,
        torch_dtype=args.torch_dtype,
        max_new_tokens=args.max_new_tokens,
        seed=args.seed,
        trust_remote_code=args.trust_remote_code,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


def build_samples(
    *,
    benchmark_ids: Sequence[str],
    max_examples_per_benchmark: int,
    seed: int,
) -> list[dict[str, Any]]:
    loaders: dict[str, Callable[..., list[dict[str, Any]]]] = {
        "bible_biblical_literacy": load_bible_biblical_literacy,
        "cbbq_christian_religion": load_cbbq_christian_religion,
        "ceval_ideological_moral": load_ceval_ideological_moral,
        "cmoraleval_chinese_moral": load_cmoraleval_chinese_moral,
        "mmmlu_zh_business_ethics": lambda seed: load_mmmlu_zh_subject(
            seed=seed,
            benchmark_id="mmmlu_zh_business_ethics",
            benchmark_name="MMMLU ZH-CN business ethics",
            subject="business_ethics",
        ),
        "mmmlu_zh_moral_disputes": lambda seed: load_mmmlu_zh_subject(
            seed=seed,
            benchmark_id="mmmlu_zh_moral_disputes",
            benchmark_name="MMMLU ZH-CN moral disputes",
            subject="moral_disputes",
        ),
        "mmmlu_zh_moral_scenarios": lambda seed: load_mmmlu_zh_subject(
            seed=seed,
            benchmark_id="mmmlu_zh_moral_scenarios",
            benchmark_name="MMMLU ZH-CN moral scenarios",
            subject="moral_scenarios",
        ),
        "mmmlu_zh_philosophy": lambda seed: load_mmmlu_zh_subject(
            seed=seed,
            benchmark_id="mmmlu_zh_philosophy",
            benchmark_name="MMMLU ZH-CN philosophy",
            subject="philosophy",
        ),
        "mmmlu_zh_world_religions": lambda seed: load_mmmlu_zh_subject(
            seed=seed,
            benchmark_id="mmmlu_zh_world_religions",
            benchmark_name="MMMLU ZH-CN world religions",
            subject="world_religions",
        ),
        "mmlu_business_ethics": lambda seed: load_mmlu_subject(
            seed=seed,
            benchmark_id="mmlu_business_ethics",
            benchmark_name="MMLU business ethics",
            subject="business_ethics",
        ),
        "mmlu_moral_disputes": lambda seed: load_mmlu_subject(
            seed=seed,
            benchmark_id="mmlu_moral_disputes",
            benchmark_name="MMLU moral disputes",
            subject="moral_disputes",
        ),
        "mmlu_moral_scenarios": lambda seed: load_mmlu_subject(
            seed=seed,
            benchmark_id="mmlu_moral_scenarios",
            benchmark_name="MMLU moral scenarios",
            subject="moral_scenarios",
        ),
        "mmlu_philosophy": lambda seed: load_mmlu_subject(
            seed=seed,
            benchmark_id="mmlu_philosophy",
            benchmark_name="MMLU philosophy",
            subject="philosophy",
        ),
        "mmlu_world_religions": load_mmlu_world_religions,
        "moralexceptqa": load_moralexceptqa,
    }
    samples: list[dict[str, Any]] = []
    for benchmark_id in benchmark_ids:
        if benchmark_id not in loaders:
            raise ValueError(f"Unknown benchmark id: {benchmark_id}")
        rows = loaders[benchmark_id](seed=seed)
        rows = _stable_sample(rows, max_examples_per_benchmark, seed=seed + len(samples))
        samples.extend(rows)
    return samples


def load_ceval_ideological_moral(*, seed: int) -> list[dict[str, Any]]:
    from datasets import load_dataset

    _ = seed
    dataset = load_dataset(
        "ceval/ceval-exam",
        "ideological_and_moral_cultivation",
        split="val",
    )
    rows = []
    for row in dataset:
        choices = [str(row[label]) for label in CHOICE_LABELS]
        rows.append(
            build_choice_sample(
                benchmark_id="ceval_ideological_moral",
                benchmark_name="C-Eval ideological and moral cultivation",
                language="zh",
                prompt=(
                    "以下是中国思想道德修养与法律基础单项选择题。"
                    "请只回答一个选项字母 A、B、C 或 D。\n\n"
                    f"题目：{row['question']}"
                ),
                choices=choices,
                target=str(row["answer"]).strip().upper(),
                source_id=f"ceval/ceval-exam:ideological_and_moral_cultivation:val:{row['id']}",
                source_url="https://huggingface.co/datasets/ceval/ceval-exam",
                metadata={"row_id": row["id"], "split": "val"},
            )
        )
    return rows


def load_cmoraleval_chinese_moral(*, seed: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file_name in CMORALEVAL_FILES:
        url = f"{CMORALEVAL_RAW_ROOT}/{file_name}"
        with urllib.request.urlopen(url, timeout=30) as response:
            for line in response.read().decode("utf-8").splitlines():
                if not line.strip():
                    continue
                payload = json.loads(line)
                choices = _choice_texts_from_prefixed_options(payload["choices"])
                rows.append(
                    build_choice_sample(
                        benchmark_id="cmoraleval_chinese_moral",
                        benchmark_name="CMoralEval Chinese moral scenarios",
                        language="zh",
                        prompt=(
                            f"{payload['question']}\n\n"
                            "请只回答一个选项字母 A、B 或 C。"
                        ),
                        choices=choices,
                        target=str(payload["correct_answer"]).strip().upper(),
                        source_id=f"tjunlp-lab/CMoralEval:{file_name}:{payload['index']}",
                        source_url=url,
                        metadata={
                            "category": payload.get("category"),
                            "file_name": file_name,
                            "index": payload.get("index"),
                            "wrong_answer": payload.get("wrong_answer"),
                        },
                    )
                )
    return _stable_sample(rows, len(rows), seed=seed)


def load_cbbq_christian_religion(*, seed: int) -> list[dict[str, Any]]:
    from datasets import load_dataset

    dataset = load_dataset("walledai/CBBQ", "default", split="religion")
    rows = []
    for index, row in enumerate(dataset):
        row_text = json.dumps(row, ensure_ascii=False)
        if "基督教" not in row_text:
            continue
        choices = [str(choice) for choice in row["choices"]]
        target = CHOICE_LABELS[int(row["answer"])]
        rows.append(
            build_choice_sample(
                benchmark_id="cbbq_christian_religion",
                benchmark_name="CBBQ Chinese religion bias with Christian mentions",
                language="zh",
                prompt=(
                    "以下是中文宗教偏见问答题。请根据上下文选择最合适答案；"
                    "如果信息不足，请选择表示信息不足的选项。只回答 A、B 或 C。\n\n"
                    f"上下文：{row['context']}\n问题：{row['question']}"
                ),
                choices=choices,
                target=target,
                source_id=f"walledai/CBBQ:religion:{index}",
                source_url="https://huggingface.co/datasets/walledai/CBBQ",
                metadata={"category": row.get("category"), "row_index": index},
            )
        )
    return _stable_sample(rows, len(rows), seed=seed)


def load_bible_biblical_literacy(*, seed: int) -> list[dict[str, Any]]:
    from datasets import load_dataset

    dataset = load_dataset("MushroomGecko/BIBLE", split="test")
    preferred_categories = {
        "Matthew",
        "Mark",
        "Luke",
        "John",
        "Romans",
        "1 Corinthians",
        "2 Corinthians",
        "Galatians",
        "Ephesians",
        "James",
        "Proverbs",
    }
    candidate_rows = [
        (index, row)
        for index, row in enumerate(dataset)
        if str(row.get("category")) in preferred_categories
    ]
    if not candidate_rows:
        candidate_rows = list(enumerate(dataset))
    rows = []
    for index, row in candidate_rows:
        choices = [str(choice) for choice in row["choices"]]
        target = str(row["answer"]).strip().upper()
        if len(choices) > len(CHOICE_LABELS) or target not in CHOICE_LABELS[: len(choices)]:
            continue
        rows.append(
            build_choice_sample(
                benchmark_id="bible_biblical_literacy",
                benchmark_name="BIBLE biblical literacy",
                language="en",
                prompt=(
                    "Answer this biblical literacy multiple-choice question. "
                    "Respond with only A, B, C, or D.\n\n"
                    f"Question: {row['question']}"
                ),
                choices=choices,
                target=target,
                source_id=f"MushroomGecko/BIBLE:test:{index}",
                source_url="https://huggingface.co/datasets/MushroomGecko/BIBLE",
                metadata={
                    "category": row.get("category"),
                    "qa_extraction": row.get("qa_extraction"),
                    "source": row.get("source"),
                },
            )
        )
    return _stable_sample(rows, len(rows), seed=seed)


def load_mmlu_world_religions(*, seed: int) -> list[dict[str, Any]]:
    return load_mmlu_subject(
        seed=seed,
        benchmark_id="mmlu_world_religions",
        benchmark_name="MMLU world religions",
        subject="world_religions",
    )


def load_mmlu_subject(
    *,
    seed: int,
    benchmark_id: str,
    benchmark_name: str,
    subject: str,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    _ = seed
    dataset = load_dataset("cais/mmlu", subject, split="test")
    rows = []
    for index, row in enumerate(dataset):
        rows.append(
            build_choice_sample(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                language="en",
                prompt=(
                    f"Answer this {subject.replace('_', ' ')} multiple-choice question. "
                    "Respond with only A, B, C, or D.\n\n"
                    f"Question: {str(row['question']).strip()}"
                ),
                choices=[str(choice) for choice in row["choices"]],
                target=CHOICE_LABELS[int(row["answer"])],
                source_id=f"cais/mmlu:{subject}:test:{index}",
                source_url="https://huggingface.co/datasets/cais/mmlu",
                metadata={"subject": row.get("subject"), "row_index": index},
            )
        )
    return rows


def load_mmmlu_zh_subject(
    *,
    seed: int,
    benchmark_id: str,
    benchmark_name: str,
    subject: str,
) -> list[dict[str, Any]]:
    from datasets import load_dataset

    _ = seed
    dataset = load_dataset("openai/MMMLU", "ZH_CN", split="test")
    rows = []
    for index, row in enumerate(dataset):
        if str(row["Subject"]) != subject:
            continue
        rows.append(
            build_choice_sample(
                benchmark_id=benchmark_id,
                benchmark_name=benchmark_name,
                language="zh",
                prompt=(
                    f"以下是 MMMLU 中文 {subject.replace('_', ' ')} 单项选择题。"
                    "请只回答一个选项字母 A、B、C 或 D。\n\n"
                    f"题目：{str(row['Question']).strip()}"
                ),
                choices=[str(row[label]) for label in CHOICE_LABELS],
                target=str(row["Answer"]).strip().upper(),
                source_id=f"openai/MMMLU:ZH_CN:{subject}:test:{index}",
                source_url="https://huggingface.co/datasets/openai/MMMLU",
                metadata={"row_index": index, "subject": subject},
            )
        )
    return rows


def load_moralexceptqa(*, seed: int) -> list[dict[str, Any]]:
    _ = seed
    dataset = _load_hf_viewer_rows(
        dataset="feradauto/MoralExceptQA",
        config="all",
        split="test",
    )
    rows = []
    for index, row in enumerate(dataset):
        human_score = float(row["human.response"])
        target = "A" if human_score >= 0.5 else "B"
        rows.append(
            build_choice_sample(
                benchmark_id="moralexceptqa",
                benchmark_name="MoralExceptQA human-majority permissibility",
                language="en",
                prompt=(
                    "Decide whether the action in the scenario is morally permissible. "
                    "Respond with only A or B.\n\n"
                    f"Scenario: {row['scenario']}"
                ),
                choices=[
                    "Permissible or morally justified in the described exception.",
                    "Not permissible or not morally justified.",
                ],
                target=target,
                source_id=f"feradauto/MoralExceptQA:all:test:{index}",
                source_url="https://huggingface.co/datasets/feradauto/MoralExceptQA",
                metadata={
                    "condition": row.get("condition"),
                    "context": row.get("context"),
                    "human_response": human_score,
                    "study": row.get("study"),
                },
            )
        )
    return rows


def _load_hf_viewer_rows(*, dataset: str, config: str, split: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    page_length = 100
    total: int | None = None
    while total is None or offset < total:
        query = urllib.parse.urlencode(
            {
                "config": config,
                "dataset": dataset,
                "length": page_length,
                "offset": offset,
                "split": split,
            }
        )
        url = f"https://datasets-server.huggingface.co/rows?{query}"
        with urllib.request.urlopen(url, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        total = int(payload["num_rows_total"])
        page_rows = payload.get("rows", [])
        rows.extend(item["row"] for item in page_rows)
        if not page_rows:
            break
        offset += len(page_rows)
    return rows


def build_choice_sample(
    *,
    benchmark_id: str,
    benchmark_name: str,
    language: str,
    prompt: str,
    choices: Sequence[str],
    target: str,
    source_id: str,
    source_url: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    labels = CHOICE_LABELS[: len(choices)]
    if target not in labels:
        raise ValueError(f"Target {target!r} is not in labels {labels!r}")
    choice_lines = "\n".join(
        f"{label}. {choice}" for label, choice in zip(labels, choices, strict=True)
    )
    system = (
        "You are taking an external multiple-choice benchmark. "
        "Answer with exactly one option letter and no explanation."
    )
    if language == "zh":
        system = "你正在参加外部单项选择评测。请只回答一个选项字母，不要解释。"
    user = f"{prompt}\n\n{choice_lines}\n\nAnswer:"
    return {
        "benchmark_id": benchmark_id,
        "benchmark_name": benchmark_name,
        "choices": list(choices),
        "choice_labels": labels,
        "example_id": source_id,
        "language": language,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "metadata": metadata,
        "prompt": user,
        "source_id": source_id,
        "source_url": source_url,
        "target": target,
    }


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
    trust_remote_code: bool,
) -> dict[str, Any]:
    config = InferenceConfig.model_validate(
        {
            "run_name": "external-candidate-benchmarks",
            "model_name_or_path": model_name_or_path,
            "dataset_dir": str(output_dir),
            "split_names": ["external_candidates"],
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
        response = _clean_assistant_text(
            tokenizer.decode(generated[0][input_length:], skip_special_tokens=True)
        )
        model_answer = parse_answer(response, row["choice_labels"])
        prediction = {
            **{key: row[key] for key in _PREDICTION_SOURCE_FIELDS},
            "adapter_path": str(adapter_path) if adapter_path is not None else None,
            "correct": model_answer == row["target"],
            "model_answer": model_answer,
            "model_name_or_path": model_name_or_path,
            "parseable": model_answer is not None,
            "response": response,
        }
        prediction_rows.append(prediction)
        with artifacts.partial_predictions_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(prediction, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        if index == total_rows or index % 10 == 0:
            _log_event(
                "external_candidate_generation_progress",
                completed=index,
                remaining=total_rows - index,
                total=total_rows,
            )

    write_jsonl(artifacts.predictions_path, prediction_rows)
    if artifacts.partial_predictions_path.exists():
        artifacts.partial_predictions_path.unlink()
    metrics = build_metrics(prediction_rows)
    write_json(artifacts.metrics_path, metrics)
    write_report(artifacts.report_path, metrics, adapter_path=adapter_path)
    write_summary_csv(output_dir / "summary_table.csv", metrics)
    end_time = iso_timestamp()
    versions = environment["versions"]
    manifest = {
        "adapter_path": str(adapter_path) if adapter_path is not None else None,
        "benchmark_count": len(rows),
        "benchmark_inputs_path": str(benchmark_inputs_path),
        "config_snapshot_path": str(config_snapshot_path),
        "end_time": end_time,
        "environment_path": str(artifacts.environment_path),
        "git_commit": environment["git_commit"],
        "max_new_tokens": max_new_tokens,
        "metrics_path": str(artifacts.metrics_path),
        "model_name_or_path": model_name_or_path,
        "peft_version": versions["peft"],
        "predictions_path": str(artifacts.predictions_path),
        "python_version": environment["platform"]["python_version"],
        "report_path": str(artifacts.report_path),
        "resolved_device": runtime.device_type,
        "run_id": output_dir.name,
        "start_time": start_time,
        "summary_csv": str(output_dir / "summary_table.csv"),
        "torch_dtype": runtime.torch_dtype_name,
        "torch_version": versions["torch"],
        "transformers_version": versions["transformers"],
    }
    write_json(artifacts.run_manifest_path, manifest)
    link_latest(output_dir.parent, output_dir)
    return manifest


def build_metrics(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_benchmark = _group_rows(rows, "benchmark_id")
    by_language = _group_rows(rows, "language")
    return {
        "by_benchmark": {
            key: _summary(value) for key, value in sorted(by_benchmark.items())
        },
        "by_language": {
            key: _summary(value) for key, value in sorted(by_language.items())
        },
        "by_model_answer": _count_by(rows, "model_answer"),
        "by_target": _count_by(rows, "target"),
        "overall": _summary(rows),
    }


def write_report(
    path: Path,
    metrics: dict[str, Any],
    *,
    adapter_path: Path | None,
) -> Path:
    lines = [
        "# External Candidate Benchmark Run",
        "",
        f"- Adapter: `{adapter_path}`" if adapter_path is not None else "- Adapter: none.",
        "- Runner: local deterministic Hugging Face generation.",
        "- Scoring: exact parsed option letter against source-provided target.",
        "",
        "## Overall",
        "",
        _summary_bullets(metrics["overall"]),
        "",
        "## By Benchmark",
        "",
        _summary_table(metrics["by_benchmark"]),
        "",
        "## By Language",
        "",
        _summary_table(metrics["by_language"]),
        "",
        "## Answer Distribution",
        "",
        _count_table(
            {
                "model_answer": metrics["by_model_answer"],
                "target": metrics["by_target"],
            }
        ),
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_summary_csv(path: Path, metrics: dict[str, Any]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "benchmark_id",
                "count",
                "correct_count",
                "accuracy",
                "parse_rate",
                "unparseable_count",
            ],
        )
        writer.writeheader()
        for benchmark_id, summary in sorted(metrics["by_benchmark"].items()):
            writer.writerow({"benchmark_id": benchmark_id, **summary})
    return path


def parse_answer(response: str, choices: Sequence[str]) -> str | None:
    labels = [choice.upper() for choice in choices]
    text = response.strip().upper()
    if not text:
        return None
    first = text[0]
    if first in labels and (len(text) == 1 or not text[1].isalpha()):
        return first
    match = re.search(r"(?:答案|ANSWER|选项|OPTION)\s*[:：是为]?\s*([A-D])", text)
    if match and match.group(1) in labels:
        return match.group(1)
    match = re.search(r"\b([A-D])\b", text)
    if match and match.group(1) in labels:
        return match.group(1)
    return None


def _choice_texts_from_prefixed_options(options: Sequence[str]) -> list[str]:
    cleaned = []
    for option in options:
        cleaned.append(re.sub(r"^[A-D]\s*[.．、]\s*", "", str(option)).strip())
    return cleaned


def _stable_sample(
    rows: Sequence[dict[str, Any]], limit: int, *, seed: int
) -> list[dict[str, Any]]:
    materialized = list(rows)
    rng = random.Random(seed)
    rng.shuffle(materialized)
    if limit > 0:
        materialized = materialized[:limit]
    return sorted(materialized, key=lambda row: str(row["example_id"]))


def _summary(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    count = len(materialized)
    if count == 0:
        return {
            "accuracy": 0.0,
            "correct_count": 0,
            "count": 0,
            "parse_rate": 0.0,
            "unparseable_count": 0,
        }
    correct_count = sum(1 for row in materialized if row["correct"])
    parseable_count = sum(1 for row in materialized if row["parseable"])
    return {
        "accuracy": correct_count / count,
        "correct_count": correct_count,
        "count": count,
        "parse_rate": parseable_count / count,
        "unparseable_count": count - parseable_count,
    }


def _group_rows(
    rows: Sequence[dict[str, Any]], field_name: str
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row[field_name])].append(row)
    return grouped


def _count_by(rows: Sequence[dict[str, Any]], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[str(row.get(field_name))] += 1
    return dict(sorted(counts.items()))


def _summary_bullets(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- Count: `{summary['count']}`",
            f"- Correct: `{summary['correct_count']}`",
            f"- Accuracy: `{summary['accuracy']:.1%}`",
            f"- Parse rate: `{summary['parse_rate']:.1%}`",
            f"- Unparseable: `{summary['unparseable_count']}`",
        ]
    )


def _summary_table(grouped: dict[str, dict[str, Any]]) -> str:
    lines = [
        "| Slice | Count | Correct | Accuracy | Parse rate | Unparseable |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, summary in grouped.items():
        lines.append(
            f"| `{key}` | `{summary['count']}` | `{summary['correct_count']}` | "
            f"`{summary['accuracy']:.1%}` | `{summary['parse_rate']:.1%}` | "
            f"`{summary['unparseable_count']}` |"
        )
    return "\n".join(lines)


def _count_table(grouped: dict[str, dict[str, int]]) -> str:
    lines = ["| Distribution | Value | Count |", "| --- | --- | ---: |"]
    for distribution, counts in grouped.items():
        for value, count in counts.items():
            lines.append(f"| `{distribution}` | `{value}` | `{count}` |")
    return "\n".join(lines)


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
        raise RuntimeError("Torch is required for external candidate inference.")
    return resolve_inference_runtime(
        config,
        cuda_available=availability.cuda_available,
        mps_available=availability.mps_available,
        bf16_supported=availability.bf16_supported,
    )


def link_latest(root_dir: Path, run_dir: Path) -> None:
    latest_path = root_dir / "latest"
    if latest_path.exists() or latest_path.is_symlink():
        latest_path.unlink()
    latest_path.symlink_to(run_dir.name)


def _log_event(event: str, **payload: Any) -> None:
    print(json.dumps({"event": event, **payload}, sort_keys=True), flush=True)


_PREDICTION_SOURCE_FIELDS = [
    "benchmark_id",
    "benchmark_name",
    "choice_labels",
    "choices",
    "example_id",
    "language",
    "metadata",
    "prompt",
    "source_id",
    "source_url",
    "target",
]


if __name__ == "__main__":
    main()
