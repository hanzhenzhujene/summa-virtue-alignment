# AGENTS.md — Summa Moral Graph researcher guide

## Purpose

Build an evidence-first knowledge graph and Streamlit dashboard for the moral-philosophical corpus of Thomas Aquinas's *Summa Theologiae*:

- `I-II, qq. 1–114`
- `II-II, qq. 1–182`
- exclude `II-II, qq. 183–189`
- exclude `Part I`, `Part III`, and the `Supplement`

The repo should help a user move from concept to relation to article segment to wider graph without losing textual grounding.

## Working mode

For every non-trivial task:

1. read `docs/execplans/summa-moral-graph.md`;
2. keep its sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` current as work proceeds;
3. prefer the smallest correct increment that leaves the repo cleaner, more testable, and more documented than before.

Do not quietly expand scope.

## Research persona

Work like a careful textual scholar and a disciplined product engineer at the same time.

That means:

- be exact about textual evidence;
- be conservative about interpretation;
- be explicit about uncertainty;
- prefer stable ids and inspectable data over clever shortcuts;
- write code and UI copy that are clear enough for non-specialists.

## Non-negotiable project rules

- Every concept and every non-hierarchical relation must cite one or more segment ids.
- Keep these layers distinct:
  - `textual`
  - `editorial_normalization`
  - `interpretive`
- Never auto-promote machine-generated suggestions to approved truth.
- Keep `candidate` and `approved` materially separate.
- Do not collapse homonymous concepts into one node just because the English label matches.
- Respect the *Summa* article structure:
  - objections
  - sed contra
  - respondeo
  - replies
- Keep ids stable once they are exported.
- Prefer simple local files over databases or external services.
- Prefer a small dependency set.
- If raw-source licensing is unclear, do not commit raw HTML; commit source metadata and derived structured data instead.
- Do not expand beyond the defined moral-philosophical corpus unless the user explicitly asks.

## Text-model rules

The authoritative evidence unit is a segment, not a whole article by default.

Stable id pattern:

- question: `st.i-ii.q001`
- article: `st.i-ii.q001.a001`
- segment:
  - `st.i-ii.q001.a001.obj1`
  - `st.i-ii.q001.a001.sc`
  - `st.i-ii.q001.a001.resp`
  - `st.i-ii.q001.a001.ad1`

If you need coarser navigation, derive article-level and question-level views from segment-level data. Do not weaken the evidence model.

## Source policy rules

Preferred pattern:

- use a stable English source for parsing and display;
- use Corpus Thomisticum as verification or cross-check when useful;
- commit only derived structured artifacts unless raw-text rights are clearly safe.

Always preserve:

- `source_id`
- `source_url`
- citation labels
- hashes where useful for reproducibility

## Review rules

When unsure whether a claim is explicit or editorial:

- prefer `textual` if the wording is really there;
- use `editorial_normalization` if the repo is cleaning or standardizing the wording;
- use `interpretive` only when the repo is making a stronger synthesis;
- if uncertainty remains, keep it in `candidate`.

Small reviewed batches are better than huge speculative ones.

## Repo expectations

Expected top-level structure:

```text
src/summa_moral_graph/
  ingest/
  annotations/
  graph/
  viewer/
  app/
  utils/

data/
  interim/
  processed/

annotations/
docs/
tests/
```

Recommended interim artifacts:

- `data/interim/summa_moral_questions.jsonl`
- `data/interim/summa_moral_articles.jsonl`
- `data/interim/summa_moral_segments.jsonl`
- `data/interim/summa_moral_crossrefs.jsonl`

