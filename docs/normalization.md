# Normalization

## Goal

The pilot normalization layer exists to help reviewed annotations point to stable concept ids without pretending that every English wording variant is safely equivalent.

The design is intentionally conservative.

## Registry Model

Each pilot concept record separates:

- `concept_id`
- `canonical_label`
- `node_type`
- `aliases`
- `description`
- `notes`
- `source_scope`

The canonical label is the stable display name. Aliases are only added when they are safe enough to help lookup and review.

## Matching Order

The normalization utilities currently resolve labels in this order:

1. exact hand-authored override
2. normalized hand-authored override
3. declared ambiguity override
4. exact canonical-label or alias match
5. normalized canonical-label or alias match

The normalization form uses:

- Unicode NFKC normalization
- case folding
- punctuation stripping
- whitespace collapse
- `&` normalized to `and`

## Hand-Authored Alias Table

Pilot alias overrides live in `data/gold/pilot_alias_overrides.yml`.

It supports three buckets:

- `exact`
- `normalized`
- `ambiguous`

Use `ambiguous` whenever a label really can name more than one concept in the pilot layer.

## Current High-Risk Ambiguities

These labels currently require especially careful review:

- `love`
  - may indicate the passion of love
  - may indicate the theological virtue of charity
- `law`
  - may indicate law in general
  - may indicate a specific law type
- `grace`
  - may indicate grace in general
  - may indicate operating or cooperating grace
- `virtue`
  - may indicate virtue generically
  - may indicate a specific virtue in context
- `ultimate end`
  - often aligns closely with beatitude
  - should not be silently flattened when the passage needs the distinction preserved
- `false prudence` and `prudence of the flesh`
  - related, but not identical shorthand
- `presumption`
  - may indicate the hope-tract sin against hope
  - may indicate the fortitude-parts vice opposed to magnanimity
- `fear`
  - can drift between passion language and vice language in nearby fortitude material
- `greatness`
  - may tempt a false merge between `magnanimity` and `magnificence`
- `honor`
  - may indicate rendered honor in the owed-relation tract
  - may indicate honor as social good harmed in verbal-injury material
  - may indicate honor as recognition in the magnanimity tract

## What The Normalizer Does Not Do

It does not:

- use fuzzy string matching
- infer equivalence from tract location alone
- collapse generic concepts into specific subtypes automatically
- resolve theological disputes by convenience

If a human reader would hesitate, the code should hesitate too.

## Review Rules

When adding an alias:

- prefer exact wording that really recurs in the pilot subset
- keep ambiguous labels out of ordinary aliases when possible
- put difficult cases into notes or explicit ambiguity declarations

When a mapping remains uncertain:

- keep the annotation in candidate review, or
- keep the concept link narrow and explain the risk in `notes`

The normalization layer should reduce clerical drift, not conceal doctrinal complexity.

## Fortitude-Parts 129-135 Risks

The fortitude-parts tract adds several high-risk distinctions that the normalizer must not flatten:

- `magnanimity` vs `magnificence`
  - one is honor- and worthiness-related
  - the other is expenditure- and great-work-related
- `presumption_magnanimity` vs hope-tract `presumption`
  - same English label
  - different tract, different doctrinal role
- `honor_recognition` vs broader `honor`
  - tract-local recognition/attestation
  - not the same as owed honor or harmed honor
- `waste_magnificence` vs `prodigality`
  - both can look like excessive expenditure in English
  - the magnificence tract keeps its own work-proportion structure

When these cases arise, prefer tract-local concept ids and explicit disambiguation notes over convenience merges.

## Fortitude Closure 136-140 Risks

The fortitude-closure tract adds another set of distinctions that the normalizer must not flatten:

- `patience` vs `perseverance_virtue`
  - both belong near fortitude
  - they are not interchangeable virtue labels
- act-level `perseverance` vs virtue-level `perseverance_virtue`
  - the earlier corpus registry already contains an act-level perseverance concept
  - the fortitude closure tract therefore uses a tract-local virtue id and avoids the bare alias `perseverance`
- `fortitude` vs `fortitude_gift`
  - same English root
  - different node type and doctrinal role
- `longanimity_fortitude` vs `patience`
  - close enough to tempt merger
  - still not identical without tract-specific warrant
- `constancy_fortitude` vs `perseverance_virtue`
  - closely compared in `q.137`
  - still not identical without tract-specific warrant

When these cases arise, prefer:

- distinct concept ids
- narrower aliases
- explicit disambiguation notes
- editorial correspondence over doctrinal collapse when the tract is comparative rather than identificatory

## Temperance 141-160 Risks

The temperance phase-1 tract adds another set of distinctions that the normalizer must not flatten:

- `abstinence` vs `fasting`
  - one is a virtue / temperance-part placement
  - the other is a tract-local practice or act treated under that virtue
- `sobriety` vs `abstinence`
  - both concern bodily moderation
  - they do not share the same matter domain
- `gluttony` vs `drunkenness`
  - both are consumption-related
  - they are not the same vice and must not collapse into one generic excess node
- `chastity` vs `virginity`
  - one is the broader sexual-matter virtue
  - the other is a narrower tract-local concept and must not silently inherit chastity's part placement
- `lust` vs tract-local parts of lust
  - the tract may support species structure
  - it does not justify collapsing all sexual vice language into one label
- `purity_temperance` vs generic `purity`
  - the q.143 taxonomy uses a temperance-local term
  - the normalizer should not silently widen it to any purity language elsewhere
- `continence` vs `temperance`
  - closely related in moral psychology
  - still not interchangeable virtue labels
- `meekness` vs `clemency`
  - both appear in `q.157`
  - they must not merge merely because they share anger-related material
- `anger` vs `anger_vice`
  - tract language can shift between passion-level and vice-level usage
  - the normalizer must keep the ambiguity explicit when the passage does not settle it
- `modesty_general` vs later humility / studiousness / exterior-modesty material
  - the current block treats modesty in general
  - later temperance closure work should not be back-projected into `q.160`

The tract also surfaced a taxonomy-specific normalization constraint:

- `q.143` explicitly supports:
  - integral parts:
    - `shamefacedness`
    - `honesty_temperance`
  - subjective parts:
    - `abstinence`
    - `sobriety`
    - `chastity`
    - `purity_temperance`
  - potential parts:
    - `continence`
    - `meekness`
    - `modesty_general`
- therefore the normalizer should not silently add:
  - `fasting` as a subjective part
  - `virginity` as a subjective part
  - `clemency` as a potential part
  unless a later reviewed passage explicitly warrants that narrower tract claim

When these cases arise, prefer:

- tract-local ids
- narrower aliases
- ambiguity overrides for collision-prone words such as `anger`
- editorial correspondence rather than doctrinal identity when the tract is comparative or taxonomic rather than identificatory

## Temperance Closure 161-170 Risks

The temperance-closure tract adds another set of distinctions that the normalizer must not flatten:

- `humility` vs `modesty_general`
  - humility is reviewed in `q.161`
  - `modesty_general` is already a potential part from `q.160`
  - the later tract compares them, but does not justify identity
- `pride` vs `adams_first_sin`
  - Adam's first sin is modeled as a tract-local doctrinal case
  - it is not a synonym for the generic vice node
- `studiousness` vs `curiosity`
  - this tract treats curiosity as disordered inquiry
  - do not import neutral modern curiosity language into the registry
- `external_behavior_modesty` vs `outward_attire_modesty`
  - both belong under later external modesty work
  - they are not interchangeable species
- `modesty_general` vs the external-modesty species
  - `q.160` remains the general potential-part node
  - `qq.168–169` introduce narrower outward-expression material
- precept nodes vs precept targets
  - `precepts_of_temperance` and `precepts_of_temperance_parts` are not aliases for `temperance`, `humility`, `meekness`, or `adultery_lust`
  - the normalizer must not treat every precept target as a precept node

The tract also surfaced a case-modeling normalization constraint:

- `Adam's first sin`
  - should remain a case-level node
  - should not silently widen into every reference to original sin, punishment, or temptation
- punishment and temptation concepts
  - should stay few and tract-local
  - do not proliferate a large narrative ontology from `qq.163–165`

When these cases arise, prefer:

- distinct concept ids
- narrow aliases
- explicit disambiguation notes
- case-level reviewed relations instead of generic vice or consequence edges
- precept focus keyed to actual precept nodes and precept relations, not to every linked concept
