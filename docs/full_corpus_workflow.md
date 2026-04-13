# Full Corpus Workflow

## What This Phase Adds

The repo now supports the entire moral corpus structurally:

- `I-II, qq. 1–114`
- `II-II, qq. 1–182`

This is a research workflow expansion, not a claim of full doctrinal annotation.

The core distinction is:

- parsed: the textual spine and structural coverage exist
- reviewed: a human has approved the annotation or edge
- candidate: the repo proposes something for review, but it is not yet a graph fact

## Build Order

Run the workflow in this order:

```bash
make build-interim
make validate-interim
make build-corpus
make validate-candidates
make review-corpus
```

Optional reviewed overlays remain separate:

```bash
make build-pilot
make build-prudence
```

## What `build-corpus` Produces

Structural coverage:

- `data/processed/corpus_manifest.json`
- `data/processed/question_index.csv`
- `data/processed/article_index.csv`
- `data/processed/ingestion_log.jsonl`

Candidate workflow:

- `data/gold/corpus_concept_registry.jsonl`
- `data/candidate/corpus_candidate_mentions.jsonl`
- `data/candidate/corpus_candidate_relation_proposals.jsonl`

Audit and review support:

- `data/processed/coverage_report.json`
- `data/processed/candidate_validation_report.json`
- `data/processed/corpus_review_queue.json`
- `data/processed/review_packets/`

## Reviewed vs Candidate Discipline

Reviewed artifacts:

- reviewed pilot annotations and edges
- reviewed prudence annotations and edges

Candidate artifacts:

- corpus candidate mentions
- corpus candidate relation proposals
- review packets and queue summaries

Candidate artifacts must not be used as reviewed doctrinal exports unless a human explicitly converts them into reviewed annotation records.

## Structural Coverage Semantics

`question_index.csv` and `article_index.csv` distinguish:

- `ok`
- `partial`
- `failed`
- `excluded`

`partial` does not mean unusable. It means the parser found something worth human attention, such as:

- missing expected segment types
- repeated label normalization
- suspiciously short article output

## How To Continue Review Safely

1. choose a question or cluster from `docs/coverage_summary.md`
2. inspect the matching review packet
3. reject ambiguous concept matches first
4. promote only the smallest defensible reviewed annotations
5. regenerate reviewed exports without touching candidate source files

The workflow is intentionally asymmetric: the corpus can be broadly parsed long before it is broadly reviewed.
