# Aquinas Summa Moral Graph — experiment and implementation plan

## 1) Reverse-engineered baseline from the Aristotle dashboard

The Aristotle Virtue Graph is valuable less as a one-off app than as a design pattern:

- **Thin, inspectable architecture**: ingest text, maintain human-reviewed annotations, export processed graph artifacts, then load them into a Streamlit viewer. There is no database and no external graph service.
- **Evidence-first graph model**: concepts and non-hierarchical relations are not free-floating summaries; they are tied to passage evidence and preserve a distinction between textual claim, editorial normalization, and interpretation.
- **Processed artifact boundary**: the app loads committed JSONL/JSON/GraphML outputs rather than rebuilding the graph on each run.
- **Viewer design**: the app is organized around a `Home` view, `Concept Explorer`, `Passage Explorer`, `Overall Map`, and `Stats`, with a sidebar for search, filtering, quick entry points, and dataset download.
- **Graph interaction**: the graph canvas is rendered with PyVis / vis-network HTML, then wrapped in a small custom Streamlit component that returns clicked node ids to Python for navigation.
- **Pragmatic graph readability**: there is a small concept-centered ego graph for close reading and a separate overall map with stronger filters and physics tuning.

For Aquinas, that design spine should be reused almost intact. The main changes are scale, richer ontology, and the fact that the *Summa* is structurally article-based rather than paragraph-based.

## 2) Project objective

Build an evidence-first Streamlit dashboard for the **moral-philosophical corpus** of Thomas Aquinas's *Summa Theologiae*:

- **I-II, qq. 1–114**
- **II-II, qq. 1–182**
- **Exclude II-II, qq. 183–189**
- **Exclude Part I, Part III, and the Supplement**

The dashboard should let a user:

1. start from a virtue, vice, gift, beatitude, passion, precept, law, grace-type, or related moral concept;
2. see how Aquinas connects it to neighboring concepts;
3. open the exact question/article/segment where the connection is grounded;
4. move back outward into the larger relational map;
5. download the reviewed structured dataset.

## 3) Success criteria

The project is successful when a user can do all of the following without leaving the app:

- open a concept such as `prudence`, `charity`, `natural law`, `fear`, or `grace`;
- see its local graph neighborhood and grouped relation cards;
- open supporting article segments directly from evidence cards;
- browse an article in structured form (`objections`, `sed contra`, `respondeo`, `replies`);
- inspect the whole filtered network by treatise / node kind / relation family;
- understand corpus coverage and annotation status from a stats page;
- download a reviewed dataset bundle.

## 4) Core design decision: keep the Aristotle architecture, but scale it carefully

### Keep

- local-file architecture
- processed reviewed exports
- evidence-first concept/relation model
- Streamlit UI with guided entry points
- clickable local ego graph + separate overall map
- GraphML interoperability export
- human-reviewed candidate/approved workflow

### Change

- move from one small book to a much larger corpus
- replace paragraph passages with **question → article → segment** evidence units
- add richer concept types and relation families
- add treatise-level and question-level filters
- prevent full-corpus graph hairballs by default
- add article-aware navigation and cross-reference extraction

## 5) Corpus and source policy

### Recommended source stance

Use a **public-domain English translation** as the main display basis, but commit only **derived structured artifacts** unless raw-text redistribution is clearly safe.

### Practical implementation choice

- Use an English source with stable question/article structure for initial fetch and parsing.
- Use **Corpus Thomisticum** as a verification source and for Latin cross-checks.
- Keep raw downloaded HTML out of git if rights are unclear.
- Commit:
  - source metadata
  - normalized question/article/segment exports
  - reviewed graph artifacts

This mirrors the cautious source policy used in the Aristotle project: preserve provenance, prefer redistributable text when possible, and do not commit raw site HTML just because the underlying translation is old.

## 6) Text segmentation model

The *Summa* is much more naturally segmented by **article structure** than by flat paragraphs.

### Canonical hierarchy

1. **Part**
   - `i-ii`
   - `ii-ii`

2. **Question**
   - Example: `st.i-ii.q001`
   - Contains question title and article list

3. **Article**
   - Example: `st.i-ii.q001.a001`
   - Contains article title and ordered segment list

4. **Segment** (authoritative evidence unit)
   - `obj1`, `obj2`, ...
   - `sc` (`sed contra`)
   - `resp` (`I answer that`)
   - `ad1`, `ad2`, ...

### Stable id pattern

- Question: `st.i-ii.q001`
- Article: `st.i-ii.q001.a001`
- Segment:
  - `st.i-ii.q001.a001.obj1`
  - `st.i-ii.q001.a001.sc`
  - `st.i-ii.q001.a001.resp`
  - `st.i-ii.q001.a001.ad1`

### Why segment-level evidence is the right default

Aquinas often makes the most important conceptual distinction in the `respondeo`, but objections and replies frequently contain important disambiguations, edge cases, and cross-references. Segment-level ids preserve that precision without forcing the graph to cite an entire article when only one segment grounds the claim.

## 7) Interim textual artifacts

Write these as the authoritative text-side artifacts:

- `data/interim/summa_moral_questions.jsonl`
- `data/interim/summa_moral_articles.jsonl`
- `data/interim/summa_moral_segments.jsonl`
- `data/interim/summa_moral_crossrefs.jsonl`

### Question record

Suggested fields:

- `question_id`
- `part_id`
- `question_number`
- `question_title`
- `treatise_key`
- `article_count`
- `source_id`
- `source_url`
- `hash`

### Article record

Suggested fields:

- `article_id`
- `question_id`
- `part_id`
- `question_number`
- `article_number`
- `article_title`
- `citation_label`
- `treatise_key`
- `segment_ids`
- `source_id`
- `source_url`
- `hash`

### Segment record

Suggested fields:

- `segment_id`
- `article_id`
- `question_id`
- `part_id`
- `question_number`
- `article_number`
- `segment_type`
- `segment_ordinal`
- `citation_label`
- `question_title`
- `article_title`
- `source_id`
- `source_url`
- `text`
- `char_count`
- `hash`

### Cross-reference record

Suggested fields:

- `crossref_id`
- `source_segment_id`
- `target_part_id`
- `target_question_number`
- `target_article_number` (optional)
- `raw_reference`
- `normalized_reference`
- `confidence`
- `note`

## 8) Concept model

Use a concept model close to the Aristotle one, but slightly richer.

### Recommended concept fields

- stable `id`
- `primary_label`
- `display_label`
- `source_labels`
- optional `latin_label`
- optional `aliases`
- `kind`
- `family`
- `description`
- `assertion_tier`
- `part_refs`
- `question_refs`
- `article_refs`
- non-empty `evidence`
- `review_status`
- optional `notes`

### Keep `assertion_tier`

Use the same three-layer discipline as the Aristotle project:

- `textual`
- `editorial_normalization`
- `interpretive`

### Keep `review_status`

- `candidate`
- `approved`

### Recommended concept kinds

Keep `kind` relatively small and push extra specificity into `family`:

- `virtue`
- `vice`
- `gift`
- `beatitude`
- `fruit`
- `passion`
- `habit`
- `act`
- `power`
- `law`
- `grace`
- `precept`
- `sin`
- `end`
- `state`
- `principle`

### Recommended concept families

Examples:

- `last_end`
- `human_acts`
- `passions_concupiscible`
- `passions_irascible`
- `habits`
- `virtues_general`
- `vice_and_sin`
- `law`
- `grace`
- `theological_faith`
- `theological_hope`
- `theological_charity`
- `prudence_family`
- `justice_family`
- `fortitude_family`
- `temperance_family`
- `gratuitous_graces`
- `active_contemplative_life`

## 9) Concept id discipline: namespacing is non-negotiable

Aquinas reuses many surface labels across distinct conceptual roles.

Examples of likely collisions:

- `fear` as a **passion**
- `fear` as the **gift of the Holy Spirit**
- `hope` as a **passion**
- `hope` as a **theological virtue**
- `presumption` opposed to **hope**
- `presumption` opposed to **magnanimity**
- `knowledge` as an **intellectual virtue context**
- `knowledge` as a **gift context**

Therefore concept ids must be **namespaced and disambiguated**, for example:

- `passion.fear`
- `gift.fear-of-the-lord`
- `virtue.hope-theological`
- `vice.presumption-against-hope`
- `vice.presumption-against-magnanimity`

The display label can stay simple, but the id cannot.

## 10) Evidence object

Use the Aristotle evidence pattern almost unchanged, but swap `passage_id` for `segment_id`.

### Evidence fields

- `segment_id`
- `support_type`
- `note`
- optional `quote_excerpt`

### Support types

- `direct`
- `paraphrase`
- `editorial`

Rule: every concept and every non-hierarchical relation must carry at least one evidence object.

## 11) Relation model

Aquinas requires a broader relation vocabulary than Aristotle, but the vocabulary must still stay disciplined.

### Recommended relation fields

- stable `id`
- `source_id`
- `relation_type`
- optional `relation_subtype`
- `target_id`
- `assertion_tier`
- non-empty `evidence`
- `review_status`
- optional `notes`

### Recommended core relation types

- `is_a`
- `part_of`
- `annexed_to`
- `opposed_to`
- `concerns`
- `perfects`
- `requires`
- `presupposes`
- `causes`
- `results_in`
- `orders_to`
- `moderates`
- `commands`
- `elicited_by`
- `corresponds_to`
- `enjoins`
- `forbids`
- `cures`
- `deforms`
- `crossref_to`

### Use `relation_subtype` instead of exploding relation types

Examples:

- `opposed_to` with subtype:
  - `contrary`
  - `privation`
  - `excess`
  - `deficiency`

- `corresponds_to` with subtype:
  - `gift`
  - `beatitude`
  - `fruit`
  - `affirmative_precept`
  - `negative_precept`

This keeps filtering manageable while preserving theology-specific distinctions.

## 12) Treatise-aware annotation layout

Do **not** put the whole corpus into one giant annotation file.

Recommended layout:

```text
annotations/
  i-ii/
    last-end-human-acts/
      concepts.candidate.yaml
      relations.candidate.yaml
      concepts.approved.yaml
      relations.approved.yaml
    passions/
      ...
    habits-virtues-gifts/
      ...
    vice-and-sin/
      ...
    law/
      ...
    grace/
      ...
  ii-ii/
    faith/
      ...
    hope/
      ...
    charity/
      ...
    prudence/
      ...
    justice/
      ...
    fortitude/
      ...
    temperance/
      ...
    gratuitous-graces-and-lives/
      ...
```

This keeps review batches small, local, and theologically coherent.

## 13) Annotation strategy: deterministic first, assisted later

### Deterministic / structural extraction

Automate these first:

- question and article index
- segment extraction
- article titles
- treatise grouping
- explicit intra-*Summa* cross-references
- article-to-question backlinks

### Human-reviewed concept graph

Then create candidate annotations for:

- key concepts
- key relations
- doctrinal correspondences

### LLM use policy

LLM output may be used to suggest candidate concepts or relations, but:

- it must enter the repo only as `candidate`
- it must never be treated as ground truth
- it must never be auto-promoted to `approved`
- every approved item must still have explicit evidence

## 14) Corpus rollout strategy

Do not try to approve the whole corpus in one pass.

### Recommended rollout

#### Phase A — infrastructure only
Whole-corpus ingest, indexing, segmentation, cross-reference extraction.

#### Phase B — pilot reviewed slice
Start with:

- `I-II q. 55–70` (virtues, gifts, beatitudes, fruits)
- `II-II q. 1–46` (faith, hope, charity)

Why this slice:

- it captures the core correspondence logic
- it tests virtue / vice / gift / beatitude / precept relations
- it is central enough to anchor the whole product

#### Phase C — finish I-II
Add human acts, passions, habits, vice/sin, law, grace.

#### Phase D — finish II-II
Add prudence, justice, fortitude, temperance, then qq. 171–182.

## 15) Processed reviewed artifacts

Mirror the Aristotle pattern, but with richer text artifacts.

Recommended files:

- `data/processed/summa_moral_questions.jsonl`
- `data/processed/summa_moral_articles.jsonl`
- `data/processed/summa_moral_segments.jsonl`
- `data/processed/summa_moral_crossrefs.jsonl`
- `data/processed/summa_moral_concepts.jsonl`
- `data/processed/summa_moral_relations.jsonl`
- `data/processed/summa_moral_graph.json`
- `data/processed/summa_moral_graph.graphml`
- `data/processed/summa_moral_stats.json`

### Export roles

- `summa_moral_graph.json` = primary rich export for the app
- `summa_moral_graph.graphml` = flattened interoperability export
- JSONL files = auditable row-level data surfaces

## 16) Graph export structure

### JSON graph payload

Suggested top-level structure:

```json
{
  "meta": {...},
  "questions": [...],
  "articles": [...],
  "segments": [...],
  "nodes": [...],
  "edges": [...],
  "crossrefs": [...]
}
```

### GraphML

Use a `networkx.MultiDiGraph` and flatten nested structures the same way the Aristotle repo does. Evidence metadata should be preserved in flattened JSON-string fields where necessary.

## 17) Viewer / dashboard design

## 17.1 Home

Purpose: orient the user immediately.

Include:

- project scope
- quick entry cards
- dataset download
- “start here” routes such as:
  - Virtue in general
  - Gifts / beatitudes
  - Law
  - Grace
  - Faith
  - Prudence
  - Justice
  - Fortitude
  - Temperance
  - Active / contemplative life

## 17.2 Concept Explorer

This is the primary reading interface.

Include:

- concept title
- plain-language doctrinal role summary
- evidence cards with article/segment jump buttons
- local graph map (1-hop / 2-hop, possibly 3-hop later)
- grouped relation cards:
  - taxonomy
  - opposition
  - causal / functional
  - correspondence
  - precept links
- optional dataset details expander

The emphasis should stay on readable doctrinal structure first, structured scaffolding second.

## 17.3 Article Explorer

This is the Aquinas-specific expansion of the Aristotle Passage Explorer.

Include:

- breadcrumbs: Part → Question → Article
- question title and article title
- structured article view:
  - objections
  - sed contra
  - respondeo
  - replies
- highlighted evidence segments
- concepts grounded here
- relations grounded here
- explicit cross-references:
  - `Aquinas cites`
  - `Cited by`

## 17.4 Question Explorer (MVP+)

Not required on day one, but strongly recommended.

Purpose:

- show article list and question-level context
- display a question synopsis
- prevent the user from seeing articles in isolation

## 17.5 Overall Map

Necessary, but must be constrained.

Include:

- part filter
- treatise filter
- node kind filter
- relation family filter
- assertion tier filter
- isolate toggle
- edge-label toggle
- click-to-open concept

Do not assume the user wants the entire moral corpus rendered at once without filters.

## 17.6 Correspondence Explorer (Phase 2)

Aquinas's structure makes this especially valuable.

Purpose:

- show virtue ↔ gift ↔ beatitude ↔ precept correspondences
- support matrix and table views
- help users navigate recurring Thomistic correspondence logic

## 17.7 Stats

Include:

- counts by concept kind
- counts by family
- counts by relation type
- counts by assertion tier
- counts by treatise
- top connected concepts
- review coverage
- cross-reference density

## 18) Sidebar design

Recommended controls:

- search text
- selected concept
- selected article / question
- graph depth
- part filter
- treatise filter
- concept kinds
- relation families / relation types
- assertion tiers
- question range
- “start here” quick buttons
- dataset download

## 19) Graph rendering strategy

### Initial recommendation

Start with the same approach as Aristotle:

- **PyVis / vis-network**
- custom Streamlit component to capture node clicks
- separate tuning for local graph and overall map

### Why start there

- the pattern is already proven
- click-bridge behavior is already solved
- it keeps the stack small

### But do not assume it is the final choice

Run an explicit benchmark against a Cytoscape-based alternative if the whole-corpus filtered map becomes sluggish or fragile.

## 20) Key experiments and decision gates

## Experiment 1 — Segment granularity
Goal: verify that objection / sed contra / respondeo / reply segmentation is stable and useful.

Acceptance:
- deterministic ids on repeated runs
- no empty segments
- article reconstruction is lossless enough for UI reading

## Experiment 2 — Source robustness
Goal: parse a representative set of I-II and II-II pages.

Acceptance:
- titles, article counts, and article order match source pages
- parser survives minor HTML differences across pages

## Experiment 3 — Cross-reference parser
Goal: extract references like `I-II:65:1` and `II-II:23:3`.

Acceptance:
- high parse accuracy on a manual sample
- normalized target fields filled correctly

## Experiment 4 — Ontology sufficiency
Goal: test whether the relation vocabulary is expressive enough.

Pilot slice:
- `I-II 55–70`
- `II-II 1–46`

Acceptance:
- no immediate pressure to explode relation types
- correspondence edges remain intelligible

## Experiment 5 — Graph renderer benchmark
Goal: compare PyVis / vis-network against a Cytoscape-style alternative.

Acceptance:
- acceptable load and interaction at:
  - local subgraph
  - treatise-scale map
  - whole-corpus filtered map

## Experiment 6 — Review throughput
Goal: estimate realistic human-review speed.

Acceptance:
- treatise chunks are small enough to review in bounded sessions
- candidate backlog remains manageable

## 21) Milestones

## Milestone 0 — Repository scaffold
Create:

- package structure
- `pyproject.toml`
- `Makefile`
- tests folder
- docs skeleton
- root agent guide
- execution plan

Acceptance:
- install works
- tests run
- lint runs
- type checking runs

## Milestone 1 — Whole-corpus ingest and segmentation
Implement:

- source adapters
- question/article index
- segment extraction
- cross-reference extraction

Write interim artifacts.

Acceptance:
- all in-scope questions indexed
- ids stable
- artifacts deterministic

## Milestone 2 — Schemas and validation
Implement:

- Pydantic models
- JSON Schema export if useful
- concept / relation / evidence validation
- annotation chunk layout

Acceptance:
- schema validation passes
- every relation endpoint resolves
- no evidence-free non-hierarchical relations

## Milestone 3 — Pilot reviewed slice
Annotate and review:

- `I-II 55–70`
- `II-II 1–46`

Acceptance:
- concept explorer works for faith / hope / charity / virtue / gift / beatitude
- article explorer works end to end
- correspondences are visible

## Milestone 4 — Complete I-II reviewed graph
Add:

- human acts
- passions
- vice/sin
- law
- grace

Acceptance:
- main I-II conceptual arcs visible and auditable

## Milestone 5 — Complete II-II reviewed graph
Add:

- prudence family
- justice family
- fortitude family
- temperance family
- qq. 171–182

Acceptance:
- all in-scope II-II questions covered
- excluded qq. 183–189 remain absent

## Milestone 6 — Processed graph exports
Write processed reviewed artifacts and dataset bundle.

Acceptance:
- app can load reviewed exports only
- GraphML export is valid
- stats load cleanly

## Milestone 7 — Dashboard MVP
Implement:

- Home
- Concept Explorer
- Article Explorer
- Overall Map
- Stats

Acceptance:
- app launches locally
- node clicks navigate correctly
- evidence jumps work correctly

## Milestone 8 — Scale polish and release
Improve:

- filtering
- performance
- docs
- screenshot / README
- hosted deployment

Acceptance:
- first-run path is obvious
- filtered whole-corpus view remains usable
- docs and tests are complete

## 22) Validation and QA

### Parser tests

- question count in scope
- article count per sample question
- segment type ordering
- cross-reference extraction

### Graph integrity tests

- every relation endpoint resolves
- every evidence segment exists
- no duplicate concept ids
- no duplicate relation ids
- no out-of-scope question or article ids in approved artifacts

### Id stability tests

- repeated runs on same source produce same ids

### UI smoke tests

- dataset loads
- concept page renders
- article jump works
- overall map click-through works

### Manual theological spot audits

Always manually audit a sample from:

- gifts / beatitudes
- theological virtues
- prudence parts
- justice connected virtues
- temperance parts
- law and grace transitions

## 23) Main risks and mitigations

### Risk: licensing ambiguity
Mitigation: commit derived structured data only until raw-text policy is fully safe.

### Risk: label collisions
Mitigation: namespaced ids and display labels separated.

### Risk: graph hairball
Mitigation: default to local graph, heavy filters for overall map, treatise-aware presets.

### Risk: interpretive drift
Mitigation: keep `textual`, `editorial_normalization`, and `interpretive` distinct; require evidence; keep draft material in `candidate`.

### Risk: annotation fatigue
Mitigation: chunk by treatise, pilot first, automate structure extraction aggressively.

### Risk: relation vocabulary explosion
Mitigation: use `relation_subtype` before inventing new top-level relation types.

## 24) Recommended immediate next step

The first implementation sprint should build **Milestones 0 and 1 only**:

- scaffold the repo,
- document source policy and data model,
- index the entire in-scope corpus,
- segment questions into article units and sub-article evidence segments,
- extract structured cross-references,
- write deterministic interim artifacts,
- add tests.

That gives the project a solid textual spine before any concept graph is approved.

## 25) “Done” definition for this project

A task is not done until:

- relevant tests pass
- lint and type checks pass
- docs are updated if schemas or behavior changed
- the execution plan is updated if the task was multi-step
- source policy is still being obeyed
- candidate and approved surfaces remain clearly separated
- every new concept or non-hierarchical relation is evidence-backed
