---
title: Small model capability
type: evidence
tags: [models, capability, limits]
updated: 2026-09-23
---

# Small model capability

## What they can do
- **Qwen2.5-Coder-1.5B-Instruct:** HumanEval 70.7, HumanEval+ 66.5, MBPP+ 59.4 — single, well-specified functions,
  right about two times in three on the first attempt. [Qwen report](https://arxiv.org/html/2409.12186v3)
- An independent study measured the same model lower, ~0.54 first-try. Expect real results **below vendor numbers**.
  [study](https://arxiv.org/html/2507.03160v3)
- **Short, structured tool calls are fine.** A study of 16 models from 0.27B to 32B found small models sufficient for
  short structured actions, with strict schemas and validators mattering more than size.
  [AgentFloor](https://arxiv.org/abs/2605.00334), [survey](https://arxiv.org/pdf/2510.03847)

## What they cannot do
- **LiveCodeBench 2.0–6.1** for 0.5B–1.5B coders, 10.8 for 3B. Algorithmic reasoning is effectively absent.
- **Sub-7B scores below 5% on SWE-bench Verified**; file location is capability-bound and erratic across repos.
  [overview](https://benchmarkingagents.com/swe-bench/)
- **Long-horizon planning is where size still wins** (AgentFloor). This is why planning is the риskiest role in our design.
- Hermes docs warn that models **under 30B claim to have used a tool without calling it**. [[hermes-agent]]

## Consequence for the design
Cards must be HumanEval-sized: one function, precise spec, input→output examples. Anything larger must be split
before a coder sees it. The open risk is that **splitting is itself a planning task** — see [[open-objections]].

Related: [[error-compounding]], [[model-lineup]], [[repair-loops]]
