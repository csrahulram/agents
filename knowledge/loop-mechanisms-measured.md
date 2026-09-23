---
title: Loop mechanisms, measured
type: measurement
tags: [experiment, candidates, repair, escalation, bottleneck]
harness: bench/card_loop.py · bench/cards/cards.json
updated: 2026-09-23
---

# Loop mechanisms, measured on this machine

First real test of the mechanisms meant to let 1.5B models survive a long run.
10 function-sized cards with hidden tests, `qwen2.5-coder:1.5b` at 4 parallel slots, every candidate executed in
an ephemeral container with no network. **n=10, single run** — directional, not conclusive.

## Strict scoring — every check, including edge cases
| Mechanism | Per-card success |
|---|---|
| pass@1, one candidate | **40%** |
| pass@4, four parallel candidates | **60%** |
| repair with fresh context (after a failed first candidate) | 50% |
| repair with failed attempts carried in context | 40% |

## Fair comparison — identical held-out checks, only the coder's view differs
| | pass@1 | pass@4 | repair fresh | repair carried |
|---|---|---|---|---|
| Coder does not see the tests | 70% | 90% | 80% | 70% |
| Coder sees 60% of the checks | **80%** | 90% | **90%** | 80% |

## Findings
1. **Candidates beat retries.** +20 points in both scorings, for 1.7 s of wall clock. The strongest single lever,
   as [[repair-loops]] predicted from the literature.
2. **Fresh context beats carried context by 10 points, in both scorings.** Consistent with the self-conditioning
   result in [[error-compounding]]: showing a small model its own failures degrades the next attempt.
   Direction reproduced twice here; magnitude uncertain at n=10.
3. **Test strictness dominates every other variable.** The same code scores 40% or 70% purely on how strict the
   checks are. A model writing lenient tests would make the system *look* like it works — so mutation testing is
   load-bearing, not optional. See [[test-quality]].
4. **Escalation is diversity, not a ladder.** On the hard cards, `qwen2.5-coder:3b` fixed `format_bytes` but
   **failed `parse_duration`, which the 1.5B solved**. Bigger was not uniformly better; the *union* of two model
   families is what raises coverage. Escalation should read "try a different model", not "try a bigger one".
5. **Failures are mostly single missed details, not incompetence.** Of four hard failures: assigning into a tuple
   (6 of 7 checks otherwise fine), stripping apostrophes the spec said to keep, `512.0 B` instead of `512 B`.
   Only `parse_duration` was a real reasoning failure. Prose specs get skimmed; concrete checks get followed.
6. **Run-to-run variance is visible.** `parse_duration` passed pass@4 in one run and failed in another. Any
   benchmark number must be avg@k over repeats, never a single run.

## The honest arithmetic
Stacking the mechanisms — 4 candidates → fresh-context repair → a different model — gets roughly **80% per card
under strict scoring**, up from 40%. On a 30-card project that still implies about **6 blocked cards** needing a
human. That is the real cost of the design, and what the recovery machinery must keep survivable
([[error-compounding]]).

Two cards (`merge_intervals`, `word_frequencies`) defeated every model and every mechanism. Those must fail
loudly into `blocked` rather than consume the retry budget.

## Effect on the open objections
- **#4 (retries degrade small models)** — supported, and mitigated: fresh context per attempt, candidates over repairs.
- **#5 (compounding maths)** — quantified: ~80% per card, ~6 blocked cards per 30-card project. Still open as a
  question of tolerance, not of fact.
- **#2 / #3 (test quality and gaming)** — sharpened, not answered. Test strictness moved results by 30 points,
  which is larger than any mechanism measured here. Next experiment: can a 1B model write tests that catch
  injected bugs?

Related: [[open-objections]], [[repair-loops]], [[error-compounding]], [[runtime-measurements]]
