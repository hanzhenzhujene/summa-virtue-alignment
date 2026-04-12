# Source Policy

## Primary source for this sprint

This repository uses the New Advent English *Summa Theologiae* pages as the initial parsing and display basis for Milestones 0 and 1:

- `https://www.newadvent.org/summa/2.htm`
- `https://www.newadvent.org/summa/3.htm`

The parser depends on New Advent's stable question and article structure:

- part landing pages list question links
- question pages contain ordered article anchors
- article bodies contain objection, sed contra, respondeo, and reply sections

## Redistribution stance

Raw HTML redistribution is not assumed to be safe merely because the underlying translation is old.

Because of that:

- raw fetched HTML is cached locally for build reproducibility only
- raw HTML is **not** committed to the repository
- only derived structured artifacts and source metadata are committed

Local cache location:

- `data/cache/newadvent/`

This directory is ignored by version control.

## What we do commit

Derived artifacts may be committed when they are generated from the in-scope corpus:

- question records
- article records
- segment records
- explicit intra-*Summa* cross-reference records

Each record preserves provenance fields such as:

- `source_id`
- `source_url`
- source part URL where relevant
- deterministic record hashes

## Verification source

Corpus Thomisticum is useful as a verification and cross-check source, especially for:

- verifying question/article structure
- checking Latin wording where an English rendering is ambiguous
- sanity-checking suspicious cross-references

For this sprint, Corpus Thomisticum is **not** the primary parser target.

## Policy summary

- parse from a stable English source
- keep raw HTML out of git
- commit only derived structured data plus provenance
- preserve deterministic hashes and stable IDs

