---
title: Test quality — the weakest foundation
type: evidence
tags: [tests, verification, risk]
updated: 2026-09-23
---

# Test quality — the weakest foundation

The whole design rests on tests deciding truth. The evidence says model-written tests are the shakiest part.

## Evidence
- LLM-generated tests detect only **29.3–60.0%** of defects. [empirical study](https://arxiv.org/html/2406.18181v1)
- For 7B and 13B models, **every defect found was a runtime crash** — they could not write meaningful assertions.
  Our models are smaller than that.
- Tests run but **rely on weak assertions, miss edge cases**, and it is hard to tell a wrong assertion from a real bug.
- **Weaker models produce more false positives**, at a rate that scales inversely with capability.
  [inference-scaling limits](https://arxiv.org/pdf/2411.17501)

## Why this is dangerous *here*
With a ratchet, a wrong test does not cause drift — it causes **permanent lock-in**. Too-weak tests bless broken
code as `done`; too-strict tests block correct code forever. A stuck project can look stable.

## Partial mitigations (none sufficient alone)
- Tests are derived from **input→output examples fixed in the card before any code exists**.
- The test is written by a **different model** than the code.
- If **every candidate fails the same assertion**, suspect the test, not the code. Catches strict tests only.
- **Mutation testing**: inject deliberate bugs and require the tests to catch them. The only check that measures
  test *strength* — currently the strongest answer to [[open-objections]] #2.
- Human-written acceptance tests live in RAW for anything that matters.

Related: [[reward-hacking]], [[repair-loops]], [[open-objections]]
