from __future__ import annotations

import json
from pathlib import Path


def test_pilot_validation_report_is_ok(pilot_artifacts) -> None:
    payload = json.loads(Path("data/processed/validation_report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["alias_collisions"] == []
    assert payload["missing_evidence"] == []
    assert payload["passage_count"] == 388
