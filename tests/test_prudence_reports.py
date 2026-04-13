from __future__ import annotations

import json
from pathlib import Path


def test_prudence_coverage_report_generation(prudence_artifacts) -> None:
    payload = json.loads(Path("data/processed/prudence_coverage.json").read_text(encoding="utf-8"))
    assert len(payload["questions"]) == 10
    q48 = next(record for record in payload["questions"] if record["question_number"] == 48)
    assert q48["part_taxonomy_usage"] == {"integral": 8, "potential": 3, "subjective": 4}


def test_prudence_validation_report_is_ok(prudence_artifacts) -> None:
    payload = json.loads(
        Path("data/processed/prudence_validation_report.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "ok"
    assert payload["reviewed_doctrinal_edge_count"] >= 150
