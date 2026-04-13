from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.fortitude_parts_129_135_spec import (
    DEFICIENCY_OPPOSITION_RELATIONS,
    EXCESS_OPPOSITION_RELATIONS,
    EXPENDITURE_RELATED_CONCEPT_IDS,
    EXPENDITURE_RELATED_RELATION_TYPES,
    FORTITUDE_PARTS_129_135_MAX_QUESTION,
    FORTITUDE_PARTS_129_135_MIN_QUESTION,
    FORTITUDE_PARTS_129_135_RELATION_TYPES,
    HONOR_RELATED_CONCEPT_IDS,
    HONOR_RELATED_RELATION_TYPES,
    cluster_for_question,
    cluster_name,
    is_expenditure_related_edge,
    is_honor_related_edge,
)
from ..models import (
    ArticleRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    FortitudeParts129135CoverageQuestionRecord,
    FortitudeParts129135EdgeRecord,
    FortitudeParts129135ValidationReport,
    PilotAnnotationRecord,
    PilotRelationType,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_fortitude_parts_129_135_reports() -> dict[str, int | str]:
    """Build coverage and validation outputs for II-II QQ. 129-135."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and FORTITUDE_PARTS_129_135_MIN_QUESTION
        <= record.question_number
        <= FORTITUDE_PARTS_129_135_MAX_QUESTION
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
        GOLD_DIR / "fortitude_parts_129_135_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "fortitude_parts_129_135_reviewed_structural_editorial_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "fortitude_parts_129_135_reviewed_doctrinal_edges.jsonl",
        FortitudeParts129135EdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "fortitude_parts_129_135_reviewed_structural_editorial_edges.jsonl",
        FortitudeParts129135EdgeRecord,
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

    coverage = build_fortitude_parts_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_fortitude_parts_artifacts(
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
            "excess_opposition_relation_count": count_relations(
                doctrinal_edges,
                relation_types=EXCESS_OPPOSITION_RELATIONS,
            ),
            "deficiency_opposition_relation_count": count_relations(
                doctrinal_edges,
                relation_types=DEFICIENCY_OPPOSITION_RELATIONS,
            ),
            "honor_related_relation_count": sum(
                1
                for edge in doctrinal_edges
                if edge.fortitude_parts_cluster == "honor_worthiness"
            ),
            "expenditure_related_relation_count": sum(
                1
                for edge in doctrinal_edges
                if edge.fortitude_parts_cluster == "expenditure_work"
            ),
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
        "questions_with_opposition_mode_risk": [
            record.question_number
            for record in coverage
            if record.reviewed_annotation_count > 0 and not record.opposition_mode_usage
        ],
        "questions_with_honor_expenditure_modeling_risk": [
            record.question_number
            for record in coverage
            if record.reviewed_annotation_count > 0 and not record.distinction_usage
        ],
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "fortitude_parts_129_135_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "fortitude_parts_129_135_validation_report.json").write_text(
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
        REPO_ROOT / "docs" / "fortitude_parts_129_135_coverage.md",
    )
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "fortitude_parts_129_135_validation.md",
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
    reviewed_path = GOLD_DIR / "fortitude_parts_129_135_reviewed_concepts.jsonl"
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


def build_fortitude_parts_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[FortitudeParts129135EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[FortitudeParts129135CoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii"
        and FORTITUDE_PARTS_129_135_MIN_QUESTION
        <= int(row["question_number"])
        <= FORTITUDE_PARTS_129_135_MAX_QUESTION
    }
    passage_counts = Counter(passage.question_id for passage in passages.values())
    reviewed_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    doctrinal_edge_counts: Counter[str] = Counter()
    candidate_mention_counts: Counter[str] = Counter()
    candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    opposition_mode_usage: dict[str, Counter[str]] = defaultdict(Counter)
    distinction_usage: dict[str, Counter[str]] = defaultdict(Counter)
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
            if edge.relation_type in EXCESS_OPPOSITION_RELATIONS:
                opposition_mode_usage[question_id]["excess"] += 1
            if edge.relation_type in DEFICIENCY_OPPOSITION_RELATIONS:
                opposition_mode_usage[question_id]["deficiency"] += 1
            if is_honor_related_edge(edge.subject_id, edge.relation_type, edge.object_id):
                distinction_usage[question_id]["honor_related"] += 1
            if is_expenditure_related_edge(edge.subject_id, edge.relation_type, edge.object_id):
                distinction_usage[question_id]["expenditure_related"] += 1
            if edge.relation_type == "related_to_fortitude":
                distinction_usage[question_id]["fortitude_related"] += 1
            if edge.relation_type in FORTITUDE_PARTS_129_135_RELATION_TYPES:
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

    rows: list[FortitudeParts129135CoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda item: item.question_number):
        rows.append(
            FortitudeParts129135CoverageQuestionRecord(
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
                opposition_mode_usage=dict(
                    sorted(opposition_mode_usage[question.question_id].items())
                ),
                distinction_usage=dict(
                    sorted(distinction_usage[question.question_id].items())
                ),
                schema_extension_usage=dict(
                    sorted(schema_extension_usage[question.question_id].items())
                ),
            )
        )
    return rows


def identify_under_annotated_questions(
    coverage: list[FortitudeParts129135CoverageQuestionRecord],
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


def validate_fortitude_parts_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[FortitudeParts129135EdgeRecord],
    structural_editorial_edges: list[FortitudeParts129135EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[FortitudeParts129135CoverageQuestionRecord],
) -> FortitudeParts129135ValidationReport:
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
        passage_text = passages[annotation.source_passage_id].text
        if not evidence_matches_passage(annotation.evidence_text, passage_text):
            warnings.append(f"Evidence text mismatch: {annotation.annotation_id}")
        if annotation.relation_type in (
            EXCESS_OPPOSITION_RELATIONS | DEFICIENCY_OPPOSITION_RELATIONS
        ):
            if annotation.object_id not in {"concept.magnanimity", "concept.magnificence"}:
                warnings.append(
                    "Opposition annotation target must be magnanimity or magnificence: "
                    f"{annotation.annotation_id}"
                )
        if annotation.subject_id == "concept.presumption":
            warnings.append(
                "Hope-tract presumption concept used in fortitude-parts reviewed annotation"
            )

    doctrinal_annotation_ids = {record.annotation_id for record in doctrinal_annotations}
    for edge in doctrinal_edges:
        if not set(edge.support_annotation_ids).issubset(doctrinal_annotation_ids):
            warnings.append(f"Doctrinal edge without reviewed support: {edge.edge_id}")
        if "structural_editorial" in edge.support_types:
            warnings.append(
                f"Default doctrinal edge includes structural_editorial support: {edge.edge_id}"
            )
        cluster_values = {
            cluster_for_question(passages[passage_id].question_number)
            for passage_id in edge.source_passage_ids
            if passage_id in passages
        }
        if len(cluster_values) > 1:
            warnings.append(f"Edge crosses tract clusters: {edge.edge_id}")
        if cluster_values and edge.fortitude_parts_cluster not in cluster_values:
            warnings.append(f"Edge cluster mismatch: {edge.edge_id}")
        if edge.relation_type in (
            EXCESS_OPPOSITION_RELATIONS | DEFICIENCY_OPPOSITION_RELATIONS
        ):
            if edge.object_id not in {"concept.magnanimity", "concept.magnificence"}:
                warnings.append(f"Opposition edge target mismatch: {edge.edge_id}")
        if (
            edge.relation_type in HONOR_RELATED_RELATION_TYPES
            and edge.object_id in EXPENDITURE_RELATED_CONCEPT_IDS
        ):
            warnings.append(f"Honor relation points to expenditure concept: {edge.edge_id}")
        if (
            edge.relation_type in EXPENDITURE_RELATED_RELATION_TYPES
            and edge.object_id in HONOR_RELATED_CONCEPT_IDS
        ):
            warnings.append(f"Expenditure relation points to honor concept: {edge.edge_id}")
        if "candidate." in edge.edge_id:
            warnings.append(f"Candidate identifier leaked into reviewed edge: {edge.edge_id}")

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Structural/editorial layer mismatch: {edge.edge_id}")

    if "concept.magnanimity" not in concepts or "concept.magnificence" not in concepts:
        warnings.append("Magnanimity and magnificence must both be present in tract concepts")
    if "concept.magnanimity" == "concept.magnificence":
        warnings.append("Magnanimity and magnificence concept ids are not distinct")
    if aliases_overlap(concepts, "concept.magnanimity", "concept.magnificence"):
        warnings.append("Magnanimity and magnificence alias sets overlap after normalization")
    if "concept.presumption_magnanimity" not in concepts:
        warnings.append("Tract-specific presumption concept is missing")
    if "concept.presumption" in {annotation.subject_id for annotation in doctrinal_annotations}:
        warnings.append("Hope-tract presumption used as reviewed fortitude-parts subject")
    for concept_id in ("concept.ambition", "concept.vainglory", "concept.pusillanimity"):
        if concept_id not in concepts:
            warnings.append(f"Missing tract vice concept: {concept_id}")
    if any(
        edge.subject_id == "concept.magnificence" and edge.object_id == "concept.liberality"
        for edge in doctrinal_edges
    ):
        warnings.append("Magnificence is being reduced to liberality in doctrinal exports")

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention outside tract passages: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation outside tract passages: {relation.proposal_id}")

    coverage_question_ids = {record.question_id for record in coverage}
    if coverage_question_ids != set(questions):
        warnings.append("Coverage rows do not match tract question set")

    return FortitudeParts129135ValidationReport(
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
        excess_opposition_relation_count=count_relations(
            doctrinal_edges,
            relation_types=EXCESS_OPPOSITION_RELATIONS,
        ),
        deficiency_opposition_relation_count=count_relations(
            doctrinal_edges,
            relation_types=DEFICIENCY_OPPOSITION_RELATIONS,
        ),
        honor_related_relation_count=sum(
            1
            for edge in doctrinal_edges
            if edge.fortitude_parts_cluster == "honor_worthiness"
        ),
        expenditure_related_relation_count=sum(
            1
            for edge in doctrinal_edges
            if edge.fortitude_parts_cluster == "expenditure_work"
        ),
        duplicate_annotation_flags=sorted(set(duplicate_flags)),
        unresolved_warnings=sorted(set(warnings)),
    )


def count_relations(
    edges: list[FortitudeParts129135EdgeRecord],
    *,
    relation_types: set[PilotRelationType],
) -> int:
    return sum(1 for edge in edges if edge.relation_type in relation_types)


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
    left_labels = {
        normalize_label(str(value))
        for value in left_values
        if value
    }
    right_labels = {
        normalize_label(str(value))
        for value in right_values
        if value
    }
    return bool(left_labels.intersection(right_labels))


def normalize_label(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").split())


def evidence_matches_passage(evidence_text: str, passage_text: str) -> bool:
    normalized_evidence = normalize_label(evidence_text)
    normalized_passage = normalize_label(passage_text)
    return normalized_evidence in normalized_passage


def write_coverage_markdown(payload: dict[str, Any], output_path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Fortitude Parts 129-135 Coverage",
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
        f"- excess-opposition relations: `{summary['excess_opposition_relation_count']}`",
        f"- deficiency-opposition relations: `{summary['deficiency_opposition_relation_count']}`",
        f"- honor-related relations: `{summary['honor_related_relation_count']}`",
        f"- expenditure-related relations: `{summary['expenditure_related_relation_count']}`",
        "",
        "## Questions",
    ]
    for row in payload["questions"]:
        subcluster = cluster_name(row["subcluster"])
        lines.append(
            f"- `II-II q.{row['question_number']}` `{row['parse_status']}`"
            f" | passages={row['passage_count']}"
            f" | reviewed={row['reviewed_annotation_count']}"
            f" | doctrinal_edges={row['reviewed_doctrinal_edge_count']}"
            f" | candidate_mentions={row['candidate_mention_count']}"
            f" | candidate_relations={row['candidate_relation_count']}"
            f" | ambiguities={row['unresolved_ambiguity_count']}"
            f" | subcluster={subcluster}"
            f" | opposition={row['opposition_mode_usage']}"
            f" | distinction={row['distinction_usage']}"
        )
    lines.extend(
        [
            "",
            "## Review Priorities",
            f"- Under-annotated questions: `{payload['under_annotated_questions']}`",
            f"- Normalization risk questions: `{payload['normalization_risk_questions']}`",
            "- Opposition-mode risk questions: "
            f"`{payload['questions_with_opposition_mode_risk']}`",
            "- Honor/expenditure modeling risk questions: "
            f"`{payload['questions_with_honor_expenditure_modeling_risk']}`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: FortitudeParts129135ValidationReport,
    output_path: Path,
) -> None:
    lines = [
        "# Fortitude Parts 129-135 Validation",
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
        f"- excess-opposition relations: `{report.excess_opposition_relation_count}`",
        f"- deficiency-opposition relations: `{report.deficiency_opposition_relation_count}`",
        f"- honor-related relations: `{report.honor_related_relation_count}`",
        f"- expenditure-related relations: `{report.expenditure_related_relation_count}`",
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


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
