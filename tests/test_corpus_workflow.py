from __future__ import annotations

import csv
import json
from pathlib import Path

from summa_moral_graph.annotations.corpus import (
    CorpusContext,
    build_candidate_mentions,
    build_candidate_relation_proposals,
    build_corpus_registry,
)
from summa_moral_graph.models import ArticleRecord, QuestionRecord, SegmentRecord
from summa_moral_graph.utils.ids import (
    article_citation_label,
    article_id,
    question_id,
    segment_citation_label,
    segment_id,
)
from summa_moral_graph.validation.corpus import build_corpus_reports


def test_corpus_manifest_integrity() -> None:
    manifest = json.loads(Path("data/processed/corpus_manifest.json").read_text(encoding="utf-8"))
    question_rows = list(csv.DictReader(Path("data/processed/question_index.csv").open()))
    article_rows = list(csv.DictReader(Path("data/processed/article_index.csv").open()))

    assert manifest["counts"] == {
        "questions_expected": 296,
        "questions_parsed": 296,
        "articles_expected": 1482,
        "articles_parsed": 1482,
        "passages_parsed": 6032,
    }
    assert len(question_rows) == 303
    assert len(article_rows) == 1482

    excluded_ids = [
        row["question_id"]
        for row in question_rows
        if row["parse_status"] == "excluded"
    ]
    assert excluded_ids == [
        "st.ii-ii.q183",
        "st.ii-ii.q184",
        "st.ii-ii.q185",
        "st.ii-ii.q186",
        "st.ii-ii.q187",
        "st.ii-ii.q188",
        "st.ii-ii.q189",
    ]


def test_build_corpus_reports_is_ok() -> None:
    summary = build_corpus_reports()
    validation = json.loads(
        Path("data/processed/candidate_validation_report.json").read_text(encoding="utf-8")
    )

    assert summary["questions_expected"] == 296
    assert summary["questions_parsed"] == 296
    assert summary["articles_expected"] == 1482
    assert summary["articles_parsed"] == 1482
    assert summary["passages_parsed"] == 6032
    assert summary["reviewed_annotations"] == 501
    assert summary["candidate_mentions"] == 25755
    assert summary["candidate_relation_proposals"] == 8977
    assert summary["validation_status"] == "ok"
    assert validation["status"] == "ok"
    assert validation["unresolved_warnings"] == []


def test_candidate_generation_on_synthetic_passage() -> None:
    registry = build_corpus_registry()

    question_identifier = question_id("ii-ii", 47)
    article_identifier = article_id(question_identifier, 1)
    passage_identifier = segment_id(article_identifier, "resp", None)
    text = "Prudence is perfected by the gift of counsel."

    question = QuestionRecord(
        question_id=question_identifier,
        part_id="ii-ii",
        question_number=47,
        question_title="Prudence",
        article_count=1,
        source_id="fixture",
        source_url="fixture://ii-ii-q47",
        source_part_url="fixture://ii-ii",
        hash="fixture-question",
    )
    article = ArticleRecord(
        article_id=article_identifier,
        question_id=question_identifier,
        part_id="ii-ii",
        question_number=47,
        article_number=1,
        article_title="Whether prudence is perfected by counsel",
        citation_label=article_citation_label("ii-ii", 47, 1),
        segment_ids=[passage_identifier],
        source_id="fixture",
        source_url="fixture://ii-ii-q47#a1",
        hash="fixture-article",
    )
    passage = SegmentRecord(
        segment_id=passage_identifier,
        article_id=article_identifier,
        question_id=question_identifier,
        part_id="ii-ii",
        question_number=47,
        question_title=question.question_title,
        article_number=1,
        article_title=article.article_title,
        segment_type="resp",
        segment_ordinal=None,
        citation_label=segment_citation_label("ii-ii", 47, 1, "resp", None),
        source_id="fixture",
        source_url="fixture://ii-ii-q47#a1-resp",
        text=text,
        char_count=len(text),
        hash="fixture-segment",
    )
    context = CorpusContext(
        questions={question_identifier: question},
        articles={article_identifier: article},
        passages={passage_identifier: passage},
    )

    mentions = build_candidate_mentions(context, registry)
    proposals = build_candidate_relation_proposals(context, registry, mentions)

    assert any(
        mention.proposed_concept_id == "concept.prudence"
        for mention in mentions
    )
    assert any(
        mention.proposed_concept_id == "concept.counsel_gift"
        for mention in mentions
    )
    assert any(
        proposal.relation_type == "perfected_by"
        and proposal.subject_id == "concept.prudence"
        and proposal.object_id == "concept.counsel_gift"
        for proposal in proposals
    )
    assert any(
        proposal.relation_type == "treated_in"
        and proposal.subject_id == article_identifier
        and proposal.object_id == "concept.prudence"
        for proposal in proposals
    )


def test_candidate_exports_remain_unreviewed() -> None:
    candidate_validation = json.loads(
        Path("data/processed/candidate_validation_report.json").read_text(encoding="utf-8")
    )
    assert candidate_validation["status"] == "ok"

    sample_mentions = [
        json.loads(line)
        for line in Path("data/candidate/corpus_candidate_mentions.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[:25]
    ]
    sample_relations = [
        json.loads(line)
        for line in Path("data/candidate/corpus_candidate_relation_proposals.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[:25]
    ]
    reviewed_edges = [
        json.loads(line)
        for line in Path("data/processed/pilot_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ] + [
        json.loads(line)
        for line in Path("data/processed/prudence_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ] + [
        json.loads(line)
        for line in Path("data/processed/theological_virtues_reviewed_doctrinal_edges.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert all(row["review_status"] == "unreviewed" for row in sample_mentions)
    assert all(row["review_status"] == "unreviewed" for row in sample_relations)
    assert all("candidate." not in json.dumps(edge, ensure_ascii=False) for edge in reviewed_edges)
