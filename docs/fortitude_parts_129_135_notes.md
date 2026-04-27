# Fortitude Parts 129-135 Notes

## Scope

This reviewed block is intentionally limited to:

- `II-II, qq. 129–135`

It treats two related but distinct sub-clusters:

- `qq. 129–133`: magnanimity, honor, worthiness, and the opposed excesses or deficiency
- `qq. 134–135`: magnificence, great expenditure, great work, and the opposed vices

## Normalization Decisions

- `magnanimity` and `magnificence` remain distinct concept ids and distinct tract neighborhoods.
- `presumption_magnanimity` remains distinct from the hope-tract `presumption`.
- `honor_recognition` is used instead of generic `honor` so the tract does not collide with owed-honor or harmed-honor uses elsewhere.
- `waste_magnificence` remains distinct from `prodigality`; the magnificence tract is specifically about proportion between expenditure and work.

## Excess / Deficiency Modeling Decisions

- opposition-mode structure is explicit rather than being flattened into a generic `opposed_by` edge
- excess-mode reviewed relations currently include:
  - `presumption_magnanimity excess_opposed_to magnanimity`
  - `ambition excess_opposed_to magnanimity`
  - `vainglory excess_opposed_to magnanimity`
  - `waste_magnificence excess_opposed_to magnificence`
- deficiency-mode reviewed relations currently include:
  - `pusillanimity deficiency_opposed_to magnanimity`
  - `meanness_magnificence deficiency_opposed_to magnificence`
- `waste_magnificence contrary_to meanness_magnificence` is kept as a separate vice-to-vice opposition, not silently folded into one of the excess/deficiency edges

## Honor-Vs-Expenditure Modeling Decisions

- the tract uses two explicit clusters:
  - `honor_worthiness`
  - `expenditure_work`
- honor-related reviewed structure uses:
  - `concerns_honor`
  - `concerns_worthiness`
- expenditure-related reviewed structure uses:
  - `concerns_great_expenditure`
  - `concerns_great_work`
- `related_to_fortitude` remains separate from both clusters so annexed-to-fortitude placement does not collapse the internal tract distinction

## Explicit vs Inferential vs Editorial

- `explicit_textual` is used where the tract directly states the relation:
  - `magnanimity concerns_honor honor_recognition`
  - `presumption_magnanimity excess_opposed_to magnanimity`
  - `magnificence concerns_great_work great_work`
  - `fortitude has_act security_assurance`
- `strong_textual_inference` is used where the tract clearly supports the structure without a formulaic statement:
  - `ambition excess_opposed_to magnanimity`
  - `vainglory excess_opposed_to magnanimity`
  - `pusillanimity deficiency_opposed_to magnanimity`
  - `meanness_magnificence deficiency_opposed_to magnificence`
- `structural_editorial` is reserved for question/article treatment correspondences and stays out of default doctrinal graph exports.

## Ambiguities Not Yet Resolved

- `q.129` is now structurally well covered, but it still concentrates multiple adjacent ideas:
  - honor
  - worthiness
  - confidence
  - security or assurance
  - goods of fortune
- `q.130` still needs human review because the tract-specific `presumption_magnanimity` label can easily be mistaken for the hope-tract `presumption`.
- `q.132` remains normalization-heavy because `glory`, `honor`, `vainglory`, and later pride-language sit close together.
- `q.135` needs continued review so `waste_magnificence` does not drift into generic prodigality.

## Questions Needing Human Review First

- `II-II q.130` because the fortitude-tract presumption must stay distinct from the hope-tract presumption
- `II-II q.129` because it is still under-annotated relative to passage count and packs several adjacent act/domain distinctions into one question
- `II-II q.132` because honor, glory, and vainglory remain the strongest local normalization pressure point
- `II-II q.135` because excess-vs-deficiency and magnificence-vs-liberality boundaries still deserve close human review
