# Justice Core Notes

## Normalization Decisions

- `right` is modeled as a stable object-level juridical concept, with `natural_right`, `positive_right`, `right_of_nations`, `dominion_right`, and `paternal_right` kept distinct rather than collapsed.
- `public_execution`, `private_execution`, `unjust_killing`, and `suicide` are kept distinct so the tract does not flatten licit punitive killing into generic homicide language.
- verbal injuries are split by harmed domain instead of merged into one vice bucket:
  - `reviling` -> `honor`
  - `backbiting` -> `reputation`
  - `tale_bearing` -> `friendship`
  - `derision` -> `honor`
- judicial roles stay role-level abstractions only:
  - `judge_role`
  - `accuser_role`
  - `defendant_role`
  - `witness_role`
  - `advocate_role`

## Justice-Species Decisions

- `general_justice` and `particular_justice` remain distinct.
- `distributive_justice` and `commutative_justice` are modeled as species of `particular_justice`, not just broad notes under `justice`.
- `respect_of_persons` is tied specifically to distributive justice and distributional fairness, not to justice in an undifferentiated way.

## Domain And Process Modeling Decisions

- harmed-domain relations use stable domain nodes instead of reusing virtue or vice nodes:
  - `life`
  - `bodily_integrity`
  - `personal_liberty`
  - `property`
  - `honor`
  - `reputation`
  - `friendship`
  - `truth_in_legal_proceedings`
  - `fairness_in_distribution`
  - `fairness_in_exchange`
- process corruption is represented separately from private harm:
  - `corrupts_process`
  - `abuses_role`
- restitution is represented explicitly through `requires_restitution` rather than by loosely inferring that every injury should point to `restitution`.

## Explicit vs Inferential vs Editorial

- `explicit_textual` is used where the passage directly states the opposition, species, or restitutional requirement:
  - `respect_of_persons opposed_by distributive_justice`
  - `commutative_justice has_act restitution`
  - `usury contrary_to justice`
- `strong_textual_inference` is used where the relation is clearly supported but not formulaically named:
  - `right_of_nations species_of right`
  - `private_execution corrupts_process judicial_process`
  - `transgression contrary_to justice`
- `structural_editorial` is reserved for question-level tract correspondences and should not be read as doctrinal graph fact.

## Ambiguities Not Yet Resolved

- `right_of_nations` still needs deeper human review on whether it should remain only `species_of right` or receive a tighter normalized relation to `natural_right` or `positive_right`.
- `public_execution` vs `unjust_killing` remains intentionally conservative. The tract records lawful public killing separately rather than pretending the corpus has one undifferentiated homicide node.
- `transgression` and `omission` are kept in the justice tract with `strong_textual_inference`, because Aquinas treats them partly as broader moral categories and partly as quasi-integral to justice.
- `false_accusation`, `calumnious_defense`, and `false_witness` are all tied to `truth_in_legal_proceedings`, but the precise boundary between direct injury to reputation and corruption of judicial truth still deserves more theological review.

## Questions Needing Human Review First

- `II-II q.59` because the general ontology of `injustice` still has low reviewed density relative to its candidate burden.
- `II-II q.79` because omission/transgression sit at the edge between justice-specific and broader moral classification.
- `II-II q.62` because restitution propagation beyond theft/robbery needs tighter article-by-article review.
- `II-II qq. 68–71` because accusation, defense, testimony, and advocacy create the highest pressure on the new role/process schema.
