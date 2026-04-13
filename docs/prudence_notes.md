# Prudence Notes

## Normalization Decisions

- Use `Prudence` as the stable core virtue node for `QQ. 47–56`.
- Represent prudence-part concepts as `prudence_part` nodes with an explicit `part_taxonomy`.
- Normalize the integral part named `reason` as `Reasoning` in the reviewed registry to keep it distinct from the faculty `Reason`.
- Keep `Understanding or Intelligence` as one prudence-part node and explicitly note its distinction from the separate gift of understanding elsewhere in the corpus.
- Normalize `political economy` and `domestic economy` article titles into `Political Prudence` and `Domestic Prudence` at the concept-registry layer while preserving source wording in article metadata.

## Part-Taxonomy Decisions

- `integral_part_of`: memory, intelligence, docility, shrewdness, reasoning, foresight, circumspection, caution
- `subjective_part_of`: regnative prudence, political prudence, domestic prudence, military prudence
- `potential_part_of`: euboulia, synesis, gnome

These are not exported as a generic `part_of`.

## Explicit vs Inferential vs Editorial

Mostly explicit:

- Q48 taxonomy enumeration
- Q50 subjective-part species language
- Q52 counsel corresponding to and perfecting prudence
- Q53 precipitation contained under imprudence
- Q54 negligence pertaining to imprudence and opposed to solicitude
- Q55 craftiness opposed to prudence

Mostly strong inference:

- prudence residing in reason in Q47 a1
- prudence of the flesh being opposed to prudence rather than merely counterfeit
- unlawful temporal and future solicitude as prudence-opposed defects
- guile and fraud as executional derivatives of craftiness

Structural-editorial only:

- question-level taxonomy grouping nodes
- tract-organization correspondences such as Q49 = integral-parts block

## Ambiguous Or Deferred Mappings

- false prudence in Q47 a13 is kept distinct from later counterfeit prudence forms, but its final edge family still needs human review
- the boundary between lawful foresight and unlawful future solicitude still needs careful theological review
- the exact app treatment of solicitude as an act node may need refinement if a fuller prudential act taxonomy is introduced later
- gnome's relation to higher-principle judgment is intentionally kept conservative in reviewed edges

## Human Theological Review First

Priority order:

1. `Q56` precepts of prudence
2. `Q49` integral-part disambiguations
3. `Q47` false prudence and core prudence-location relations
4. `Q55` unlawful solicitude boundary cases
