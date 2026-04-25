from __future__ import annotations

from pathlib import Path

from scripts.build_christian_virtue_benchmark_packet import (
    EXPECTED_ADAPTER_RUN_ID,
    build_metric_roots,
    external_benchmark_rows,
    resolve_adapter_run_dir,
    resolve_existing_metric_path,
)
from scripts.compare_external_candidate_benchmarks import (
    CandidateRun,
    build_comparison_payload,
    promoted_table,
)
from scripts.run_external_candidate_benchmarks import (
    build_choice_sample,
    build_metrics,
    parse_answer,
)


def test_external_parse_answer_accepts_chinese_and_english_prefixes() -> None:
    assert parse_answer("答案：B", ["A", "B", "C"]) == "B"
    assert parse_answer("Answer: C.", ["A", "B", "C", "D"]) == "C"
    assert parse_answer("A", ["A", "B"]) == "A"
    assert parse_answer("I cannot tell", ["A", "B"]) is None


def test_build_choice_sample_keeps_target_and_prompt_surface() -> None:
    sample = build_choice_sample(
        benchmark_id="fixture",
        benchmark_name="Fixture",
        language="zh",
        prompt="题目：哪一个更谨慎？",
        choices=["先思考", "直接冲动"],
        target="A",
        source_id="fixture:1",
        source_url="https://example.com",
        metadata={"source": "unit"},
    )

    assert sample["target"] == "A"
    assert sample["choice_labels"] == ["A", "B"]
    assert sample["messages"][0]["content"].startswith("你正在参加外部")
    assert "A. 先思考" in sample["prompt"]
    assert "B. 直接冲动" in sample["prompt"]


def test_external_metrics_group_by_benchmark_and_language() -> None:
    rows = [
        {
            "benchmark_id": "one",
            "correct": True,
            "language": "en",
            "model_answer": "A",
            "parseable": True,
            "target": "A",
        },
        {
            "benchmark_id": "one",
            "correct": False,
            "language": "en",
            "model_answer": None,
            "parseable": False,
            "target": "B",
        },
    ]

    metrics = build_metrics(rows)

    assert metrics["overall"]["accuracy"] == 0.5
    assert metrics["overall"]["parse_rate"] == 0.5
    assert metrics["by_benchmark"]["one"]["correct_count"] == 1


def test_external_comparison_promotes_only_lora_wins(tmp_path: Path) -> None:
    base = CandidateRun(
        label="Base",
        run_dir=tmp_path / "base",
        manifest={"run_id": "base"},
        metrics={
            "by_benchmark": {
                "bible_biblical_literacy": {
                    "accuracy": 0.25,
                    "correct_count": 1,
                    "count": 4,
                    "parse_rate": 1.0,
                },
                "mmlu_world_religions": {
                    "accuracy": 0.75,
                    "correct_count": 3,
                    "count": 4,
                    "parse_rate": 1.0,
                },
            },
            "overall": {},
        },
        adapter_verification=None,
    )
    lora = CandidateRun(
        label="Full-corpus LoRA",
        run_dir=tmp_path / "lora",
        manifest={"run_id": "lora"},
        metrics={
            "by_benchmark": {
                "bible_biblical_literacy": {
                    "accuracy": 0.50,
                    "correct_count": 2,
                    "count": 4,
                    "parse_rate": 1.0,
                },
                "mmlu_world_religions": {
                    "accuracy": 0.50,
                    "correct_count": 2,
                    "count": 4,
                    "parse_rate": 1.0,
                },
            },
            "overall": {},
        },
        adapter_verification=None,
    )

    payload = build_comparison_payload(base, lora, output_dir=tmp_path)
    table = promoted_table(payload["promoted_rows"])

    assert [row["benchmark_id"] for row in payload["promoted_rows"]] == [
        "bible_biblical_literacy"
    ]
    assert "`mmlu_world_religions`" not in table
    assert "+25.0 pts" in table


def test_benchmark_packet_imports_only_promoted_external_rows() -> None:
    rows = external_benchmark_rows(
        {
            "promoted_rows": [
                {
                    "base_accuracy": 0.50,
                    "benchmark_id": "mmlu_world_religions",
                    "count": 10,
                    "domain": "World religions knowledge",
                    "lora_accuracy": 0.60,
                    "lora_parse_rate": 1.0,
                    "source_url": "https://huggingface.co/datasets/cais/mmlu",
                }
            ]
        }
    )

    assert len(rows) == 1
    assert rows[0].benchmark == "External mmlu_world_religions"
    assert round(rows[0].delta, 2) == 0.10
    assert rows[0].coverage == "10/10; parse 100.0%"


def test_benchmark_packet_prefers_explicit_metric_roots(tmp_path: Path) -> None:
    explicit_root = tmp_path / "other_worktree" / "runs"
    repo_root = tmp_path / "current_worktree" / "runs"
    metric_path = explicit_root / "base_test/latest/metrics.json"
    metric_path.parent.mkdir(parents=True)
    metric_path.write_text('{"overall": {"count": 1}}\n', encoding="utf-8")

    roots = build_metric_roots(str(explicit_root), default_root=repo_root)

    assert roots == (explicit_root.resolve(), repo_root.resolve())
    assert resolve_existing_metric_path("base_test/latest/metrics.json", roots) == metric_path


def test_benchmark_packet_resolves_cross_worktree_adapter_run(tmp_path: Path) -> None:
    run_family_root = tmp_path / "other_worktree" / "qwen2_5_1_5b_instruct"
    adapter_dir = run_family_root / "full_corpus" / EXPECTED_ADAPTER_RUN_ID
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "train_metadata.json").write_text('{"run_id": "demo"}\n', encoding="utf-8")

    resolved = resolve_adapter_run_dir(run_family_root, (tmp_path / "repo_runs",))

    assert resolved == adapter_dir.resolve()
