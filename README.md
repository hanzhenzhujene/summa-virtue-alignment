# Summa Virtutum

An interactive map of Thomas Aquinas's moral corpus.

This repository turns Aquinas's moral corpus into something you can read, inspect, and navigate:
open a concept, move into its supporting passages, and then step outward into the graph without
losing evidence.

## Open The Dashboard

| GitHub | Run locally | Deploy from GitHub | Docs |
| --- | --- | --- | --- |
| **[github.com/hanzhenzhujene/summa-moral-graph](https://github.com/hanzhenzhujene/summa-moral-graph)** | [`make app`](#run-the-dashboard) | [Streamlit Community Cloud](#deploy-from-github-with-streamlit) | [Dashboard audit](./docs/dashboard_interaction_audit.md) |

Author: [Jenny Zhu](https://www.linkedin.com/in/hanzhen-zhu/)

## What This Project Is

`summa-moral-graph` is an evidence-first research workspace and Streamlit dashboard for the
moral-philosophical corpus of Thomas Aquinas's *Summa Theologiae*.

It is built to help a reader move through four connected layers without losing textual grounding:

1. concept
2. relation
3. passage
4. graph

The project is not a vague summary graph. It preserves segment-level evidence, stable ids, and
clear separation between reviewed doctrine, editorial correspondences, structural links, and
candidate review material.

## What You Can Do In The Dashboard

The unified Streamlit app lets you:

- start from a concept, passage, tract scope, or graph view
- move from concept pages to supporting passages and back again
- inspect reviewed doctrinal edges first, with editorial and candidate layers kept visibly separate
- open local concept maps and broader overall maps
- browse tract overlays without losing evidence traceability
- export the current graph slice or dashboard data directly from the UI

Primary views in the app:

- `Home`
- `Concept Explorer`
- `Passage Explorer`
- `Overall Map`
- `Stats / Audit`

## Run The Dashboard

Use Python `3.12` if possible.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src ./.venv/bin/streamlit run streamlit_app.py
```

Or:

```bash
make app
```

Then open:

- [http://localhost:8501](http://localhost:8501)

The Streamlit entrypoint is:

- [`streamlit_app.py`](./streamlit_app.py)

If you just want the app and not the full maintainer workflow, this is the only command path you
need.

## Deploy From GitHub With Streamlit

If you want the app hosted publicly from GitHub, the right target is **Streamlit Community Cloud**,
not GitHub Pages.

Why:

- GitHub Pages is for static sites
- this dashboard is a Python Streamlit app
- it needs a live Python runtime, package install, and server-side execution

Recommended deployment path:

1. Push this repository to GitHub.
2. Go to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app**.
4. Choose:
   - repository: `hanzhenzhujene/summa-moral-graph`
   - branch: `main`
   - main file path: `streamlit_app.py`
5. Deploy.

Once deployed, Streamlit gives you a fixed app URL like:

- `https://<your-app-name>.streamlit.app`

Streamlit's sharing docs:

- [Run your Streamlit app](https://docs.streamlit.io/develop/concepts/architecture/run-your-app)
- [Share your app](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)

After it is live, add the Streamlit badge to the top of this README:

```md
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://<your-app-name>.streamlit.app)
```

## Corpus Scope

The textual spine currently covers:

- `I-II, qq. 1–114`
- `II-II, qq. 1–182`

Explicit exclusions:

- `II-II, qq. 183–189`
- `Part I`
- `Part III`
- `Supplement`

Current structural corpus size:

- `296` questions
- `1482` articles
- `12,337` segment-level passages

## Current Reviewed Coverage

The repo does **not** claim the whole corpus is doctrinally reviewed.

It currently includes reviewed overlays for:

- pilot vertical slice across selected `I-II` and `II-II` questions
- theological virtues: `II-II, qq. 1–46`
- prudence: `II-II, qq. 47–56`
- justice core: `II-II, qq. 57–79`
- religion tract: `II-II, qq. 80–100`
- owed-relation tract: `II-II, qq. 101–108`
- connected virtues: `II-II, qq. 109–120`
- fortitude parts and closure: `II-II, qq. 129–140`
- temperance: `II-II, qq. 141–170`

The repo also keeps a full-corpus candidate workflow for:

- structural coverage audit
- candidate concept mentions
- candidate relation proposals
- review packets and review queues

Questions `II-II, qq. 121–128` remain structurally available in the corpus but do not yet have
their own dedicated reviewed doctrinal block.

## Evidence Discipline

This repository is designed around a few non-negotiable rules:

- the canonical evidence unit is the segment, not the whole article
- stable ids remain the anchor for every exported record
- reviewed doctrine, editorial correspondences, structural links, and candidate material stay
  separate in data, validation, and UI
- candidate material is never auto-promoted into reviewed doctrine
- alias handling is conservative, especially where one English label could hide multiple Thomistic
  concepts

In practice, that means the app defaults to reviewed doctrinal graph material, and users opt into
editorial, structural, or candidate overlays only when they want them.

## Quickstart

If you want the full repo in editable local mode first:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Build And Validate

If you want the full structural and candidate workflow:

```bash
make build-interim
make validate-interim
make build-corpus
make validate-candidates
make review-corpus
```

If you want the dashboard and reviewed overlays in a ready-to-use local state:

```bash
make build-interim
make build-corpus
make validate-candidates
make build-pilot
make validate-pilot
make build-prudence
make build-theological-virtues
make test
```

Useful direct commands:

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
```

## Most Useful Docs

- Schema: [docs/schema.md](./docs/schema.md)
- Annotation guide: [docs/annotation_guide.md](./docs/annotation_guide.md)
- Normalization guide: [docs/normalization.md](./docs/normalization.md)
- Full-corpus workflow: [docs/full_corpus_workflow.md](./docs/full_corpus_workflow.md)
- Review queue guide: [docs/review_queue_guide.md](./docs/review_queue_guide.md)
- Coverage summary: [docs/coverage_summary.md](./docs/coverage_summary.md)
- Dashboard interaction audit: [docs/dashboard_interaction_audit.md](./docs/dashboard_interaction_audit.md)

## Important Outputs

The most important generated material lives under:

- `data/interim/` for parsed textual structure
- `data/gold/` for reviewed concepts and annotations
- `data/candidate/` for unreviewed concept and relation proposals
- `data/processed/` for coverage, validation, graph exports, and synthesis artifacts

Examples:

- `data/processed/corpus_manifest.json`
- `data/processed/coverage_report.json`
- `data/processed/candidate_validation_report.json`
- `data/processed/fortitude_tract_synthesis.graphml`
- `data/processed/temperance_full_synthesis.graphml`

## Dashboard Architecture

The current app is a unified Streamlit shell rooted at [`streamlit_app.py`](./streamlit_app.py).

The newer viewer layer lives under:

- `src/summa_moral_graph/viewer/`

That shared layer now drives:

- shared session state
- cross-view navigation
- concept, passage, and map transitions
- tract adapter registration
- reusable UI rendering helpers

Legacy files in `app/Home.py` and `app/pages/*` remain as compatibility wrappers rather than the
main dashboard architecture.

## Status

This repository is in active research use, but the dashboard and evidence model are now organized
as a polished, reader-facing product rather than a loose prototype.

The right way to read the current state is:

- the structural corpus is broad
- the reviewed doctrinal layer is substantial but partial
- the candidate layer is there to support human review, not to pretend to be finished doctrine

That separation is deliberate, and it is one of the main guarantees of the project.
