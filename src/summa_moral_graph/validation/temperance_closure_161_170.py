from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.temperance_closure_161_170_spec import (
    ADAM_CASE_RELATION_TYPES,
    EXTERNAL_BEHAVIOR_RELATION_TYPES,
    ORDERED_INQUIRY_RELATION_TYPES,
    OUTWARD_ATTIRE_RELATION_TYPES,
    PRECEPT_RELATION_TYPES,
    TEMPERANCE_CLOSURE_161_170_MAX_QUESTION,
    TEMPERANCE_CLOSURE_161_170_MIN_QUESTION,
    cluster_for_question,
    cluster_name,
    focus_tags_for_edge,
)
from ..models import (
    ArticleRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    PilotAnnotationRecord,
    QuestionRecord,
    SegmentRecord,
    TemperanceClosure161170CoverageQuestionRecord,
    TemperanceClosure161170EdgeRecord,
    TemperanceClosure161170ValidationReport,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_temperance_closure_161_170_reports() -> dict[str, int | str]:
    """Build coverage and validation outputs for II-II QQ. 161-170."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_CLOSURE_161_170_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_CLOSURE_161_170_MAX_QUESTION
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
        GOLD_DIR / "temperance_closure_161_170_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "temperance_closure_161_170_reviewed_structural_editorial_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "temperance_closure_161_170_reviewed_doctrinal_edges.jsonl",
        TemperanceClosure161170EdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "temperance_closure_161_170_reviewed_structural_editorial_edges.jsonl",
        TemperanceClosure161170EdgeRecord,
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
    synthesis_summary = load_temperance_full_synthesis_summary()
    prior_temperance_coverage = load_optional_json(
        PROCESSED_DIR / "temperance_141_160_coverage.json"
    )
    prior_summary = prior_temperance_coverage.get("summary", {})

    coverage = build_temperance_closure_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_temperance_closure_artifacts(
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

    unresolved_hotspots = sorted(
        set(prior_temperance_coverage.get("normalization_risk_questions", []))
        | {record.question_number for record in coverage if record.unresolved_ambiguity_count > 0}
    )
    concepts_linked_to_precepts = sorted(
        {
            edge.object_id
            for edge in doctrinal_edges
            if "precept_linkage" in edge.temperance_closure_focus
            and edge.object_id.startswith("concept.")
            and edge.object_type != "precept"
        }
    )
    concepts_linked_to_humility_pride = sorted(
        {
            edge.subject_id
            for edge in doctrinal_edges
            if "humility_pride" in edge.temperance_closure_focus
            and edge.subject_id.startswith("concept.")
        }
        | {
            edge.object_id
            for edge in doctrinal_edges
            if "humility_pride" in edge.temperance_closure_focus
            and edge.object_id.startswith("concept.")
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
            "humility_pride_relation_count": count_focus(doctrinal_edges, "humility_pride"),
            "adams_first_sin_case_relation_count": count_focus(doctrinal_edges, "adam_case"),
            "studiousness_curiosity_relation_count": count_focus(
                doctrinal_edges,
                "study_curiosity",
            ),
            "external_modesty_relation_count": count_focus(
                doctrinal_edges,
                "external_modesty",
            ),
            "precept_linkage_relation_count": count_focus(
                doctrinal_edges,
                "precept_linkage",
            ),
            "temperance_full_synthesis_node_count": synthesis_summary["nodes"],
            "temperance_full_synthesis_edge_count": synthesis_summary["edges"],
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
        "questions_with_case_modeling_risk": [
            record.question_number
            for record in coverage
            if record.question_number in {163, 164, 165} and record.unresolved_ambiguity_count > 0
        ],
        "questions_with_external_modesty_risk": [
            record.question_number
            for record in coverage
            if record.question_number in {168, 169}
            and "concerns_external_behavior" not in record.schema_extension_usage
            and "concerns_outward_attire" not in record.schema_extension_usage
        ],
        "temperance_tract_summary": {
            "reviewed_annotations_total": int(prior_summary.get("reviewed_annotation_count", 0))
            + len(doctrinal_annotations)
            + len(structural_editorial_annotations),
            "reviewed_doctrinal_edges_total": int(
                prior_summary.get("reviewed_doctrinal_edge_count", 0)
            )
            + len(doctrinal_edges),
            "integral_part_relations_total": int(
                prior_summary.get("integral_part_relation_count", 0)
            ),
            "subjective_part_relations_total": int(
                prior_summary.get("subjective_part_relation_count", 0)
            ),
            "potential_part_relations_total": int(
                prior_summary.get("potential_part_relation_count", 0)
            ),
            "humility_pride_relations": count_focus(doctrinal_edges, "humility_pride"),
            "adams_first_sin_case_relations": count_focus(doctrinal_edges, "adam_case"),
            "studiousness_curiosity_relations": count_focus(doctrinal_edges, "study_curiosity"),
            "external_modesty_relations": count_focus(doctrinal_edges, "external_modesty"),
            "precept_linkage_relations": count_focus(doctrinal_edges, "precept_linkage"),
            "concepts_linked_to_precepts": len(concepts_linked_to_precepts),
            "concepts_linked_to_humility_pride": len(concepts_linked_to_humility_pride),
            "unresolved_normalization_hotspots": unresolved_hotspots,
        },
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "temperance_closure_161_170_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "temperance_closure_161_170_validation_report.json").write_text(
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
        REPO_ROOT / "docs" / "temperance_closure_161_170_coverage.md",
    )
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "temperance_closure_161_170_validation.md",
    )
    write_synthesis_markdown(
        coverage_payload,
        synthesis_summary,
        REPO_ROOT / "docs" / "temperance_full_synthesis.md",
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
        "temperance_141_160_reviewed_concepts.jsonl",
        "temperance_closure_161_170_reviewed_concepts.jsonl",
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
    return {
        concept_id: registry[concept_id].model_dump(mode="json")
        for concept_id in sorted(concept_ids)
    }


def build_temperance_closure_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[TemperanceClosure161170EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[TemperanceClosure161170CoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii"
        and TEMPERANCE_CLOSURE_161_170_MIN_QUESTION
        <= int(row["question_number"])
        <= TEMPERANCE_CLOSURE_161_170_MAX_QUESTION
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
            for focus in edge.temperance_closure_focus:
                if focus != "synthesis":
                    focus_usage[question_id][focus] += 1
            if edge.relation_type in {
                "case_of",
                "results_in_punishment",
                "tempted_by",
                "concerns_ordered_inquiry",
                "concerns_external_behavior",
                "concerns_outward_attire",
                "precept_of",
                "forbids_opposed_vice_of",
            }:
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

    rows: list[TemperanceClosure161170CoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda item: item.question_number):
        rows.append(
            TemperanceClosure161170CoverageQuestionRecord(
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
                subcluster=cluster_for_question(question.question_number),
                focus_usage=dict(sorted(focus_usage[question.question_id].items())),
                schema_extension_usage=dict(
                    sorted(schema_extension_usage[question.question_id].items())
                ),
            )
        )
    return rows


def identify_under_annotated_questions(
    coverage: list[TemperanceClosure161170CoverageQuestionRecord],
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


def validate_temperance_closure_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[TemperanceClosure161170EdgeRecord],
    structural_editorial_edges: list[TemperanceClosure161170EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[TemperanceClosure161170CoverageQuestionRecord],
    synthesis_summary: dict[str, int],
) -> TemperanceClosure161170ValidationReport:
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
        question_numbers = {
            passages[passage_id].question_number
            for passage_id in edge.source_passage_ids
            if passage_id in passages
        }
        if len({cluster_for_question(number) for number in question_numbers}) > 1:
            warnings.append(f"Temperance closure edge crosses sub-clusters: {edge.edge_id}")
        if edge.temperance_closure_cluster != cluster_for_question(min(question_numbers)):
            warnings.append(f"Temperance closure cluster mismatch: {edge.edge_id}")
        expected_focus = {
            tag
            for question_number in question_numbers
            for tag in focus_tags_for_edge(
                question_number,
                edge.subject_id,
                edge.relation_type,
                edge.object_id,
            )
        }
        if not expected_focus.issubset(set(edge.temperance_closure_focus)):
            warnings.append(f"Temperance closure focus tags inconsistent: {edge.edge_id}")
        if edge.relation_type == "case_of":
            if edge.subject_id != "concept.adams_first_sin" or edge.object_id != "concept.pride":
                warnings.append(
                    f"Case relation must preserve Adam/pride distinction: {edge.edge_id}"
                )
        if (
            edge.relation_type in ADAM_CASE_RELATION_TYPES
            and "adam_case" not in edge.temperance_closure_focus
        ):
            warnings.append(f"Adam-case relation missing adam_case focus tag: {edge.edge_id}")
        if (
            edge.relation_type == "results_in_punishment"
            and edge.subject_id != "concept.adams_first_sin"
        ):
            warnings.append(f"Punishment relation must stem from Adam's first sin: {edge.edge_id}")
        if (
            edge.relation_type == "tempted_by"
            and edge.object_id != "concept.first_parents_temptation"
        ):
            warnings.append(
                f"Tempted-by relation must target first-parents temptation: {edge.edge_id}"
            )
        if edge.relation_type in ORDERED_INQUIRY_RELATION_TYPES and edge.object_id not in {
            "concept.ordered_inquiry",
            "concept.disordered_inquiry",
        }:
            warnings.append(f"Ordered-inquiry relation must target inquiry nodes: {edge.edge_id}")
        if edge.relation_type in EXTERNAL_BEHAVIOR_RELATION_TYPES and edge.object_id not in {
            "concept.outward_behavior",
            "concept.playful_actions",
        }:
            warnings.append(
                f"External-behavior relation must target outward behavior or play: {edge.edge_id}"
            )
        if (
            edge.relation_type in OUTWARD_ATTIRE_RELATION_TYPES
            and edge.object_id != "concept.outward_apparel"
        ):
            warnings.append(
                f"Outward-attire relation must point to concept.outward_apparel: {edge.edge_id}"
            )
        if edge.relation_type in PRECEPT_RELATION_TYPES and not edge.subject_id.startswith(
            "concept.precepts_of_temperance"
        ):
            warnings.append(
                f"Precept relation must originate in temperance precept nodes: {edge.edge_id}"
            )
        if "candidate." in edge.edge_id:
            warnings.append(f"Candidate identifier leaked into reviewed edge: {edge.edge_id}")

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Structural/editorial layer mismatch: {edge.edge_id}")

    for left_id, right_id, label in (
        ("concept.humility", "concept.pride", "humility vs pride"),
        ("concept.pride", "concept.adams_first_sin", "pride vs Adam's first sin"),
        ("concept.studiousness", "concept.curiosity", "studiousness vs curiosity"),
        (
            "concept.modesty_general",
            "concept.external_behavior_modesty",
            "modesty-general vs external-behavior modesty",
        ),
        (
            "concept.modesty_general",
            "concept.outward_attire_modesty",
            "modesty-general vs outward-attire modesty",
        ),
    ):
        if aliases_overlap(concepts, left_id, right_id):
            warnings.append(f"Identity separation failed for {label}")
    if aliases_overlap(concepts, "concept.humility", "concept.modesty_general"):
        warnings.append("Humility aliases overlap with modesty-general aliases")
    if aliases_overlap(concepts, "concept.pride", "concept.adams_first_sin"):
        warnings.append("Pride aliases overlap with Adam's first sin aliases")

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention outside tract passages: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation outside tract passages: {relation.proposal_id}")

    coverage_question_ids = {record.question_id for record in coverage}
    if coverage_question_ids != set(questions):
        warnings.append("Coverage rows do not match temperance closure tract question set")
    if synthesis_summary["nodes"] <= 0 or synthesis_summary["edges"] <= 0:
        warnings.append("Temperance full synthesis summary is empty")

    return TemperanceClosure161170ValidationReport(
        status="ok" if not duplicate_flags and not warnings else "warning",
        question_count=len(questions),
        passage_count=len(passages),
        reviewed_annotation_count=(
            len(doctrinal_annotations) + len(structural_editorial_annotations)
        ),
        reviewed_doctrinal_edge_count=len(doctrinal_edges),
        reviewed_structural_editorial_count=len(structural_editorial_annotations),
        candidate_mention_count=len(candidate_mentions),
        candidate_relation_count=len(candidate_relations),
        humility_pride_relation_count=count_focus(doctrinal_edges, "humility_pride"),
        adams_first_sin_case_relation_count=count_focus(doctrinal_edges, "adam_case"),
        studiousness_curiosity_relation_count=count_focus(doctrinal_edges, "study_curiosity"),
        external_modesty_relation_count=count_focus(doctrinal_edges, "external_modesty"),
        precept_linkage_relation_count=count_focus(doctrinal_edges, "precept_linkage"),
        temperance_full_synthesis_node_count=synthesis_summary["nodes"],
        temperance_full_synthesis_edge_count=synthesis_summary["edges"],
        duplicate_annotation_flags=sorted(set(duplicate_flags)),
        unresolved_warnings=sorted(set(warnings)),
    )


def count_focus(
    edges: list[TemperanceClosure161170EdgeRecord],
    focus: str,
) -> int:
    return sum(1 for edge in edges if focus in edge.temperance_closure_focus)


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
    return " ".join(value.casefold().replace("-", " ").split())


def evidence_matches_passage(evidence_text: str, passage_text: str) -> bool:
    normalized_evidence = " ".join(evidence_text.casefold().split())
    normalized_passage = " ".join(passage_text.casefold().split())
    if not normalized_evidence:
        return False
    return normalized_evidence in normalized_passage


def load_temperance_full_synthesis_summary() -> dict[str, int]:
    with (PROCESSED_DIR / "temperance_full_synthesis_nodes.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        nodes = list(csv.DictReader(handle))
    with (PROCESSED_DIR / "temperance_full_synthesis_edges.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        edges = list(csv.DictReader(handle))
    return {"nodes": len(nodes), "edges": len(edges)}


def load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def write_coverage_markdown(payload: dict[str, Any], output_path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Temperance Closure 161-170 Coverage",
        "",
        (
            "This report summarizes the reviewed temperance-closure block for "
            "`II-II qq. 161-170` and its role in the completed temperance synthesis."
        ),
        "",
        "## Summary",
        f"- questions covered: `{summary['question_count']}`",
        f"- passages: `{summary['passage_count']}`",
        f"- registered concepts used: `{summary['registered_concepts_used']}`",
        f"- reviewed annotations: `{summary['reviewed_annotation_count']}`",
        f"- reviewed doctrinal edges: `{summary['reviewed_doctrinal_edge_count']}`",
        "- reviewed structural-editorial correspondences: "
        f"`{summary['reviewed_structural_editorial_count']}`",
        f"- candidate mentions: `{summary['candidate_mention_count']}`",
        f"- candidate relation proposals: `{summary['candidate_relation_count']}`",
        f"- humility/pride relations: `{summary['humility_pride_relation_count']}`",
        f"- Adam's-first-sin case relations: `{summary['adams_first_sin_case_relation_count']}`",
        f"- studiousness/curiosity relations: `{summary['studiousness_curiosity_relation_count']}`",
        f"- external-modesty relations: `{summary['external_modesty_relation_count']}`",
        f"- precept-linkage relations: `{summary['precept_linkage_relation_count']}`",
        f"- temperance full-synthesis nodes: `{summary['temperance_full_synthesis_node_count']}`",
        f"- temperance full-synthesis edges: `{summary['temperance_full_synthesis_edge_count']}`",
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
            f" | subcluster={cluster_name(row['subcluster'])}"
            f" | focus={row['focus_usage']}"
        )
    lines.extend(
        [
            "",
            "## Review Priorities",
            f"- Under-annotated questions: `{payload['under_annotated_questions']}`",
            f"- Normalization risk questions: `{payload['normalization_risk_questions']}`",
            (
                "- Adam-case modeling risk questions: "
                f"`{payload['questions_with_case_modeling_risk']}`"
            ),
            "- External-modesty modeling risk questions: "
            f"`{payload['questions_with_external_modesty_risk']}`",
            "",
            "## Temperance Tract Summary",
            "- Total reviewed annotations across `qq.141-170`: "
            f"`{payload['temperance_tract_summary']['reviewed_annotations_total']}`",
            "- Total reviewed doctrinal edges across `qq.141-170`: "
            f"`{payload['temperance_tract_summary']['reviewed_doctrinal_edges_total']}`",
            "- Integral-part relations across full temperance tract: "
            f"`{payload['temperance_tract_summary']['integral_part_relations_total']}`",
            "- Subjective-part relations across full temperance tract: "
            f"`{payload['temperance_tract_summary']['subjective_part_relations_total']}`",
            "- Potential-part relations across full temperance tract: "
            f"`{payload['temperance_tract_summary']['potential_part_relations_total']}`",
            "- Concepts linked to temperance precepts: "
            f"`{payload['temperance_tract_summary']['concepts_linked_to_precepts']}`",
            "- Concepts linked to humility/pride block: "
            f"`{payload['temperance_tract_summary']['concepts_linked_to_humility_pride']}`",
            "- Unresolved normalization hotspots: "
            f"`{payload['temperance_tract_summary']['unresolved_normalization_hotspots']}`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: TemperanceClosure161170ValidationReport,
    output_path: Path,
) -> None:
    lines = [
        "# Temperance Closure 161-170 Validation",
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
        f"- humility/pride relations: `{report.humility_pride_relation_count}`",
        f"- Adam's-first-sin case relations: `{report.adams_first_sin_case_relation_count}`",
        f"- studiousness/curiosity relations: `{report.studiousness_curiosity_relation_count}`",
        f"- external-modesty relations: `{report.external_modesty_relation_count}`",
        f"- precept-linkage relations: `{report.precept_linkage_relation_count}`",
        f"- temperance full-synthesis nodes: `{report.temperance_full_synthesis_node_count}`",
        f"- temperance full-synthesis edges: `{report.temperance_full_synthesis_edge_count}`",
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
        "# Temperance Full Synthesis",
        "",
        (
            "This synthesis export combines the reviewed temperance phase-1 block "
            "(`II-II qq.141-160`) with the temperance closure block "
            "(`II-II qq.161-170`)."
        ),
        "",
        "Default synthesis behavior:",
        "- includes only reviewed doctrinal edges",
        "- preserves provenance to annotation ids and passage ids",
        "- excludes candidate mentions and candidate relation proposals",
        "- preserves tract-local part-taxonomy and closure-focus metadata",
        "",
        "Optional editorial layer:",
        (
            "- `data/processed/temperance_full_synthesis_with_editorial.graphml` adds "
            "reviewed structural-editorial correspondences for inspection"
        ),
        "- editorial correspondences remain outside default doctrinal graph views",
        "",
        "Current counts:",
        f"- synthesis nodes: `{synthesis_summary['nodes']}`",
        f"- synthesis edges: `{synthesis_summary['edges']}`",
        "- humility/pride relations in closure block: "
        f"`{payload['summary']['humility_pride_relation_count']}`",
        "- Adam's-first-sin case relations in closure block: "
        f"`{payload['summary']['adams_first_sin_case_relation_count']}`",
        "- studiousness/curiosity relations in closure block: "
        f"`{payload['summary']['studiousness_curiosity_relation_count']}`",
        "- external-modesty relations in closure block: "
        f"`{payload['summary']['external_modesty_relation_count']}`",
        "- precept-linkage relations in closure block: "
        f"`{payload['summary']['precept_linkage_relation_count']}`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
