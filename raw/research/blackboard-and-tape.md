---
title: Prior art for the tape machine
type: prior-art
tags: [architecture, blackboard, loop]
updated: 2026-09-23
---

# Prior art for the tape machine

Control living in shared state, with a dumb loop applying rules, is an old idea with current momentum.

- **Blackboard systems** (Hearsay-II, 1970s): independent specialists act on a shared blackboard, no central planner.
- **Stigmergy**: coordination through traces left in the environment. No LLM-agent papers found using the term.
- **[Schuurmans 2023](https://arxiv.org/abs/2301.04589)** — an LLM plus external read/write memory driven by a fixed
  loop can simulate a universal Turing machine, with no weight changes. Caveat: demonstrated with a 540B model.
- **[Blackboard multi-agent LLM systems](https://arxiv.org/abs/2507.01701)** (2025) — the next agent is chosen from
  what is on the blackboard; matched state-of-the-art systems **using fewer tokens**. Their selector is still an LLM.
- **[Ralph loop](https://ghuntley.com/ralph/)** (Huntley, 2025) — `while :; do cat PROMPT.md | agent; done`;
  fresh context each iteration, state in files. Closest practical relative, but with one large model.
- **[Anthropic long-running agent harness](https://anthropic.com/engineering/effective-harnesses-for-long-running-agents)**
  — an initializer plus a coding agent that leaves a progress file and feature list for the next session.
- **[NVIDIA: small models are the future of agentic AI](https://arxiv.org/abs/2506.02153)** — most agent steps are
  narrow and repetitive. The prevailing pattern still pairs a **large planner** with small workers.

## What is genuinely untested in our design
Only ~1B models, **no model deciding what runs next** (a markdown transition table instead), **tests deciding every
state change**, and rules that improve under probation. The pieces are proven separately; the combination is not.

Related: [[agent-loop-failures]], [[small-model-capability]]
