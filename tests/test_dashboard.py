from __future__ import annotations

from summa_moral_graph.app.dashboard import load_dashboard_payload


def test_dashboard_payload_surfaces_current_reviewed_blocks(
    temperance_closure_161_170_artifacts: dict[str, object],
) -> None:
    _ = temperance_closure_161_170_artifacts
    payload = load_dashboard_payload()

    assert payload["summary"]["questions_parsed"] == 296
    assert payload["summary"]["passages_parsed"] == 6032
    assert payload["summary"]["reviewed_tract_blocks"] == 10
    assert payload["summary"]["ok_validation_blocks"] == 10

    tract_rows = {row["slug"]: row for row in payload["tract_rows"]}
    temperance_closure = tract_rows["temperance_closure_161_170"]

    assert temperance_closure["reviewed_annotations"] == 148
    assert temperance_closure["reviewed_doctrinal_edges"] == 41
    assert temperance_closure["candidate_relation_proposals"] == 223
    assert temperance_closure["review_packet_question"] == 162
    assert all(
        "candidate relation" not in highlight
        for highlight in temperance_closure["highlights"]
    )


def test_dashboard_synthesis_rows_include_editorial_exports_when_available(
    temperance_closure_161_170_artifacts: dict[str, object],
) -> None:
    _ = temperance_closure_161_170_artifacts
    payload = load_dashboard_payload()

    synthesis_rows = {row["slug"]: row for row in payload["synthesis_rows"]}

    assert synthesis_rows["fortitude_tract"]["nodes"] == 89
    assert synthesis_rows["fortitude_tract"]["edges"] == 64
    assert synthesis_rows["fortitude_tract"]["editorial_graphml_path"] is not None

    assert synthesis_rows["temperance_phase1"]["nodes"] == 163
    assert synthesis_rows["temperance_phase1"]["edges"] == 67
    assert synthesis_rows["temperance_phase1"]["editorial_graphml_path"] is not None

    assert synthesis_rows["temperance_full"]["nodes"] == 237
    assert synthesis_rows["temperance_full"]["edges"] == 108


def test_dashboard_review_priority_rows_surface_real_queue_targets(
    temperance_closure_161_170_artifacts: dict[str, object],
) -> None:
    _ = temperance_closure_161_170_artifacts
    payload = load_dashboard_payload()

    review_rows = {row["tract"]: row for row in payload["review_priority_rows"]}

    assert review_rows["Theological Virtues"]["packet_target_question"] == 19
    assert review_rows["Prudence"]["packet_target_question"] == 56
    assert review_rows["Temperance Closure"]["packet_target_question"] == 162
    assert review_rows["Temperance Closure"]["under_annotated_questions"] == [161, 162, 163]
    assert review_rows["Temperance Closure"]["review_queue_path"].endswith(
        "temperance_closure_161_170_review_queue.json"
    )
