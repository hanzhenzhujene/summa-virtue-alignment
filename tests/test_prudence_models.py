from __future__ import annotations

from typing import Any, cast

import pytest
from pydantic import ValidationError

from summa_moral_graph.models.prudence import PrudenceAnnotationRecord


def test_support_type_validation_accepts_reviewed_values() -> None:
    record = PrudenceAnnotationRecord(
        annotation_id="ann.example",
        source_passage_id="st.ii-ii.q047.a001.resp",
        subject_id="concept.prudence",
        subject_label="Prudence",
        subject_type="virtue",
        relation_type="treated_in",
        object_id="st.ii-ii.q047.a001",
        object_label="II-II q.47 a.1 — Is prudence in the will or in the reason?",
        object_type="article",
        evidence_text="prudence belongs directly to the cognitive",
        evidence_rationale="Explicit textual support.",
        confidence=0.95,
        review_status="approved",
        support_type="explicit_textual",
    )
    assert record.support_type == "explicit_textual"


def test_support_type_validation_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        PrudenceAnnotationRecord(
            annotation_id="ann.example.bad",
            source_passage_id="st.ii-ii.q047.a001.resp",
            subject_id="concept.prudence",
            subject_label="Prudence",
            subject_type="virtue",
            relation_type="treated_in",
            object_id="st.ii-ii.q047.a001",
            object_label="Article",
            object_type="article",
            evidence_text="prudence belongs directly to the cognitive",
            evidence_rationale="Bad support type.",
            confidence=0.95,
            review_status="approved",
            support_type=cast(Any, "weak_guess"),
        )
