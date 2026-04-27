# Review Queue Guide

## Purpose

The corpus review queue turns broad candidate output into manageable human review work.

Primary files:

- `data/processed/corpus_review_queue.json`
- `data/processed/review_packets/`

## What The Queue Contains

The queue summarizes:

- question-level candidate counts
- reviewed annotation counts
- ambiguity counts
- candidate node-type distribution
- candidate relation-type distribution
- confidence buckets
- suggested question packet

Use it to prioritize areas where:

- candidate density is high
- reviewed coverage is zero or thin
- ambiguity is high
- parse status is `partial`

## What A Review Packet Contains

Each packet includes:

- passage citation
- stable passage id
- full passage text
- candidate concept matches
- candidate relation proposals
- nearby reviewed annotations if any
- blank reviewer decision slots

The packet is meant to be used alongside the reviewed annotation guide, not as a substitute for it.

## Suggested Workflow

1. start with the suggested packet in `corpus_review_queue.json`
2. verify each concept match against the passage text
3. reject or defer ambiguous matches that need broader normalization work
4. approve only relations that remain evidence-first after compression into a graph edge
5. record unresolved cases for registry or alias-table follow-up

## Current First Packet

The current example packet is:

- `data/processed/review_packets/st_i-ii_q100_corpus_review_packet.md`

It is intentionally outside the original pilot subset, because the goal is to open the full-corpus review workflow without pretending the whole corpus is already reviewed.
