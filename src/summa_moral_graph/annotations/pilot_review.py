from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from ..app.pilot import PilotAppBundle, load_pilot_bundle
from ..utils.paths import PROCESSED_DIR, repo_relative_path_str


def build_pilot_review_artifacts(question_id: str | None = None) -> dict[str, str]:
    """Build pilot review-queue artifacts and one concrete question packet."""

    bundle = load_pilot_bundle()
    all_annotations = [*bundle.structural_annotations, *bundle.doctrinal_annotations]
    annotation_counts = Counter(record.source_passage_id for record in all_annotations)
    under_annotated_passages = [
        {
            "passage_id": passage.segment_id,
            "citation_label": passage.citation_label,
            "annotation_count": annotation_counts[passage.segment_id],
        }
        for passage in sorted(
            bundle.passages.values(),
            key=lambda record: (
                annotation_counts[record.segment_id],
                record.part_id,
                record.question_number,
                record.article_number,
            ),
        )
        if annotation_counts[passage.segment_id] <= 1
    ][:40]
    concepts_with_many_aliases = [
        {
            "concept_id": record.concept_id,
            "label": record.canonical_label,
            "alias_count": len(record.aliases),
        }
        for record in sorted(
            bundle.registry.values(),
            key=lambda item: (-len(item.aliases), item.canonical_label),
        )
        if len(record.aliases) >= 3
    ]
    low_confidence_annotations = [
        record.model_dump(mode="json")
        for record in sorted(
            all_annotations,
            key=lambda item: (item.confidence, item.annotation_id),
        )
        if record.confidence < 0.9
    ]

    target_question_id = question_id or choose_review_question(bundle)
    packet_path = build_question_review_packet(bundle, target_question_id)
    queue_payload = {
        "under_annotated_passages": under_annotated_passages,
        "concepts_with_many_aliases": concepts_with_many_aliases,
        "low_confidence_annotations": low_confidence_annotations,
        "suggested_question_packet": target_question_id,
        "packet_path": repo_relative_path_str(packet_path),
    }
    queue_path = PROCESSED_DIR / "pilot_review_queue.json"
    queue_path.write_text(
        json.dumps(queue_payload, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return {
        "queue_path": repo_relative_path_str(queue_path),
        "packet_path": repo_relative_path_str(packet_path),
    }


def choose_review_question(bundle: PilotAppBundle) -> str:
    """Choose the next pilot question with the lowest annotation density."""

    counts = Counter(
        bundle.passages[record.source_passage_id].question_id
        for record in [*bundle.structural_annotations, *bundle.doctrinal_annotations]
    )
    passage_counts = Counter(record.question_id for record in bundle.passages.values())
    questions = sorted(
        bundle.questions.values(),
        key=lambda record: (
            counts[record.question_id] / max(1, passage_counts[record.question_id]),
            record.question_id,
        ),
    )
    return questions[0].question_id


def build_question_review_packet(bundle: PilotAppBundle, question_id: str) -> Path:
    """Write a markdown review packet for a selected pilot question."""

    question = bundle.questions[question_id]
    question_articles = [
        record
        for record in bundle.articles.values()
        if record.question_id == question.question_id
    ]
    question_passages = [
        record
        for record in bundle.passages.values()
        if record.question_id == question.question_id
    ]
    question_annotations = [
        record
        for record in [*bundle.structural_annotations, *bundle.doctrinal_annotations]
        if bundle.passages[record.source_passage_id].question_id == question.question_id
    ]
    lines = [
        f"# Pilot Review Packet: {question.part_id.upper()} q.{question.question_number}",
        "",
        f"Question title: {question.question_title}",
        f"Article count: {len(question_articles)}",
        f"Passage count: {len(question_passages)}",
        f"Reviewed annotations: {len(question_annotations)}",
        "",
        "## Articles",
    ]
    for article in sorted(question_articles, key=lambda item: item.article_number):
        lines.append(f"- {article.citation_label}: {article.article_title}")
    lines.extend(["", "## Respondeo Passages"])
    for passage in sorted(
        question_passages,
        key=lambda item: (item.article_number, item.segment_id),
    ):
        if passage.segment_type != "resp":
            continue
        lines.append(f"- `{passage.segment_id}`: {passage.text[:280]}...")
    lines.extend(["", "## Low-Confidence Reviewed Annotations"])
    low_confidence = sorted(
        [record for record in question_annotations if record.confidence < 0.9],
        key=lambda item: (item.confidence, item.annotation_id),
    )
    if low_confidence:
        for record in low_confidence:
            lines.append(
                f"- `{record.annotation_id}` ({record.confidence:.2f}): "
                f"{record.subject_label} {record.relation_type} {record.object_label}"
            )
    else:
        lines.append("- None below the current low-confidence threshold.")
    lines.extend(
        [
            "",
            "## Review Prompts",
            (
                "- Check whether article-level `treated_in` annotations are still "
                "appropriately conservative."
            ),
            (
                "- Confirm that doctrinal relations in this question are directly "
                "supported by the cited respondeo passages."
            ),
            (
                "- Add new reviewed relations only where the passage wording, not "
                "outside synthesis, carries the claim."
            ),
        ]
    )

    packet_dir = PROCESSED_DIR / "review_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    for existing in packet_dir.glob("st_*_review_packet.md"):
        existing.unlink()
    packet_path = packet_dir / f"{question.question_id.replace('.', '_')}_review_packet.md"
    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return packet_path
