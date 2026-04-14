from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Literal, TypeVar, cast

from pydantic import BaseModel

from ..models import (
    ArticleRecord,
    CandidateValidationReport,
    CorpusArticleManifestRecord,
    CorpusCandidateMentionRecord,
    CorpusCandidateRelationProposalRecord,
    CorpusConceptRecord,
    CorpusQuestionManifestRecord,
    ParseLogRecord,
    QuestionRecord,
    SegmentRecord,
)
from ..utils.jsonl import load_jsonl
from ..utils.paths import CANDIDATE_DIR, GOLD_DIR, INTERIM_DIR, PROCESSED_DIR, REPO_ROOT
from ..utils.segments import DISALLOWED_PASSAGE_ID_RE

ModelT = TypeVar("ModelT", bound=BaseModel)

REVIEWED_ANNOTATION_FILES = (
    GOLD_DIR / "pilot_reviewed_doctrinal_annotations.jsonl",
    GOLD_DIR / "pilot_reviewed_structural_annotations.jsonl",
    GOLD_DIR / "prudence_reviewed_doctrinal_annotations.jsonl",
    GOLD_DIR / "prudence_reviewed_structural_editorial_annotations.jsonl",
    GOLD_DIR / "theological_virtues_reviewed_doctrinal_annotations.jsonl",
    GOLD_DIR / "theological_virtues_reviewed_structural_editorial_annotations.jsonl",
)

REVIEWED_EDGE_FILES = (
    PROCESSED_DIR / "pilot_doctrinal_edges.jsonl",
    PROCESSED_DIR / "prudence_reviewed_doctrinal_edges.jsonl",
    PROCESSED_DIR / "theological_virtues_reviewed_doctrinal_edges.jsonl",
)
SCANNED_EXPORT_SUFFIXES = {".jsonl", ".json", ".csv", ".graphml"}
EXCLUDED_SCAN_PATHS = {
    PROCESSED_DIR / "candidate_validation_report.json",
}


def build_corpus_reports() -> dict[str, int | str]:
    """Build corpus coverage/audit and candidate validation outputs."""

    question_rows = _load_csv_records(
        PROCESSED_DIR / "question_index.csv",
        CorpusQuestionManifestRecord,
    )
    article_rows = _load_csv_records(
        PROCESSED_DIR / "article_index.csv",
        CorpusArticleManifestRecord,
    )
    log_rows = _load_records(PROCESSED_DIR / "ingestion_log.jsonl", ParseLogRecord)
    candidate_mentions = _load_records(
        CANDIDATE_DIR / "corpus_candidate_mentions.jsonl",
        CorpusCandidateMentionRecord,
    )
    candidate_relations = _load_records(
        CANDIDATE_DIR / "corpus_candidate_relation_proposals.jsonl",
        CorpusCandidateRelationProposalRecord,
    )
    registry = {
        record.concept_id: record
        for record in _load_records(
            GOLD_DIR / "corpus_concept_registry.jsonl",
            CorpusConceptRecord,
        )
    }
    questions = {
        record.question_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_questions.jsonl", QuestionRecord)
    }
    articles = {
        record.article_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_articles.jsonl", ArticleRecord)
    }
    passages = {
        record.segment_id: record
        for record in _load_records(INTERIM_DIR / "summa_moral_segments.jsonl", SegmentRecord)
    }

    coverage_payload = build_coverage_report(
        question_rows=question_rows,
        article_rows=article_rows,
        log_rows=log_rows,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
        passages=passages,
    )
    (PROCESSED_DIR / "coverage_report.json").write_text(
        json.dumps(coverage_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    write_coverage_summary(coverage_payload, REPO_ROOT / "docs" / "coverage_summary.md")

    validation_report = validate_candidate_artifacts(
        question_rows=question_rows,
        article_rows=article_rows,
        candidate_mentions=candidate_mentions,
        candidate_relations=candidate_relations,
        registry=registry,
        questions=questions,
        articles=articles,
        passages=passages,
        coverage_payload=coverage_payload,
    )
    (PROCESSED_DIR / "candidate_validation_report.json").write_text(
        json.dumps(
            validation_report.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    write_candidate_validation_summary(
        validation_report,
        REPO_ROOT / "docs" / "candidate_validation_summary.md",
    )
    return {
        "questions_expected": coverage_payload["summary"]["questions_expected"],
        "questions_parsed": coverage_payload["summary"]["questions_parsed"],
        "articles_expected": coverage_payload["summary"]["articles_expected"],
        "articles_parsed": coverage_payload["summary"]["articles_parsed"],
        "passages_parsed": coverage_payload["summary"]["passages_parsed"],
        "reviewed_annotations": coverage_payload["summary"]["reviewed_annotations"],
        "candidate_mentions": coverage_payload["summary"]["candidate_mentions"],
        "candidate_relation_proposals": coverage_payload["summary"]["candidate_relation_proposals"],
        "validation_status": validation_report.status,
    }


def build_coverage_report(
    *,
    question_rows: list[CorpusQuestionManifestRecord],
    article_rows: list[CorpusArticleManifestRecord],
    log_rows: list[ParseLogRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    passages: dict[str, SegmentRecord],
) -> dict[str, Any]:
    """Build a machine-readable corpus coverage and parse audit report."""

    reviewed_annotations = load_reviewed_annotation_rows()
    question_reviewed_counts: Counter[str] = Counter()
    article_reviewed_counts: Counter[str] = Counter()
    for row in reviewed_annotations:
        passage = passages.get(str(row["source_passage_id"]))
        if passage is None:
            continue
        question_reviewed_counts[passage.question_id] += 1
        article_reviewed_counts[passage.article_id] += 1

    question_candidate_mention_counts: Counter[str] = Counter()
    question_candidate_relation_counts: Counter[str] = Counter()
    article_candidate_mention_counts: Counter[str] = Counter()
    article_candidate_relation_counts: Counter[str] = Counter()
    ambiguity_counts: Counter[str] = Counter()

    for mention in candidate_mentions:
        passage = passages[mention.passage_id]
        question_candidate_mention_counts[passage.question_id] += 1
        article_candidate_mention_counts[passage.article_id] += 1
        if mention.ambiguity_flag:
            ambiguity_counts[passage.question_id] += 1

    for proposal in candidate_relations:
        passage = passages[proposal.source_passage_id]
        question_candidate_relation_counts[passage.question_id] += 1
        article_candidate_relation_counts[passage.article_id] += 1

    article_warning_counts: Counter[str] = Counter()
    for log_row in log_rows:
        if log_row.article_id is not None:
            article_warning_counts[log_row.article_id] += 1

    question_entries: list[dict[str, Any]] = []
    for question_row in question_rows:
        question_entries.append(
            {
                **question_row.model_dump(mode="json"),
                "reviewed_annotation_count": question_reviewed_counts[question_row.question_id],
                "candidate_mention_count": question_candidate_mention_counts[
                    question_row.question_id
                ],
                "candidate_relation_count": question_candidate_relation_counts[
                    question_row.question_id
                ],
                "ambiguity_count": ambiguity_counts[question_row.question_id],
            }
        )

    article_entries: list[dict[str, Any]] = []
    for article_row in article_rows:
        article_entries.append(
            {
                **article_row.model_dump(mode="json"),
                "reviewed_annotation_count": article_reviewed_counts[article_row.article_id],
                "candidate_mention_count": article_candidate_mention_counts[
                    article_row.article_id
                ],
                "candidate_relation_count": article_candidate_relation_counts[
                    article_row.article_id
                ],
                "warning_count": article_warning_counts[article_row.article_id],
            }
        )

    warning_counts = Counter(log_row.log_type for log_row in log_rows if log_row.level == "warning")
    error_counts = Counter(log_row.log_type for log_row in log_rows if log_row.level == "error")
    repeated_uncertainty = []
    by_source_url: dict[str, list[ParseLogRecord]] = defaultdict(list)
    for log_row in log_rows:
        by_source_url[log_row.source_url].append(log_row)
    for source_url, rows in sorted(by_source_url.items()):
        if len(rows) < 2:
            continue
        repeated_uncertainty.append(
            {
                "source_url": source_url,
                "count": len(rows),
                "warning_types": sorted({row.log_type for row in rows}),
            }
        )

    segment_count_distribution = Counter(row.segment_count for row in article_rows)
    suspiciously_short_articles = [
        row.article_id for row in article_rows if row.suspiciously_short
    ]
    missing_segment_articles = [
        {
            "article_id": row.article_id,
            "missing_segment_types": row.missing_segment_types,
        }
        for row in article_rows
        if row.missing_segment_types
    ]
    missing_articles = [
        {
            "question_id": row.question_id,
            "missing_article_numbers": row.missing_article_numbers,
        }
        for row in question_rows
        if row.missing_article_numbers
    ]
    under_reviewed_clusters = identify_under_reviewed_clusters(question_entries)

    return {
        "summary": {
            "questions_expected": len(
                [row for row in question_rows if row.parse_status != "excluded"]
            ),
            "questions_parsed": len(
                [row for row in question_rows if row.parse_status in {"ok", "partial"}]
            ),
            "articles_expected": len(article_rows),
            "articles_parsed": len(
                [row for row in article_rows if row.parse_status in {"ok", "partial"}]
            ),
            "passages_parsed": len(passages),
            "reviewed_annotations": len(reviewed_annotations),
            "candidate_mentions": len(candidate_mentions),
            "candidate_relation_proposals": len(candidate_relations),
            "parse_failure_count": sum(
                1 for row in question_rows if row.parse_status == "failed"
            ),
            "ambiguity_count": sum(1 for mention in candidate_mentions if mention.ambiguity_flag),
        },
        "questions": question_entries,
        "articles": article_entries,
        "missing_articles": missing_articles,
        "suspiciously_short_articles": suspiciously_short_articles,
        "articles_missing_expected_segment_types": missing_segment_articles,
        "segment_count_distribution": dict(sorted(segment_count_distribution.items())),
        "parse_warnings_grouped_by_type": dict(sorted(warning_counts.items())),
        "parse_errors_grouped_by_type": dict(sorted(error_counts.items())),
        "source_files_with_repeated_parser_uncertainty": repeated_uncertainty,
        "under_reviewed_question_clusters": under_reviewed_clusters,
    }


def validate_candidate_artifacts(
    *,
    question_rows: list[CorpusQuestionManifestRecord],
    article_rows: list[CorpusArticleManifestRecord],
    candidate_mentions: list[CorpusCandidateMentionRecord],
    candidate_relations: list[CorpusCandidateRelationProposalRecord],
    registry: dict[str, CorpusConceptRecord],
    questions: dict[str, QuestionRecord],
    articles: dict[str, ArticleRecord],
    passages: dict[str, SegmentRecord],
    coverage_payload: dict[str, Any],
) -> CandidateValidationReport:
    """Validate candidate artifacts and reviewed/candidate separation."""

    warnings: list[str] = []
    manifest_warnings: list[str] = []
    warnings.extend(scan_exported_artifacts_for_disallowed_passage_refs())

    for mention in candidate_mentions:
        if mention.passage_id not in passages:
            warnings.append(f"Candidate mention references missing passage: {mention.candidate_id}")
        if mention.proposed_concept_id and mention.proposed_concept_id not in registry:
            warnings.append(f"Candidate mention references unknown concept: {mention.candidate_id}")
        if mention.proposed_concept_ids:
            for concept_id in mention.proposed_concept_ids:
                if concept_id not in registry:
                    warnings.append(
                        "Candidate mention option references "
                        f"unknown concept: {mention.candidate_id}"
                    )

    valid_structural_ids = set(questions) | set(articles)
    for proposal in candidate_relations:
        if proposal.source_passage_id not in passages:
            warnings.append(
                f"Candidate relation references missing passage: {proposal.proposal_id}"
            )
        for candidate_id in proposal.support_candidate_ids:
            if not any(mention.candidate_id == candidate_id for mention in candidate_mentions):
                warnings.append(
                    "Candidate relation references missing "
                    f"support candidate: {proposal.proposal_id}"
                )
        for node_id in (proposal.subject_id, proposal.object_id):
            if node_id.startswith("concept.") and node_id not in registry:
                warnings.append(
                    "Candidate relation references unknown "
                    f"concept: {proposal.proposal_id}"
                )
            if node_id.startswith("st.") and node_id not in valid_structural_ids:
                warnings.append(
                    f"Candidate relation references unknown structural id: {proposal.proposal_id}"
                )

    if coverage_payload["summary"]["questions_expected"] != 296:
        manifest_warnings.append(
            "Coverage report question count drifted "
            "from expected scope of 296."
        )
    if coverage_payload["summary"]["articles_expected"] != len(article_rows):
        manifest_warnings.append(
            "Coverage report article count does not match article index."
        )
    if (
        coverage_payload["summary"]["questions_parsed"]
        > coverage_payload["summary"]["questions_expected"]
    ):
        manifest_warnings.append("Parsed question count exceeded expected question count.")

    excluded_question_ids = {
        row.question_id for row in question_rows if row.parse_status == "excluded"
    }
    if excluded_question_ids & set(questions):
        manifest_warnings.append("Excluded questions leaked into interim structural records.")
    for passage in passages.values():
        if passage.part_id == "ii-ii" and passage.question_number >= 183:
            manifest_warnings.append("Excluded II-II question leaked into interim passages.")
            break

    reviewed_edge_rows = load_reviewed_edge_rows()
    if any("candidate." in json.dumps(row, ensure_ascii=False) for row in reviewed_edge_rows):
        warnings.append("Candidate identifiers leaked into reviewed edge exports.")

    status = "warning" if warnings or manifest_warnings else "ok"
    return CandidateValidationReport(
        status=cast(Literal["ok", "warning"], status),
        candidate_mention_count=len(candidate_mentions),
        candidate_relation_count=len(candidate_relations),
        unresolved_warnings=sorted(set(warnings)),
        manifest_consistency_warnings=sorted(set(manifest_warnings)),
    )


def scan_exported_artifacts_for_disallowed_passage_refs() -> list[str]:
    warnings: list[str] = []
    for base_dir in (INTERIM_DIR, CANDIDATE_DIR, GOLD_DIR, PROCESSED_DIR):
        for path in sorted(base_dir.rglob("*")):
            if not path.is_file() or path.suffix not in SCANNED_EXPORT_SUFFIXES:
                continue
            if path in EXCLUDED_SCAN_PATHS:
                continue
            match = DISALLOWED_PASSAGE_ID_RE.search(path.read_text(encoding="utf-8"))
            if match is None:
                continue
            warnings.append(
                f"Disallowed objection/sed-contra passage id found in "
                f"{path.relative_to(REPO_ROOT)}: {match.group(0)}"
            )
    return warnings


def identify_under_reviewed_clusters(
    question_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Identify contiguous question bands with candidates but no reviewed coverage."""

    included = [
        entry
        for entry in question_entries
        if entry["parse_status"] != "excluded"
    ]
    included.sort(key=lambda item: (item["part_id"], item["question_number"]))
    clusters: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    for entry in included:
        is_under_reviewed = (
            entry["reviewed_annotation_count"] == 0
            and (
                entry["candidate_mention_count"] > 0
                or entry["candidate_relation_count"] > 0
            )
        )
        if not is_under_reviewed:
            if current:
                clusters.append(summarize_cluster(current))
                current = []
            continue
        if current and (
            current[-1]["part_id"] != entry["part_id"]
            or current[-1]["question_number"] + 1 != entry["question_number"]
        ):
            clusters.append(summarize_cluster(current))
            current = []
        current.append(entry)
    if current:
        clusters.append(summarize_cluster(current))
    return clusters[:10]


def summarize_cluster(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "part_id": entries[0]["part_id"],
        "question_range": [entries[0]["question_number"], entries[-1]["question_number"]],
        "question_ids": [entry["question_id"] for entry in entries],
        "candidate_mentions": sum(entry["candidate_mention_count"] for entry in entries),
        "candidate_relations": sum(entry["candidate_relation_count"] for entry in entries),
        "parsed_passages": sum(entry["parsed_passage_count"] for entry in entries),
    }


def write_coverage_summary(payload: dict[str, Any], path: Path) -> None:
    """Write a concise human-readable coverage summary."""

    summary = payload["summary"]
    lines = [
        "# Coverage Summary",
        "",
        f"- questions expected: `{summary['questions_expected']}`",
        f"- questions parsed: `{summary['questions_parsed']}`",
        f"- articles expected: `{summary['articles_expected']}`",
        f"- articles parsed: `{summary['articles_parsed']}`",
        f"- passages parsed: `{summary['passages_parsed']}`",
        f"- reviewed annotations: `{summary['reviewed_annotations']}`",
        f"- candidate mentions: `{summary['candidate_mentions']}`",
        f"- candidate relation proposals: `{summary['candidate_relation_proposals']}`",
        f"- parse failure count: `{summary['parse_failure_count']}`",
        f"- ambiguity count: `{summary['ambiguity_count']}`",
        "",
        "## Parse Warnings By Type",
    ]
    for warning_type, count in payload["parse_warnings_grouped_by_type"].items():
        lines.append(f"- `{warning_type}`: `{count}`")
    lines.extend(["", "## Top Under-Reviewed Question Clusters"])
    for cluster in payload["under_reviewed_question_clusters"]:
        start, end = cluster["question_range"]
        lines.append(
            f"- `{cluster['part_id']}` qq.`{start}`–`{end}`: "
            f"{cluster['candidate_mentions']} mentions, "
            f"{cluster['candidate_relations']} relation proposals, "
            f"{cluster['parsed_passages']} passages"
        )
    lines.extend(["", "## Repeated Parser Uncertainty"])
    for row in payload["source_files_with_repeated_parser_uncertainty"][:12]:
        lines.append(
            f"- `{row['source_url']}`: `{row['count']}` warnings/errors "
            f"across {', '.join(row['warning_types'])}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_candidate_validation_summary(
    report: CandidateValidationReport,
    path: Path,
) -> None:
    """Write a short markdown summary for candidate validation."""

    lines = [
        "# Candidate Validation Summary",
        "",
        f"- status: `{report.status}`",
        f"- candidate mentions: `{report.candidate_mention_count}`",
        f"- candidate relation proposals: `{report.candidate_relation_count}`",
        f"- unresolved warnings: `{len(report.unresolved_warnings)}`",
        f"- manifest consistency warnings: `{len(report.manifest_consistency_warnings)}`",
    ]
    if report.unresolved_warnings:
        lines.extend(["", "## Warnings", *[f"- `{item}`" for item in report.unresolved_warnings]])
    if report.manifest_consistency_warnings:
        lines.extend(
            [
                "",
                "## Manifest Consistency",
                *[f"- `{item}`" for item in report.manifest_consistency_warnings],
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_reviewed_annotation_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in REVIEWED_ANNOTATION_FILES:
        if not path.exists():
            continue
        layer_name = path.stem
        for payload in load_jsonl(path):
            rows.append({**payload, "review_layer": layer_name})
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[str(row["annotation_id"])] = row
    return list(sorted(deduped.values(), key=lambda item: str(item["annotation_id"])))


def load_reviewed_edge_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in REVIEWED_EDGE_FILES:
        if not path.exists():
            continue
        layer_name = path.stem
        for payload in load_jsonl(path):
            rows.append({**payload, "review_layer": layer_name})
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[str(row["edge_id"])] = row
    return list(sorted(deduped.values(), key=lambda item: str(item["edge_id"])))


def _load_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    return [model_cls.model_validate(payload) for payload in load_jsonl(path)]


def _load_csv_records(path: Path, model_cls: type[ModelT]) -> list[ModelT]:
    with path.open("r", encoding="utf-8") as handle:
        rows: list[ModelT] = []
        for payload in csv.DictReader(handle):
            for field_name in (
                "missing_article_numbers",
                "segment_types",
                "missing_segment_types",
                "warning_types",
            ):
                if field_name in payload and payload[field_name]:
                    payload[field_name] = json.loads(payload[field_name])
            rows.append(model_cls.model_validate(payload))
        return rows
