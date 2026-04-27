from __future__ import annotations

from summa_moral_graph.sft.comparison import build_comparison_report, write_comparison_report


def _metrics_fixture() -> tuple[dict[str, object], dict[str, object]]:
    baseline = {
        "overall": {
            "count": 12,
            "citation_exact_match": 0.1,
            "citation_partial_match": 0.2,
            "citation_overlap": 0.25,
            "relation_type_accuracy": 0.3,
        },
        "by_split": {
            "test": {
                "count": 12,
                "citation_exact_match": 0.1,
                "citation_partial_match": 0.2,
                "citation_overlap": 0.25,
                "relation_type_accuracy": 0.3,
            }
        },
        "by_tract": {
            "prudence": {
                "count": 5,
                "citation_exact_match": 0.0,
                "citation_partial_match": 0.2,
                "citation_overlap": 0.2,
                "relation_type_accuracy": 0.25,
            }
        },
        "by_support_type": {
            "explicit_textual": {
                "count": 9,
                "citation_exact_match": 0.1,
                "citation_partial_match": 0.2,
                "citation_overlap": 0.2,
                "relation_type_accuracy": None,
            }
        },
        "by_task_type": {
            "reviewed_relation_explanation": {
                "count": 4,
                "citation_exact_match": 0.25,
                "citation_partial_match": 0.25,
                "citation_overlap": 0.25,
                "relation_type_accuracy": None,
            }
        },
    }
    candidate = {
        "overall": {
            "count": 12,
            "citation_exact_match": 0.4,
            "citation_partial_match": 0.5,
            "citation_overlap": 0.55,
            "relation_type_accuracy": 0.6,
        },
        "by_split": {
            "test": {
                "count": 12,
                "citation_exact_match": 0.4,
                "citation_partial_match": 0.5,
                "citation_overlap": 0.55,
                "relation_type_accuracy": 0.6,
            }
        },
        "by_tract": {
            "prudence": {
                "count": 5,
                "citation_exact_match": 0.2,
                "citation_partial_match": 0.4,
                "citation_overlap": 0.5,
                "relation_type_accuracy": 0.5,
            }
        },
        "by_support_type": {
            "explicit_textual": {
                "count": 9,
                "citation_exact_match": 0.3,
                "citation_partial_match": 0.3,
                "citation_overlap": 0.3,
                "relation_type_accuracy": None,
            }
        },
        "by_task_type": {
            "reviewed_relation_explanation": {
                "count": 4,
                "citation_exact_match": 0.5,
                "citation_partial_match": 0.5,
                "citation_overlap": 0.5,
                "relation_type_accuracy": None,
            }
        },
    }
    return baseline, candidate


def test_build_comparison_report_includes_all_metric_sections() -> None:
    baseline, candidate = _metrics_fixture()

    report = build_comparison_report(
        baseline,
        candidate,
        baseline_label="base",
        candidate_label="adapter",
    )

    assert "# Christian Virtue Run Comparison" in report
    assert "## Overall" in report
    assert "## By Split" in report
    assert "## By Tract" in report
    assert "## By Support Type" in report
    assert "## By Task Type" in report
    assert "### test" in report
    assert "### prudence" in report
    assert "### explicit_textual" in report
    assert "### reviewed_relation_explanation" in report
    assert "| citation_exact_match | 0.100 | 0.400 | +0.300 |" in report


def test_write_comparison_report_writes_markdown_file(tmp_path) -> None:
    baseline, candidate = _metrics_fixture()
    output_path = tmp_path / "compare" / "report.md"

    written_path = write_comparison_report(
        baseline,
        candidate,
        output_path,
        baseline_label="base",
        candidate_label="adapter",
    )

    assert written_path == output_path
    assert output_path.exists()
    assert "Christian Virtue Run Comparison" in output_path.read_text(encoding="utf-8")
