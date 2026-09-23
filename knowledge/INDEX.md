---
title: Research Index
type: index
updated: 2026-09-23
---

# Research Index

> **Library rules.** This folder is **read-only**. Nothing here — notes, sources, papers — changes without the
> owner's explicit approval, including corrections. Agents may never write to `knowledge/`; the permissions gate
> rejects it. Proposals go to `proposals/`, with the evidence attached, and wait.

Evidence behind the design in [[../PLAN|PLAN]]. Every claim here carries a source. Notes are atomic — one topic each — and linked rather
than nested, so the folder opens as a graph in Obsidian.

**Papers:** [[papers/sources|every cited URL]], and 16 PDFs in `papers/` — not committed, rebuilt with
`python knowledge/papers/fetch.py`.

## The problem we are betting against
- [[small-model-capability]] — what 1B–3B models can and cannot do
- [[error-compounding]] — why per-step accuracy decides project-level success
- [[repair-loops]] — retries have a hard ceiling, and weak models repair badly
- [[test-quality]] — tests written by small models are the weakest foundation
- [[reward-hacking]] — passing tests is not the same as solving the task
- [[agent-loop-failures]] — how agent loops fail structurally

## What we borrow from
- [[self-evolving-agents-survey]] — the field's reference map: Three Laws, the MASE framework, every optimiser family
- [[evoagentx]] — the reference implementation: optimisers, MAP-Elites, and a first-class human-in-the-loop module
- [[agentevolver]] — RL training framework: self-generated tasks, experience reuse, per-step credit assignment
- [[awesome-self-evolving-agents]] — the curated corpus (367 entries, May 2026): what appeared after the survey
- [[mase-mapping]] — where our design sits in that framework, and the six things it says we are missing
- [[hermes-agent]] — memory hygiene done well, loop safety done poorly
- [[wiki-memory]] — Karpathy's LLM Wiki, A-MEM, and Obsidian-style memory
- [[self-improvement-fragility]] — why learned lessons need probation
- [[blackboard-and-tape]] — prior art for control living in shared state

## Our own measurements and choices
- [[runtime-measurements]] — llama.cpp on the RTX 3060, measured
- [[model-lineup]] — models, scores, licences
- [[open-objections]] — the unanswered arguments against the design
