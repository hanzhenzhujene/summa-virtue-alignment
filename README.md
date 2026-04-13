# summa-moral-graph

`summa-moral-graph` is an evidence-first research workspace for the moral corpus of Thomas Aquinas's *Summa Theologiae*. The stable base layer is the full interim textual corpus for:

- `I-II, qq. 1–114`
- `II-II, qq. 1–182`

On top of that textual spine, the repo currently maintains three reviewed research overlays:

- a broader pilot vertical slice across `12` questions in `I-II` and `II-II`
- a tighter prudence tract block for `II-II, QQ. 47–56`
- a theological virtues block for `II-II, QQ. 1–46`
- a full-corpus candidate workflow for structural coverage, candidate mentions, candidate relations, and review packets

The repo does not claim that the reviewed graph is complete. It keeps structural, doctrinal, structural-editorial, and candidate layers separate so every exported edge stays inspectable.

## Pipeline Stages

1. raw source acquisition
2. structural parsing
3. canonical passage segmentation
4. reviewed and candidate annotation layers
5. graph export
6. Streamlit visualization

## Current Pilot Slice

The pilot slice currently covers:

- `I-II q.1`
- `I-II q.6`
- `I-II q.22`
- `I-II q.55`
- `I-II q.71`
- `I-II q.90`
- `I-II q.109`
- `II-II q.1`
- `II-II q.23`
- `II-II q.47`
- `II-II q.58`
- `II-II q.171`

Current pilot counts:

- `792` passages
- `66` registered concepts
- `187` reviewed annotations
- `29` doctrinal edges
- `253` structural edges

## Quickstart

Use Python `3.11+`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

make build-interim
make build-corpus
make validate-candidates
make build-pilot
make validate-pilot
make build-prudence
make build-theological-virtues
make test
```

If you want the full corpus workflow from textual spine through candidate review prep:

```bash
make build-interim
make validate-interim
make build-corpus
make validate-candidates
make review-corpus
```

Run the app:

```bash
make app
```

## Main Commands

```bash
summa-moral-graph build-interim
summa-moral-graph validate-interim
summa-moral-graph build-corpus
summa-moral-graph validate-candidates
summa-moral-graph build-pilot
summa-moral-graph validate-pilot
summa-moral-graph build-prudence
summa-moral-graph validate-prudence
summa-moral-graph build-theological-virtues
summa-moral-graph validate-theological-virtues
python scripts/build_corpus_workflow.py
python scripts/build_corpus_review_queue.py
python scripts/pilot_review_tools.py
python scripts/build_prudence_review_queue.py
python scripts/build_theological_virtues_review_queue.py
```

## Full-Corpus Workflow Artifacts

Structural coverage and audit:

- `data/processed/corpus_manifest.json`
- `data/processed/question_index.csv`
- `data/processed/article_index.csv`
- `data/processed/ingestion_log.jsonl`
- `data/processed/coverage_report.json`
- `docs/coverage_summary.md`

Corpus-scale candidate layer:

- `data/gold/corpus_concept_registry.jsonl`
- `data/gold/corpus_alias_overrides.yml`
- `data/candidate/corpus_candidate_mentions.jsonl`
- `data/candidate/corpus_candidate_relation_proposals.jsonl`
- `data/processed/candidate_validation_report.json`
- `docs/candidate_validation_summary.md`

Human review workflow:

- `data/processed/corpus_review_queue.json`
- `data/processed/review_packets/st_i-ii_q100_corpus_review_packet.md`
- `docs/full_corpus_workflow.md`
- `docs/review_queue_guide.md`

## Key Pilot Artifacts

Reviewed registry and annotations:

- `data/gold/pilot_concept_registry.jsonl`
- `data/gold/pilot_reviewed_structural_annotations.jsonl`
- `data/gold/pilot_reviewed_doctrinal_annotations.jsonl`
- `data/gold/pilot_alias_overrides.yml`

Processed exports:

- `data/processed/pilot_nodes.csv`
- `data/processed/pilot_structural_edges.jsonl`
- `data/processed/pilot_doctrinal_edges.jsonl`
- `data/processed/pilot_doctrinal.graphml`
- `data/processed/pilot_combined.graphml`
- `data/processed/validation_report.json`
- `data/processed/pilot_review_queue.json`
- `data/processed/review_packets/`

## Key Prudence Artifacts

The prudence tract remains separate and intact:

- `data/gold/prudence_reviewed_concepts.jsonl`
- `data/gold/prudence_reviewed_doctrinal_annotations.jsonl`
- `data/gold/prudence_reviewed_structural_editorial_annotations.jsonl`
- `data/candidate/prudence_candidate_mentions.jsonl`
- `data/candidate/prudence_candidate_relation_proposals.jsonl`
- `data/processed/prudence_reviewed_doctrinal_edges.jsonl`
- `data/processed/prudence_reviewed_structural_editorial_edges.jsonl`
- `data/processed/prudence_structural_edges.jsonl`
- `data/processed/prudence_coverage.json`
- `data/processed/prudence_validation_report.json`

## Key Theological Virtues Artifacts

The theological virtues tract is reviewed separately for `II-II, QQ. 1–46`:

- `data/gold/theological_virtues_reviewed_concepts.jsonl`
- `data/gold/theological_virtues_reviewed_doctrinal_annotations.jsonl`
- `data/gold/theological_virtues_reviewed_structural_editorial_annotations.jsonl`
- `data/processed/theological_virtues_reviewed_doctrinal_edges.jsonl`
- `data/processed/theological_virtues_reviewed_structural_editorial_edges.jsonl`
- `data/processed/theological_virtues_structural_edges.jsonl`
- `data/processed/theological_virtues_coverage.json`
- `data/processed/theological_virtues_validation_report.json`
- `data/processed/theological_virtues_review_queue.json`

## Notes

- Stable segment ids remain the canonical evidence anchors.
- The pilot graph distinguishes structural edges from doctrinal edges in code, exports, validation, and app filters.
- Alias matching is conservative and hand-auditable; ambiguous labels are declared explicitly instead of auto-collapsed.
- Default concept and graph views emphasize evidence-backed doctrinal edges first.
- Prudence part-taxonomy relations remain explicitly typed as `integral_part_of`, `subjective_part_of`, and `potential_part_of`.
- Candidate data stays separate and is never promoted automatically.
- The full-corpus candidate layer is for review support, not for doctrinal completeness claims.
