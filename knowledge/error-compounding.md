---
title: Error compounding and long horizons
type: evidence
tags: [reliability, horizon, math]
updated: 2026-09-23
---

# Error compounding and long horizons

## The arithmetic
- A 10-step pipeline needs **98.9% per step** to finish 90% of the time; 5 steps need 98%.
  [analysis](https://prefactor.tech/blog/step-level-accuracy-compounding-failure-production-agents)
- At 95% per card, a 30-card project completes untouched **21%** of the time. At 99%, 74%.
- Therefore the design target is not "high per-card success" but **cheap, correct recovery** when a card fails.

## Self-conditioning: retries can make it worse
Per-step accuracy **degrades when the context contains the model's own earlier errors**, beyond any long-context
effect, and scaling does not fix it. Models that reason step by step before answering avoid it; small non-thinking
models do not. [ICLR 2026](https://arxiv.org/abs/2509.09677)

**Design consequence:** each attempt starts from a **fresh context** holding the spec, the extracted failure and
nothing else — never an accumulated transcript of failed attempts. See [[repair-loops]].

## Where the field stands
- Frontier 50%-success time horizon: ~12 hours of human work, doubling every 4–7 months.
  [METR](https://metr.org/time-horizons/)
- Long-horizon agents degrade sharply as horizon grows; a formal study measured a **24.3 point drop** from tasks
  under 5 minutes to tasks over 2 hours. [Zylos](https://zylos.ai/research/2026-06-22-long-horizon-agent-reliability-science/)
- Retry loops that do not converge match a known control failure (integral windup), which argues for hard limits.

Related: [[small-model-capability]], [[agent-loop-failures]], [[open-objections]]
