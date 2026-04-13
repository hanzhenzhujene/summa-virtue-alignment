# Religion Tract Notes

## Scope

This reviewed block is intentionally limited to:

- `II-II, qq. 80–100`

It treats:

- `q.80` as the structural gateway from justice into the annexed virtue of religion
- `qq. 81–91` as the core positive acts of religion
- `qq. 92–96` as superstition-side excesses
- `qq. 97–100` as irreligion-side deficiencies

## Normalization Decisions

- `religion` is kept as the annexed virtue of due divine worship, not as generic creed or confession.
- `devotion`, `prayer`, `adoration`, `sacrifice`, `oblation`, `first_fruits`, `tithes`, `vow`, `oath`, and `adjuration` remain separate act nodes.
- `oath`, `vow`, and `adjuration` are not collapsed into one generic verbal or divine-name practice.
- `superstition`, `idolatry`, `divination`, and `superstitious_observance` remain distinct rather than being flattened into one vice bucket.
- `perjury`, `sacrilege`, and `simony` remain separate deficiency-side sins rather than being treated as generic irreligion.

## Act-Taxonomy Decisions

- the positive half of the tract is modeled mainly through `religion has_act <act>` edges plus narrower `species_of` relations where Aquinas treats a practice as a subtype
- `first_fruits` is treated as a narrower form under `oblation`
- `praise_of_god` is kept conservative as a tract-level act node without splitting it further into a larger liturgical taxonomy
- `religion annexed_to justice` is represented, but the app and exports keep tract-structural/editorial support separate from default doctrinal views

## Sacred-Object And Domain Modeling Decisions

- positive acts use `concerns_sacred_object` only when the passage supports a stable sacred object or domain:
  - `divine_worship`
  - `divine_name`
  - `promise_to_god`
  - `sworn_assertion`
- profanatory or abusive practices use `misuses_sacred_object`:
  - `perjury` -> `divine_name`
  - `sacrilege` -> `sacred_thing` / `sacred_person` / `sacred_place`
- `simony` uses `corrupts_spiritual_exchange` together with sacred-object modeling:
  - `spiritual_thing`
  - `sacrament`
  - `spiritual_action`
  - `spiritual_office`

## Opposition-Mode Decisions

- `excess_opposed_to` is reserved for superstition-side excesses:
  - `undue_worship_of_true_god`
  - `idolatry`
  - `divination`
  - `superstitious_observance`
- `deficiency_opposed_to` is reserved for irreligion-side defects:
  - `temptation_of_god`
  - `perjury`
  - `sacrilege`
  - `simony`
- the tract does not reuse a single generic contrary relation where the text is making an excess/deficiency distinction worth preserving

## Explicit vs Inferential vs Editorial

- `explicit_textual` is used where Aquinas directly names the act, subtype, or opposed abuse:
  - `religion has_act prayer`
  - `idolatry excess_opposed_to religion`
  - `perjury deficiency_opposed_to oath`
- `strong_textual_inference` is used sparingly where the tract strongly supports a stable relation without naming it formulaically:
  - `religion has_act praise_of_god`
  - some narrower sacred-object alignments inside the sacrilege and simony material
- `structural_editorial` is reserved for question-level and article-level treatment correspondences, especially around `q.80` as the annexed-virtue bridge

## Ambiguities Not Yet Resolved

- `adjuration` still needs more human review on when it should be read as a positive reverential practice and when it edges toward abuse or coercive misuse.
- `undue_worship_of_true_god` is intentionally distinct from `idolatry`, but the boundary between defective mode and false-object worship still deserves closer review.
- `divination` and `superstitious_observance` are represented through conservative subtype nodes rather than an exhaustive late-medieval taxonomy.
- `sacred_time` was not introduced as a reviewed node in this pass because the tract support was cleaner for sacred things, persons, places, sacraments, and spiritual offices.
- `simony` is modeled through sacred and spiritual goods rather than broad market analogies; this is deliberate, but the exact best object set still deserves human review.

## Questions Needing Human Review First

- `II-II q.97` because temptation of God is still under-annotated and is now the tract review-packet target
- `II-II qq. 81–83` because the positive-act foundations of religion, devotion, and prayer remain lighter than the tract center
- `II-II qq. 87–89` because tithes, vows, and oaths put the most pressure on promise, offering, and divine-name distinctions
- `II-II qq. 92, 95, 96` because superstition-side subtype boundaries and sacred-object modeling are still the noisiest normalization areas
- `II-II q.100` because simony needs careful theological review to keep sacred exchange distinct from ordinary commercial injustice
