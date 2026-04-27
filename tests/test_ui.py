from __future__ import annotations

import json

import pandas as pd

from summa_moral_graph.app.ui import (
    basename,
    dataframe_to_csv_bytes,
    format_edge_option,
    format_question_list,
    payload_to_json_bytes,
    pretty_tag,
    status_tone,
)


def test_format_question_list_handles_empty_and_truncation() -> None:
    assert format_question_list([]) == "None"
    assert format_question_list([1, 2, 3]) == "1, 2, 3"
    assert format_question_list([1, 2, 3, 4, 5, 6, 7], limit=4) == "1, 2, 3, 4, +3 more"


def test_status_tone_maps_common_states() -> None:
    assert status_tone("ok") == "ok"
    assert status_tone("parsed") == "ok"
    assert status_tone("partial") == "warn"
    assert status_tone("failed") == "alert"


def test_text_helpers_format_labels_and_paths() -> None:
    assert pretty_tag("precept_linkage") == "Precept Linkage"
    assert basename("/tmp/example.json") == "example.json"
    assert basename(None) == "None"


def test_download_helpers_emit_expected_payloads() -> None:
    csv_payload = dataframe_to_csv_bytes(pd.DataFrame.from_records([{"a": 1, "b": "two"}])).decode(
        "utf-8"
    )
    json_payload = json.loads(payload_to_json_bytes({"ok": True}).decode("utf-8"))

    assert "a,b" in csv_payload
    assert "1,two" in csv_payload
    assert json_payload == {"ok": True}


def test_format_edge_option_builds_readable_label() -> None:
    label = format_edge_option(
        {
            "layer": "reviewed_doctrinal",
            "subject_label": "Justice",
            "relation_type": "opposed_by",
            "object_label": "Injustice",
        }
    )

    assert "reviewed doctrinal" in label
    assert "Justice" in label
    assert "opposed by" in label
    assert "Injustice" in label
