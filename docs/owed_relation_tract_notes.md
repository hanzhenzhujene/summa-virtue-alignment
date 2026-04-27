# Owed-Relation Tract Notes

## Scope

This reviewed block is intentionally limited to:

- `II-II, qq. 101–108`

It treats the annexed virtues and contrary defects concerned with distinct modes of what is due:

- origin-related debt
- excellence-related debt
- authority-related debt
- benefaction-related debt
- rectificatory due after prior wrong

## Normalization Decisions

- `piety`, `observance`, `dulia`, `obedience`, `gratitude`, and `vengeance` remain distinct virtues rather than being flattened into one generic justice note.
- `disobedience` and `ingratitude` remain distinct sins rather than being absorbed into broad vice language.
- `country` remains an object-level target of piety, not a person instance.
- `parent_role`, `person_in_dignity_role`, `human_lord_role`, `superior_role`, and `benefactor_role` remain role-level abstractions only.

## Due-Mode Modeling Decisions

- `due_mode` is explicit on every reviewed doctrinal annotation and edge in this tract.
- the tract uses five modes only:
  - `origin`
  - `excellence`
  - `authority`
  - `benefaction`
  - `rectificatory`
- `concerns_due_to` is used to show the kind of debt a virtue or contrary sin concerns.
- `owed_to_role` is reserved for stable role targets and is not used for person instances.
- `responds_to_command`, `responds_to_benefaction`, and `rectifies_wrong` keep authority, benefit, and rectificatory structures distinct.

## Role-Level Concept Modeling Decisions

- `parent_role` covers father/mother/parents as a role-level origin category.
- `person_in_dignity_role` is used for observance rather than introducing multiple low-support sub-roles.
- `human_lord_role` is used for strict dulia.
- `superior_role` is used for obedience/disobedience rather than multiplying ruler/prelate/master nodes too early.
- `benefactor_role` is used for gratitude/ingratitude.
- `wrongdoer_role` remains in the registry overlay for future use, but the current reviewed block stays focused on `prior_wrong`, `punishment`, and `rectification`.

## Explicit vs Inferential vs Editorial

- `explicit_textual` is used where Aquinas directly states the due relation, object, or contrary:
  - `dulia species_of observance`
  - `obedience responds_to_command command`
  - `ingratitude contrary_to gratitude`
- `strong_textual_inference` is used sparingly for tract placement:
  - `piety annexed_to justice`
  - `gratitude annexed_to justice`
  - `vengeance annexed_to justice`
- `structural_editorial` is reserved for question/article treatment correspondences and does not appear in default doctrinal exports.

## Ambiguities Not Yet Resolved

- `dulia` still carries a dual sense in `q.103`: broad reverence to human excellence and strict servant-to-lord reverence.
- `observance` in `q.102 a.2` touches honor, service, command, and repayment of benefits; the current model keeps the tract centered on excellence rather than trying to absorb obedience and gratitude into observance.
- `gratitude` and `ingratitude` remain partially parsed questions, so article-level review on timing and degrees of repayment is still lighter than it should be.
- `vengeance` is intentionally modeled as rectificatory response rather than generic anger, but later human review may still want finer distinction between punitive medicine, restraint, and exemplary punishment.

## Questions Needing Human Review First

- `II-II q.104` because it is under-annotated relative to candidate burden and carries the highest pressure on authority/command structure
- `II-II q.106` because gratitude is partially parsed and central to benefaction-related debt
- `II-II qq. 101–103` because piety / observance / dulia still put the most pressure on due-mode distinctions and role normalization
- `II-II q.108` because vengeance needs continued review to keep rectificatory structure from drifting into generic anger or retaliation language
