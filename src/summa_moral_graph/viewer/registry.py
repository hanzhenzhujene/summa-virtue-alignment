from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, cast

from ..app.connected_virtues_109_120 import (
    CONNECTED_VIRTUES_109_120_PRESETS,
    connected_virtues_109_120_concept_page_data,
)
from ..app.connected_virtues_109_120 import (
    edge_evidence_panel as connected_edge_evidence_panel,
)
from ..app.connected_virtues_109_120 import (
    filter_edges_by_preset as filter_connected_edges_by_preset,
)
from ..app.connected_virtues_109_120 import (
    filter_edges_by_question_range as filter_connected_edges_by_question_range,
)
from ..app.corpus import CorpusAppBundle, candidate_relation_rows
from ..app.fortitude_closure_136_140 import (
    FORTITUDE_CLOSURE_136_140_PRESETS,
    fortitude_closure_136_140_concept_page_data,
)
from ..app.fortitude_closure_136_140 import (
    edge_evidence_panel as fortitude_closure_edge_evidence_panel,
)
from ..app.fortitude_closure_136_140 import (
    filter_edges_by_preset as filter_fortitude_closure_edges_by_preset,
)
from ..app.fortitude_closure_136_140 import (
    filter_edges_by_question_range as filter_fortitude_closure_edges_by_question_range,
)
from ..app.fortitude_parts_129_135 import (
    FORTITUDE_PARTS_129_135_PRESETS,
    fortitude_parts_129_135_concept_page_data,
)
from ..app.fortitude_parts_129_135 import (
    edge_evidence_panel as fortitude_edge_evidence_panel,
)
from ..app.fortitude_parts_129_135 import (
    filter_edges_by_preset as filter_fortitude_edges_by_preset,
)
from ..app.fortitude_parts_129_135 import (
    filter_edges_by_question_range as filter_fortitude_edges_by_question_range,
)
from ..app.justice_core import (
    JUSTICE_CORE_PRESETS,
    justice_core_concept_page_data,
)
from ..app.justice_core import (
    edge_evidence_panel as justice_edge_evidence_panel,
)
from ..app.justice_core import (
    filter_edges_by_preset as filter_justice_edges_by_preset,
)
from ..app.justice_core import (
    filter_edges_by_question_range as filter_justice_edges_by_question_range,
)
from ..app.owed_relation_tract import (
    OWED_RELATION_TRACT_PRESETS,
    owed_relation_tract_concept_page_data,
)
from ..app.owed_relation_tract import (
    edge_evidence_panel as owed_edge_evidence_panel,
)
from ..app.owed_relation_tract import (
    filter_edges_by_preset as filter_owed_edges_by_preset,
)
from ..app.owed_relation_tract import (
    filter_edges_by_question_range as filter_owed_edges_by_question_range,
)
from ..app.prudence import PRUDENCE_PRESETS
from ..app.religion_tract import (
    RELIGION_TRACT_PRESETS,
    religion_tract_concept_page_data,
)
from ..app.religion_tract import (
    edge_evidence_panel as religion_edge_evidence_panel,
)
from ..app.religion_tract import (
    filter_edges_by_preset as filter_religion_edges_by_preset,
)
from ..app.religion_tract import (
    filter_edges_by_question_range as filter_religion_edges_by_question_range,
)
from ..app.temperance_141_160 import (
    TEMPERANCE_141_160_PRESETS,
    temperance_141_160_concept_page_data,
)
from ..app.temperance_141_160 import (
    edge_evidence_panel as temperance_edge_evidence_panel,
)
from ..app.temperance_141_160 import (
    filter_edges_by_preset as filter_temperance_edges_by_preset,
)
from ..app.temperance_141_160 import (
    filter_edges_by_question_range as filter_temperance_edges_by_question_range,
)
from ..app.temperance_closure_161_170 import (
    TEMPERANCE_CLOSURE_161_170_PRESETS,
    temperance_closure_161_170_concept_page_data,
)
from ..app.temperance_closure_161_170 import (
    edge_evidence_panel as temperance_closure_edge_evidence_panel,
)
from ..app.temperance_closure_161_170 import (
    filter_edges_by_preset as filter_temperance_closure_edges_by_preset,
)
from ..app.temperance_closure_161_170 import (
    filter_edges_by_question_range as filter_temperance_closure_edges_by_question_range,
)
from ..app.theological_virtues import (
    THEOLOGICAL_VIRTUES_PRESETS,
    edge_in_question_range,
    theological_virtues_concept_page_data,
    trim_edge_to_question_range,
)
from ..app.theological_virtues import (
    edge_evidence_panel as theological_edge_evidence_panel,
)
from ..app.theological_virtues import (
    filter_edges_by_preset as filter_theological_edges_by_preset,
)
from ..app.theological_virtues import (
    filter_edges_by_question_range as filter_theological_edges_by_question_range,
)

EdgeFilterByRange = Callable[..., list[dict[str, Any]]]
EdgeFilterByPreset = Callable[..., list[dict[str, Any]]]
ConceptPayloadBuilder = Callable[..., dict[str, Any]]
EvidencePanelBuilder = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class ViewerPreset:
    family: str
    key: str
    label: str
    start_question: int
    end_question: int


@dataclass(frozen=True)
class TractAdapter:
    family: str
    label: str
    range_start: int
    range_end: int
    presets: dict[str, Any]
    filter_edges_by_question_range: EdgeFilterByRange
    filter_edges_by_preset: EdgeFilterByPreset
    concept_page_data: ConceptPayloadBuilder
    edge_evidence_panel: EvidencePanelBuilder


def _prudence_presets() -> dict[str, dict[str, Any]]:
    presets: dict[str, dict[str, Any]] = {}
    for key, value in PRUDENCE_PRESETS.items():
        questions = [int(question) for question in cast(list[int], value["questions"])]
        presets[key] = {
            "label": str(value["label"]),
            "start_question": min(questions),
            "end_question": max(questions),
        }
    return presets


def _filter_kwargs_for_callable(
    func: Callable[..., list[dict[str, Any]]],
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    signature = inspect.signature(func)
    accepted = set(signature.parameters)
    return {key: value for key, value in kwargs.items() if key in accepted}


def _wrap_range_filter(
    func: EdgeFilterByRange,
) -> EdgeFilterByRange:
    def wrapped(
        bundle: CorpusAppBundle,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        filtered_kwargs = _filter_kwargs_for_callable(func, kwargs)
        return func(bundle, **filtered_kwargs)

    return wrapped


def _wrap_preset_filter(
    func: EdgeFilterByPreset,
) -> EdgeFilterByPreset:
    def wrapped(
        bundle: CorpusAppBundle,
        preset_name: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        filtered_kwargs = _filter_kwargs_for_callable(func, kwargs)
        return func(bundle, preset_name, **filtered_kwargs)

    return wrapped


def _generic_filter_edges_by_question_range(
    bundle: CorpusAppBundle,
    *,
    start_question: int,
    end_question: int,
    include_editorial: bool = False,
    include_candidate: bool = False,
    relation_types: set[str] | None = None,
    node_types: set[str] | None = None,
    center_concept: str | None = None,
    focus_tags: set[str] | None = None,
) -> list[dict[str, Any]]:
    _ = focus_tags
    edges = [
        edge
        for edge in bundle.reviewed_doctrinal_edges
        if edge_in_question_range(bundle, edge, start_question, end_question)
    ]
    if include_editorial:
        edges.extend(
            edge
            for edge in bundle.reviewed_structural_edges
            if edge_in_question_range(bundle, edge, start_question, end_question)
        )
    if include_candidate:
        edges.extend(
            edge
            for edge in candidate_relation_rows(
                bundle,
                question_id=None,
                center_concept=center_concept,
            )
            if edge_in_question_range(bundle, edge, start_question, end_question)
        )

    filtered: list[dict[str, Any]] = []
    for edge in edges:
        trimmed = trim_edge_to_question_range(
            bundle,
            edge,
            start_question=start_question,
            end_question=end_question,
        )
        if trimmed is None:
            continue
        if relation_types and str(trimmed["relation_type"]) not in relation_types:
            continue
        if node_types and (
            str(trimmed["subject_type"]) not in node_types
            or str(trimmed["object_type"]) not in node_types
        ):
            continue
        if center_concept and center_concept not in {
            str(trimmed["subject_id"]),
            str(trimmed["object_id"]),
        }:
            continue
        filtered.append(trimmed)
    filtered.sort(key=lambda item: (str(item["layer"]), str(item["edge_id"])))
    return filtered


def _generic_filter_edges_by_preset(
    bundle: CorpusAppBundle,
    preset_name: str,
    *,
    presets: dict[str, dict[str, Any]],
    include_editorial: bool = False,
    include_candidate: bool = False,
    relation_types: set[str] | None = None,
    node_types: set[str] | None = None,
    center_concept: str | None = None,
    focus_tags: set[str] | None = None,
) -> list[dict[str, Any]]:
    preset = presets[preset_name]
    return _generic_filter_edges_by_question_range(
        bundle,
        start_question=int(preset["start_question"]),
        end_question=int(preset["end_question"]),
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types,
        node_types=node_types,
        center_concept=center_concept,
        focus_tags=focus_tags,
    )


def _generic_concept_payload_for_range(
    bundle: CorpusAppBundle,
    concept_id: str,
    *,
    start_question: int,
    end_question: int,
) -> dict[str, Any]:
    reviewed_edges = [
        edge
        for edge in bundle.reviewed_doctrinal_edges
        if concept_id in {str(edge["subject_id"]), str(edge["object_id"])}
        and edge_in_question_range(bundle, edge, start_question, end_question)
    ]
    editorial_edges = [
        edge
        for edge in bundle.reviewed_structural_edges
        if concept_id in {str(edge["subject_id"]), str(edge["object_id"])}
        and edge_in_question_range(bundle, edge, start_question, end_question)
    ]
    reviewed_annotations = [
        row
        for row in bundle.reviewed_annotations
        if row["source_passage_id"] in bundle.passages
        and bundle.passages[str(row["source_passage_id"])].part_id == "ii-ii"
        and start_question
        <= bundle.passages[str(row["source_passage_id"])].question_number
        <= end_question
        and concept_id in {str(row["subject_id"]), str(row["object_id"])}
    ]
    candidate_mentions = [
        mention.model_dump(mode="json")
        for mention in bundle.candidate_mentions
        if mention.passage_id in bundle.passages
        and bundle.passages[mention.passage_id].part_id == "ii-ii"
        and start_question <= bundle.passages[mention.passage_id].question_number <= end_question
        and (
            mention.proposed_concept_id == concept_id or concept_id in mention.proposed_concept_ids
        )
    ]
    candidate_relations = [
        relation.model_dump(mode="json")
        for relation in bundle.candidate_relations
        if relation.source_passage_id in bundle.passages
        and bundle.passages[relation.source_passage_id].part_id == "ii-ii"
        and start_question
        <= bundle.passages[relation.source_passage_id].question_number
        <= end_question
        and concept_id in {relation.subject_id, relation.object_id}
    ]
    supporting_passage_ids: list[str] = []
    for row in reviewed_annotations:
        passage_id = str(row["source_passage_id"])
        if passage_id not in supporting_passage_ids:
            supporting_passage_ids.append(passage_id)
    for row in candidate_mentions:
        passage_id = str(row["passage_id"])
        if passage_id not in supporting_passage_ids:
            supporting_passage_ids.append(passage_id)
    related_questions = sorted(
        {
            bundle.passages[passage_id].question_number
            for passage_id in supporting_passage_ids
            if passage_id in bundle.passages
        }
    )
    concept = bundle.registry[concept_id]
    return {
        "concept": concept.model_dump(mode="json"),
        "reviewed_annotations": reviewed_annotations,
        "reviewed_incident_edges": reviewed_edges,
        "reviewed_doctrinal_edges": reviewed_edges,
        "editorial_correspondences": editorial_edges,
        "reviewed_structural_edges": editorial_edges,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
        "supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in supporting_passage_ids[:12]
            if passage_id in bundle.passages
        ],
        "related_questions": related_questions,
        "coverage": {
            "reviewed_annotation_count": len(reviewed_annotations),
            "reviewed_edge_count": len(reviewed_edges),
            "editorial_edge_count": len(editorial_edges),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
        },
        "ambiguity_notes": concept.disambiguation_notes,
    }


PRUDENCE_VIEWER_PRESETS = _prudence_presets()


def _prudence_filter_edges_by_preset(
    bundle: CorpusAppBundle,
    preset_name: str,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    return _generic_filter_edges_by_preset(
        bundle,
        preset_name,
        presets=PRUDENCE_VIEWER_PRESETS,
        **kwargs,
    )

TRACT_ADAPTERS: dict[str, TractAdapter] = {
    "theological": TractAdapter(
        family="theological",
        label="Theological virtues",
        range_start=1,
        range_end=46,
        presets=THEOLOGICAL_VIRTUES_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_theological_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_theological_edges_by_preset),
        concept_page_data=theological_virtues_concept_page_data,
        edge_evidence_panel=theological_edge_evidence_panel,
    ),
    "prudence": TractAdapter(
        family="prudence",
        label="Prudence",
        range_start=47,
        range_end=56,
        presets=PRUDENCE_VIEWER_PRESETS,
        filter_edges_by_question_range=_generic_filter_edges_by_question_range,
        filter_edges_by_preset=_prudence_filter_edges_by_preset,
        concept_page_data=_generic_concept_payload_for_range,
        edge_evidence_panel=theological_edge_evidence_panel,
    ),
    "justice": TractAdapter(
        family="justice",
        label="Justice core",
        range_start=57,
        range_end=79,
        presets=JUSTICE_CORE_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_justice_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_justice_edges_by_preset),
        concept_page_data=justice_core_concept_page_data,
        edge_evidence_panel=justice_edge_evidence_panel,
    ),
    "religion": TractAdapter(
        family="religion",
        label="Religion tract",
        range_start=80,
        range_end=100,
        presets=RELIGION_TRACT_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_religion_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_religion_edges_by_preset),
        concept_page_data=religion_tract_concept_page_data,
        edge_evidence_panel=religion_edge_evidence_panel,
    ),
    "owed": TractAdapter(
        family="owed",
        label="Owed-relation tract",
        range_start=101,
        range_end=108,
        presets=OWED_RELATION_TRACT_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_owed_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_owed_edges_by_preset),
        concept_page_data=owed_relation_tract_concept_page_data,
        edge_evidence_panel=owed_edge_evidence_panel,
    ),
    "connected": TractAdapter(
        family="connected",
        label="Connected virtues",
        range_start=109,
        range_end=120,
        presets=CONNECTED_VIRTUES_109_120_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_connected_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_connected_edges_by_preset),
        concept_page_data=connected_virtues_109_120_concept_page_data,
        edge_evidence_panel=connected_edge_evidence_panel,
    ),
    "fortitude": TractAdapter(
        family="fortitude",
        label="Fortitude parts",
        range_start=129,
        range_end=135,
        presets=FORTITUDE_PARTS_129_135_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_fortitude_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_fortitude_edges_by_preset),
        concept_page_data=fortitude_parts_129_135_concept_page_data,
        edge_evidence_panel=fortitude_edge_evidence_panel,
    ),
    "fortitude_closure": TractAdapter(
        family="fortitude_closure",
        label="Fortitude closure",
        range_start=136,
        range_end=140,
        presets=FORTITUDE_CLOSURE_136_140_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_fortitude_closure_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(
            filter_fortitude_closure_edges_by_preset
        ),
        concept_page_data=fortitude_closure_136_140_concept_page_data,
        edge_evidence_panel=fortitude_closure_edge_evidence_panel,
    ),
    "temperance": TractAdapter(
        family="temperance",
        label="Temperance phase 1",
        range_start=141,
        range_end=160,
        presets=TEMPERANCE_141_160_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_temperance_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(filter_temperance_edges_by_preset),
        concept_page_data=temperance_141_160_concept_page_data,
        edge_evidence_panel=temperance_edge_evidence_panel,
    ),
    "temperance_closure": TractAdapter(
        family="temperance_closure",
        label="Temperance closure",
        range_start=161,
        range_end=170,
        presets=TEMPERANCE_CLOSURE_161_170_PRESETS,
        filter_edges_by_question_range=_wrap_range_filter(
            filter_temperance_closure_edges_by_question_range
        ),
        filter_edges_by_preset=_wrap_preset_filter(
            filter_temperance_closure_edges_by_preset
        ),
        concept_page_data=temperance_closure_161_170_concept_page_data,
        edge_evidence_panel=temperance_closure_edge_evidence_panel,
    ),
}

VIEWER_PRESETS: dict[str, ViewerPreset] = {
    f"{family}:{key}": ViewerPreset(
        family=family,
        key=key,
        label=str(value["label"]),
        start_question=int(value["start_question"]),
        end_question=int(value["end_question"]),
    )
    for family, adapter in TRACT_ADAPTERS.items()
    for key, value in adapter.presets.items()
}


def sorted_preset_names() -> list[str]:
    return sorted(
        VIEWER_PRESETS,
        key=lambda name: (
            VIEWER_PRESETS[name].start_question,
            VIEWER_PRESETS[name].end_question,
            VIEWER_PRESETS[name].label.casefold(),
        ),
    )


def preset_label(preset_name: str) -> str:
    return VIEWER_PRESETS[preset_name].label


def preset_range(preset_name: str) -> tuple[int, int]:
    preset = VIEWER_PRESETS[preset_name]
    return preset.start_question, preset.end_question


def preset_family(preset_name: str) -> str:
    return VIEWER_PRESETS[preset_name].family


def adapter_for_family(family: str | None) -> TractAdapter | None:
    if family is None:
        return None
    return TRACT_ADAPTERS.get(family)


def adapter_for_preset(preset_name: str | None) -> TractAdapter | None:
    if not preset_name:
        return None
    return adapter_for_family(preset_family(preset_name))


def family_for_range(start_question: int, end_question: int) -> str | None:
    matching = [
        adapter
        for adapter in TRACT_ADAPTERS.values()
        if adapter.range_start <= start_question <= end_question <= adapter.range_end
    ]
    if not matching:
        return None
    matching.sort(
        key=lambda adapter: (
            adapter.range_end - adapter.range_start,
            adapter.range_start,
        )
    )
    return matching[0].family
