---
title: Repair loops
type: evidence
tags: [repair, candidates, feedback]
updated: 2026-09-23
---

# Repair loops

## Diminishing returns are measured
- **Most of the achievable gain lands in the first 2–4 repair attempts**; later ones add almost nothing.
  Measured with low-cost models. [2026](https://arxiv.org/abs/2607.05197), [across scales](https://arxiv.org/abs/2604.10508)
- Loop behaviour depends **more on orchestration, validation and feedback design than on the model**. Same source.

## Weak models repair badly
*Is Self-Repair a Silver Bullet?* (ICLR 2024): counting the cost of repair, gains are often modest or absent, and
weaker models introduce new errors while repairing. Two findings drive our design:
1. **Diverse first attempts beat repeated repair** of one attempt.
2. **Feedback quality dominates:** human-written feedback instead of the model's own fixed **1.58×** more programs.
   Models are poor at explaining why their own code is wrong. [paper](https://arxiv.org/abs/2306.09896)

## Design consequences
- **4 parallel candidates per card**, first to pass every gate wins.
- **Feedback is extracted by code** — failing assertion, expected vs actual, line, traceback — never model-written.
- Repair capped at **2–3** attempts, then escalate rather than retry.
- Each attempt gets a fresh context, because of self-conditioning ([[error-compounding]]).

Related: [[small-model-capability]], [[test-quality]]
