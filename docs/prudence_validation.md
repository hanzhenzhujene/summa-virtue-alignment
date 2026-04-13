# Prudence Validation

Validation report artifact:

- [prudence_validation_report.json](/Users/hanzhenzhu/Desktop/aquinas/data/processed/prudence_validation_report.json)

Current status:

- `ok`

## Checks Enforced

- every reviewed doctrinal edge has at least one reviewed annotation
- every reviewed annotation uses known node ids for subjects and objects
- every reviewed annotation cites a real passage id
- every reviewed annotation has evidence text that matches the cited passage
- reviewed doctrinal edges do not include `structural_editorial` support
- reviewed doctrinal edges do not depend on candidate ids
- duplicate reviewed annotation tuples are flagged
- prudence-part relations target `concept.prudence`
- prudence-part relations use `integral_part_of`, `subjective_part_of`, or `potential_part_of`
- prudence-part concepts used in those edges carry the matching `part_taxonomy`

## Current Outcome

- reviewed doctrinal annotations: `156`
- reviewed doctrinal edges: `152`
- reviewed structural-editorial correspondences: `12`
- candidate mentions: `4`
- candidate relation proposals: `5`
- duplicate annotation flags: `0`
- unresolved validation warnings: `0`

## Remaining Review Risks

Passing validation does not mean theological completeness. It means the current reviewed export is internally consistent with the stated prudence-layer rules.
