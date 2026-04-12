# summa-moral-graph

`summa-moral-graph` is the textual spine for an evidence-first knowledge graph of the moral-philosophical corpus of Thomas Aquinas's *Summa Theologiae*.

This sprint implements Milestones 0 and 1 only:

- repository scaffold
- deterministic ingest for the in-scope corpus
- question/article/segment/cross-reference interim artifacts
- validation, tests, and local CLI entry points

The current scope is:

- `I-II, qq. 1–114`
- `II-II, qq. 1–182`

Explicitly out of scope:

- `II-II, qq. 183–189`
- `Part I`
- `Part III`
- `Supplement`
- concept graph construction
- Streamlit dashboard work
- databases or external graph services

## Quickstart

Use any Python `3.11+` interpreter.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make build-interim
make validate
make test
```

You can also inspect the corpus scope before building:

```bash
summa-moral-graph show-scope
```

## What It Produces

The build writes deterministic interim artifacts under `data/interim/`:

- `summa_moral_questions.jsonl`
- `summa_moral_articles.jsonl`
- `summa_moral_segments.jsonl`
- `summa_moral_crossrefs.jsonl`

These artifacts are derived data only. Raw fetched HTML is cached locally under `data/cache/` and intentionally excluded from version control.

## Commands

- `summa-moral-graph build-interim`
- `summa-moral-graph validate-interim`
- `summa-moral-graph show-scope`

Or through `make`:

- `make install`
- `make build-interim`
- `make validate`
- `make test`
- `make lint`
- `make typecheck`
- `make check`

## Project Notes

- The authoritative evidence unit is the article **segment**.
- Stable IDs are deterministic and documented in [docs/data_model.md](/Users/hanzhenzhu/Desktop/aquinas/docs/data_model.md).
- Source and redistribution policy is documented in [docs/source_policy.md](/Users/hanzhenzhu/Desktop/aquinas/docs/source_policy.md).
- Implementation progress is tracked in [docs/execplans/summa-moral-graph.md](/Users/hanzhenzhu/Desktop/aquinas/docs/execplans/summa-moral-graph.md).

