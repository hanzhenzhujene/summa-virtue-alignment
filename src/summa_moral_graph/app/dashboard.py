from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, TypedDict, cast

from .corpus import load_corpus_bundle, stats_payload


class DashboardTractSpec(TypedDict):
    slug: str
    label: str
    range_label: str
    coverage_file: str
    validation_file: str
    review_queue_file: str | None
    review_packet_glob: str | None
    start_question: int
    end_question: int


class DashboardTractRow(TypedDict):
    slug: str
    label: str
    range_label: str
    start_question: int
    end_question: int
    validation_status: str
    question_count: int
    passage_count: int
    reviewed_annotations: int
    reviewed_doctrinal_edges: int
    reviewed_structural_editorial: int
    candidate_mentions: int
    candidate_relation_proposals: int
    under_annotated_questions: list[int]
    normalization_risk_questions: list[int]
    normalization_risk_count: int
    review_packet_question: int | None
    review_packet_path: str | None
    review_queue_path: str | None
    highlights: list[str]
    annotation_density: float


class DashboardSynthesisSpec(TypedDict):
    slug: str
    label: str
    range_label: str
    nodes_file: str
    edges_file: str
    graphml_file: str
    editorial_graphml_file: str | None


class DashboardSynthesisRow(TypedDict):
    slug: str
    label: str
    range_label: str
    nodes: int
    edges: int
    graphml_path: str
    editorial_graphml_path: str | None


DASHBOARD_TRACTS: list[DashboardTractSpec] = [
    {
        "slug": "theological_virtues",
        "label": "Theological Virtues",
        "range_label": "II-II qq. 1-46",
        "coverage_file": "theological_virtues_coverage.json",
        "validation_file": "theological_virtues_validation_report.json",
        "review_queue_file": "theological_virtues_review_queue.json",
        "review_packet_glob": "st_ii-ii_q*_theological_virtues_review_packet.md",
        "start_question": 1,
        "end_question": 46,
    },
    {
        "slug": "prudence",
        "label": "Prudence",
        "range_label": "II-II qq. 47-56",
        "coverage_file": "prudence_coverage.json",
        "validation_file": "prudence_validation_report.json",
        "review_queue_file": "prudence_review_queue.json",
        "review_packet_glob": "prudence_q*_review_packet.md",
        "start_question": 47,
        "end_question": 56,
    },
    {
        "slug": "justice_core",
        "label": "Justice Core",
        "range_label": "II-II qq. 57-79",
        "coverage_file": "justice_core_coverage.json",
        "validation_file": "justice_core_validation_report.json",
        "review_queue_file": "justice_core_review_queue.json",
        "review_packet_glob": None,
        "start_question": 57,
        "end_question": 79,
    },
    {
        "slug": "religion_tract",
        "label": "Religion Tract",
        "range_label": "II-II qq. 80-100",
        "coverage_file": "religion_tract_coverage.json",
        "validation_file": "religion_tract_validation_report.json",
        "review_queue_file": "religion_tract_review_queue.json",
        "review_packet_glob": "st_ii-ii_q*_religion_tract_review_packet.md",
        "start_question": 80,
        "end_question": 100,
    },
    {
        "slug": "owed_relation_tract",
        "label": "Owed-Relation Tract",
        "range_label": "II-II qq. 101-108",
        "coverage_file": "owed_relation_tract_coverage.json",
        "validation_file": "owed_relation_tract_validation_report.json",
        "review_queue_file": "owed_relation_tract_review_queue.json",
        "review_packet_glob": None,
        "start_question": 101,
        "end_question": 108,
    },
    {
        "slug": "connected_virtues_109_120",
        "label": "Connected Virtues",
        "range_label": "II-II qq. 109-120",
        "coverage_file": "connected_virtues_109_120_coverage.json",
        "validation_file": "connected_virtues_109_120_validation_report.json",
        "review_queue_file": "connected_virtues_109_120_review_queue.json",
        "review_packet_glob": None,
        "start_question": 109,
        "end_question": 120,
    },
    {
        "slug": "fortitude_parts_129_135",
        "label": "Fortitude Parts",
        "range_label": "II-II qq. 129-135",
        "coverage_file": "fortitude_parts_129_135_coverage.json",
        "validation_file": "fortitude_parts_129_135_validation_report.json",
        "review_queue_file": "fortitude_parts_129_135_review_queue.json",
        "review_packet_glob": None,
        "start_question": 129,
        "end_question": 135,
    },
    {
        "slug": "fortitude_closure_136_140",
        "label": "Fortitude Closure",
        "range_label": "II-II qq. 136-140",
        "coverage_file": "fortitude_closure_136_140_coverage.json",
        "validation_file": "fortitude_closure_136_140_validation_report.json",
        "review_queue_file": "fortitude_closure_136_140_review_queue.json",
        "review_packet_glob": None,
        "start_question": 136,
        "end_question": 140,
    },
    {
        "slug": "temperance_141_160",
        "label": "Temperance Phase 1",
        "range_label": "II-II qq. 141-160",
        "coverage_file": "temperance_141_160_coverage.json",
        "validation_file": "temperance_141_160_validation_report.json",
        "review_queue_file": "temperance_141_160_review_queue.json",
        "review_packet_glob": "st_ii-ii_q*_temperance_141_160_review_packet.md",
        "start_question": 141,
        "end_question": 160,
    },
    {
        "slug": "temperance_closure_161_170",
        "label": "Temperance Closure",
        "range_label": "II-II qq. 161-170",
        "coverage_file": "temperance_closure_161_170_coverage.json",
        "validation_file": "temperance_closure_161_170_validation_report.json",
        "review_queue_file": "temperance_closure_161_170_review_queue.json",
        "review_packet_glob": "st_ii-ii_q*_temperance_closure_161_170_review_packet.md",
        "start_question": 161,
        "end_question": 170,
    },
]


DASHBOARD_SYNTHESES: list[DashboardSynthesisSpec] = [
    {
        "slug": "fortitude_tract",
        "label": "Fortitude Tract Synthesis",
        "range_label": "II-II qq. 123-140",
        "nodes_file": "fortitude_tract_synthesis_nodes.csv",
        "edges_file": "fortitude_tract_synthesis_edges.csv",
        "graphml_file": "fortitude_tract_synthesis.graphml",
        "editorial_graphml_file": "fortitude_tract_synthesis_with_editorial.graphml",
    },
    {
        "slug": "temperance_phase1",
        "label": "Temperance Phase 1 Synthesis",
        "range_label": "II-II qq. 141-160",
        "nodes_file": "temperance_phase1_synthesis_nodes.csv",
        "edges_file": "temperance_phase1_synthesis_edges.csv",
        "graphml_file": "temperance_phase1_synthesis.graphml",
        "editorial_graphml_file": "temperance_phase1_synthesis_with_editorial.graphml",
    },
    {
        "slug": "temperance_full",
        "label": "Temperance Full Synthesis",
        "range_label": "II-II qq. 141-170",
        "nodes_file": "temperance_full_synthesis_nodes.csv",
        "edges_file": "temperance_full_synthesis_edges.csv",
        "graphml_file": "temperance_full_synthesis.graphml",
        "editorial_graphml_file": "temperance_full_synthesis_with_editorial.graphml",
    },
]


def load_dashboard_payload(root: Path | None = None) -> dict[str, Any]:
    base = root or Path(__file__).resolve().parents[3]
    bundle = load_corpus_bundle(base)
    corpus_stats = stats_payload(bundle)

    tract_rows = [build_tract_row(base, spec) for spec in DASHBOARD_TRACTS]
    tract_rows.sort(key=lambda row: (row["start_question"], row["end_question"]))

    synthesis_rows = [
        build_synthesis_row(base, spec)
        for spec in DASHBOARD_SYNTHESES
        if (base / "data" / "processed" / spec["nodes_file"]).exists()
        and (base / "data" / "processed" / spec["edges_file"]).exists()
    ]
    review_priority_rows = build_review_priority_rows(tract_rows)

    return {
        "summary": {
            **corpus_stats["summary"],
            "reviewed_tract_blocks": len(tract_rows),
            "ok_validation_blocks": sum(
                1 for row in tract_rows if row["validation_status"] == "ok"
            ),
            "synthesis_exports": len(synthesis_rows),
        },
        "scope": {
            "included": ["I-II qq. 1-114", "II-II qq. 1-182"],
            "excluded": ["II-II qq. 183-189", "Part I", "Part III", "Supplement"],
        },
        "layer_discipline": [
            "Reviewed doctrinal edges remain separate from structural/editorial edges.",
            "Candidate mentions and candidate relation proposals are never shown "
            "as reviewed facts by default.",
            "Every non-hierarchical reviewed relation remains traceable to segment-level evidence.",
        ],
        "top_under_reviewed_clusters": corpus_stats["top_under_reviewed_clusters"],
        "tract_rows": tract_rows,
        "review_priority_rows": review_priority_rows,
        "synthesis_rows": synthesis_rows,
    }


def build_tract_row(base: Path, spec: DashboardTractSpec) -> DashboardTractRow:
    coverage = _load_json(base / "data" / "processed" / spec["coverage_file"])
    validation = _load_json(base / "data" / "processed" / spec["validation_file"])
    summary = cast(dict[str, Any], coverage.get("summary", {}))
    questions = cast(list[dict[str, Any]], coverage.get("questions", []))

    question_count = _safe_int(
        summary.get("question_count"),
        fallback=len(questions),
    )
    passage_count = _safe_int(
        summary.get("passage_count"),
        fallback=sum(_safe_int(row.get("passage_count"), fallback=0) for row in questions),
    )
    reviewed_annotations = _safe_int(
        summary.get("reviewed_annotation_count"),
        fallback=_safe_int(validation.get("reviewed_annotation_count"), fallback=0),
    )
    reviewed_doctrinal_edges = _safe_int(
        summary.get("reviewed_doctrinal_edge_count"),
        fallback=_safe_int(validation.get("reviewed_doctrinal_edge_count"), fallback=0),
    )
    reviewed_structural_editorial = _safe_int(
        summary.get("reviewed_structural_editorial_count"),
        fallback=_safe_int(validation.get("reviewed_structural_editorial_count"), fallback=0),
    )
    candidate_mentions = _safe_int(
        summary.get("candidate_mention_count"),
        fallback=_safe_int(validation.get("candidate_mention_count"), fallback=0),
    )
    candidate_relations = _safe_int(
        summary.get("candidate_relation_count"),
        fallback=_safe_int(validation.get("candidate_relation_count"), fallback=0),
    )

    under_annotated_questions = sorted(
        _coerce_question_numbers(cast(list[Any], coverage.get("under_annotated_questions", [])))
    )
    normalization_risk_questions = sorted(
        _coerce_question_numbers(
            cast(list[Any], coverage.get("normalization_risk_questions", []))
        )
    )
    review_packet_path = (
        find_review_packet(base, spec["review_packet_glob"]) if spec["review_packet_glob"] else None
    )
    review_packet_question = (
        extract_question_number_from_path(review_packet_path) if review_packet_path else None
    )
    review_queue_path = (
        str(base / "data" / "processed" / spec["review_queue_file"])
        if spec["review_queue_file"]
        and (base / "data" / "processed" / spec["review_queue_file"]).exists()
        else None
    )

    return {
        "slug": spec["slug"],
        "label": spec["label"],
        "range_label": spec["range_label"],
        "start_question": spec["start_question"],
        "end_question": spec["end_question"],
        "validation_status": str(validation.get("status", "unknown")),
        "question_count": question_count,
        "passage_count": passage_count,
        "reviewed_annotations": reviewed_annotations,
        "reviewed_doctrinal_edges": reviewed_doctrinal_edges,
        "reviewed_structural_editorial": reviewed_structural_editorial,
        "candidate_mentions": candidate_mentions,
        "candidate_relation_proposals": candidate_relations,
        "under_annotated_questions": under_annotated_questions,
        "normalization_risk_questions": normalization_risk_questions,
        "normalization_risk_count": len(normalization_risk_questions),
        "review_packet_question": review_packet_question,
        "review_packet_path": review_packet_path,
        "review_queue_path": review_queue_path,
        "highlights": summarize_relation_highlights(summary),
        "annotation_density": round(
            reviewed_annotations / passage_count,
            3,
        )
        if passage_count
        else 0.0,
    }


def build_review_priority_rows(
    tract_rows: list[DashboardTractRow],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in tract_rows:
        if not row["under_annotated_questions"] and not row["review_packet_question"]:
            continue
        rows.append(
            {
                "tract": row["label"],
                "range": row["range_label"],
                "validation_status": row["validation_status"],
                "packet_target_question": row["review_packet_question"],
                "under_annotated_questions": row["under_annotated_questions"],
                "normalization_risk_count": row["normalization_risk_count"],
                "review_queue_path": row["review_queue_path"],
            }
        )
    return rows


def build_synthesis_row(base: Path, spec: DashboardSynthesisSpec) -> DashboardSynthesisRow:
    processed = base / "data" / "processed"
    return {
        "slug": spec["slug"],
        "label": spec["label"],
        "range_label": spec["range_label"],
        "nodes": count_csv_rows(processed / spec["nodes_file"]),
        "edges": count_csv_rows(processed / spec["edges_file"]),
        "graphml_path": str(processed / spec["graphml_file"]),
        "editorial_graphml_path": (
            str(processed / spec["editorial_graphml_file"])
            if spec["editorial_graphml_file"]
            and (processed / spec["editorial_graphml_file"]).exists()
            else None
        ),
    }


def count_csv_rows(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as handle:
        return len(list(csv.DictReader(handle)))


def summarize_relation_highlights(summary: dict[str, Any]) -> list[str]:
    highlights: list[str] = []
    excluded_keys = {"candidate_relation_count"}
    for key, value in sorted(summary.items()):
        if not key.endswith("_relation_count"):
            continue
        if key in excluded_keys:
            continue
        count = _safe_int(value, fallback=0)
        if count <= 0:
            continue
        label = key.removesuffix("_count").replace("_", " ")
        highlights.append(f"{label}: {count}")
    return highlights[:4]


def find_review_packet(base: Path, pattern: str) -> str | None:
    packets_dir = base / "data" / "processed" / "review_packets"
    matches = sorted(packets_dir.glob(pattern))
    if not matches:
        return None
    return str(matches[-1])


def extract_question_number_from_path(path: str) -> int | None:
    match = re.search(r"q(\d{3})", path)
    if match is None:
        return None
    return int(match.group(1))


def _coerce_question_numbers(values: list[Any]) -> list[int]:
    question_numbers: list[int] = []
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            question_numbers.append(value)
            continue
        if isinstance(value, str) and value.isdigit():
            question_numbers.append(int(value))
    return question_numbers


def _safe_int(value: Any, *, fallback: int) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return fallback


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return cast(dict[str, Any], payload)
