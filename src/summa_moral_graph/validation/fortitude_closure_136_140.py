from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.fortitude_closure_136_140_spec import (
    FORTITUDE_CLOSURE_136_140_MAX_QUESTION,
    FORTITUDE_CLOSURE_136_140_MIN_QUESTION,
    FORTITUDE_CLOSURE_RELATION_TYPES,
    GIFT_RELATION_TYPES,
    PATIENCE_CONCEPT_IDS,
    PATIENCE_RELATION_TYPES,
    PERSEVERANCE_CONCEPT_IDS,
    PERSEVERANCE_RELATION_TYPES,
    PRECEPT_RELATION_TYPES,
)
from ..models import (
    ArticleRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    FortitudeClosure136140CoverageQuestionRecord,
    FortitudeClosure136140EdgeRecord,
    FortitudeClosure136140ValidationReport,
    PilotAnnotationRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_fortitude_closure_136_140_reports() -> dict[str, int | str]:
    """Build coverage and validation outputs for II-II QQ. 136-140."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and FORTITUDE_CLOSURE_136_140_MIN_QUESTION
        <= record.question_number
        <= FORTITUDE_CLOSURE_136_140_MAX_QUESTION
    }
    articles = {
        record.article_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_articles.jsonl", ArticleRecord)
        if record.question_id in questions
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
        if record.article_id in articles
    }

    doctrinal_annotations = _load_records(
        GOLD_DIR / "fortitude_closure_136_140_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "fortitude_closure_136_140_reviewed_structural_editorial_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_doctrinal_edges.jsonl",
        FortitudeClosure136140EdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "fortitude_closure_136_140_reviewed_structural_editorial_edges.jsonl",
        FortitudeClosure136140EdgeRecord,
    )
    candidate_mentions = [
        record
        for record in _load_records(
            CANDIDATE_DIR / "corpus_candidate_mentions.jsonl",
            CorpusCandidateMentionRecord,
        )
        if record.passage_id in passages
    ]
    candidate_relations = [
        record
        for record in _load_records(
            CANDIDATE_DIR / "corpus_candidate_relation_proposals.jsonl",
            CorpusCandidateRelationProposalRecord,
        )
        if record.source_passage_id in passages
    ]
    concepts = load_tract_concepts(doctrinal_annotations + structural_editorial_annotations)
    synthesis_summary = load_fortitude_synthesis_summary()

    coverage = build_fortitude_closure_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_fortitude_closure_artifacts(
        concepts=concepts,
        questions=questions,
        articles=articles,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        structural_editorial_edges=structural_editorial_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
        coverage=coverage,
        synthesis_summary=synthesis_summary,
    )

    prior_fortitude_parts_coverage = load_optional_json(
        PROCESSED_DIR / "fortitude_parts_129_135_coverage.json"
    )
    prior_summary = prior_fortitude_parts_coverage.get("summary", {})
    concepts_linked_to_gift = sorted(
        {
            edge.subject_id
            for edge in doctrinal_edges
            if "gift" in edge.fortitude_closure_focus and edge.subject_id.startswith("concept.")
        }
        | {
            edge.object_id
            for edge in doctrinal_edges
            if "gift" in edge.fortitude_closure_focus and edge.object_id.startswith("concept.")
        }
    )
    concepts_linked_to_precepts = sorted(
        {
            edge.subject_id
            for edge in doctrinal_edges
            if "precept" in edge.fortitude_closure_focus and edge.subject_id.startswith("concept.")
        }
        | {
            edge.object_id
            for edge in doctrinal_edges
            if "precept" in edge.fortitude_closure_focus and edge.object_id.startswith("concept.")
        }
    )
    unresolved_hotspots = sorted(
        set(prior_fortitude_parts_coverage.get("normalization_risk_questions", []))
        | {
            record.question_number
            for record in coverage
            if record.unresolved_ambiguity_count > 0
        }
    )

    coverage_payload = {
        "summary": {
            "question_count": len(coverage),
            "passage_count": len(passages),
            "registered_concepts_used": len(concepts),
            "reviewed_annotation_count": len(doctrinal_annotations)
            + len(structural_editorial_annotations),
            "reviewed_doctrinal_edge_count": len(doctrinal_edges),
            "reviewed_structural_editorial_count": len(structural_editorial_annotations),
            "candidate_mention_count": len(candidate_mentions),
            "candidate_relation_count": len(candidate_relations),
            "patience_relation_count": count_focus(doctrinal_edges, "patience"),
            "perseverance_relation_count": count_focus(doctrinal_edges, "perseverance"),
            "opposed_vice_relation_count": count_focus(doctrinal_edges, "opposed_vice"),
            "gift_linkage_relation_count": count_focus(doctrinal_edges, "gift"),
            "precept_linkage_relation_count": count_focus(doctrinal_edges, "precept"),
            "fortitude_synthesis_node_count": synthesis_summary["nodes"],
            "fortitude_synthesis_edge_count": synthesis_summary["edges"],
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
        "fortitude_tract_summary": {
            "reviewed_annotations_total": int(prior_summary.get("reviewed_annotation_count", 0))
            + len(doctrinal_annotations)
            + len(structural_editorial_annotations),
            "reviewed_doctrinal_edges_total": int(
                prior_summary.get("reviewed_doctrinal_edge_count", 0)
            )
            + len(doctrinal_edges),
            "fortitude_subtracts_covered": 2,
            "concepts_linked_to_gift_of_fortitude": len(concepts_linked_to_gift),
            "concepts_linked_to_precepts_of_fortitude": len(concepts_linked_to_precepts),
            "unresolved_normalization_hotspots": unresolved_hotspots,
            "notes": [
                (
                    "The repository currently has reviewed fortitude material for "
                    "qq.129-135 and qq.136-140."
                ),
                (
                    "No dedicated reviewed doctrinal fortitude-core block for qq.123-128 "
                    "exists yet, so the synthesis layer remains structurally scoped to "
                    "qq.123-140 but doctrinally populated only where reviewed fortitude "
                    "exports exist."
                ),
            ],
        },
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "fortitude_closure_136_140_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "fortitude_closure_136_140_validation_report.json").write_text(
        json.dumps(
            validation.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    write_coverage_markdown(
        coverage_payload,
        REPO_ROOT / "docs" / "fortitude_closure_136_140_coverage.md",
    )
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "fortitude_closure_136_140_validation.md",
    )
    write_synthesis_markdown(
        coverage_payload,
        synthesis_summary,
        REPO_ROOT / "docs" / "fortitude_tract_synthesis.md",
    )
    return {
        "status": validation.status,
        "questions": len(coverage),
        "passages": len(passages),
        "reviewed_annotations": len(doctrinal_annotations) + len(structural_editorial_annotations),
        "reviewed_doctrinal_edges": len(doctrinal_edges),
        "reviewed_structural_editorial": len(structural_editorial_annotations),
        "candidate_mentions": len(candidate_mentions),
        "candidate_relation_proposals": len(candidate_relations),
    }


def load_tract_concepts(
    annotations: list[PilotAnnotationRecord],
) -> dict[str, dict[str, object]]:
    registry = build_corpus_registry()
    for filename in (
        "fortitude_parts_129_135_reviewed_concepts.jsonl",
        "fortitude_closure_136_140_reviewed_concepts.jsonl",
    ):
        reviewed_path = GOLD_DIR / filename
        if reviewed_path.exists():
            for payload in load_jsonl(reviewed_path):
                concept = CorpusConceptRecord.model_validate(payload)
                registry[concept.concept_id] = concept
    concept_ids = {
        node_id
        for annotation in annotations
        for node_id in (annotation.subject_id, annotation.object_id)
        if node_id.startswith("concept.")
    }
    concept_ids.update(
        {
            "concept.patience",
            "concept.perseverance",
            "concept.perseverance_virtue",
            "concept.longanimity_fortitude",
            "concept.constancy_fortitude",
            "concept.fortitude",
            "concept.fortitude_gift",
        }
    )
    return {
        concept_id: registry[concept_id].model_dump(mode="json")
        for concept_id in sorted(concept_ids)
        if concept_id in registry
    }


def build_fortitude_closure_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[FortitudeClosure136140EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[FortitudeClosure136140CoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii"
        and FORTITUDE_CLOSURE_136_140_MIN_QUESTION
        <= int(row["question_number"])
        <= FORTITUDE_CLOSURE_136_140_MAX_QUESTION
    }
    passage_counts = Counter(passage.question_id for passage in passages.values())
    reviewed_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    doctrinal_edge_counts: Counter[str] = Counter()
    candidate_mention_counts: Counter[str] = Counter()
    candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    focus_usage: dict[str, Counter[str]] = defaultdict(Counter)
    schema_extension_usage: dict[str, Counter[str]] = defaultdict(Counter)
    question_by_passage = {
        passage_id: passage.question_id for passage_id, passage in passages.items()
    }

    for annotation in doctrinal_annotations:
        question_id = question_by_passage[annotation.source_passage_id]
        reviewed_counts[question_id] += 1
        if annotation.subject_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.subject_label)
        if annotation.object_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.object_label)

    for annotation in structural_editorial_annotations:
        question_id = question_by_passage[annotation.source_passage_id]
        structural_counts[question_id] += 1
        if annotation.object_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.object_label)

    for edge in doctrinal_edges:
        question_ids = {
            question_by_passage[passage_id]
            for passage_id in edge.source_passage_ids
            if passage_id in question_by_passage
        }
        for question_id in question_ids:
            doctrinal_edge_counts[question_id] += 1
            for tag in edge.fortitude_closure_focus:
                focus_usage[question_id][tag] += 1
            if edge.relation_type in FORTITUDE_CLOSURE_RELATION_TYPES:
                schema_extension_usage[question_id][edge.relation_type] += 1

    for mention in candidate_mentions:
        question_id = question_by_passage[mention.passage_id]
        candidate_mention_counts[question_id] += 1
        if mention.ambiguity_flag:
            ambiguity_counts[question_id] += 1

    for relation in candidate_relations:
        question_id = question_by_passage[relation.source_passage_id]
        candidate_relation_counts[question_id] += 1
        if relation.ambiguity_flag:
            ambiguity_counts[question_id] += 1

    rows: list[FortitudeClosure136140CoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda item: item.question_number):
        rows.append(
            FortitudeClosure136140CoverageQuestionRecord(
                question_id=question.question_id,
                question_number=question.question_number,
                question_title=question.question_title,
                parse_status=question_status[question.question_id],
                passage_count=passage_counts[question.question_id],
                reviewed_annotation_count=reviewed_counts[question.question_id],
                reviewed_doctrinal_edge_count=doctrinal_edge_counts[question.question_id],
                reviewed_structural_editorial_count=structural_counts[question.question_id],
                candidate_mention_count=candidate_mention_counts[question.question_id],
                candidate_relation_count=candidate_relation_counts[question.question_id],
                major_concepts=sorted(concepts_by_question[question.question_id]),
                unresolved_ambiguity_count=ambiguity_counts[question.question_id],
                focus_usage=dict(sorted(focus_usage[question.question_id].items())),
                schema_extension_usage=dict(
                    sorted(schema_extension_usage[question.question_id].items())
                ),
            )
        )
    return rows


def identify_under_annotated_questions(
    coverage: list[FortitudeClosure136140CoverageQuestionRecord],
) -> list[int]:
    ratios = {
        record.question_number: (
            record.reviewed_annotation_count / record.passage_count if record.passage_count else 0.0
        )
        for record in coverage
    }
    threshold = sorted(ratios.values())[max(0, len(ratios) // 3 - 1)]
    return [
        question_number for question_number, ratio in sorted(ratios.items()) if ratio <= threshold
    ]


def validate_fortitude_closure_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[FortitudeClosure136140EdgeRecord],
    structural_editorial_edges: list[FortitudeClosure136140EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[FortitudeClosure136140CoverageQuestionRecord],
    synthesis_summary: dict[str, int],
) -> FortitudeClosure136140ValidationReport:
    warnings: list[str] = []
    duplicate_flags: list[str] = []
    valid_node_ids = set(concepts) | set(questions) | set(articles)
    seen_review_keys: set[tuple[str, str, str, str, str]] = set()

    for annotation in doctrinal_annotations + structural_editorial_annotations:
        if annotation.subject_id not in valid_node_ids:
            warnings.append(f"Unknown annotation subject: {annotation.annotation_id}")
        if annotation.object_id not in valid_node_ids:
            warnings.append(f"Unknown annotation object: {annotation.annotation_id}")
        if annotation.source_passage_id not in passages:
            warnings.append(f"Unknown annotation passage: {annotation.annotation_id}")
            continue
        review_key = (
            annotation.source_passage_id,
            annotation.subject_id,
            annotation.relation_type,
            annotation.object_id,
            annotation.support_type,
        )
        if review_key in seen_review_keys:
            duplicate_flags.append(annotation.annotation_id)
        seen_review_keys.add(review_key)
        if not evidence_matches_passage(
            annotation.evidence_text,
            passages[annotation.source_passage_id].text,
        ):
            warnings.append(f"Evidence text mismatch: {annotation.annotation_id}")

    doctrinal_annotation_ids = {record.annotation_id for record in doctrinal_annotations}
    for edge in doctrinal_edges:
        if not set(edge.support_annotation_ids).issubset(doctrinal_annotation_ids):
            warnings.append(f"Doctrinal edge without reviewed support: {edge.edge_id}")
        if "structural_editorial" in edge.support_types:
            warnings.append(
                f"Default doctrinal edge includes structural_editorial support: {edge.edge_id}"
            )
        if "candidate." in edge.edge_id:
            warnings.append(f"Candidate identifier leaked into reviewed edge: {edge.edge_id}")
        if not edge.fortitude_closure_focus:
            warnings.append(f"Fortitude closure edge missing focus tags: {edge.edge_id}")
        if (
            edge.relation_type in PATIENCE_RELATION_TYPES
            and {edge.subject_id, edge.object_id}.intersection(PATIENCE_CONCEPT_IDS)
            and not ({"patience"} & set(edge.fortitude_closure_focus))
        ):
            warnings.append(f"Patience-sensitive edge missing patience tag: {edge.edge_id}")
        if (
            edge.relation_type in PERSEVERANCE_RELATION_TYPES
            and {edge.subject_id, edge.object_id}.intersection(PERSEVERANCE_CONCEPT_IDS)
            and not ({"perseverance"} & set(edge.fortitude_closure_focus))
        ):
            warnings.append(f"Perseverance-sensitive edge missing perseverance tag: {edge.edge_id}")
        if (
            edge.relation_type in GIFT_RELATION_TYPES
            and "gift" not in edge.fortitude_closure_focus
        ):
            warnings.append(f"Gift-sensitive edge missing gift tag: {edge.edge_id}")
        if (
            edge.relation_type in PRECEPT_RELATION_TYPES
            and "precept" not in edge.fortitude_closure_focus
        ):
            warnings.append(f"Precept-sensitive edge missing precept tag: {edge.edge_id}")

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Structural/editorial layer mismatch: {edge.edge_id}")

    if "concept.patience" not in concepts or "concept.perseverance_virtue" not in concepts:
        warnings.append("Patience and perseverance concepts must both be present")
    if "concept.fortitude" not in concepts or "concept.fortitude_gift" not in concepts:
        warnings.append("Virtue-fortitude and gift-fortitude concepts must both be present")
    if aliases_overlap(concepts, "concept.patience", "concept.perseverance_virtue"):
        warnings.append("Patience and perseverance alias sets overlap after normalization")
    if aliases_overlap(concepts, "concept.fortitude", "concept.fortitude_gift"):
        warnings.append(
            "Gift-fortitude and virtue-fortitude alias sets overlap after normalization"
        )
    if aliases_overlap(
        concepts,
        "concept.perseverance",
        "concept.perseverance_virtue",
    ):
        warnings.append(
            "Act-level and virtue-level perseverance alias sets overlap after normalization"
        )
    if "concept.longanimity_fortitude" in concepts and "concept.constancy_fortitude" in concepts:
        if aliases_overlap(
            concepts,
            "concept.longanimity_fortitude",
            "concept.constancy_fortitude",
        ):
            warnings.append("Longanimity and constancy alias sets overlap after normalization")

    precept_edges = [
        edge for edge in doctrinal_edges if "precept" in edge.fortitude_closure_focus
    ]
    for edge in precept_edges:
        if edge.subject_id not in {
            "concept.precepts_of_fortitude",
            "concept.precepts_of_fortitude_parts",
        }:
            warnings.append(f"Precept linkage has unexpected subject: {edge.edge_id}")

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention outside tract passages: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation outside tract passages: {relation.proposal_id}")

    coverage_question_ids = {record.question_id for record in coverage}
    if coverage_question_ids != set(questions):
        warnings.append("Coverage rows do not match tract question set")
    if synthesis_summary["nodes"] <= 0 or synthesis_summary["edges"] <= 0:
        warnings.append("Fortitude tract synthesis exports are missing or empty")

    return FortitudeClosure136140ValidationReport(
        status="ok" if not duplicate_flags and not warnings else "warning",
        question_count=len(questions),
        passage_count=len(passages),
        reviewed_annotation_count=len(doctrinal_annotations)
        + len(structural_editorial_annotations),
        reviewed_doctrinal_edge_count=len(doctrinal_edges),
        reviewed_structural_editorial_count=len(structural_editorial_annotations),
        candidate_mention_count=len(candidate_mentions),
        candidate_relation_count=len(candidate_relations),
        patience_relation_count=count_focus(doctrinal_edges, "patience"),
        perseverance_relation_count=count_focus(doctrinal_edges, "perseverance"),
        opposed_vice_relation_count=count_focus(doctrinal_edges, "opposed_vice"),
        gift_linkage_relation_count=count_focus(doctrinal_edges, "gift"),
        precept_linkage_relation_count=count_focus(doctrinal_edges, "precept"),
        fortitude_synthesis_node_count=synthesis_summary["nodes"],
        fortitude_synthesis_edge_count=synthesis_summary["edges"],
        duplicate_annotation_flags=sorted(set(duplicate_flags)),
        unresolved_warnings=sorted(set(warnings)),
    )


def count_focus(
    edges: list[FortitudeClosure136140EdgeRecord],
    focus: str,
) -> int:
    return sum(1 for edge in edges if focus in edge.fortitude_closure_focus)


def aliases_overlap(
    concepts: dict[str, dict[str, object]],
    left_id: str,
    right_id: str,
) -> bool:
    left = concepts.get(left_id, {})
    right = concepts.get(right_id, {})
    left_aliases = left.get("aliases", [])
    if not isinstance(left_aliases, list):
        left_aliases = []
    right_aliases = right.get("aliases", [])
    if not isinstance(right_aliases, list):
        right_aliases = []
    left_values = [left.get("canonical_label")]
    left_values.extend(left_aliases)
    right_values = [right.get("canonical_label")]
    right_values.extend(right_aliases)
    left_labels = {normalize_label(str(value)) for value in left_values if value}
    right_labels = {normalize_label(str(value)) for value in right_values if value}
    return bool(left_labels.intersection(right_labels))


def normalize_label(value: str) -> str:
    return " ".join(
        value.casefold().replace("-", " ").replace("(", " ").replace(")", " ").split()
    )


def evidence_matches_passage(evidence_text: str, passage_text: str) -> bool:
    return normalize_label(evidence_text) in normalize_label(passage_text)


def load_fortitude_synthesis_summary() -> dict[str, int]:
    nodes = load_optional_csv_rows(PROCESSED_DIR / "fortitude_tract_synthesis_nodes.csv")
    edges = load_optional_csv_rows(PROCESSED_DIR / "fortitude_tract_synthesis_edges.csv")
    return {"nodes": len(nodes), "edges": len(edges)}


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def load_optional_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_coverage_markdown(payload: dict[str, Any], output_path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Fortitude Closure 136-140 Coverage",
        "",
        "## Summary",
        f"- questions: `{summary['question_count']}`",
        f"- passages: `{summary['passage_count']}`",
        f"- registered concepts used: `{summary['registered_concepts_used']}`",
        f"- reviewed annotations: `{summary['reviewed_annotation_count']}`",
        f"- reviewed doctrinal edges: `{summary['reviewed_doctrinal_edge_count']}`",
        "- reviewed structural-editorial correspondences: "
        f"`{summary['reviewed_structural_editorial_count']}`",
        f"- candidate mentions: `{summary['candidate_mention_count']}`",
        f"- candidate relation proposals: `{summary['candidate_relation_count']}`",
        f"- patience relations: `{summary['patience_relation_count']}`",
        f"- perseverance relations: `{summary['perseverance_relation_count']}`",
        f"- opposed-vice relations: `{summary['opposed_vice_relation_count']}`",
        f"- gift-linkage relations: `{summary['gift_linkage_relation_count']}`",
        f"- precept-linkage relations: `{summary['precept_linkage_relation_count']}`",
        f"- fortitude-tract synthesis nodes: `{summary['fortitude_synthesis_node_count']}`",
        f"- fortitude-tract synthesis edges: `{summary['fortitude_synthesis_edge_count']}`",
        "",
        "## Questions",
    ]
    for row in payload["questions"]:
        lines.append(
            f"- `II-II q.{row['question_number']}` `{row['parse_status']}`"
            f" | passages={row['passage_count']}"
            f" | reviewed={row['reviewed_annotation_count']}"
            f" | doctrinal_edges={row['reviewed_doctrinal_edge_count']}"
            f" | candidate_mentions={row['candidate_mention_count']}"
            f" | candidate_relations={row['candidate_relation_count']}"
            f" | ambiguities={row['unresolved_ambiguity_count']}"
            f" | focus={row['focus_usage']}"
        )
    lines.extend(
        [
            "",
            "## Review Priorities",
            f"- Under-annotated questions: `{payload['under_annotated_questions']}`",
            f"- Normalization risk questions: `{payload['normalization_risk_questions']}`",
            "",
            "## Fortitude Tract Summary",
            "- Total reviewed annotations across reviewed fortitude blocks: "
            f"`{payload['fortitude_tract_summary']['reviewed_annotations_total']}`",
            "- Total reviewed doctrinal edges across reviewed fortitude blocks: "
            f"`{payload['fortitude_tract_summary']['reviewed_doctrinal_edges_total']}`",
            "- Fortitude sub-tracts currently covered by reviewed exports: "
            f"`{payload['fortitude_tract_summary']['fortitude_subtracts_covered']}`",
            "- Concepts linked to gift of fortitude: "
            f"`{payload['fortitude_tract_summary']['concepts_linked_to_gift_of_fortitude']}`",
            "- Concepts linked to precepts of fortitude: "
            f"`{payload['fortitude_tract_summary']['concepts_linked_to_precepts_of_fortitude']}`",
            "- Unresolved normalization hotspots: "
            f"`{payload['fortitude_tract_summary']['unresolved_normalization_hotspots']}`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: FortitudeClosure136140ValidationReport,
    output_path: Path,
) -> None:
    lines = [
        "# Fortitude Closure 136-140 Validation",
        "",
        f"- status: `{report.status}`",
        f"- questions: `{report.question_count}`",
        f"- passages: `{report.passage_count}`",
        f"- reviewed annotations: `{report.reviewed_annotation_count}`",
        f"- reviewed doctrinal edges: `{report.reviewed_doctrinal_edge_count}`",
        "- reviewed structural-editorial correspondences: "
        f"`{report.reviewed_structural_editorial_count}`",
        f"- candidate mentions: `{report.candidate_mention_count}`",
        f"- candidate relation proposals: `{report.candidate_relation_count}`",
        f"- patience relations: `{report.patience_relation_count}`",
        f"- perseverance relations: `{report.perseverance_relation_count}`",
        f"- opposed-vice relations: `{report.opposed_vice_relation_count}`",
        f"- gift-linkage relations: `{report.gift_linkage_relation_count}`",
        f"- precept-linkage relations: `{report.precept_linkage_relation_count}`",
        f"- fortitude-tract synthesis nodes: `{report.fortitude_synthesis_node_count}`",
        f"- fortitude-tract synthesis edges: `{report.fortitude_synthesis_edge_count}`",
        "",
        "## Duplicate Flags",
    ]
    if report.duplicate_annotation_flags:
        lines.extend(f"- `{value}`" for value in report.duplicate_annotation_flags)
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if report.unresolved_warnings:
        lines.extend(f"- `{value}`" for value in report.unresolved_warnings)
    else:
        lines.append("- none")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_synthesis_markdown(
    payload: dict[str, Any],
    synthesis_summary: dict[str, int],
    output_path: Path,
) -> None:
    lines = [
        "# Fortitude Tract Synthesis",
        "",
        (
            "This synthesis export combines the existing reviewed fortitude-parts "
            "block (`II-II qq.129-135`) with the fortitude-closure block "
            "(`II-II qq.136-140`)."
        ),
        "",
        "Default synthesis behavior:",
        "- includes only reviewed doctrinal edges",
        "- preserves provenance to annotation ids and passage ids",
        "- excludes candidate mentions and candidate relation proposals",
        "",
        "Optional editorial layer:",
        "- `data/processed/fortitude_tract_synthesis_with_editorial.graphml` adds "
        "reviewed structural-editorial correspondences for inspection",
        "- editorial correspondences remain outside default doctrinal graph views",
        "",
        "Current scope note:",
        "- this repository state does not yet include a dedicated reviewed doctrinal "
        "fortitude-core block for `II-II qq.123-128`",
        "- accordingly, the synthesis export is structurally situated inside the "
        "fortitude tract `qq.123-140`, but its doctrinal population currently comes "
        "from the reviewed `qq.129-140` layers only",
        "",
        "Current counts:",
        f"- synthesis nodes: `{synthesis_summary['nodes']}`",
        f"- synthesis edges: `{synthesis_summary['edges']}`",
        "- gift-linkage relations in closure block: "
        f"`{payload['summary']['gift_linkage_relation_count']}`",
        "- precept-linkage relations in closure block: "
        f"`{payload['summary']['precept_linkage_relation_count']}`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
