from __future__ import annotations

import html as html_lib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx

from ..models import (
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..ontology import load_corpus_registry, search_registry
from ..utils.jsonl import load_jsonl
from ..utils.paths import PROCESSED_DIR
from ..utils.text import normalize_text

NODE_COLORS = {
    "virtue": "#1d3557",
    "vice": "#b00020",
    "sin_type": "#7f1d1d",
    "wrong_act": "#9c2f00",
    "habit": "#6b7280",
    "passion": "#c05621",
    "act_type": "#6d597a",
    "law": "#006d77",
    "law_type": "#2a9d8f",
    "grace": "#3a86ff",
    "grace_type": "#4895ef",
    "beatitude": "#6a994e",
    "gift_holy_spirit": "#5a189a",
    "charism": "#7b2cbf",
    "precept": "#ff8800",
    "faculty": "#4d908e",
    "object": "#adb5bd",
    "domain": "#2b9348",
    "role": "#577590",
    "process": "#8d99ae",
    "doctrine": "#495057",
    "end": "#e09f3e",
    "question": "#5c677d",
    "article": "#7f5539",
}

EDGE_COLORS = {
    "reviewed_doctrinal": "#264653",
    "reviewed_structural": "#6c757d",
    "structural": "#b0b7c3",
    "candidate": "#d97706",
}


@dataclass(frozen=True)
class CorpusAppBundle:
    registry: dict[str, CorpusConceptRecord]
    questions: dict[str, QuestionRecord]
    passages: dict[str, SegmentRecord]
    coverage: dict[str, Any]
    candidate_validation: dict[str, Any]
    manifest: dict[str, Any]
    candidate_mentions: list[CorpusCandidateMentionRecord]
    candidate_relations: list[CorpusCandidateRelationProposalRecord]
    reviewed_annotations: list[dict[str, Any]]
    reviewed_doctrinal_edges: list[dict[str, Any]]
    reviewed_structural_edges: list[dict[str, Any]]


def load_corpus_bundle(root: Path | None = None) -> CorpusAppBundle:
    """Load corpus-scale structural, reviewed, and candidate artifacts."""

    base = root or PROCESSED_DIR.parent.parent
    registry = load_corpus_registry(base / "data" / "gold" / "corpus_concept_registry.jsonl")
    for concept_record in load_reviewed_registry_overlays(base).values():
        registry[concept_record.concept_id] = concept_record
    questions = {
        record.question_id: record
        for record in (
            QuestionRecord.model_validate(payload)
            for payload in load_jsonl(base / "data" / "interim" / "summa_moral_questions.jsonl")
        )
    }
    passages = {
        record.segment_id: record
        for record in (
            SegmentRecord.model_validate(payload)
            for payload in load_jsonl(base / "data" / "interim" / "summa_moral_segments.jsonl")
        )
    }
    coverage = json.loads(
        (base / "data" / "processed" / "coverage_report.json").read_text(encoding="utf-8")
    )
    candidate_validation = json.loads(
        (base / "data" / "processed" / "candidate_validation_report.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = json.loads(
        (base / "data" / "processed" / "corpus_manifest.json").read_text(encoding="utf-8")
    )
    candidate_mentions = [
        CorpusCandidateMentionRecord.model_validate(payload)
        for payload in load_jsonl(base / "data" / "candidate" / "corpus_candidate_mentions.jsonl")
    ]
    candidate_relations = [
        CorpusCandidateRelationProposalRecord.model_validate(payload)
        for payload in load_jsonl(
            base / "data" / "candidate" / "corpus_candidate_relation_proposals.jsonl"
        )
    ]
    reviewed_annotations = load_reviewed_annotations(base)
    reviewed_doctrinal_edges = load_reviewed_doctrinal_edges(base)
    reviewed_structural_edges = load_reviewed_structural_edges(base)
    return CorpusAppBundle(
        registry=registry,
        questions=questions,
        passages=passages,
        coverage=coverage,
        candidate_validation=candidate_validation,
        manifest=manifest,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
        reviewed_annotations=reviewed_annotations,
        reviewed_doctrinal_edges=reviewed_doctrinal_edges,
        reviewed_structural_edges=reviewed_structural_edges,
    )


def load_reviewed_registry_overlays(base: Path) -> dict[str, CorpusConceptRecord]:
    overlays: dict[str, CorpusConceptRecord] = {}
    for filename in (
        "connected_virtues_109_120_reviewed_concepts.jsonl",
        "fortitude_closure_136_140_reviewed_concepts.jsonl",
        "fortitude_parts_129_135_reviewed_concepts.jsonl",
        "prudence_reviewed_concepts.jsonl",
        "theological_virtues_reviewed_concepts.jsonl",
        "justice_core_reviewed_concepts.jsonl",
        "owed_relation_tract_reviewed_concepts.jsonl",
        "religion_tract_reviewed_concepts.jsonl",
        "temperance_141_160_reviewed_concepts.jsonl",
        "temperance_closure_161_170_reviewed_concepts.jsonl",
    ):
        path = base / "data" / "gold" / filename
        if not path.exists():
            continue
        for payload in load_jsonl(path):
            record = coerce_overlay_record(payload)
            overlays[record.concept_id] = record
    return overlays


def coerce_overlay_record(payload: dict[str, Any]) -> CorpusConceptRecord:
    if "canonical_label" in payload:
        return CorpusConceptRecord.model_validate(payload)
    if "label" in payload:
        node_type_map = {
            "act": "act_type",
            "defect": "sin_type",
            "prudence_part": "virtue",
            "taxonomy": "doctrine",
        }
        notes = list(payload.get("notes", []))
        part_taxonomy = payload.get("part_taxonomy")
        disambiguation_notes = []
        if payload.get("disambiguation_note"):
            disambiguation_notes.append(str(payload["disambiguation_note"]))
        unresolved_note = payload.get("unresolved_note")
        if unresolved_note:
            disambiguation_notes.append(str(unresolved_note))
        if part_taxonomy:
            notes.append(f"part_taxonomy:{part_taxonomy}")
        return CorpusConceptRecord.model_validate(
            {
                "concept_id": payload["concept_id"],
                "canonical_label": payload["label"],
                "node_type": node_type_map.get(
                    str(payload["node_type"]),
                    payload["node_type"],
                ),
                "aliases": payload.get("aliases", []),
                "description": payload["description"],
                "notes": notes,
                "source_scope": [],
                "parent_concept_id": None,
                "registry_status": "reviewed_seed",
                "disambiguation_notes": disambiguation_notes,
                "related_concepts": [],
                "introduced_in_questions": [],
            }
        )
    raise ValueError("Unsupported reviewed concept overlay payload")


def corpus_browser_rows(
    bundle: CorpusAppBundle,
    *,
    level: str = "question",
    part_id: str | None = None,
    question_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return question or article browser rows with coverage metadata."""

    rows = bundle.coverage["questions"] if level == "question" else bundle.coverage["articles"]
    filtered: list[dict[str, Any]] = []
    for row in rows:
        if part_id and row["part_id"] != part_id:
            continue
        if question_id and row.get("question_id") != question_id:
            continue
        filtered.append(row)
    if level == "question":
        filtered.sort(key=lambda item: (item["part_id"], item["question_number"]))
    else:
        filtered.sort(
            key=lambda item: (
                item["part_id"],
                item["question_number"],
                item["article_number"],
            )
        )
    return filtered


def passage_search(
    bundle: CorpusAppBundle,
    *,
    query: str = "",
    part_id: str | None = None,
    question_id: str | None = None,
    article_id: str | None = None,
    segment_type: str | None = None,
) -> list[SegmentRecord]:
    """Search full-corpus passages by id, citation, text, or concept label."""

    normalized_query = normalize_text(query).casefold()
    concept_ids = (
        {record.concept_id for record in search_registry(query, bundle.registry)}
        if query.strip()
        else set()
    )
    supporting_passages = supporting_passages_for_concepts(bundle, concept_ids)
    results: list[SegmentRecord] = []
    for passage in sorted(
        bundle.passages.values(),
        key=lambda item: (
            item.part_id,
            item.question_number,
            item.article_number,
            item.segment_id,
        ),
    ):
        if part_id and passage.part_id != part_id:
            continue
        if question_id and passage.question_id != question_id:
            continue
        if article_id and passage.article_id != article_id:
            continue
        if segment_type and passage.segment_type != segment_type:
            continue
        if not normalized_query:
            results.append(passage)
            continue
        haystacks = [
            passage.segment_id.casefold(),
            passage.citation_label.casefold(),
            normalize_text(passage.text).casefold(),
        ]
        if any(normalized_query in haystack for haystack in haystacks):
            results.append(passage)
            continue
        if passage.segment_id in supporting_passages:
            results.append(passage)
    return results


def passage_activity_summary(bundle: CorpusAppBundle, passage_id: str) -> dict[str, int]:
    """Return reviewed/candidate counts for a passage."""

    reviewed = sum(
        1 for row in bundle.reviewed_annotations if row["source_passage_id"] == passage_id
    )
    candidate_mentions = sum(
        1 for record in bundle.candidate_mentions if record.passage_id == passage_id
    )
    candidate_relations = sum(
        1 for record in bundle.candidate_relations if record.source_passage_id == passage_id
    )
    return {
        "reviewed_annotations": reviewed,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
    }


def reviewed_annotations_for_passage(
    bundle: CorpusAppBundle,
    passage_id: str,
) -> list[dict[str, Any]]:
    return [
        row
        for row in sorted(
            bundle.reviewed_annotations,
            key=lambda item: (str(item["source_layer"]), str(item["annotation_id"])),
        )
        if row["source_passage_id"] == passage_id
    ]


def candidate_items_for_passage(
    bundle: CorpusAppBundle,
    passage_id: str,
) -> dict[str, list[dict[str, Any]]]:
    mentions = [
        record.model_dump(mode="json")
        for record in bundle.candidate_mentions
        if record.passage_id == passage_id
    ]
    relations = [
        record.model_dump(mode="json")
        for record in bundle.candidate_relations
        if record.source_passage_id == passage_id
    ]
    return {"mentions": mentions, "relations": relations}


def highlight_passage_text(
    passage_text: str,
    reviewed_rows: list[dict[str, Any]],
    candidate_mentions: list[dict[str, Any]],
) -> str:
    """Highlight reviewed evidence snippets and candidate matches in a passage."""

    highlighted = html_lib.escape(passage_text)
    reviewed_snippets = {
        str(row["evidence_text"]) for row in reviewed_rows if row.get("evidence_text")
    }
    for snippet in sorted(reviewed_snippets, key=len, reverse=True)[:8]:
        escaped = html_lib.escape(snippet)
        if escaped in highlighted:
            highlighted = highlighted.replace(escaped, f"<mark>{escaped}</mark>", 1)
    candidate_texts = {
        str(row["matched_text"]) for row in candidate_mentions if row.get("matched_text")
    }
    for snippet in sorted(candidate_texts, key=len, reverse=True)[:8]:
        escaped = html_lib.escape(snippet)
        if escaped in highlighted:
            highlighted = highlighted.replace(escaped, f"<u>{escaped}</u>", 1)
    return highlighted


def concept_page_data(bundle: CorpusAppBundle, concept_id: str) -> dict[str, Any]:
    """Build a coverage-aware concept payload with reviewed and candidate layers separated."""

    concept = bundle.registry[concept_id]
    reviewed_annotations = [
        row
        for row in bundle.reviewed_annotations
        if row["subject_id"] == concept_id or row["object_id"] == concept_id
    ]
    reviewed_doctrinal_edges = [
        row
        for row in bundle.reviewed_doctrinal_edges
        if row["subject_id"] == concept_id or row["object_id"] == concept_id
    ]
    reviewed_structural_edges = [
        row
        for row in bundle.reviewed_structural_edges
        if row["subject_id"] == concept_id or row["object_id"] == concept_id
    ]
    candidate_mentions = [
        record.model_dump(mode="json")
        for record in bundle.candidate_mentions
        if record.proposed_concept_id == concept_id or concept_id in record.proposed_concept_ids
    ]
    candidate_relations = [
        record.model_dump(mode="json")
        for record in bundle.candidate_relations
        if record.subject_id == concept_id or record.object_id == concept_id
    ]
    support_passages = top_supporting_passages(bundle, concept_id)
    related_questions = sorted(
        {bundle.passages[passage_id].question_id for passage_id in support_passages}
    )
    return {
        "concept": concept.model_dump(mode="json"),
        "reviewed_annotations": reviewed_annotations,
        "reviewed_doctrinal_edges": reviewed_doctrinal_edges,
        "reviewed_structural_edges": reviewed_structural_edges,
        "candidate_mentions": candidate_mentions,
        "candidate_relations": candidate_relations,
        "supporting_passages": [
            {
                "passage_id": passage_id,
                "citation_label": bundle.passages[passage_id].citation_label,
                "text": bundle.passages[passage_id].text,
            }
            for passage_id in support_passages
        ],
        "related_questions": related_questions,
        "coverage": {
            "reviewed_annotation_count": len(reviewed_annotations),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
        },
        "ambiguity_notes": concept.disambiguation_notes,
    }


def filter_graph_edges(
    bundle: CorpusAppBundle,
    *,
    include_structural: bool = False,
    include_candidate: bool = False,
    relation_types: set[str] | None = None,
    node_types: set[str] | None = None,
    question_id: str | None = None,
    center_concept: str | None = None,
) -> list[dict[str, Any]]:
    """Filter graph rows with explicit layer separation."""

    edges = list(bundle.reviewed_doctrinal_edges)
    if include_structural:
        edges.extend(generate_structural_edges(bundle, question_id=question_id))
        edges.extend(bundle.reviewed_structural_edges)
    if include_candidate:
        edges.extend(
            candidate_relation_rows(bundle, question_id=question_id, center_concept=center_concept)
        )

    filtered: list[dict[str, Any]] = []
    for edge in edges:
        if relation_types and edge["relation_type"] not in relation_types:
            continue
        if node_types and (
            edge["subject_type"] not in node_types or edge["object_type"] not in node_types
        ):
            continue
        if question_id and not edge_touches_question(bundle, edge, question_id):
            continue
        if center_concept and center_concept not in {edge["subject_id"], edge["object_id"]}:
            continue
        filtered.append(edge)
    filtered.sort(key=lambda row: (row["layer"], row["edge_id"]))
    return filtered


def build_graph_for_edges(edges: list[dict[str, Any]]) -> nx.MultiDiGraph:
    """Build a graph from generic app edge rows."""

    graph = nx.MultiDiGraph()
    for edge in edges:
        for side in ("subject", "object"):
            node_id = edge[f"{side}_id"]
            if node_id not in graph:
                graph.add_node(
                    node_id,
                    label=edge[f"{side}_label"],
                    node_type=edge[f"{side}_type"],
                )
        graph.add_edge(
            edge["subject_id"],
            edge["object_id"],
            key=edge["edge_id"],
            **edge,
        )
    return graph


def graph_html(graph: nx.MultiDiGraph, *, height: int = 760) -> str:
    """Render a readable graph with explicit layer coloring."""

    from pyvis.network import Network

    network = Network(
        height=f"{height}px",
        width="100%",
        directed=True,
        bgcolor="#faf5ec",
        font_color="#13273f",
    )
    for node_id, attrs in graph.nodes(data=True):
        node_label = str(attrs.get("label", node_id))
        node_type = str(attrs.get("node_type", ""))
        network.add_node(
            node_id,
            label=node_label,
            color=NODE_COLORS.get(node_type, "#6c757d"),
            title=(
                f"<b>{html_lib.escape(node_label)}</b><br>"
                f"Type: {html_lib.escape(node_type or 'unknown')}<br>"
                f"Id: {html_lib.escape(str(node_id))}"
            ),
        )
    for source, target, edge_id, attrs in graph.edges(data=True, keys=True):
        support_types = attrs.get("support_types", [])
        support_label = (
            ", ".join(str(value) for value in support_types)
            if isinstance(support_types, list)
            else str(support_types or "n/a")
        )
        annotation_count = len(attrs.get("support_annotation_ids", []) or [])
        passage_count = len(attrs.get("source_passage_ids", []) or [])
        network.add_edge(
            source,
            target,
            label=str(attrs.get("relation_type", "")),
            title=(
                f"<b>{html_lib.escape(str(attrs.get('subject_label', source)))}</b> → "
                f"<b>{html_lib.escape(str(attrs.get('object_label', target)))}</b><br>"
                f"Relation: {html_lib.escape(str(attrs.get('relation_type', '')))}<br>"
                f"Layer: {html_lib.escape(str(attrs.get('layer', '')))}<br>"
                f"Support: {html_lib.escape(support_label)}<br>"
                f"Annotations: {annotation_count}<br>"
                f"Passages: {passage_count}<br>"
                f"Edge id: {html_lib.escape(str(edge_id))}"
            ),
            color=EDGE_COLORS.get(str(attrs.get("layer", "")), "#6c757d"),
            arrows="to",
            dashes=str(attrs.get("layer")) == "candidate",
        )
    network.set_options(
        """
        var options = {
          "interaction": {
            "hover": true,
            "tooltipDelay": 140,
            "hoverConnectedEdges": true,
            "selectConnectedEdges": true,
            "navigationButtons": true,
            "multiselect": true,
            "hideEdgesOnDrag": true,
            "keyboard": false
          },
          "nodes": {
            "shape": "dot",
            "size": 18,
            "font": {
              "face": "Public Sans",
              "size": 16,
              "color": "#13273f"
            },
            "borderWidth": 1.5,
            "shadow": {
              "enabled": true,
              "color": "rgba(33, 44, 55, 0.12)",
              "size": 12,
              "x": 0,
              "y": 8
            }
          },
          "edges": {
            "smooth": {
              "type": "dynamic"
            },
            "font": {
              "face": "Public Sans",
              "size": 12,
              "color": "#46566b",
              "strokeWidth": 5,
              "strokeColor": "#faf5ec"
            },
            "width": 1.6,
            "selectionWidth": 2.4,
            "hoverWidth": 1.1
          },
          "physics": {
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
              "gravitationalConstant": -38,
              "centralGravity": 0.02,
              "springLength": 185,
              "springConstant": 0.08
            },
            "stabilization": {
              "enabled": true,
              "iterations": 140
            }
          }
        }
        """
    )
    html = str(network.generate_html(notebook=False))
    wrapped_body = (
        '<body style="margin:0;background:#faf5ec;'
        "font-family:'Public Sans',sans-serif;\">"
        '<div style="height:100%;padding:14px;border-radius:22px;'
        "background:linear-gradient(180deg, rgba(255,251,245,0.95), "
        'rgba(246,239,227,0.92));">'
    )
    return html.replace(
        "<body>",
        wrapped_body,
        1,
    ).replace("</body>", "</div></body>", 1)


def stats_payload(bundle: CorpusAppBundle) -> dict[str, Any]:
    """Compute corpus-wide structural, reviewed, and candidate stats."""

    concept_type_counts = Counter(record.node_type for record in bundle.registry.values())
    relation_type_counts = Counter(
        edge["relation_type"] for edge in bundle.reviewed_doctrinal_edges
    )
    candidate_relation_counts = Counter(
        record.relation_type for record in bundle.candidate_relations
    )
    top_under_reviewed = bundle.coverage["under_reviewed_question_clusters"][:10]
    return {
        "summary": bundle.coverage["summary"],
        "concept_type_counts": dict(sorted(concept_type_counts.items())),
        "reviewed_relation_type_counts": dict(sorted(relation_type_counts.items())),
        "candidate_relation_type_counts": dict(sorted(candidate_relation_counts.items())),
        "top_under_reviewed_clusters": top_under_reviewed,
        "parse_warnings_grouped_by_type": bundle.coverage["parse_warnings_grouped_by_type"],
        "ambiguity_count": bundle.coverage["summary"]["ambiguity_count"],
    }


def graph_legends() -> dict[str, dict[str, str]]:
    return {"node_colors": NODE_COLORS, "edge_colors": EDGE_COLORS}


def load_reviewed_annotations(base: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for filename in (
        "pilot_reviewed_doctrinal_annotations.jsonl",
        "pilot_reviewed_structural_annotations.jsonl",
        "prudence_reviewed_doctrinal_annotations.jsonl",
        "prudence_reviewed_structural_editorial_annotations.jsonl",
        "connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl",
        "connected_virtues_109_120_reviewed_structural_editorial_annotations.jsonl",
        "fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl",
        "fortitude_closure_136_140_reviewed_structural_editorial_annotations.jsonl",
        "fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl",
        "fortitude_parts_129_135_reviewed_structural_editorial_annotations.jsonl",
        "theological_virtues_reviewed_doctrinal_annotations.jsonl",
        "theological_virtues_reviewed_structural_editorial_annotations.jsonl",
        "justice_core_reviewed_doctrinal_annotations.jsonl",
        "justice_core_reviewed_structural_editorial_annotations.jsonl",
        "owed_relation_tract_reviewed_doctrinal_annotations.jsonl",
        "owed_relation_tract_reviewed_structural_editorial_annotations.jsonl",
        "religion_tract_reviewed_doctrinal_annotations.jsonl",
        "religion_tract_reviewed_structural_editorial_annotations.jsonl",
        "temperance_141_160_reviewed_doctrinal_annotations.jsonl",
        "temperance_141_160_reviewed_structural_editorial_annotations.jsonl",
        "temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl",
        "temperance_closure_161_170_reviewed_structural_editorial_annotations.jsonl",
    ):
        path = base / "data" / "gold" / filename
        if not path.exists():
            continue
        for payload in load_jsonl(path):
            rows.append({**payload, "source_layer": filename.replace(".jsonl", "")})
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[str(row["annotation_id"])] = row
    return list(sorted(deduped.values(), key=lambda item: str(item["annotation_id"])))


def load_reviewed_doctrinal_edges(base: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for filename in (
        "pilot_doctrinal_edges.jsonl",
        "prudence_reviewed_doctrinal_edges.jsonl",
        "connected_virtues_109_120_reviewed_doctrinal_edges.jsonl",
        "fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl",
        "fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl",
        "theological_virtues_reviewed_doctrinal_edges.jsonl",
        "justice_core_reviewed_doctrinal_edges.jsonl",
        "owed_relation_tract_reviewed_doctrinal_edges.jsonl",
        "religion_tract_reviewed_doctrinal_edges.jsonl",
        "temperance_141_160_reviewed_doctrinal_edges.jsonl",
        "temperance_closure_161_170_reviewed_doctrinal_edges.jsonl",
    ):
        path = base / "data" / "processed" / filename
        if not path.exists():
            continue
        for payload in load_jsonl(path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_doctrinal",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    return merge_edge_rows(rows)


def load_reviewed_structural_edges(base: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pilot_path = base / "data" / "processed" / "pilot_structural_edges.jsonl"
    if pilot_path.exists():
        for payload in load_jsonl(pilot_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    prudence_path = (
        base / "data" / "processed" / "prudence_reviewed_structural_editorial_edges.jsonl"
    )
    if prudence_path.exists():
        for payload in load_jsonl(prudence_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    connected_path = (
        base
        / "data"
        / "processed"
        / "connected_virtues_109_120_reviewed_structural_editorial_edges.jsonl"
    )
    if connected_path.exists():
        for payload in load_jsonl(connected_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    fortitude_closure_path = (
        base
        / "data"
        / "processed"
        / "fortitude_closure_136_140_reviewed_structural_editorial_edges.jsonl"
    )
    if fortitude_closure_path.exists():
        for payload in load_jsonl(fortitude_closure_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    fortitude_path = (
        base
        / "data"
        / "processed"
        / "fortitude_parts_129_135_reviewed_structural_editorial_edges.jsonl"
    )
    if fortitude_path.exists():
        for payload in load_jsonl(fortitude_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    theological_path = (
        base
        / "data"
        / "processed"
        / "theological_virtues_reviewed_structural_editorial_edges.jsonl"
    )
    if theological_path.exists():
        for payload in load_jsonl(theological_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    justice_path = (
        base / "data" / "processed" / "justice_core_reviewed_structural_editorial_edges.jsonl"
    )
    if justice_path.exists():
        for payload in load_jsonl(justice_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    religion_path = (
        base / "data" / "processed" / "religion_tract_reviewed_structural_editorial_edges.jsonl"
    )
    if religion_path.exists():
        for payload in load_jsonl(religion_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    owed_path = (
        base
        / "data"
        / "processed"
        / "owed_relation_tract_reviewed_structural_editorial_edges.jsonl"
    )
    if owed_path.exists():
        for payload in load_jsonl(owed_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    temperance_path = (
        base / "data" / "processed" / "temperance_141_160_reviewed_structural_editorial_edges.jsonl"
    )
    if temperance_path.exists():
        for payload in load_jsonl(temperance_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    temperance_closure_path = (
        base
        / "data"
        / "processed"
        / "temperance_closure_161_170_reviewed_structural_editorial_edges.jsonl"
    )
    if temperance_closure_path.exists():
        for payload in load_jsonl(temperance_closure_path):
            rows.append(
                {
                    **payload,
                    "layer": "reviewed_structural",
                    "edge_id": str(payload["edge_id"]),
                }
            )
    return merge_edge_rows(rows)


def merge_edge_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row["layer"]), str(row["edge_id"]))
        if key not in merged:
            merged[key] = row
            continue
        existing = merged[key]
        for field in (
            "support_annotation_ids",
            "source_passage_ids",
            "support_types",
            "evidence_snippets",
        ):
            existing_values = list(existing.get(field, []))
            for value in row.get(field, []):
                if value not in existing_values:
                    existing_values.append(value)
            existing[field] = existing_values
    return list(
        sorted(
            merged.values(),
            key=lambda item: (str(item["layer"]), str(item["edge_id"])),
        )
    )


def generate_structural_edges(
    bundle: CorpusAppBundle,
    *,
    question_id: str | None,
) -> list[dict[str, Any]]:
    """Generate full-corpus question->article structural rows on demand."""

    edges: list[dict[str, Any]] = []
    for article in bundle.coverage["articles"]:
        if question_id and article["question_id"] != question_id:
            continue
        question = bundle.questions[article["question_id"]]
        edge_id = f"structural.{question.question_id}.contains.{article['article_id']}"
        edges.append(
            {
                "edge_id": edge_id,
                "layer": "structural",
                "subject_id": question.question_id,
                "subject_label": f"{question.part_id.upper()} q.{question.question_number}",
                "subject_type": "question",
                "relation_type": "contains_article",
                "object_id": article["article_id"],
                "object_label": article["citation_label"],
                "object_type": "article",
                "source_passage_ids": [],
                "evidence_snippets": [],
            }
        )
    return edges


def candidate_relation_rows(
    bundle: CorpusAppBundle,
    *,
    question_id: str | None,
    center_concept: str | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in bundle.candidate_relations:
        if question_id and bundle.passages[record.source_passage_id].question_id != question_id:
            continue
        if center_concept and center_concept not in {record.subject_id, record.object_id}:
            continue
        rows.append(
            {
                **record.model_dump(mode="json"),
                "layer": "candidate",
                "edge_id": record.proposal_id,
                "source_passage_ids": [record.source_passage_id],
                "evidence_snippets": [record.evidence_text],
            }
        )
    return rows


def edge_touches_question(bundle: CorpusAppBundle, edge: dict[str, Any], question_id: str) -> bool:
    passage_ids = edge.get("source_passage_ids", [])
    if any(
        passage_id in bundle.passages and bundle.passages[passage_id].question_id == question_id
        for passage_id in passage_ids
    ):
        return True
    return bool(str(edge["subject_id"]) == question_id or str(edge["object_id"]) == question_id)


def supporting_passages_for_concepts(
    bundle: CorpusAppBundle,
    concept_ids: set[str],
) -> set[str]:
    if not concept_ids:
        return set()
    supporting_passage_ids = {
        row["source_passage_id"]
        for row in bundle.reviewed_annotations
        if row["subject_id"] in concept_ids or row["object_id"] in concept_ids
    }
    for mention in bundle.candidate_mentions:
        if mention.proposed_concept_id in concept_ids:
            supporting_passage_ids.add(mention.passage_id)
        elif concept_ids.intersection(mention.proposed_concept_ids):
            supporting_passage_ids.add(mention.passage_id)
    return supporting_passage_ids


def top_supporting_passages(bundle: CorpusAppBundle, concept_id: str) -> list[str]:
    seen: list[str] = []
    for row in bundle.reviewed_annotations:
        if row["subject_id"] == concept_id or row["object_id"] == concept_id:
            passage_id = str(row["source_passage_id"])
            if passage_id not in seen:
                seen.append(passage_id)
    for mention in bundle.candidate_mentions:
        if mention.proposed_concept_id == concept_id or concept_id in mention.proposed_concept_ids:
            if mention.passage_id not in seen:
                seen.append(mention.passage_id)
    return seen[:12]
