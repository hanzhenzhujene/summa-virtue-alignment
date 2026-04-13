from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..annotations.connected_virtues_109_120_spec import (
    CONNECTED_VIRTUES_109_120_MAX_QUESTION,
    CONNECTED_VIRTUES_109_120_MIN_QUESTION,
    CONNECTED_VIRTUES_RELATION_TYPES,
    cluster_for_question,
    cluster_name,
)
from ..annotations.corpus import build_corpus_registry
from ..models import (
    ArticleRecord,
    ConnectedVirtues109120CoverageQuestionRecord,
    ConnectedVirtues109120EdgeRecord,
    ConnectedVirtues109120ValidationReport,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    PilotAnnotationRecord,
    PilotConnectedVirtuesCluster,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)

SCHEMA_RELATION_TO_CLUSTER: dict[str, PilotConnectedVirtuesCluster] = {
    "concerns_self_presentation": "self_presentation",
    "concerns_social_interaction": "social_interaction",
    "concerns_external_goods": "external_goods",
    "corrects_legal_letter": "legal_equity",
    "preserves_intent_of_law": "legal_equity",
}
CLUSTER_ORDER: tuple[PilotConnectedVirtuesCluster, ...] = (
    "self_presentation",
    "social_interaction",
    "external_goods",
    "legal_equity",
)


def build_connected_virtues_109_120_reports() -> dict[str, int | str]:
    """Build coverage and validation outputs for II-II QQ. 109-120."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and CONNECTED_VIRTUES_109_120_MIN_QUESTION
        <= record.question_number
        <= CONNECTED_VIRTUES_109_120_MAX_QUESTION
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
        GOLD_DIR / "connected_virtues_109_120_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "connected_virtues_109_120_reviewed_structural_editorial_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "connected_virtues_109_120_reviewed_doctrinal_edges.jsonl",
        ConnectedVirtues109120EdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "connected_virtues_109_120_reviewed_structural_editorial_edges.jsonl",
        ConnectedVirtues109120EdgeRecord,
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

    coverage = build_connected_virtues_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_connected_virtues_artifacts(
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
            "self_presentation_relation_count": count_cluster(
                doctrinal_edges,
                "self_presentation",
            ),
            "social_interaction_relation_count": count_cluster(
                doctrinal_edges,
                "social_interaction",
            ),
            "external_goods_relation_count": count_cluster(
                doctrinal_edges,
                "external_goods",
            ),
            "legal_equity_relation_count": count_cluster(doctrinal_edges, "legal_equity"),
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
        "questions_with_subcluster_semantics_risk": [
            record.question_number
            for record in coverage
            if record.reviewed_annotation_count > 0
            and not record.schema_extension_usage
            and record.subcluster == "legal_equity"
        ],
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "connected_virtues_109_120_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "connected_virtues_109_120_validation_report.json").write_text(
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
        REPO_ROOT / "docs" / "connected_virtues_109_120_coverage.md",
    )
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "connected_virtues_109_120_validation.md",
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
    reviewed_path = GOLD_DIR / "connected_virtues_109_120_reviewed_concepts.jsonl"
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


def build_connected_virtues_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[ConnectedVirtues109120EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[ConnectedVirtues109120CoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii"
        and CONNECTED_VIRTUES_109_120_MIN_QUESTION
        <= int(row["question_number"])
        <= CONNECTED_VIRTUES_109_120_MAX_QUESTION
    }
    passage_counts = Counter(passage.question_id for passage in passages.values())
    reviewed_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    doctrinal_edge_counts: Counter[str] = Counter()
    candidate_mention_counts: Counter[str] = Counter()
    candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    cluster_usage: dict[str, Counter[str]] = defaultdict(Counter)
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
            if edge.connected_virtues_cluster is not None:
                cluster_usage[question_id][cluster_name(edge.connected_virtues_cluster)] += 1
            if edge.relation_type in CONNECTED_VIRTUES_RELATION_TYPES:
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

    rows: list[ConnectedVirtues109120CoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda item: item.question_number):
        rows.append(
            ConnectedVirtues109120CoverageQuestionRecord(
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
                cluster_usage=dict(sorted(cluster_usage[question.question_id].items())),
                schema_extension_usage=dict(
                    sorted(schema_extension_usage[question.question_id].items())
                ),
            )
        )
    return rows


def identify_under_annotated_questions(
    coverage: list[ConnectedVirtues109120CoverageQuestionRecord],
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


def validate_connected_virtues_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[ConnectedVirtues109120EdgeRecord],
    structural_editorial_edges: list[ConnectedVirtues109120EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[ConnectedVirtues109120CoverageQuestionRecord],
) -> ConnectedVirtues109120ValidationReport:
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
        if annotation.evidence_text not in passages[annotation.source_passage_id].text:
            warnings.append(f"Evidence text mismatch: {annotation.annotation_id}")
        if not annotation.evidence_text.strip():
            warnings.append(f"Empty evidence text: {annotation.annotation_id}")
        if annotation.connected_virtues_cluster is None:
            warnings.append(
                "Missing connected_virtues_cluster on tract annotation: "
                f"{annotation.annotation_id}"
            )
        else:
            expected_cluster = cluster_for_question(
                passages[annotation.source_passage_id].question_number
            )
            if annotation.connected_virtues_cluster != expected_cluster:
                warnings.append(
                    "Question/cluster mismatch on annotation: "
                    f"{annotation.annotation_id}"
                )
        review_key = (
            annotation.source_passage_id,
            annotation.subject_id,
            annotation.relation_type,
            annotation.object_id,
            annotation.support_type,
        )
        if review_key in seen_review_keys:
            duplicate_flags.append(
                f"Duplicate reviewed annotation tuple: {annotation.annotation_id}"
            )
        seen_review_keys.add(review_key)

    doctrinal_annotation_ids = {annotation.annotation_id for annotation in doctrinal_annotations}
    observed_clusters: set[PilotConnectedVirtuesCluster] = set()
    observed_truth_ids: set[str] = set()
    observed_social_ids: set[str] = set()
    observed_goods_ids: set[str] = set()
    observed_epikeia_ids: set[str] = set()
    for edge in doctrinal_edges:
        if edge.review_layer != "reviewed_doctrinal":
            warnings.append(f"Wrong doctrinal review layer: {edge.edge_id}")
        if "structural_editorial" in edge.support_types:
            warnings.append(f"Editorial support leaked into doctrinal edge: {edge.edge_id}")
        if any(
            annotation_id not in doctrinal_annotation_ids
            for annotation_id in edge.support_annotation_ids
        ):
            warnings.append(f"Doctrinal edge missing reviewed annotation backing: {edge.edge_id}")
        if edge.connected_virtues_cluster is None:
            warnings.append(f"Missing cluster on doctrinal edge: {edge.edge_id}")
        else:
            observed_clusters.add(edge.connected_virtues_cluster)
        for passage_id in edge.source_passage_ids:
            if passage_id not in passages:
                warnings.append(f"Doctrinal edge missing passage: {edge.edge_id}")
                continue
            expected_cluster = cluster_for_question(passages[passage_id].question_number)
            if edge.connected_virtues_cluster != expected_cluster:
                warnings.append(f"Question/cluster mismatch on doctrinal edge: {edge.edge_id}")
        if edge.relation_type in SCHEMA_RELATION_TO_CLUSTER:
            expected_cluster = SCHEMA_RELATION_TO_CLUSTER[edge.relation_type]
            if edge.connected_virtues_cluster != expected_cluster:
                warnings.append(f"Schema relation in wrong cluster: {edge.edge_id}")
        if edge.subject_id == "concept.first_truth" or edge.object_id == "concept.first_truth":
            warnings.append("Faith-related truth leaked into QQ. 109-113 reviewed doctrine.")
        if edge.subject_id == "concept.charity" or edge.object_id == "concept.charity":
            warnings.append("Charity leaked into affability tract reviewed doctrine.")
        if edge.subject_id in {"concept.almsgiving", "concept.mercy"} or edge.object_id in {
            "concept.almsgiving",
            "concept.mercy",
        }:
            warnings.append("Liberality tract should not collapse into almsgiving or mercy.")
        if edge.connected_virtues_cluster == "self_presentation":
            observed_truth_ids.update({edge.subject_id, edge.object_id})
        if edge.connected_virtues_cluster == "social_interaction":
            observed_social_ids.update({edge.subject_id, edge.object_id})
        if edge.connected_virtues_cluster == "external_goods":
            observed_goods_ids.update({edge.subject_id, edge.object_id})
        if edge.connected_virtues_cluster == "legal_equity":
            observed_epikeia_ids.update({edge.subject_id, edge.object_id})

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Wrong structural-editorial review layer: {edge.edge_id}")
        if edge.connected_virtues_cluster is None:
            warnings.append(f"Missing cluster on structural-editorial edge: {edge.edge_id}")

    required_truth_ids = {
        "concept.truth_self_presentation",
        "concept.lying",
        "concept.dissimulation",
        "concept.hypocrisy",
        "concept.boasting",
        "concept.irony",
    }
    if not required_truth_ids.issubset(observed_truth_ids):
        warnings.append("Self-presentation cluster is missing one or more core tract concepts.")
    if "concept.friendliness_affability" not in observed_social_ids:
        warnings.append("Social-interaction cluster is missing friendliness/affability.")
    if not {"concept.liberality", "concept.covetousness", "concept.prodigality"}.issubset(
        observed_goods_ids
    ):
        warnings.append("External-goods cluster is missing one or more core tract concepts.")
    if "concept.epikeia" not in observed_epikeia_ids:
        warnings.append("Legal-equity cluster is missing epikeia.")
    if "concept.legal_letter" not in observed_epikeia_ids:
        warnings.append("Legal-equity cluster is missing the letter-of-law relation.")
    if "concept.intent_of_law" not in observed_epikeia_ids:
        warnings.append("Legal-equity cluster is missing the intent-of-law relation.")

    for cluster in CLUSTER_ORDER:
        if cluster not in observed_clusters:
            warnings.append(f"Missing reviewed sub-cluster in doctrinal export: {cluster}")

    if len({record.question_id for record in coverage}) != len(questions):
        warnings.append(
            "Coverage question count does not match connected virtues 109-120 question count."
        )

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention missing passage: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation missing passage: {relation.proposal_id}")

    return ConnectedVirtues109120ValidationReport(
        status="warning" if warnings or duplicate_flags else "ok",
        question_count=len(coverage),
        passage_count=len(passages),
        reviewed_annotation_count=(
            len(doctrinal_annotations) + len(structural_editorial_annotations)
        ),
        reviewed_doctrinal_edge_count=len(doctrinal_edges),
        reviewed_structural_editorial_count=len(structural_editorial_annotations),
        candidate_mention_count=len(candidate_mentions),
        candidate_relation_count=len(candidate_relations),
        self_presentation_relation_count=count_cluster(doctrinal_edges, "self_presentation"),
        social_interaction_relation_count=count_cluster(doctrinal_edges, "social_interaction"),
        external_goods_relation_count=count_cluster(doctrinal_edges, "external_goods"),
        legal_equity_relation_count=count_cluster(doctrinal_edges, "legal_equity"),
        duplicate_annotation_flags=duplicate_flags,
        unresolved_warnings=warnings,
    )


def count_cluster(
    doctrinal_edges: list[ConnectedVirtues109120EdgeRecord],
    cluster: PilotConnectedVirtuesCluster,
) -> int:
    return sum(
        1
        for edge in doctrinal_edges
        if edge.connected_virtues_cluster == cluster
    )


def write_coverage_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Connected Virtues 109-120 Coverage",
        "",
        "## Summary",
        f"- Questions covered: `{payload['summary']['question_count']}`",
        f"- Passages: `{payload['summary']['passage_count']}`",
        f"- Registered concepts used: `{payload['summary']['registered_concepts_used']}`",
        f"- Reviewed annotations: `{payload['summary']['reviewed_annotation_count']}`",
        f"- Reviewed doctrinal edges: `{payload['summary']['reviewed_doctrinal_edge_count']}`",
        (
            "- Reviewed structural-editorial correspondences: "
            f"`{payload['summary']['reviewed_structural_editorial_count']}`"
        ),
        f"- Candidate mentions: `{payload['summary']['candidate_mention_count']}`",
        f"- Candidate relation proposals: `{payload['summary']['candidate_relation_count']}`",
        (
            "- Self-presentation relations: "
            f"`{payload['summary']['self_presentation_relation_count']}`"
        ),
        (
            "- Social-interaction relations: "
            f"`{payload['summary']['social_interaction_relation_count']}`"
        ),
        (
            "- External-goods relations: "
            f"`{payload['summary']['external_goods_relation_count']}`"
        ),
        (
            "- Epikeia / legal-equity relations: "
            f"`{payload['summary']['legal_equity_relation_count']}`"
        ),
        "",
        "## Under-Annotated Questions",
    ]
    for question_number in payload["under_annotated_questions"]:
        lines.append(f"- `II-II q.{question_number}`")
    lines.extend(["", "## Question Detail"])
    for row in payload["questions"]:
        lines.append(
            f"- `II-II q.{row['question_number']}` `{row['parse_status']}` "
            f"| subcluster={row['subcluster']} "
            f"| passages={row['passage_count']} "
            f"| reviewed={row['reviewed_annotation_count']} "
            f"| doctrinal_edges={row['reviewed_doctrinal_edge_count']} "
            f"| candidate_mentions={row['candidate_mention_count']} "
            f"| candidate_relations={row['candidate_relation_count']} "
            f"| ambiguities={row['unresolved_ambiguity_count']} "
            f"| schema_relations={sum(row['schema_extension_usage'].values())}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: ConnectedVirtues109120ValidationReport,
    path: Path,
) -> None:
    lines = [
        "# Connected Virtues 109-120 Validation",
        "",
        f"- Status: `{report.status}`",
        f"- Questions: `{report.question_count}`",
        f"- Passages: `{report.passage_count}`",
        f"- Reviewed annotations: `{report.reviewed_annotation_count}`",
        f"- Reviewed doctrinal edges: `{report.reviewed_doctrinal_edge_count}`",
        (
            "- Reviewed structural-editorial correspondences: "
            f"`{report.reviewed_structural_editorial_count}`"
        ),
        f"- Candidate mentions: `{report.candidate_mention_count}`",
        f"- Candidate relation proposals: `{report.candidate_relation_count}`",
        f"- Self-presentation relations: `{report.self_presentation_relation_count}`",
        f"- Social-interaction relations: `{report.social_interaction_relation_count}`",
        f"- External-goods relations: `{report.external_goods_relation_count}`",
        f"- Epikeia / legal-equity relations: `{report.legal_equity_relation_count}`",
    ]
    if report.duplicate_annotation_flags:
        lines.extend(["", "## Duplicate Flags"])
        lines.extend(f"- `{item}`" for item in report.duplicate_annotation_flags)
    if report.unresolved_warnings:
        lines.extend(["", "## Warnings"])
        lines.extend(f"- `{item}`" for item in report.unresolved_warnings)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
