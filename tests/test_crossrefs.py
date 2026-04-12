from __future__ import annotations

from summa_moral_graph.ingest.crossrefs import extract_crossrefs


def test_cross_reference_normalization_on_sample_strings() -> None:
    text = "Compare I-II:65:1, II-II:23:3, I:85:5, III:12:4, and Suppl.:5:2."
    matches = extract_crossrefs(text)

    assert [match.normalized_reference for match in matches] == [
        "I-II:65:1",
        "II-II:23:3",
        "I:85:5",
        "III:12:4",
        "Suppl.:5:2",
    ]
    assert [match.target_part_id for match in matches] == [
        "i-ii",
        "ii-ii",
        "i",
        "iii",
        "supplement",
    ]

