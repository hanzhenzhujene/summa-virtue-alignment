from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.religion_tract_spec import (
    DEFICIENCY_CONCEPT_IDS,
    EXCESS_CONCEPT_IDS,
    POSITIVE_ACT_CONCEPT_IDS,
    RELIGION_TRACT_MAX_QUESTION,
    RELIGION_TRACT_MIN_QUESTION,
    SACRED_OBJECT_CONCEPT_IDS,
    is_deficiency_opposition_relation,
    is_excess_opposition_relation,
    is_positive_act_relation,
    is_sacred_object_relation,
)
from ..models import (
    ArticleRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    PilotAnnotationRecord,
    QuestionRecord,
    ReligionTractCoverageQuestionRecord,
    ReligionTractEdgeRecord,
    ReligionTractValidationReport,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_religion_tract_reports() -> dict[str, int | str]:
    """Build religion-tract coverage and validation outputs."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and RELIGION_TRACT_MIN_QUESTION <= record.question_number <= RELIGION_TRACT_MAX_QUESTION
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

    doctrinal_annotations = load_combined_annotations(edge_layer="doctrinal")
    structural_editorial_annotations = load_combined_annotations(edge_layer="structural")
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "religion_tract_reviewed_doctrinal_edges.jsonl",
        ReligionTractEdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "religion_tract_reviewed_structural_editorial_edges.jsonl",
        ReligionTractEdgeRecord,
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

    coverage = build_religion_tract_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_religion_tract_artifacts(
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
            "positive_act_relation_count": sum(
                1
                for edge in doctrinal_edges
                if is_positive_act_relation(
                    edge.subject_id,
                    edge.relation_type,
                    edge.object_id,
                )
            ),
            "excess_opposition_relation_count": sum(
                1
                for edge in doctrinal_edges
                if is_excess_opposition_relation(
                    edge.subject_id,
                    edge.relation_type,
                    edge.object_id,
                )
            ),
            "deficiency_opposition_relation_count": sum(
                1
                for edge in doctrinal_edges
                if is_deficiency_opposition_relation(
                    edge.subject_id,
                    edge.relation_type,
                    edge.object_id,
                )
            ),
            "sacred_object_relation_count": sum(
                1
                for edge in doctrinal_edges
                if is_sacred_object_relation(
                    edge.subject_id,
                    edge.relation_type,
                    edge.object_id,
                )
            ),
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
        "questions_with_sacred_object_modeling_risk": [
            record.question_number
            for record in coverage
            if (
                record.question_number >= 88
                and not record.sacred_object_usage
                and record.reviewed_annotation_count > 0
            )
        ],
        "questions_with_act_taxonomy_risk": [
            record.question_number
            for record in coverage
            if 81 <= record.question_number <= 91 and not record.positive_act_usage
        ],
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "religion_tract_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "religion_tract_validation_report.json").write_text(
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
        REPO_ROOT / "docs" / "religion_tract_coverage.md",
    )
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "religion_tract_validation.md",
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


def load_combined_annotations(*, edge_layer: str) -> list[PilotAnnotationRecord]:
    pilot_path = (
        GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl"
        if edge_layer == "doctrinal"
        else GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl"
    )
    tract_path = (
        GOLD_DIR / "religion_tract_reviewed_doctrinal_annotations.jsonl"
        if edge_layer == "doctrinal"
        else GOLD_DIR / "religion_tract_reviewed_structural_editorial_annotations.jsonl"
    )
    combined = [
        *[
            annotation
            for annotation in _load_records(pilot_path, PilotAnnotationRecord)
            if annotation.source_passage_id.startswith("st.ii-ii.q")
            and RELIGION_TRACT_MIN_QUESTION
            <= int(annotation.source_passage_id.split(".q")[1][:3])
            <= RELIGION_TRACT_MAX_QUESTION
        ],
        *_load_records(tract_path, PilotAnnotationRecord),
    ]
    deduped: dict[str, PilotAnnotationRecord] = {}
    for annotation in combined:
        deduped[annotation.annotation_id] = annotation
    return sorted(deduped.values(), key=lambda record: record.annotation_id)


def load_tract_concepts(
    annotations: list[PilotAnnotationRecord],
) -> dict[str, dict[str, object]]:
    registry = build_corpus_registry()
    reviewed_path = GOLD_DIR / "religion_tract_reviewed_concepts.jsonl"
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


def build_religion_tract_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[ReligionTractEdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[ReligionTractCoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii"
        and RELIGION_TRACT_MIN_QUESTION
        <= int(row["question_number"])
        <= RELIGION_TRACT_MAX_QUESTION
    }
    passage_counts = Counter(passage.question_id for passage in passages.values())
    reviewed_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    doctrinal_edge_counts: Counter[str] = Counter()
    candidate_mention_counts: Counter[str] = Counter()
    candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    positive_act_usage: dict[str, Counter[str]] = defaultdict(Counter)
    excess_usage: dict[str, Counter[str]] = defaultdict(Counter)
    deficiency_usage: dict[str, Counter[str]] = defaultdict(Counter)
    sacred_object_usage: dict[str, Counter[str]] = defaultdict(Counter)
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
        reviewed_counts[question_id] += 1
        structural_counts[question_id] += 1
        if annotation.object_id.startswith("concept."):
            concepts_by_question[question_id].add(annotation.object_label)

    edge_seen_by_question: dict[str, set[str]] = defaultdict(set)
    for edge in doctrinal_edges:
        for passage_id in edge.source_passage_ids:
            question_id = question_by_passage[passage_id]
            edge_seen_by_question[question_id].add(edge.edge_id)
            if is_positive_act_relation(edge.subject_id, edge.relation_type, edge.object_id):
                tracked_label = (
                    edge.object_label if edge.relation_type == "has_act" else edge.subject_label
                )
                positive_act_usage[question_id][tracked_label] += 1
            if is_excess_opposition_relation(edge.subject_id, edge.relation_type, edge.object_id):
                excess_usage[question_id][edge.subject_label] += 1
            if is_deficiency_opposition_relation(
                edge.subject_id,
                edge.relation_type,
                edge.object_id,
            ):
                deficiency_usage[question_id][edge.subject_label] += 1
            if is_sacred_object_relation(edge.subject_id, edge.relation_type, edge.object_id):
                tracked_label = edge.object_label
                if edge.relation_type == "directed_to":
                    tracked_label = edge.object_label
                sacred_object_usage[question_id][tracked_label] += 1
    for question_id, edge_ids in edge_seen_by_question.items():
        doctrinal_edge_counts[question_id] = len(edge_ids)

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

    records: list[ReligionTractCoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda record: record.question_number):
        records.append(
            ReligionTractCoverageQuestionRecord(
                question_id=question.question_id,
                question_number=question.question_number,
                question_title=question.question_title,
                parse_status=question_status.get(question.question_id, "ok"),
                passage_count=passage_counts[question.question_id],
                reviewed_annotation_count=reviewed_counts[question.question_id],
                reviewed_doctrinal_edge_count=doctrinal_edge_counts[question.question_id],
                reviewed_structural_editorial_count=structural_counts[question.question_id],
                candidate_mention_count=candidate_mention_counts[question.question_id],
                candidate_relation_count=candidate_relation_counts[question.question_id],
                major_concepts=sorted(concepts_by_question[question.question_id])[:24],
                unresolved_ambiguity_count=ambiguity_counts[question.question_id],
                positive_act_usage=dict(sorted(positive_act_usage[question.question_id].items())),
                excess_opposition_usage=dict(sorted(excess_usage[question.question_id].items())),
                deficiency_opposition_usage=dict(
                    sorted(deficiency_usage[question.question_id].items())
                ),
                sacred_object_usage=dict(sorted(sacred_object_usage[question.question_id].items())),
            )
        )
    return records


def identify_under_annotated_questions(
    coverage: list[ReligionTractCoverageQuestionRecord],
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


def validate_religion_tract_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[ReligionTractEdgeRecord],
    structural_editorial_edges: list[ReligionTractEdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[ReligionTractCoverageQuestionRecord],
) -> ReligionTractValidationReport:
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
        if edge.relation_type == "has_act":
            if edge.subject_type != "virtue" or edge.object_type != "act_type":
                warnings.append(f"Act relation with wrong node types: {edge.edge_id}")
        if is_excess_opposition_relation(edge.subject_id, edge.relation_type, edge.object_id):
            if edge.subject_id not in EXCESS_CONCEPT_IDS:
                warnings.append(f"Excess relation with non-excess subject: {edge.edge_id}")
        if is_deficiency_opposition_relation(
            edge.subject_id,
            edge.relation_type,
            edge.object_id,
        ):
            if edge.subject_id not in DEFICIENCY_CONCEPT_IDS:
                warnings.append(f"Deficiency relation with non-deficiency subject: {edge.edge_id}")
        if edge.relation_type in {"concerns_sacred_object", "misuses_sacred_object"}:
            if edge.object_id not in SACRED_OBJECT_CONCEPT_IDS:
                warnings.append(f"Sacred-object edge with unexpected target: {edge.edge_id}")
        if edge.relation_type == "corrupts_spiritual_exchange":
            if edge.subject_id != "concept.simony":
                warnings.append(
                    f"Spiritual-exchange corruption should be modeled from simony: {edge.edge_id}"
                )
            if edge.object_id not in {
                "concept.spiritual_thing",
                "concept.sacrament",
                "concept.spiritual_action",
                "concept.spiritual_office",
            }:
                warnings.append(
                    f"Spiritual-exchange corruption has unexpected target: {edge.edge_id}"
                )

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Wrong structural-editorial review layer: {edge.edge_id}")

    for concept_id, concept in concepts.items():
        node_type = str(concept["node_type"])
        if concept_id in POSITIVE_ACT_CONCEPT_IDS and node_type != "act_type":
            warnings.append(f"Positive religion act is not typed as act_type: {concept_id}")
        if concept_id in EXCESS_CONCEPT_IDS and node_type not in {"vice", "sin_type"}:
            warnings.append(f"Excess concept has unstable node type: {concept_id}")
        if concept_id in DEFICIENCY_CONCEPT_IDS and node_type not in {"vice", "sin_type"}:
            warnings.append(f"Deficiency concept has unstable node type: {concept_id}")
        if concept_id in SACRED_OBJECT_CONCEPT_IDS and node_type not in {"object", "domain"}:
            warnings.append(f"Sacred-object concept has unstable node type: {concept_id}")

    name_act_concepts = {
        concept_id: concepts[concept_id]["canonical_label"]
        for concept_id in ("concept.oath", "concept.vow", "concept.adjuration")
        if concept_id in concepts
    }
    if len(name_act_concepts) != 3:
        warnings.append("Oath, vow, and adjuration must remain distinct registered concepts.")
    if len(set(str(label) for label in name_act_concepts.values())) != len(name_act_concepts):
        warnings.append("Oath, vow, and adjuration labels must stay distinct.")

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention missing passage: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation missing passage: {relation.proposal_id}")

    if len({record.question_id for record in coverage}) != len(questions):
        warnings.append("Coverage question count does not match religion tract question count.")

    return ReligionTractValidationReport(
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
        positive_act_relation_count=sum(
            1
            for edge in doctrinal_edges
            if is_positive_act_relation(edge.subject_id, edge.relation_type, edge.object_id)
        ),
        excess_opposition_relation_count=sum(
            1
            for edge in doctrinal_edges
            if is_excess_opposition_relation(
                edge.subject_id,
                edge.relation_type,
                edge.object_id,
            )
        ),
        deficiency_opposition_relation_count=sum(
            1
            for edge in doctrinal_edges
            if is_deficiency_opposition_relation(
                edge.subject_id,
                edge.relation_type,
                edge.object_id,
            )
        ),
        sacred_object_relation_count=sum(
            1
            for edge in doctrinal_edges
            if is_sacred_object_relation(
                edge.subject_id,
                edge.relation_type,
                edge.object_id,
            )
        ),
        duplicate_annotation_flags=duplicate_flags,
        unresolved_warnings=warnings,
    )


def write_coverage_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Religion Tract Coverage",
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
        f"- Positive-act relations: `{payload['summary']['positive_act_relation_count']}`",
        (
            "- Excess-opposition relations: "
            f"`{payload['summary']['excess_opposition_relation_count']}`"
        ),
        (
            "- Deficiency-opposition relations: "
            f"`{payload['summary']['deficiency_opposition_relation_count']}`"
        ),
        (
            "- Sacred-object / domain relations: "
            f"`{payload['summary']['sacred_object_relation_count']}`"
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
            f"| passages={row['passage_count']} "
            f"| reviewed={row['reviewed_annotation_count']} "
            f"| doctrinal_edges={row['reviewed_doctrinal_edge_count']} "
            f"| candidate_mentions={row['candidate_mention_count']} "
            f"| candidate_relations={row['candidate_relation_count']} "
            f"| ambiguities={row['unresolved_ambiguity_count']} "
            f"| positive={sum(row['positive_act_usage'].values())} "
            f"| excess={sum(row['excess_opposition_usage'].values())} "
            f"| deficiency={sum(row['deficiency_opposition_usage'].values())} "
            f"| sacred={sum(row['sacred_object_usage'].values())}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: ReligionTractValidationReport,
    path: Path,
) -> None:
    lines = [
        "# Religion Tract Validation",
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
        f"- Positive-act relations: `{report.positive_act_relation_count}`",
        f"- Excess-opposition relations: `{report.excess_opposition_relation_count}`",
        f"- Deficiency-opposition relations: `{report.deficiency_opposition_relation_count}`",
        f"- Sacred-object / domain relations: `{report.sacred_object_relation_count}`",
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
