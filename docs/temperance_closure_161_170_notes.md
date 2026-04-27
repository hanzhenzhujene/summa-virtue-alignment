# Temperance Closure 161-170 Notes

## Scope

Reviewed doctrinal work in this block is limited to:

- `II-II q.161` humility
- `II-II q.162` pride
- `II-II qq.163–165` Adam's first sin, its punishments, and the temptation
- `II-II q.166` studiousness
- `II-II q.167` curiosity
- `II-II qq.168–169` external modesty
- `II-II q.170` the precepts of temperance

The full temperance synthesis now spans `II-II qq. 141–170`, but earlier temperance material was not re-annotated in this pass.

## Normalization Decisions

- `concept.humility` remains distinct from `concept.modesty_general`.
- `concept.pride` remains distinct from `concept.adams_first_sin`.
- `concept.studiousness` remains distinct from `concept.curiosity`.
- `concept.external_behavior_modesty` remains distinct from:
  - `concept.modesty_general`
  - `concept.outward_attire_modesty`
- precept nodes remain distinct from the virtues or vices they regulate:
  - `concept.precepts_of_temperance`
  - `concept.precepts_of_temperance_parts`

## Adam's-First-Sin Case Modeling

- The tract uses a case-level node:
  - `concept.adams_first_sin`
- This node is linked to generic pride by reviewed `case_of`, not identity.
- Punishments and temptation are modeled conservatively through:
  - `results_in_punishment`
  - `tempted_by`
- The current block does not introduce person-instance machinery for Adam, Eve, or the serpent.

## Studiousness / Curiosity Decisions

- `studiousness` is modeled through ordered inquiry and temperance/modesty placement.
- `curiosity` is modeled as disordered inquiry and as contrary to studiousness.
- Neutral modern curiosity language is intentionally excluded from reviewed aliases and doctrinal edges.

## External-Modesty Decisions

- `q.168` is modeled through outward behavior and play:
  - `external_behavior_modesty`
  - `eutrapelia`
  - `playful_actions`
  - `excessive_play`
  - `boorishness`
- `q.169` is modeled through attire:
  - `outward_attire_modesty`
  - `outward_apparel`
  - `excessive_adornment`
- `modesty_general` from `q.160` remains a broader temperance-part node and is not silently widened into these later species.

## Precept-Linkage Decisions

- Precept-linkage is intentionally conservative.
- Focus tags for `precept` / `precept_linkage` are attached only to:
  - `q.170`
  - actual precept relations
  - actual precept nodes
- This avoids falsely labeling every humility or pride edge as precept material merely because those concepts appear as precept targets later in the tract.

## Support Classification

- `explicit_textual`
  - used where the relation is directly named or very tightly stated in the cited segment
- `strong_textual_inference`
  - used where the tract supports the relation clearly, but not in a fully formulaic wording
- `structural_editorial`
  - used for reviewed treatment correspondences and tract-organization links
  - excluded from default doctrinal graph exports

## Remaining Human Review Needs

- `q.161` humility:
  - still needs more direct doctrinal support beyond the current modesty / God / truth-about-self spine
- `q.162` pride:
  - candidate-heavy and still the clearest under-annotated closure question
- `qq.163–165`:
  - case/punishment/temptation boundaries need continued theological review so they do not drift into a broader original-sin ontology
- `qq.168–169`:
  - external-modesty wording remains ambiguity-heavy and should be reviewed before expanding more species edges
- `q.170`:
  - precept-linkage should stay conservative as the full temperance synthesis grows
