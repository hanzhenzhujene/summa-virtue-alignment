# Connected Virtues 109-120 Notes

## Scope

This reviewed block is intentionally limited to:

- `II-II, qq. 109–120`

It treats four related but distinct sub-clusters:

- `qq. 109–113`: truthfulness and false self-presentation
- `qq. 114–116`: ordinary social interaction
- `qq. 117–119`: right use of external goods
- `q.120`: epikeia / equity

## Normalization Decisions

- `truth_self_presentation` is a tract-local truthfulness node and is not merged with faith-tract truth or `first_truth`.
- `lying`, `dissimulation`, `hypocrisy`, `boasting`, and `irony` remain distinct nodes rather than being flattened into one falsehood bucket.
- `friendliness_affability` remains distinct from `charity`.
- `liberality` remains distinct from `almsgiving`, `mercy`, and broader exchange-justice language.
- `epikeia` remains distinct from generic fairness and generic justice language.

## Sub-Cluster Modeling Decisions

- `connected_virtues_cluster` is explicit on every reviewed doctrinal annotation and edge in this tract.
- the tract uses four clusters only:
  - `self_presentation`
  - `social_interaction`
  - `external_goods`
  - `legal_equity`
- tract-specific relation families remain narrow:
  - `concerns_self_presentation`
  - `concerns_social_interaction`
  - `concerns_external_goods`
  - `corrects_legal_letter`
  - `preserves_intent_of_law`
- `has_act` is used conservatively inside the liberality cluster for tract-local giving/retaining structure rather than as a broad generosity schema.

## Schema-Extension Decisions

- `self_presentation`, `social_interaction`, and `external_goods` are modeled as stable tract domains rather than loose notes.
- `legal_letter` is modeled as a law-level concept because the equity question is specifically about rigid literal application of law.
- `intent_of_law` and `common_good` remain separate so that epikeia can be shown as preserving lawful intention without collapsing intention into end language generally.

## Explicit vs Inferential vs Editorial

- `explicit_textual` is used where Aquinas directly states the contrary, subtype, or tract-local structure:
  - `truth_self_presentation opposed_by lying`
  - `hypocrisy species_of dissimulation`
  - `liberality opposed_by prodigality`
  - `epikeia corrects_legal_letter legal_letter`
- `strong_textual_inference` is used sparingly for annexed-to-justice placement and a few tract-structuring relations where the passage support is strong but less formulaic:
  - `truth_self_presentation annexed_to justice`
  - `friendliness_affability annexed_to justice`
  - `liberality annexed_to justice`
- `structural_editorial` is reserved for question/article treatment correspondences and does not appear in default doctrinal exports.

## Ambiguities Not Yet Resolved

- `q.109` still carries heavy ambiguity because English `truth` can drift toward broader theological or generic truth language.
- `q.110` and `q.111` remain partially parsed, so lying, dissimulation, and hypocrisy support is usable but still lighter than ideal.
- `hypocrisy` is currently modeled as a species of `dissimulation`; this is textually grounded in the tract, but later human review may still want a more explicit distinction between feigned holiness and broader concealment.
- `irony` is intentionally treated in its Thomistic moral sense and not in a modern rhetorical sense, but the English label still creates normalization pressure.
- `q.120` is structurally clear yet doctrinally risky because `epikeia` can be flattened too easily into generic fairness.

## Questions Needing Human Review First

- `II-II q.109` because it is the generated review-packet target and remains highly ambiguous relative to reviewed density
- `II-II q.110` because lying and false self-presentation remain partially parsed and candidate-heavy
- `II-II q.117` and `q.118` because liberality and covetousness still carry the highest external-goods normalization pressure
- `II-II q.120` because equity must stay tethered to legal letter and intent of law rather than drifting into generic justice language
