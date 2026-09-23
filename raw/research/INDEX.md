---
title: Research Index
type: index
updated: 2026-09-23
---

# Research Index

Evidence behind the design in [[../../PLAN|PLAN]]. Every claim here carries a source. This folder is RAW:
agents may read it, never write it. Notes are atomic — one topic each — and linked rather than nested.

## The problem we are betting against
- [[small-model-capability]] — what 1B–3B models can and cannot do
- [[error-compounding]] — why per-step accuracy decides project-level success
- [[repair-loops]] — retries have a hard ceiling, and weak models repair badly
- [[test-quality]] — tests written by small models are the weakest foundation
- [[reward-hacking]] — passing tests is not the same as solving the task
- [[agent-loop-failures]] — how agent loops fail structurally

## What we borrow from
- [[self-evolving-agents-survey]] — the field's reference map: Three Laws, the MASE framework, every optimiser family
- [[mase-mapping]] — where our design sits in that framework, and the six things it says we are missing
- [[hermes-agent]] — memory hygiene done well, loop safety done poorly
- [[wiki-memory]] — Karpathy's LLM Wiki, A-MEM, and Obsidian-style memory
- [[self-improvement-fragility]] — why learned lessons need probation
- [[blackboard-and-tape]] — prior art for control living in shared state

## Our own measurements and choices
- [[runtime-measurements]] — llama.cpp on the RTX 3060, measured
- [[model-lineup]] — models, scores, licences
- [[open-objections]] — the unanswered arguments against the design
