# Data Model

## Stable IDs

The authoritative evidence unit is the **segment**.

Stable ID format:

- question: `st.i-ii.q001`
- article: `st.i-ii.q001.a001`
- segment:
  - `st.i-ii.q001.a001.obj1`
  - `st.i-ii.q001.a001.sc`
  - `st.i-ii.q001.a001.resp`
  - `st.i-ii.q001.a001.ad1`

ID generation is deterministic and derived only from:

- part id
- question number
- article number
- segment type
- segment ordinal when relevant

Titles and source URLs never affect stable IDs.

## Part IDs

Supported normalized part ids for parsing and cross-reference normalization:

- `i`
- `i-ii`
- `ii-ii`
- `iii`
- `supplement`

Current ingest scope uses only:

- `i-ii`
- `ii-ii`

## Record Schemas

### Question record

Fields:

- `question_id`
- `part_id`
- `question_number`
- `question_title`
- `article_count`
- `source_id`
- `source_url`
- `source_part_url`
- `hash`

Notes:

- one record per in-scope question page
- `hash` is a SHA-256 digest over the canonical JSON payload without the hash field

### Article record

Fields:

- `article_id`
- `question_id`
- `part_id`
- `question_number`
- `article_number`
- `article_title`
- `citation_label`
- `segment_ids`
- `source_id`
- `source_url`
- `hash`

Notes:

- `source_url` points to the article anchor on the source question page
- `citation_label` is human-readable, for example `I-II q.1 a.1`

### Segment record

Fields:

- `segment_id`
- `article_id`
- `question_id`
- `part_id`
- `question_number`
- `question_title`
- `article_number`
- `article_title`
- `segment_type`
- `segment_ordinal`
- `citation_label`
- `source_id`
- `source_url`
- `text`
- `char_count`
- `hash`

Segment types:

- `obj`
- `sc`
- `resp`
- `ad`

Segment ordering inside an article must be:

1. zero or more objections
2. optional sed contra
3. optional respondeo
4. zero or more replies

Ordinal rules:

- `obj` and `ad` require `segment_ordinal`
- `sc` and `resp` must have `segment_ordinal = null`
- if source numbering is irregular or duplicated, exported objection and reply ordinals are normalized to occurrence order within the article so ids remain unique and deterministic

Normalized segment text excludes boilerplate labels such as `Objection 1.` or `I answer that,` because that structure is already represented explicitly in typed fields.

### Cross-reference record

Fields:

- `crossref_id`
- `source_segment_id`
- `source_part_id`
- `source_question_number`
- `source_article_number`
- `raw_reference`
- `normalized_reference`
- `target_part_id`
- `target_question_number`
- `target_article_number`
- `source_url`
- `hash`

Notes:

- one record per explicit citation occurrence
- `crossref_id` is stable within a segment, for example `st.ii-ii.q001.a001.obj1.xref01`
- local references like `Article 1` are ignored unless they explicitly name a *Summa* part/question/article

## Cross-reference normalization

Supported explicit formats include:

- `I:85:5`
- `I-II:65:1`
- `II-II:23:3`
- `III:12:4`
- `Suppl.:5:2`
- `Supplement:5:2`

Normalized fields:

- `target_part_id`: lowercase machine id such as `ii-ii`
- `target_question_number`: integer
- `target_article_number`: integer
- `normalized_reference`: canonical display form such as `II-II:23:3`
