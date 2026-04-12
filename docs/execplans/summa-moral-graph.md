# Summa Moral Graph Execution Plan

## Progress

- Milestone 0 scaffold is complete: packaging, docs, tests, CLI, repo guidance, and Make targets are in place.
- Milestone 1 textual ingest is complete for the in-scope corpus:
  - `296` questions
  - `1482` articles
  - `12337` segments
  - `2238` explicit cross-reference records
- Interim artifacts are generated and validated under `data/interim/`.

## Surprises & Discoveries

- New Advent part landing pages are structurally usable for scope discovery.
- Question pages expose article structure through `h2#articleN` anchors and labeled paragraphs.
- Some explicit *Summa* cross-references appear inside malformed anchor markup, so visible-text extraction is safer than relying only on `href` attributes.
- At least one live page (`I-II q.40 a.1`) contains duplicated reply numbering in the source HTML, so exported `obj` and `ad` ordinals need normalization by occurrence order.
- At least one live page (`I-II q.87 a.7`) repeats `On the contrary` across multiple paragraphs, and another (`I-II q.89 a.1`) incorrectly reuses `On the contrary` inside a reply.
- At least one live page (`II-II q.172 a.1`) uses `Objection 2.` inside the replies section, so objection labels cannot be trusted blindly once an article has entered its response/reply phase.
- Because raw HTML redistribution is unclear, fixture strategy uses synthetic structural HTML plus optional live-network smoke tests instead of committed full source pages.

## Decision Log

- Use New Advent as the primary parser target for the first sprint.
- Keep raw HTML cached locally and out of version control.
- Treat the full run of paragraphs belonging to each objection, sed contra, respondeo, or reply as the authoritative segment unit.
- Use stable ids derived only from normalized part/question/article/segment coordinates.
- Record explicit cross-references even when their targets are outside the current ingest scope.
- Normalize objection and reply ordinals by occurrence order when source numbering is duplicated or irregular, in order to preserve stable unique segment ids.
- Normalize repeated or backward `sed contra` / `respondeo` labels into the current segment when the source markup would otherwise violate canonical article order.
- Reinterpret late-stage `Objection N.` labels as replies when they appear after the article has already entered the respondeo/reply phase.

## Outcomes & Retrospective

- The sprint finished with a clean editable install on Python `3.12`, deterministic interim artifacts, explicit source/data-model documentation, and wired validation/test/type-check/lint entry points.
- Offline fixture tests pass, and optional live smoke tests against New Advent pass.
- The parser now defends against several real-world source irregularities without weakening the canonical article model.
- The next milestone should build on these exported records rather than reparsing the corpus ad hoc.
