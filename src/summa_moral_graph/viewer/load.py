"""Load and cache the reviewed corpus payloads that back the unified Streamlit viewer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import streamlit as st

from ..app.corpus import CorpusAppBundle, load_corpus_bundle, top_supporting_passages
from ..app.dashboard import load_dashboard_payload

HOME_START_CONCEPT_IDS = (
    "concept.charity",
    "concept.prudence",
    "concept.justice",
    "concept.temperance",
    "concept.fortitude",
)


@dataclass(frozen=True)
class ViewerAppData:
    bundle: CorpusAppBundle
    dashboard: dict[str, Any]
    reviewed_concept_ids: frozenset[str]
    reviewed_passage_ids: frozenset[str]
    candidate_active_passage_ids: frozenset[str]
    tract_rows_by_slug: dict[str, dict[str, Any]]
    question_label_by_id: dict[str, str]
    concept_label_by_id: dict[str, str]
    home_start_concepts: tuple[str, ...]
    home_start_passages: tuple[str, ...]


def _curated_start_concepts(bundle: CorpusAppBundle) -> tuple[str, ...]:
    concepts = [
        concept_id for concept_id in HOME_START_CONCEPT_IDS if concept_id in bundle.registry
    ]
    if concepts:
        return tuple(concepts)
    return tuple(sorted(bundle.registry)[:4])


def _curated_start_passages(
    bundle: CorpusAppBundle,
    concept_ids: tuple[str, ...],
) -> tuple[str, ...]:
    ordered: list[str] = []
    for concept_id in concept_ids:
        for passage_id in top_supporting_passages(bundle, concept_id):
            if passage_id in bundle.passages and passage_id not in ordered:
                ordered.append(passage_id)
            if len(ordered) >= 4:
                return tuple(ordered)
    return tuple(sorted(bundle.passages)[:4])


@st.cache_resource(show_spinner=False)
def load_viewer_data(root: Path | None = None) -> ViewerAppData:
    bundle = load_corpus_bundle(root)
    dashboard = load_dashboard_payload(root)

    reviewed_concept_ids = frozenset(
        {
            str(edge["subject_id"])
            for edge in bundle.reviewed_doctrinal_edges
        }
        | {
            str(edge["object_id"])
            for edge in bundle.reviewed_doctrinal_edges
        }
    )
    reviewed_passage_ids = frozenset(
        str(row["source_passage_id"]) for row in bundle.reviewed_annotations
    )
    candidate_active_passage_ids = frozenset(
        {mention.passage_id for mention in bundle.candidate_mentions}
        | {relation.source_passage_id for relation in bundle.candidate_relations}
    )

    home_start_concepts = _curated_start_concepts(bundle)
    home_start_passages = _curated_start_passages(bundle, home_start_concepts)

    return ViewerAppData(
        bundle=bundle,
        dashboard=dashboard,
        reviewed_concept_ids=reviewed_concept_ids,
        reviewed_passage_ids=reviewed_passage_ids,
        candidate_active_passage_ids=candidate_active_passage_ids,
        tract_rows_by_slug={
            str(row["slug"]): row for row in dashboard["tract_rows"]
        },
        question_label_by_id={
            question_id: (
                f"{record.part_id.upper()} q.{record.question_number} — {record.question_title}"
            )
            for question_id, record in sorted(bundle.questions.items())
        },
        concept_label_by_id={
            concept_id: f"{record.canonical_label} · {record.node_type}"
            for concept_id, record in sorted(bundle.registry.items())
        },
        home_start_concepts=home_start_concepts,
        home_start_passages=home_start_passages,
    )
