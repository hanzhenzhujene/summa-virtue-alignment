from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from ..annotations.corpus import build_corpus_registry
from ..annotations.temperance_141_160_spec import (
    ANGER_RELATION_TYPES,
    DRINK_RELATION_TYPES,
    FOOD_RELATION_TYPES,
    INTEGRAL_PART_RELATIONS,
    MODESTY_RELATION_TYPES,
    POTENTIAL_PART_RELATIONS,
    SEX_RELATION_TYPES,
    SUBJECTIVE_PART_RELATIONS,
    TEMPERANCE_141_160_MAX_QUESTION,
    TEMPERANCE_141_160_MIN_QUESTION,
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
    PilotRelationType,
    QuestionRecord,
    SegmentRecord,
    Temperance141160CoverageQuestionRecord,
    Temperance141160EdgeRecord,
    Temperance141160ValidationReport,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_temperance_141_160_reports() -> dict[str, int | str]:
    """Build coverage and validation outputs for II-II QQ. 141-160."""

    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
        if record.part_id == "ii-ii"
        and TEMPERANCE_141_160_MIN_QUESTION
        <= record.question_number
        <= TEMPERANCE_141_160_MAX_QUESTION
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
        GOLD_DIR / "temperance_141_160_reviewed_doctrinal_annotations.jsonl",
        PilotAnnotationRecord,
    )
    structural_editorial_annotations = _load_records(
        GOLD_DIR / "temperance_141_160_reviewed_structural_editorial_annotations.jsonl",
        PilotAnnotationRecord,
    )
    doctrinal_edges = _load_records(
        PROCESSED_DIR / "temperance_141_160_reviewed_doctrinal_edges.jsonl",
        Temperance141160EdgeRecord,
    )
    structural_editorial_edges = _load_records(
        PROCESSED_DIR / "temperance_141_160_reviewed_structural_editorial_edges.jsonl",
        Temperance141160EdgeRecord,
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
    synthesis_summary = load_temperance_phase1_synthesis_summary()

    coverage = build_temperance_coverage(
        questions=questions,
        passages=passages,
        doctrinal_annotations=doctrinal_annotations,
        structural_editorial_annotations=structural_editorial_annotations,
        doctrinal_edges=doctrinal_edges,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
    )
    validation = validate_temperance_artifacts(
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
            "integral_part_relation_count": count_relations(
                doctrinal_edges,
                relation_types=INTEGRAL_PART_RELATIONS,
            ),
            "subjective_part_relation_count": count_relations(
                doctrinal_edges,
                relation_types=SUBJECTIVE_PART_RELATIONS,
            ),
            "potential_part_relation_count": count_relations(
                doctrinal_edges,
                relation_types=POTENTIAL_PART_RELATIONS,
            ),
            "food_related_relation_count": count_focus(doctrinal_edges, "food"),
            "drink_related_relation_count": count_focus(doctrinal_edges, "drink"),
            "sex_related_relation_count": count_focus(doctrinal_edges, "sex"),
            "continence_incontinence_relation_count": count_focus(
                doctrinal_edges,
                "continence_incontinence",
            ),
            "meekness_anger_relation_count": count_focus(doctrinal_edges, "meekness_anger"),
            "clemency_cruelty_relation_count": count_focus(
                doctrinal_edges,
                "clemency_cruelty",
            ),
            "modesty_general_relation_count": count_focus(doctrinal_edges, "modesty_general"),
            "temperance_phase1_synthesis_node_count": synthesis_summary["nodes"],
            "temperance_phase1_synthesis_edge_count": synthesis_summary["edges"],
        },
        "questions": [record.model_dump(mode="json") for record in coverage],
        "under_annotated_questions": identify_under_annotated_questions(coverage),
        "normalization_risk_questions": [
            record.question_number for record in coverage if record.unresolved_ambiguity_count > 0
        ],
        "questions_with_part_taxonomy_risk": [
            record.question_number
            for record in coverage
            if record.question_number in {143, 145, 155, 157, 160}
            and not record.part_taxonomy_usage
        ],
        "questions_with_matter_domain_risk": [
            record.question_number
            for record in coverage
            if record.question_number
            in {141, 146, 147, 148, 149, 150, 151, 153, 154, 156, 158, 160}
            and not record.matter_domain_usage
        ],
    }

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "temperance_141_160_coverage.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    (PROCESSED_DIR / "temperance_141_160_validation_report.json").write_text(
        json.dumps(
            validation.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    write_coverage_markdown(coverage_payload, REPO_ROOT / "docs" / "temperance_141_160_coverage.md")
    write_validation_markdown(
        validation,
        REPO_ROOT / "docs" / "temperance_141_160_validation.md",
    )
    write_synthesis_markdown(
        coverage_payload,
        synthesis_summary,
        REPO_ROOT / "docs" / "temperance_phase1_synthesis.md",
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
    reviewed_path = GOLD_DIR / "temperance_141_160_reviewed_concepts.jsonl"
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


def build_temperance_coverage(
    *,
    questions: dict[str, QuestionRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[Temperance141160EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
) -> list[Temperance141160CoverageQuestionRecord]:
    question_status = {
        row["question_id"]: row["parse_status"]
        for row in json.loads((PROCESSED_DIR / "coverage_report.json").read_text(encoding="utf-8"))[
            "questions"
        ]
        if row["part_id"] == "ii-ii"
        and TEMPERANCE_141_160_MIN_QUESTION
        <= int(row["question_number"])
        <= TEMPERANCE_141_160_MAX_QUESTION
    }
    passage_counts = Counter(passage.question_id for passage in passages.values())
    reviewed_counts: Counter[str] = Counter()
    structural_counts: Counter[str] = Counter()
    doctrinal_edge_counts: Counter[str] = Counter()
    candidate_mention_counts: Counter[str] = Counter()
    candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()
    concepts_by_question: dict[str, set[str]] = defaultdict(set)
    part_usage: dict[str, Counter[str]] = defaultdict(Counter)
    matter_usage: dict[str, Counter[str]] = defaultdict(Counter)
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
            if edge.relation_type in INTEGRAL_PART_RELATIONS:
                part_usage[question_id]["integral"] += 1
            if edge.relation_type in SUBJECTIVE_PART_RELATIONS:
                part_usage[question_id]["subjective"] += 1
            if edge.relation_type in POTENTIAL_PART_RELATIONS:
                part_usage[question_id]["potential"] += 1
            for focus in edge.temperance_focus:
                if focus in {
                    "food",
                    "drink",
                    "sex",
                    "continence_incontinence",
                    "meekness_anger",
                    "clemency_cruelty",
                    "modesty_general",
                }:
                    matter_usage[question_id][focus] += 1
            if edge.relation_type in {
                "integral_part_of",
                "subjective_part_of",
                "potential_part_of",
                "act_of",
                "concerns_food",
                "concerns_drink",
                "concerns_sexual_pleasure",
                "concerns_anger",
                "concerns_outward_moderation",
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

    rows: list[Temperance141160CoverageQuestionRecord] = []
    for question in sorted(questions.values(), key=lambda item: item.question_number):
        rows.append(
            Temperance141160CoverageQuestionRecord(
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
                part_taxonomy_usage=dict(sorted(part_usage[question.question_id].items())),
                matter_domain_usage=dict(sorted(matter_usage[question.question_id].items())),
                schema_extension_usage=dict(
                    sorted(schema_extension_usage[question.question_id].items())
                ),
            )
        )
    return rows


def identify_under_annotated_questions(
    coverage: list[Temperance141160CoverageQuestionRecord],
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


def validate_temperance_artifacts(
    *,
    concepts: dict[str, dict[str, object]],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    doctrinal_annotations: list[PilotAnnotationRecord],
    structural_editorial_annotations: list[PilotAnnotationRecord],
    doctrinal_edges: list[Temperance141160EdgeRecord],
    structural_editorial_edges: list[Temperance141160EdgeRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    coverage: list[Temperance141160CoverageQuestionRecord],
    synthesis_summary: dict[str, int],
) -> Temperance141160ValidationReport:
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
        if edge.temperance_cluster is None:
            warnings.append(f"Temperance cluster missing on reviewed edge: {edge.edge_id}")
        else:
            cluster_values = {
                cluster_for_question(passages[passage_id].question_number)
                for passage_id in edge.source_passage_ids
                if passage_id in passages
            }
            if len(cluster_values) > 1:
                warnings.append(f"Reviewed edge crosses temperance clusters: {edge.edge_id}")
            if cluster_values and edge.temperance_cluster not in cluster_values:
                warnings.append(f"Temperance cluster mismatch: {edge.edge_id}")
        if not edge.temperance_focus:
            warnings.append(f"Temperance focus missing on reviewed edge: {edge.edge_id}")
        if edge.relation_type in (
            INTEGRAL_PART_RELATIONS
            | SUBJECTIVE_PART_RELATIONS
            | POTENTIAL_PART_RELATIONS
        ):
            if edge.object_id != "concept.temperance":
                warnings.append(f"Part-taxonomy edge must target temperance: {edge.edge_id}")
        if edge.relation_type in FOOD_RELATION_TYPES and edge.object_id != "concept.food":
            warnings.append(f"Food relation must point to concept.food: {edge.edge_id}")
        if edge.relation_type in DRINK_RELATION_TYPES and edge.object_id != "concept.drink":
            warnings.append(f"Drink relation must point to concept.drink: {edge.edge_id}")
        if edge.relation_type in SEX_RELATION_TYPES and edge.object_id != "concept.sexual_pleasure":
            warnings.append(
                f"Sexual-pleasure relation must point to concept.sexual_pleasure: {edge.edge_id}"
            )
        if edge.relation_type in ANGER_RELATION_TYPES and edge.object_id != "concept.anger":
            warnings.append(f"Anger relation must point to passion-level anger: {edge.edge_id}")
        if (
            edge.relation_type in MODESTY_RELATION_TYPES
            and edge.object_id != "concept.outward_moderation"
        ):
            warnings.append(
                (
                    "Outward-moderation relation must point to "
                    f"concept.outward_moderation: {edge.edge_id}"
                )
            )
        if "candidate." in edge.edge_id:
            warnings.append(f"Candidate identifier leaked into reviewed edge: {edge.edge_id}")
        expected_focus = set(
            focus_tags_for_edge(
                passages[edge.source_passage_ids[0]].question_number,
                edge.subject_id,
                edge.relation_type,
                edge.object_id,
            )
        )
        if not expected_focus.issubset(set(edge.temperance_focus)):
            warnings.append(f"Temperance focus tags inconsistent: {edge.edge_id}")

    for edge in structural_editorial_edges:
        if edge.review_layer != "reviewed_structural_editorial":
            warnings.append(f"Structural/editorial layer mismatch: {edge.edge_id}")

    for left_id, right_id, label in (
        ("concept.abstinence", "concept.fasting", "abstinence vs fasting"),
        ("concept.chastity", "concept.virginity", "chastity vs virginity"),
        ("concept.continence", "concept.temperance", "continence vs temperance"),
        ("concept.meekness", "concept.clemency", "meekness vs clemency"),
        ("concept.gluttony", "concept.drunkenness", "gluttony vs drunkenness"),
    ):
        if left_id == right_id or aliases_overlap(concepts, left_id, right_id):
            warnings.append(f"Identity separation failed for {label}")
    if "concept.humility" in concepts and aliases_overlap(
        concepts,
        "concept.modesty_general",
        "concept.humility",
    ):
        warnings.append("Modesty-general aliases overlap with humility")
    if aliases_overlap(concepts, "concept.anger", "concept.anger_vice"):
        anger_notes = concepts.get("concept.anger_vice", {}).get("disambiguation_notes", [])
        if not isinstance(anger_notes, list) or not anger_notes:
            warnings.append(
                "Passion-level anger and vice-level anger aliases overlap without disambiguation"
            )
    allowed_lust_targets = {
        "concept.simple_fornication",
        "concept.seduction_lust",
        "concept.rape_lust",
        "concept.adultery_lust",
        "concept.incest_lust",
        "concept.sacrilege_lust",
        "concept.unnatural_vice_lust",
    }
    for edge in doctrinal_edges:
        if edge.object_id == "concept.lust" and edge.relation_type == "species_of":
            if edge.subject_id not in allowed_lust_targets:
                warnings.append(f"Lust taxonomy over-asserted beyond reviewed set: {edge.edge_id}")

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention outside tract passages: {mention.candidate_id}")
    for relation in candidate_relations:
        if relation.source_passage_id not in passages:
            warnings.append(f"Candidate relation outside tract passages: {relation.proposal_id}")

    coverage_question_ids = {record.question_id for record in coverage}
    if coverage_question_ids != set(questions):
        warnings.append("Coverage rows do not match temperance tract question set")
    if synthesis_summary["nodes"] <= 0 or synthesis_summary["edges"] <= 0:
        warnings.append("Temperance phase-1 synthesis summary is empty")

    return Temperance141160ValidationReport(
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
        integral_part_relation_count=count_relations(
            doctrinal_edges,
            relation_types=INTEGRAL_PART_RELATIONS,
        ),
        subjective_part_relation_count=count_relations(
            doctrinal_edges,
            relation_types=SUBJECTIVE_PART_RELATIONS,
        ),
        potential_part_relation_count=count_relations(
            doctrinal_edges,
            relation_types=POTENTIAL_PART_RELATIONS,
        ),
        food_related_relation_count=count_focus(doctrinal_edges, "food"),
        drink_related_relation_count=count_focus(doctrinal_edges, "drink"),
        sex_related_relation_count=count_focus(doctrinal_edges, "sex"),
        continence_incontinence_relation_count=count_focus(
            doctrinal_edges,
            "continence_incontinence",
        ),
        meekness_anger_relation_count=count_focus(doctrinal_edges, "meekness_anger"),
        clemency_cruelty_relation_count=count_focus(doctrinal_edges, "clemency_cruelty"),
        modesty_general_relation_count=count_focus(doctrinal_edges, "modesty_general"),
        temperance_phase1_synthesis_node_count=synthesis_summary["nodes"],
        temperance_phase1_synthesis_edge_count=synthesis_summary["edges"],
        duplicate_annotation_flags=sorted(set(duplicate_flags)),
        unresolved_warnings=sorted(set(warnings)),
    )


def count_relations(
    edges: list[Temperance141160EdgeRecord],
    *,
    relation_types: set[PilotRelationType],
) -> int:
    return sum(1 for edge in edges if edge.relation_type in relation_types)


def count_focus(
    edges: list[Temperance141160EdgeRecord],
    focus: str,
) -> int:
    return sum(1 for edge in edges if focus in edge.temperance_focus)


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
    return normalize_label(evidence_text) in normalize_label(passage_text)


def load_temperance_phase1_synthesis_summary() -> dict[str, int]:
    node_path = PROCESSED_DIR / "temperance_phase1_synthesis_nodes.csv"
    edge_path = PROCESSED_DIR / "temperance_phase1_synthesis_edges.csv"
    node_count = 0
    edge_count = 0
    if node_path.exists():
        with node_path.open("r", encoding="utf-8", newline="") as handle:
            node_count = max(sum(1 for _ in csv.DictReader(handle)), 0)
    if edge_path.exists():
        with edge_path.open("r", encoding="utf-8", newline="") as handle:
            edge_count = max(sum(1 for _ in csv.DictReader(handle)), 0)
    return {"nodes": node_count, "edges": edge_count}


def write_coverage_markdown(payload: dict[str, Any], output_path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# Temperance 141-160 Coverage",
        "",
        "## Summary",
        f"- questions: `{summary['question_count']}`",
        f"- passages: `{summary['passage_count']}`",
        f"- registered concepts used: `{summary['registered_concepts_used']}`",
        f"- reviewed annotations: `{summary['reviewed_annotation_count']}`",
        f"- reviewed doctrinal edges: `{summary['reviewed_doctrinal_edge_count']}`",
        (
            "- reviewed structural-editorial correspondences: "
            f"`{summary['reviewed_structural_editorial_count']}`"
        ),
        f"- candidate mentions: `{summary['candidate_mention_count']}`",
        f"- candidate relation proposals: `{summary['candidate_relation_count']}`",
        f"- integral-part relations: `{summary['integral_part_relation_count']}`",
        f"- subjective-part relations: `{summary['subjective_part_relation_count']}`",
        f"- potential-part relations: `{summary['potential_part_relation_count']}`",
        f"- food-related relations: `{summary['food_related_relation_count']}`",
        f"- drink-related relations: `{summary['drink_related_relation_count']}`",
        f"- sex-related relations: `{summary['sex_related_relation_count']}`",
        (
            "- continence/incontinence relations: "
            f"`{summary['continence_incontinence_relation_count']}`"
        ),
        f"- meekness/anger relations: `{summary['meekness_anger_relation_count']}`",
        f"- clemency/cruelty relations: `{summary['clemency_cruelty_relation_count']}`",
        f"- modesty-general relations: `{summary['modesty_general_relation_count']}`",
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
            f" | part_taxonomy={row['part_taxonomy_usage']}"
            f" | domains={row['matter_domain_usage']}"
        )
    lines.extend(
        [
            "",
            "## Review Priorities",
            f"- Under-annotated questions: `{payload['under_annotated_questions']}`",
            f"- Normalization risk questions: `{payload['normalization_risk_questions']}`",
            f"- Part-taxonomy risk questions: `{payload['questions_with_part_taxonomy_risk']}`",
            f"- Matter-domain risk questions: `{payload['questions_with_matter_domain_risk']}`",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_validation_markdown(
    report: Temperance141160ValidationReport,
    output_path: Path,
) -> None:
    lines = [
        "# Temperance 141-160 Validation",
        "",
        f"- status: `{report.status}`",
        f"- questions: `{report.question_count}`",
        f"- passages: `{report.passage_count}`",
        f"- reviewed annotations: `{report.reviewed_annotation_count}`",
        f"- reviewed doctrinal edges: `{report.reviewed_doctrinal_edge_count}`",
        (
            "- reviewed structural-editorial correspondences: "
            f"`{report.reviewed_structural_editorial_count}`"
        ),
        f"- candidate mentions: `{report.candidate_mention_count}`",
        f"- candidate relation proposals: `{report.candidate_relation_count}`",
        f"- integral-part relations: `{report.integral_part_relation_count}`",
        f"- subjective-part relations: `{report.subjective_part_relation_count}`",
        f"- potential-part relations: `{report.potential_part_relation_count}`",
        f"- food-related relations: `{report.food_related_relation_count}`",
        f"- drink-related relations: `{report.drink_related_relation_count}`",
        f"- sex-related relations: `{report.sex_related_relation_count}`",
        f"- continence/incontinence relations: `{report.continence_incontinence_relation_count}`",
        f"- meekness/anger relations: `{report.meekness_anger_relation_count}`",
        f"- clemency/cruelty relations: `{report.clemency_cruelty_relation_count}`",
        f"- modesty-general relations: `{report.modesty_general_relation_count}`",
        f"- temperance phase-1 synthesis nodes: `{report.temperance_phase1_synthesis_node_count}`",
        f"- temperance phase-1 synthesis edges: `{report.temperance_phase1_synthesis_edge_count}`",
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
    coverage_payload: dict[str, Any],
    synthesis_summary: dict[str, int],
    output_path: Path,
) -> None:
    summary = coverage_payload["summary"]
    lines = [
        "# Temperance Phase-1 Synthesis",
        "",
        (
            "The temperance phase-1 synthesis is a controlled view over the "
            "reviewed doctrinal material for `II-II qq. 141-160`."
        ),
        "Candidate artifacts are excluded from the default synthesis exports.",
        "",
        "## Summary",
        f"- doctrinal synthesis nodes: `{synthesis_summary['nodes']}`",
        f"- doctrinal synthesis edges: `{synthesis_summary['edges']}`",
        f"- doctrinal annotations feeding the tract: `{summary['reviewed_annotation_count']}`",
        f"- integral-part edges: `{summary['integral_part_relation_count']}`",
        f"- subjective-part edges: `{summary['subjective_part_relation_count']}`",
        f"- potential-part edges: `{summary['potential_part_relation_count']}`",
        "",
        "## Output Files",
        "- `data/processed/temperance_phase1_synthesis_nodes.csv`",
        "- `data/processed/temperance_phase1_synthesis_edges.csv`",
        "- `data/processed/temperance_phase1_synthesis.graphml`",
        "- `data/processed/temperance_phase1_synthesis_with_editorial.graphml`",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]
