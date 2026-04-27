# Objection Content Audit

This repo now enforces a strict doctrinal-content policy for the *Summa Theologiae* article parser and every downstream artifact that depends on it.

## Allowed doctrinal sections

Usable content is restricted to:

- `I answer that` (`resp`)
- `Reply to Objection ...` (`ad`)

## Excluded source sections

The pipeline excludes:

- `Objection 1`, `Objection 2`, and the rest of the opening objection block (`obj`)
- `On the contrary` / `Sed contra` (`sc`)
- any standalone objection text that appears before the respondeo / replies phase

Important distinction:

- `Objection ...` is excluded
- `Reply to Objection ...` is retained

## Root cause

The original parser correctly recognized article section boundaries, but it exported all parsed sections into the interim corpus. That meant the opening objection block and `On the contrary` became ordinary passages in:

- interim segment artifacts
- candidate mention generation
- candidate relation proposal generation
- some tract review/support exports
- app search and display filters

Downstream code mostly trusted the interim segment table as already doctrinally safe, so contamination propagated automatically.

## Rule now enforced in code

The parser still recognizes the full article structure for boundary detection:

- `obj`
- `sc`
- `resp`
- `ad`

But exported / usable content is now limited to:

- `resp`
- `ad`

Implementation notes:

- `src/summa_moral_graph/ingest/parser.py` parses all section markers but only emits `resp` and `ad` segments.
- `src/summa_moral_graph/models/records.py` rejects any segment type outside `resp` / `ad`.
- `src/summa_moral_graph/utils/ids.py` rejects segment ids for `obj` / `sc`.
- `src/summa_moral_graph/validation/interim.py` fails if non-usable segment types appear in interim data.
- `src/summa_moral_graph/viewer/` filters only expose `resp` / `ad` in the app.
- `src/summa_moral_graph/validation/corpus.py` scans exported artifacts for disallowed passage ids such as `.obj1` or `.sc`.

## Contamination audit result

After the fix and regeneration:

- interim segment counts are now:
  - `resp`: `1482`
  - `ad`: `4550`
- total usable passages: `6032`
- disallowed passage-id scan reports no exported `.objN` or `.sc` passage references in the final pipeline artifacts
- reviewed fortitude closure seeds that previously cited `sc` passages were removed

## Regenerated artifacts

The fix required regeneration of:

- `data/interim/*`
- `data/candidate/*`
- affected `data/gold/*`
- corpus and tract reports under `data/processed/*`
- review packets and coverage / validation summaries under `docs/*`

## Regression protection

Regression coverage now includes:

- parser fixture tests that expect only `resp` / `ad`
- id/model validation tests that reject `obj` / `sc`
- live parsing smoke tests that assert exported segments are `resp` / `ad` only
- `tests/test_doctrinal_content_policy.py`, which verifies:
  - interim data contains only `resp` / `ad`
  - exported artifacts contain no objection / sed-contra passage ids
