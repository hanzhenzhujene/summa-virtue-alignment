from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from summa_moral_graph.sft.reporting import (
    build_goal_demo_panel,
    write_publishable_local_report,
    write_task_comparison_svg,
    write_training_curves_svg,
)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_build_goal_demo_panel_and_report_outputs(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    train_run_dir = tmp_path / "runs" / "local_baseline" / "20260418_101010"
    base_run_dir = tmp_path / "runs" / "base_test" / "20260418_111111"
    adapter_run_dir = tmp_path / "runs" / "adapter_test" / "20260418_121212"
    panel_path = tmp_path / "panel.jsonl"
    report_path = tmp_path / "docs" / "report.md"
    training_svg_path = tmp_path / "docs" / "assets" / "training.svg"
    comparison_svg_path = tmp_path / "docs" / "assets" / "comparison.svg"
    timing_svg_path = tmp_path / "docs" / "assets" / "timing.svg"

    example = {
        "example_id": "demo.example",
        "task_type": "reviewed_relation_explanation",
        "split": "test",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "Explain charity and correction."},
            {
                "role": "assistant",
                "content": (
                    "Charity includes fraternal correction.\n\n"
                    "Citations:\n- st.ii-ii.q033.a001.resp"
                ),
            },
        ],
        "metadata": {
            "tract": "theological_virtues",
            "source_passage_ids": ["st.ii-ii.q033.a001.resp"],
        },
    }
    _write_jsonl(dataset_dir / "all.jsonl", [cast(dict[str, object], example)])
    _write_json(
        dataset_dir / "manifest.json",
        {
            "dataset_name": "christian_virtue_v1",
            "grouping_key": "question_id",
            "source_annotations_used": 555,
            "split_sizes": {"train": 10, "val": 2, "test": 1},
            "annotation_counts_by_support_type": {
                "explicit_textual": 400,
                "strong_textual_inference": 155,
            },
        },
    )
    panel_rows: list[dict[str, object]] = [
        {
            "slot": 1,
            "title": "Charity",
            "focus": "Act relation",
            "example_id": "demo.example",
        }
    ]
    _write_jsonl(panel_path, panel_rows)
    _write_jsonl(
        base_run_dir / "predictions.jsonl",
        [{"example_id": "demo.example", "assistant_text": "Generic answer."}],
    )
    _write_jsonl(
        adapter_run_dir / "predictions.jsonl",
        [
            {
                "example_id": "demo.example",
                "assistant_text": (
                    "Charity includes fraternal correction.\n\n"
                    "Citations:\n- st.ii-ii.q033.a001.resp"
                ),
            }
        ],
    )
    _write_json(
        train_run_dir / "train_metadata.json",
        {
            "accelerate_version": "1.13.0",
            "eval_examples": 16,
            "git_commit": "abc123",
            "global_step": 20,
            "model_name_or_path": "Qwen/Qwen2.5-1.5B-Instruct",
            "peft_version": "0.19.1",
            "python_version": "3.12.2",
            "resolved_device": "mps",
            "run_id": "20260418_101010",
            "start_time": "2026-04-18T10:10:10-04:00",
            "end_time": "2026-04-18T10:14:10-04:00",
            "torch_version": "2.11.0",
            "torch_dtype": "float16",
            "train_examples": 128,
            "transformers_version": "4.57.6",
            "trl_version": "0.29.1",
        },
    )
    _write_jsonl(
        train_run_dir / "train_log_history.jsonl",
        [
            {"step": 5, "loss": 3.0, "mean_token_accuracy": 0.4},
            {"step": 10, "loss": 1.5, "mean_token_accuracy": 0.7},
            {"step": 10, "eval_loss": 1.2, "eval_mean_token_accuracy": 0.8},
        ],
    )
    _write_json(
        base_run_dir / "metrics.json",
        {
            "overall": {
                "count": 1,
                "citation_exact_match": 0.0,
                "citation_partial_match": 0.0,
                "citation_overlap": 0.0,
                "relation_type_accuracy": None,
            },
            "by_split": {
                "test": {
                    "count": 1,
                    "citation_exact_match": 0.0,
                    "citation_partial_match": 0.0,
                    "citation_overlap": 0.0,
                    "relation_type_accuracy": None,
                }
            },
            "by_tract": {
                "theological_virtues": {
                    "count": 1,
                    "citation_exact_match": 0.0,
                    "citation_partial_match": 0.0,
                    "citation_overlap": 0.0,
                    "relation_type_accuracy": None,
                }
            },
            "by_support_type": {
                "explicit_textual": {
                    "count": 1,
                    "citation_exact_match": 0.0,
                    "citation_partial_match": 0.0,
                    "citation_overlap": 0.0,
                    "relation_type_accuracy": None,
                }
            },
            "by_task_type": {
                "reviewed_relation_explanation": {
                    "count": 1,
                    "citation_exact_match": 0.0,
                    "citation_partial_match": 0.0,
                    "citation_overlap": 0.0,
                    "relation_type_accuracy": None,
                }
            },
        },
    )
    _write_json(
        adapter_run_dir / "metrics.json",
        {
            "overall": {
                "count": 1,
                "citation_exact_match": 1.0,
                "citation_partial_match": 1.0,
                "citation_overlap": 1.0,
                "relation_type_accuracy": None,
            },
            "by_split": {
                "test": {
                    "count": 1,
                    "citation_exact_match": 1.0,
                    "citation_partial_match": 1.0,
                    "citation_overlap": 1.0,
                    "relation_type_accuracy": None,
                }
            },
            "by_tract": {
                "theological_virtues": {
                    "count": 1,
                    "citation_exact_match": 1.0,
                    "citation_partial_match": 1.0,
                    "citation_overlap": 1.0,
                    "relation_type_accuracy": None,
                }
            },
            "by_support_type": {
                "explicit_textual": {
                    "count": 1,
                    "citation_exact_match": 1.0,
                    "citation_partial_match": 1.0,
                    "citation_overlap": 1.0,
                    "relation_type_accuracy": None,
                }
            },
            "by_task_type": {
                "reviewed_relation_explanation": {
                    "count": 1,
                    "citation_exact_match": 1.0,
                    "citation_partial_match": 1.0,
                    "citation_overlap": 1.0,
                    "relation_type_accuracy": None,
                }
            },
        },
    )

    panel_rows = build_goal_demo_panel(
        dataset_dir=dataset_dir,
        panel_path=panel_path,
        base_predictions_path=base_run_dir / "predictions.jsonl",
        adapter_predictions_path=adapter_run_dir / "predictions.jsonl",
    )
    assert len(panel_rows) == 1
    assert panel_rows[0]["base_exact_match"] is False
    assert panel_rows[0]["adapter_exact_match"] is True

    write_training_curves_svg(train_run_dir / "train_log_history.jsonl", training_svg_path)
    write_task_comparison_svg(
        json.loads((base_run_dir / "metrics.json").read_text(encoding="utf-8")),
        json.loads((adapter_run_dir / "metrics.json").read_text(encoding="utf-8")),
        comparison_svg_path,
    )
    timing_svg_path.write_text("<svg />\n", encoding="utf-8")
    written_report = write_publishable_local_report(
        dataset_dir=dataset_dir,
        train_run_dir=train_run_dir,
        base_run_dir=base_run_dir,
        adapter_run_dir=adapter_run_dir,
        panel_path=panel_path,
        output_path=report_path,
        training_curves_asset_path=Path("./assets/training.svg"),
        comparison_asset_path=Path("./assets/comparison.svg"),
        timing_comparison_asset_path=Path("./assets/timing.svg"),
        published_model_url="https://huggingface.co/example/model",
        release_url="https://github.com/example/release",
    )

    assert written_report == report_path
    training_svg_text = training_svg_path.read_text(encoding="utf-8")
    comparison_svg_text = comparison_svg_path.read_text(encoding="utf-8")
    assert "<svg" in training_svg_text
    assert "Canonical local-baseline training trace" in training_svg_text
    assert "Cross-entropy loss" in training_svg_text
    assert "Training step" in training_svg_text
    assert ">3<" in training_svg_text
    assert ">0.40<" in training_svg_text
    assert "<svg" in comparison_svg_text
    assert "Held-out virtue-goal citation exact" in comparison_svg_text
    assert "Selected strongest virtue-aligned held-out slices" in comparison_svg_text
    assert "Small-model demo: Qwen/Qwen2.5-1.5B-Instruct (1.5B)" in comparison_svg_text
    assert "marker-end='url(#improvement-arrowhead)'" in comparison_svg_text
    assert "Strongest public slice" in comparison_svg_text
    assert "Exact citation match" in comparison_svg_text
    assert "n=1" in comparison_svg_text
    assert "+100.0 pts" in comparison_svg_text
    assert "Citation-grounded moral answer" not in comparison_svg_text
    assert "Reviewed relation explanation" in comparison_svg_text
    assert "Virtue concept explanation" not in comparison_svg_text
    assert "Passage-grounded doctrinal QA" not in comparison_svg_text
    report_text = report_path.read_text(encoding="utf-8")
    assert "## Canonical Purpose" in report_text
    assert "## Executive Readout" in report_text
    assert "*Figure 1." in report_text
    assert "*Figure 2." in report_text
    assert "*Figure 3." in report_text
    assert "## Why `local-baseline` Is The Official Local Rung" in report_text
    assert "Goal-demo exact citations" in report_text
    assert "Held-out overall citation exact" not in report_text
    assert "Clear adapter win" in report_text
    assert "## Goal Demo Panel" in report_text
    assert "| Panel summary | Value |" in report_text
    assert "<details>" in report_text
    assert "Citation outcome" in report_text
    assert "**Reference answer**" in report_text
    assert "Main remaining weak spot" not in report_text
    assert "Zero-gain tracts in this run" not in report_text
    assert "The overall benchmark is still modest" not in report_text
    assert "https://huggingface.co/example/model" in report_text
    assert "https://github.com/example/release" in report_text
    assert "# Christian Virtue Run Comparison" not in report_text
    assert "### Overall" in report_text
    assert "make verify-christian-virtue-qwen2-5-1-5b-local-publishable" in report_text
    assert "Why this is a persuasive demo baseline" in report_text
