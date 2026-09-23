---
title: Open objections
type: risk-register
tags: [risk, debate, falsifiable]
updated: 2026-09-23
---

# Open objections

The strongest arguments against this design, each with the evidence behind it, the current answer, and what would
settle it. **An objection is only closed by a measurement, never by an argument.**

| # | Objection | Evidence | Current answer | Status |
|---|---|---|---|---|
| 1 | **The weakest model does the hardest job** — a 1B model designs the contracts, and coordination is where multi-agent systems fail | [[small-model-capability]], [[agent-loop-failures]] | Contracts are written first, checked for type/name consistency by code; an end-to-end test catches interface errors | **Open** — needs the 20-card pilot |
| 2 | **Tests written by a small model are weak** — 29–60% defect detection; 7B models produced only crash-detection | [[test-quality]] | Tests from fixed examples, written by a different model, plus mutation testing | **Open** — target: catch 8 of 10 injected bugs |
| 3 | **Test-gating invites cheating** — hardcoding, editing tests, deleting assertions | [[reward-hacking]] | Held-out tests, immutable test files, edit detection, exclusion from training data | **Open** — must be measured, not assumed |
| 4 | **Retries degrade small models** — self-conditioning on their own errors | [[error-compounding]], [[repair-loops]] | Fresh context per attempt, code-written feedback, candidates over repairs, cap 2–3 | Partly answered by design; needs measuring |
| 5 | **Compounding maths** — 95% per card gives 21% on a 30-card project | [[error-compounding]] | Goal is cheap recovery, not high per-card success; blocked cards are the real metric | **Open** — set a tolerance for blocked cards |
| 6 | **Opportunity cost** — a frontier model does the same job in minutes | [METR](https://metr.org/time-horizons/) | Valid only if the goal is privacy, offline use, cost or the research itself — not raw capability | **Accepted**: this is not a capability play |
| 7 | **The station may not work, and its safety check is weak** — survivorship bias; a 50-card canary cannot detect a 5-point regression; the promotion bar may be unreachable | [[self-improvement-fragility]] | Held-out projects, teacher-model data for failures | **Open** — needs a power calculation for canary size and threshold |
| 8 | **The ceiling is the human-written spec and acceptance tests** | — | Possibly true; then the honest claim is "a code generator with good hygiene", not "builds any project" | **Open** — decide what success means |

## Falsification tests (cheap, before committing months)
1. **Decomposition pilot:** a 1B model splits 3 real goals into cards. How many contracts need human correction?
2. **Mutation test:** 10 injected bugs; do the generated tests catch 8?
3. **Gaming probe:** run cards where hardcoding passes the visible tests. How often does it happen?
4. **Blocked-card rate:** one real 30-card project. How many cards end blocked?

Related: [[../../PLAN|PLAN]]
