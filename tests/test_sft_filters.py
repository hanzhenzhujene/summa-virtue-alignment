from __future__ import annotations

from summa_moral_graph.sft.filters import apply_annotation_filters
from summa_moral_graph.sft.loaders import load_doctrinal_annotation_sources
from tests.sft_test_utils import build_fixture_dataset_config


def test_apply_annotation_filters_tracks_duplicates_and_policy_drops(tmp_path) -> None:
    config = build_fixture_dataset_config(tmp_path)
    annotations = load_doctrinal_annotation_sources(config.sources)
    duplicate = annotations[0].model_copy()
    strong_guess = annotations[1].model_copy(update={"support_type": "weak_guess"})
    rejected = annotations[2].model_copy(update={"review_status": "rejected"})
    editorial = annotations[3].model_copy(update={"edge_layer": "structural_editorial"})

    result = apply_annotation_filters(
        [*annotations, duplicate, strong_guess, rejected, editorial],
        config.filters,
    )

    assert len(result.annotations) == len(annotations)
    assert result.dropped_counts == {
        "duplicate_annotation_id": 1,
        "review_status_filtered": 1,
        "support_type_filtered": 1,
        "wrong_edge_layer": 1,
    }
