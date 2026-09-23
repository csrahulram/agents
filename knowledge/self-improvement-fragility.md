---
title: Self-improvement is fragile
type: evidence
tags: [learning, lessons, training, risk]
updated: 2026-09-23
---

# Self-improvement is fragile

## Evidence
- **[Salesforce, 2026](https://arxiv.org/abs/2608.18066)** — agents that learn by writing notes to memory:
  variance between runs rose in **71%** of cases, with best-vs-worst gaps up to **10 points**;
  shuffling task order turned **+1.5% into −4.5%**, meaning published gains depended on an easy-to-hard order;
  vague task or environment descriptions produced **wrong lessons that propagated** to later tasks.
- **[CMU, 2026](https://publications.ri.cmu.edu/storage/publications/2026/07/main_20260731120034.pdf)** — instructions
  that keep growing degrade performance; self-critique without an external check confirms the original mistake.
- Fine-tuning small models on their own accepted outputs risks **survivorship bias**: the failures, which matter most,
  have no correct examples to learn from.

## Consequences for our design
1. **Lessons are off by default** until the core loop is stable.
2. A lesson goes on **probation**, judged over several runs, not one, because of the variance finding.
3. Every lesson prompt carries the **setup facts** (Python 3.12, standard library, unittest, no network) — vague
   context is what produced bad lessons in the study.
4. **Build easy-to-hard on purpose:** dependency-free functions first. That ordering is a prerequisite, not a detail.
5. Instruction files have a **hard size cap**, per [[hermes-agent]].
6. Model adapters may promote automatically only against a **human-owned, frozen** benchmark and chaos suite.
   Statistical caveat: see [[open-objections]] #7 — the promotion threshold may be unreachable, or the canary blind.

Related: [[wiki-memory]], [[reward-hacking]]
