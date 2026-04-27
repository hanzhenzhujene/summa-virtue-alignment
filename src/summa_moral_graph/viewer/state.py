from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ..app.corpus import (
    CorpusAppBundle,
    build_graph_for_edges,
    candidate_items_for_passage,
    concept_page_data,
    filter_graph_edges,
    generate_structural_edges,
    passage_search,
    reviewed_annotations_for_passage,
)
from ..ontology import search_registry
from .load import ViewerAppData
from .navigation import ACTIVE_PRESET_KEY, CONCEPT_ID_KEY, PASSAGE_ID_KEY
from .registry import (
    adapter_for_preset,
    adapters_for_range,
    preset_family,
    preset_label,
    preset_range,
)

RELATION_GROUPS: dict[str, tuple[str, ...]] = {
    "Opposition": (
        "opposed_by",
        "contrary_to",
        "excess_opposed_to",
        "deficiency_opposed_to",
    ),
    "Parts and taxonomy": (
        "integral_part_of",
        "subjective_part_of",
        "potential_part_of",
        "part_of",
        "part_of_fortitude",
        "species_of",
    ),
    "Acts, gifts, precepts": (
        "act_of",
        "has_act",
        "principal_act_of",
        "corresponding_gift_of",
        "corresponds_to",
        "precept_of",
        "commands_act_of",
        "forbids_opposed_vice_of",
    ),
    "Domain and process": (
        "concerns_food",
        "concerns_drink",
        "concerns_sexual_pleasure",
        "concerns_anger",
        "concerns_honor",
        "concerns_great_expenditure",
        "concerns_external_goods",
        "harms_domain",
        "corrupts_process",
        "requires_restitution",
        "concerns_sacred_object",
        "misuses_sacred_object",
    ),
    "Structure and treatment": (
        "treated_in",
        "contains_article",
        "annexed_to",
        "defined_as",
        "directed_to",
        "regulated_by",
        "perfected_by",
        "requires",
        "resides_in",
        "case_of",
        "results_in_punishment",
        "tempted_by",
    ),
}


@dataclass(frozen=True)
class ScopeSummary:
    label: str
    preset_name: str | None
    family: str | None
    start_question: int | None
    end_question: int | None


@dataclass(frozen=True)
class PassageFilterState:
    part_options: tuple[str, ...]
    question_options: tuple[str, ...]
    article_options: tuple[str, ...]
    selected_part: str
    selected_question: str
    selected_article: str
    part_locked: bool


def active_scope_summary(session_state: Mapping[str, object]) -> ScopeSummary:
    preset_name = str(session_state.get(ACTIVE_PRESET_KEY, "") or "")
    if preset_name:
        start_question, end_question = preset_range(preset_name)
        return ScopeSummary(
            label=preset_label(preset_name),
            preset_name=preset_name,
            family=preset_family(preset_name),
            start_question=start_question,
            end_question=end_question,
        )
    return ScopeSummary(
        label="Full corpus",
        preset_name=None,
        family=None,
        start_question=None,
        end_question=None,
    )


def concept_ids_in_question_range(
    bundle: CorpusAppBundle,
    *,
    start_question: int,
    end_question: int,
) -> set[str]:
    concept_ids: set[str] = set()
    for row in bundle.reviewed_annotations:
        passage_id = str(row["source_passage_id"])
        if passage_id not in bundle.passages:
            continue
        passage = bundle.passages[passage_id]
        if passage.part_id != "ii-ii" or not (
            start_question <= passage.question_number <= end_question
        ):
            continue
        concept_ids.add(str(row["subject_id"]))
        concept_ids.add(str(row["object_id"]))
    for mention in bundle.candidate_mentions:
        if mention.passage_id not in bundle.passages:
            continue
        passage = bundle.passages[mention.passage_id]
        if passage.part_id != "ii-ii" or not (
            start_question <= passage.question_number <= end_question
        ):
            continue
        if mention.proposed_concept_id:
            concept_ids.add(mention.proposed_concept_id)
        concept_ids.update(mention.proposed_concept_ids)
    for relation in bundle.candidate_relations:
        if relation.source_passage_id not in bundle.passages:
            continue
        passage = bundle.passages[relation.source_passage_id]
        if passage.part_id != "ii-ii" or not (
            start_question <= passage.question_number <= end_question
        ):
            continue
        concept_ids.add(relation.subject_id)
        concept_ids.add(relation.object_id)
    return {concept_id for concept_id in concept_ids if concept_id in bundle.registry}


def concept_matches(
    data: ViewerAppData,
    *,
    query: str,
    node_types: set[str],
    preset_name: str | None,
) -> list[tuple[str, str]]:
    bundle = data.bundle
    if query.strip():
        matches = search_registry(query, bundle.registry)
    else:
        matches = sorted(
            bundle.registry.values(),
            key=lambda record: record.canonical_label.casefold(),
        )
    if preset_name:
        start_question, end_question = preset_range(preset_name)
        allowed_ids = concept_ids_in_question_range(
            bundle,
            start_question=start_question,
            end_question=end_question,
        )
        matches = [record for record in matches if record.concept_id in allowed_ids]
    if node_types:
        matches = [record for record in matches if record.node_type in node_types]
    return [
        (
            record.concept_id,
            f"{record.canonical_label} · {record.node_type}",
        )
        for record in matches
    ]


def supporting_concepts_for_passage(
    data: ViewerAppData,
    passage_id: str,
) -> dict[str, list[dict[str, str]]]:
    bundle = data.bundle
    reviewed_ids: set[str] = set()
    for row in reviewed_annotations_for_passage(bundle, passage_id):
        for key in ("subject_id", "object_id"):
            concept_id = str(row[key])
            if concept_id in bundle.registry:
                reviewed_ids.add(concept_id)
    candidate_ids: set[str] = set()
    candidate_items = candidate_items_for_passage(bundle, passage_id)
    for row in candidate_items["mentions"]:
        proposed = row.get("proposed_concept_id")
        if proposed in bundle.registry:
            candidate_ids.add(str(proposed))
        for concept_id in row.get("proposed_concept_ids", []):
            if concept_id in bundle.registry:
                candidate_ids.add(str(concept_id))
    return {
        "reviewed": [
            {
                "concept_id": concept_id,
                "label": bundle.registry[concept_id].canonical_label,
                "node_type": bundle.registry[concept_id].node_type,
            }
            for concept_id in sorted(
                reviewed_ids,
                key=lambda value: bundle.registry[value].canonical_label.casefold(),
            )
        ],
        "candidate": [
            {
                "concept_id": concept_id,
                "label": bundle.registry[concept_id].canonical_label,
                "node_type": bundle.registry[concept_id].node_type,
            }
            for concept_id in sorted(
                candidate_ids - reviewed_ids,
                key=lambda value: bundle.registry[value].canonical_label.casefold(),
            )
        ],
    }


def passage_results(
    data: ViewerAppData,
    *,
    query: str,
    part_id: str | None,
    question_id: str | None,
    article_id: str | None,
    segment_type: str | None,
    preset_name: str | None,
) -> list[Any]:
    bundle = data.bundle
    effective_part = "ii-ii" if preset_name else part_id
    results = passage_search(
        bundle,
        query=query,
        part_id=effective_part or None,
        question_id=question_id or None,
        article_id=article_id or None,
        segment_type=segment_type or None,
    )
    if preset_name:
        start_question, end_question = preset_range(preset_name)
        results = [
            passage
            for passage in results
            if passage.part_id == "ii-ii"
            and start_question <= passage.question_number <= end_question
        ]
    return results


def normalize_passage_filter_state(
    data: ViewerAppData,
    *,
    part_id: str | None,
    question_id: str | None,
    article_id: str | None,
    preset_name: str | None,
) -> PassageFilterState:
    bundle = data.bundle
    part_locked = preset_name is not None
    if preset_name is not None:
        start_question, end_question = preset_range(preset_name)
        scoped_passages = [
            passage
            for passage in bundle.passages.values()
            if passage.part_id == "ii-ii"
            and start_question <= passage.question_number <= end_question
        ]
        selected_part = "ii-ii"
        part_options: tuple[str, ...] = ("ii-ii",)
    else:
        selected_part = str(part_id or "")
        if selected_part not in {"", "i-ii", "ii-ii"}:
            selected_part = ""
        part_options = ("", "i-ii", "ii-ii")
        scoped_passages = [
            passage
            for passage in bundle.passages.values()
            if not selected_part or passage.part_id == selected_part
        ]

    question_options = tuple(sorted({passage.question_id for passage in scoped_passages}))
    selected_question = str(question_id or "")
    if selected_question not in question_options:
        selected_question = ""

    article_source_passages = [
        passage
        for passage in scoped_passages
        if not selected_question or passage.question_id == selected_question
    ]
    article_options = tuple(sorted({passage.article_id for passage in article_source_passages}))
    selected_article = str(article_id or "")
    if selected_article not in article_options:
        selected_article = ""

    return PassageFilterState(
        part_options=part_options,
        question_options=question_options,
        article_options=article_options,
        selected_part=selected_part,
        selected_question=selected_question,
        selected_article=selected_article,
        part_locked=part_locked,
    )


def selected_passage_for_results(
    session_state: Mapping[str, object],
    results: list[Any],
    bundle: CorpusAppBundle,
) -> Any | None:
    selected_id = str(session_state.get(PASSAGE_ID_KEY, "") or "")
    if results:
        if selected_id in bundle.passages and any(
            result.segment_id == selected_id for result in results
        ):
            return bundle.passages[selected_id]
        return results[0]
    return None


def selected_concept_id(session_state: dict[str, object]) -> str:
    return str(session_state.get(CONCEPT_ID_KEY, "") or "")


def concept_payload_for_selection(
    data: ViewerAppData,
    concept_id: str,
    *,
    preset_name: str | None,
) -> dict[str, Any]:
    bundle = data.bundle
    if preset_name:
        adapter = adapter_for_preset(preset_name)
        if adapter is not None:
            start_question, end_question = preset_range(preset_name)
            payload = adapter.concept_page_data(
                bundle,
                concept_id,
                start_question=start_question,
                end_question=end_question,
            )
            return _normalize_concept_payload(
                bundle,
                concept_id,
                payload,
                scope_mode="tract",
                scope_label=preset_label(preset_name),
                preset_name=preset_name,
            )
    fallback_note = None
    scope_mode = "full_corpus"
    scope_label = "Full corpus"
    if preset_name:
        scope_mode = "broader_corpus_fallback"
        scope_label = preset_label(preset_name)
        fallback_note = (
            f"{scope_label} concept rendering is unavailable here, so the page is showing a "
            "broader corpus fallback."
        )
    return _normalize_concept_payload(
        bundle,
        concept_id,
        concept_page_data(bundle, concept_id),
        scope_mode=scope_mode,
        scope_label=scope_label,
        preset_name=preset_name,
        fallback_note=fallback_note,
    )


def _normalize_concept_payload(
    bundle: CorpusAppBundle,
    concept_id: str,
    payload: dict[str, Any],
    *,
    scope_mode: str,
    scope_label: str,
    preset_name: str | None,
    fallback_note: str | None = None,
) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.setdefault("concept", bundle.registry[concept_id].model_dump(mode="json"))

    reviewed_incident_edges = list(normalized.get("reviewed_incident_edges", []))
    reviewed_doctrinal_edges = list(normalized.get("reviewed_doctrinal_edges", []))
    if reviewed_incident_edges and not reviewed_doctrinal_edges:
        normalized["reviewed_doctrinal_edges"] = reviewed_incident_edges
        reviewed_doctrinal_edges = reviewed_incident_edges
    elif reviewed_doctrinal_edges and not reviewed_incident_edges:
        normalized["reviewed_incident_edges"] = reviewed_doctrinal_edges

    editorial_correspondences = list(normalized.get("editorial_correspondences", []))
    reviewed_structural_edges = list(normalized.get("reviewed_structural_edges", []))
    if editorial_correspondences and not reviewed_structural_edges:
        normalized["reviewed_structural_edges"] = editorial_correspondences
        reviewed_structural_edges = editorial_correspondences
    elif reviewed_structural_edges and not editorial_correspondences:
        normalized["editorial_correspondences"] = reviewed_structural_edges

    top_supporting_passages = list(normalized.get("top_supporting_passages", []))
    supporting_passages = list(normalized.get("supporting_passages", []))
    if top_supporting_passages and not supporting_passages:
        normalized["supporting_passages"] = top_supporting_passages
    elif supporting_passages and not top_supporting_passages:
        normalized["top_supporting_passages"] = supporting_passages

    unresolved_notes = list(normalized.get("unresolved_disambiguation_notes", []))
    ambiguity_notes = list(normalized.get("ambiguity_notes", []))
    if unresolved_notes and not ambiguity_notes:
        normalized["ambiguity_notes"] = unresolved_notes
    elif ambiguity_notes and not unresolved_notes:
        normalized["unresolved_disambiguation_notes"] = ambiguity_notes

    for key in (
        "reviewed_doctrinal_edges",
        "reviewed_structural_edges",
        "reviewed_incident_edges",
        "editorial_correspondences",
        "candidate_mentions",
        "candidate_relations",
        "supporting_passages",
        "top_supporting_passages",
        "related_questions",
        "ambiguity_notes",
        "unresolved_disambiguation_notes",
    ):
        normalized.setdefault(key, [])
    normalized["scope_mode"] = scope_mode
    normalized["scope_label"] = scope_label
    normalized["preset_name"] = preset_name
    normalized["scope_fallback_note"] = fallback_note
    normalized["broader_corpus_fallback"] = bool(fallback_note)
    return normalized


def relation_groups_for_concept(
    edges: list[dict[str, Any]],
    *,
    concept_id: str,
) -> list[tuple[str, list[dict[str, Any]]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        grouped[str(edge["relation_type"])].append(edge)
    return [
        (
            relation_type,
            sorted(
                relation_edges,
                key=lambda row: (
                    str(
                        row["object_label"]
                        if str(row["subject_id"]) == concept_id
                        else row["subject_label"]
                    ).casefold(),
                    str(row["edge_id"]),
                ),
            ),
        )
        for relation_type, relation_edges in sorted(grouped.items())
    ]


def graph_relation_type_options(bundle: CorpusAppBundle) -> list[str]:
    return sorted(
        {
            str(edge["relation_type"])
            for edge in [*bundle.reviewed_doctrinal_edges, *bundle.reviewed_structural_edges]
        }
        | {str(record.relation_type) for record in bundle.candidate_relations}
    )


def graph_focus_tag_options(edges: list[dict[str, Any]]) -> list[str]:
    tags: set[str] = set()
    for edge in edges:
        for key, value in edge.items():
            if key.endswith("_focus_tags") and isinstance(value, list):
                tags.update(str(item) for item in value)
    return sorted(tags)


def available_focus_tags_for_scope(
    data: ViewerAppData,
    *,
    preset_name: str | None,
    map_range: tuple[int, int],
) -> list[str]:
    bundle = data.bundle
    adapter = adapter_for_preset(preset_name) if preset_name else None
    range_adapters = adapters_for_range(*map_range) if preset_name is None else []
    edges: list[dict[str, Any]] = []
    seen_edge_keys: set[tuple[str, str]] = set()

    if preset_name and adapter is not None:
        edges = adapter.filter_edges_by_preset(
            bundle,
            preset_name.split(":", 1)[1],
            include_editorial=True,
            include_candidate=True,
            relation_types=None,
            node_types=None,
            center_concept=None,
            focus_tags=None,
        )
    else:
        start_question, end_question = map_range
        for range_adapter in range_adapters:
            overlap_start = max(start_question, range_adapter.range_start)
            overlap_end = min(end_question, range_adapter.range_end)
            if overlap_start > overlap_end:
                continue
            adapter_edges = range_adapter.filter_edges_by_question_range(
                bundle,
                start_question=overlap_start,
                end_question=overlap_end,
                include_editorial=True,
                include_candidate=True,
                relation_types=None,
                node_types=None,
                center_concept=None,
                focus_tags=None,
            )
            for edge in adapter_edges:
                edge_key = (str(edge.get("edge_id", "")), str(edge.get("layer", "")))
                if edge_key in seen_edge_keys:
                    continue
                seen_edge_keys.add(edge_key)
                edges.append(edge)

    return graph_focus_tag_options(edges)


def expand_relation_groups(
    group_names: set[str],
    *,
    available_relation_types: set[str],
) -> set[str]:
    relation_types: set[str] = set()
    for group_name in group_names:
        relation_types.update(
            relation_type
            for relation_type in RELATION_GROUPS.get(group_name, ())
            if relation_type in available_relation_types
        )
    return relation_types


def graph_edges_for_view(
    data: ViewerAppData,
    *,
    preset_name: str | None,
    map_range: tuple[int, int],
    include_structural: bool,
    include_editorial: bool,
    include_candidate: bool,
    relation_types: set[str] | None,
    relation_groups: set[str] | None,
    node_types: set[str] | None,
    focus_tags: set[str] | None,
    question_id: str | None,
    center_concept: str | None,
    segment_types: set[str] | None,
    local_only: bool,
) -> tuple[list[dict[str, Any]], str | None]:
    bundle = data.bundle
    visible_relation_types = set(graph_relation_type_options(bundle))
    effective_relation_types: set[str] | None = set(relation_types or set())
    if relation_groups:
        if effective_relation_types is None:
            effective_relation_types = set()
        effective_relation_types.update(
            expand_relation_groups(
                relation_groups,
                available_relation_types=visible_relation_types,
            )
        )
    if effective_relation_types is not None and not effective_relation_types:
        effective_relation_types = None

    adapter = adapter_for_preset(preset_name) if preset_name else None
    range_adapters = adapters_for_range(*map_range) if preset_name is None else []

    if local_only and not center_concept:
        return ([], "Pick a center concept to build a local map.")

    if preset_name and adapter is not None:
        edges = adapter.filter_edges_by_preset(
            bundle,
            preset_name.split(":", 1)[1],
            include_editorial=include_editorial,
            include_candidate=include_candidate,
            relation_types=effective_relation_types,
            node_types=node_types,
            center_concept=center_concept,
            focus_tags=focus_tags,
        )
    elif range_adapters:
        start_question, end_question = map_range
        edges = []
        seen_edge_keys: set[tuple[str, str]] = set()
        for range_adapter in range_adapters:
            overlap_start = max(start_question, range_adapter.range_start)
            overlap_end = min(end_question, range_adapter.range_end)
            if overlap_start > overlap_end:
                continue
            adapter_edges = range_adapter.filter_edges_by_question_range(
                bundle,
                start_question=overlap_start,
                end_question=overlap_end,
                include_editorial=include_editorial,
                include_candidate=include_candidate,
                relation_types=effective_relation_types,
                node_types=node_types,
                center_concept=center_concept,
                focus_tags=focus_tags,
            )
            for edge in adapter_edges:
                edge_key = (str(edge.get("edge_id", "")), str(edge.get("layer", "")))
                if edge_key in seen_edge_keys:
                    continue
                seen_edge_keys.add(edge_key)
                edges.append(edge)
    else:
        if not center_concept and not question_id:
            return (
                [],
                (
                    "No reviewed doctrinal graph coverage is available in this question "
                    "span yet. Try a reviewed tract span, enable structural edges, or "
                    "narrow to a reviewed block."
                ),
            )
        edges = filter_graph_edges(
            bundle,
            include_structural=False,
            include_candidate=include_candidate,
            relation_types=effective_relation_types,
            node_types=node_types,
            question_id=question_id,
            center_concept=center_concept,
        )
        if not include_editorial:
            edges = [edge for edge in edges if edge["layer"] == "reviewed_doctrinal"]
        else:
            edges = [
                edge
                for edge in [*edges, *bundle.reviewed_structural_edges]
                if center_concept is None
                or center_concept in {str(edge["subject_id"]), str(edge["object_id"])}
            ]

    if question_id:
        edges = [
            edge
            for edge in edges
            if question_id in {str(edge["subject_id"]), str(edge["object_id"])}
            or any(
                passage_id in bundle.passages
                and bundle.passages[passage_id].question_id == question_id
                for passage_id in edge.get("source_passage_ids", [])
            )
        ]
    if segment_types:
        edges = [
            edge
            for edge in edges
            if any(
                passage_id in bundle.passages
                and bundle.passages[passage_id].segment_type in segment_types
                for passage_id in edge.get("source_passage_ids", [])
            )
        ]
    if include_structural:
        structural_edges = generate_structural_edges_for_range(
            bundle,
            question_id=question_id,
            map_range=map_range,
            center_concept=center_concept,
        )
        edges = [*edges, *structural_edges]
    edges.sort(key=lambda item: (str(item["layer"]), str(item["edge_id"])))
    return (edges, None)


def center_concept_ids_for_view(
    data: ViewerAppData,
    *,
    preset_name: str | None,
    map_range: tuple[int, int],
    include_structural: bool,
    include_editorial: bool,
    include_candidate: bool,
    relation_types: set[str] | None,
    relation_groups: set[str] | None,
    node_types: set[str] | None,
    focus_tags: set[str] | None,
    question_id: str | None,
    segment_types: set[str] | None,
) -> list[str]:
    edges, _ = graph_edges_for_view(
        data,
        preset_name=preset_name,
        map_range=map_range,
        include_structural=include_structural,
        include_editorial=include_editorial,
        include_candidate=include_candidate,
        relation_types=relation_types,
        relation_groups=relation_groups,
        node_types=node_types,
        focus_tags=focus_tags,
        question_id=question_id,
        center_concept=None,
        segment_types=segment_types,
        local_only=False,
    )
    concept_ids = {
        concept_id
        for edge in edges
        for concept_id in (str(edge["subject_id"]), str(edge["object_id"]))
        if concept_id in data.bundle.registry
    }
    return sorted(
        concept_ids,
        key=lambda concept_id: (
            data.bundle.registry[concept_id].canonical_label.casefold(),
            concept_id,
        ),
    )


def generate_structural_edges_for_range(
    bundle: CorpusAppBundle,
    *,
    question_id: str | None,
    map_range: tuple[int, int],
    center_concept: str | None,
) -> list[dict[str, Any]]:
    start_question, end_question = map_range
    rows = [
        edge
        for edge in generate_structural_edges(bundle, question_id=question_id)
        if str(edge["subject_id"]) in bundle.questions
        and bundle.questions[str(edge["subject_id"])].part_id in {"i-ii", "ii-ii"}
        and start_question
        <= bundle.questions[str(edge["subject_id"])].question_number
        <= end_question
    ]
    if center_concept:
        rows = [
            edge
            for edge in rows
            if center_concept in {str(edge["subject_id"]), str(edge["object_id"])}
        ]
    return rows


def graph_rows(edges: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node_catalog = {
        str(edge[f"{side}_id"]): {
            "node_id": str(edge[f"{side}_id"]),
            "label": str(edge[f"{side}_label"]),
            "node_type": str(edge[f"{side}_type"]),
        }
        for edge in edges
        for side in ("subject", "object")
    }
    node_rows = sorted(
        node_catalog.values(),
        key=lambda item: (item["node_type"], item["label"]),
    )
    return (node_rows, edges)


def graph_focus_counts(edges: list[dict[str, Any]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for edge in edges:
        for key, value in edge.items():
            if key.endswith("_focus_tags") and isinstance(value, list):
                counter.update(str(tag) for tag in value)
    return counter


def graph_payload_for_export(
    edges: list[dict[str, Any]],
    *,
    scope_label: str,
    preset_name: str | None,
    map_range: tuple[int, int],
    question_id: str | None,
    center_concept: str | None,
) -> dict[str, Any]:
    graph = build_graph_for_edges(edges)
    return {
        "scope": {
            "scope_label": scope_label,
            "preset_name": preset_name,
            "range": [map_range[0], map_range[1]],
            "question_id": question_id,
            "center_concept": center_concept,
        },
        "counts": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "layer_counts": Counter(str(edge["layer"]) for edge in edges),
        },
        "edges": edges,
    }
