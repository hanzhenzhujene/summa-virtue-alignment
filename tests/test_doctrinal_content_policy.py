from __future__ import annotations

from pathlib import Path

from summa_moral_graph.models import SegmentRecord
from summa_moral_graph.utils.jsonl import load_jsonl
from summa_moral_graph.validation.corpus import scan_exported_artifacts_for_disallowed_passage_refs


def test_interim_segments_are_respondeo_or_reply_only() -> None:
    segment_records = [
        SegmentRecord.model_validate(payload)
        for payload in load_jsonl(Path("data/interim/summa_moral_segments.jsonl"))
    ]

    assert segment_records
    assert {record.segment_type for record in segment_records} <= {"resp", "ad"}


def test_exported_artifacts_contain_no_objection_or_sed_contra_passage_ids() -> None:
    assert scan_exported_artifacts_for_disallowed_passage_refs() == []
