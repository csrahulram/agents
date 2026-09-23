---
title: AgentEvolver
type: prior-art
tags: [self-evolution, training, rl, codebase, credit-assignment]
source: https://github.com/modelscope/AgentEvolver
paper: https://arxiv.org/abs/2511.10395
read: README, module tree, task_manager / exp_manager / adv_processor / context_manager sources, and the report abstract, 2026-09-23
updated: 2026-09-23
---

# AgentEvolver (ModelScope / Alibaba)

Apache-2.0, ~40k lines of Python, Nov 2025, still active (Mar 2026). Where [[evoagentx]] evolves *workflows
around* a model, AgentEvolver **trains the model itself** with RL, and attacks the part of self-evolution we
have no answer for: **where the training data comes from**.

## The problem it names
Building agents requires "manually constructed task datasets and RL pipelines with extensive random
exploration" — costly, inefficient to explore, wasteful of samples. Three mechanisms, each targeting one of those:

| Mechanism | What it does | Our equivalent gap |
|---|---|---|
| **Self-Questioning** | explores the environment and **generates its own tasks**, removing the handcrafted dataset | our station trains only on cards it already solved — survivorship bias ([[open-objections]] #7) |
| **Self-Navigating** | summarises and reuses experience across tasks to guide rollouts | our memory is read at inference but never shapes training |
| **Self-Attributing** | assigns **per-step credit** inside a long trajectory instead of one score per run | the step-level signal the survey said we lack ([[mase-mapping]]) |

## The results, and what they actually show
avg@8 / best@8, i.e. 8 samples per task — note that they report *both*, which is honest practice for a noisy metric.

| Model | AppWorld avg@8 | BFCL v3 avg@8 |
|---|---|---|
| Qwen2.5-**7B** baseline | **1.8** | 29.8 |
| + Questioning | 23.2 | 49.0 |
| + Questioning & Navigating | 26.3 | 53.3 |
| + Questioning & Attributing | 25.7 | 56.8 |
| **All three** | **32.4** | **57.9** |
| Qwen2.5-**14B** baseline | 18.0 | 41.6 |
| **All three** | **48.7** | **66.5** |

Two readings, both important for us:
1. **A 7B model scores 1.8% on a real agentic benchmark out of the box.** Independent confirmation of
   [[small-model-capability]] — untrained small models are near-useless at long agentic tasks.
2. **Task generation alone did most of the work** (1.8 → 23.2). The *data* mattered far more than the clever
   RL algorithm on top. If any part of our station is worth building first, it is task generation, not GRPO.

## How it is built
- **RL stack:** `verl` + `vLLM` + `Ray` + torch 2.6, `main_ppo.py`, FSDP workers. Cluster-scale, multi-GPU —
  **not runnable on a 12 GB 3060** as-is. The ideas transfer; the pipeline does not.
- **`task_manager/`** — task generation with `env_profiles` (entities, options, **relation_difficulty** — tasks are
  synthesised at graded difficulty), `filters/` (naive + **LLM filter** to discard bad generated tasks),
  `rewards/` (binary judge, judge-with-ground-truth, **env_grader**, avg judge), `data_mixture.py` for blending
  generated and original data.
- **`exp_manager/`** — "hybrid experience training": inject retrieved experience into a *fraction* of rollouts
  (`rollout_expratio: 0.5`), then choose whether training samples **keep / discard / hybrid** that injected
  experience (`train_sample_keepratio`). Ablations named EC / EI / HET. External memory service: ReMe.
- **`adv_processor/`** — `adca_grpo.py` + `semantic_attribution.py`: an LLM scores **each step** of a rollout and
  those scores become per-step advantages in GRPO, rather than one reward per trajectory.
- **`context_manager/`** — context handling as a first-class, swappable component: linear, linear+think,
  **self context clip**, memory, phantom hint. Includes tokenisation and **loss masking**.
- **`env_service/`** — standalone sandboxed environment service (AppWorld, BFCL, OpenWorld) with a client/registry
  interface. Same shape as our sandbox container.
- Extras: a Game Arena (Avalon, Diplomacy) for social-reasoning training, and **SeeUPO** (Mar 2026) —
  sequence-level agentic RL with stated convergence guarantees.

## What to take
1. **Generate tasks, don't only harvest them.** Their biggest win. For us: synthesise extra cards at graded
   difficulty from the project's contract and from *failed* cards, so the station has data for the cases we
   currently have no solutions for. Cheap version: mutate solved cards into harder variants.
2. **Filter generated tasks before use** — they run both a rule filter and an LLM filter. Ours would be: a
   generated card only enters the dataset if its tests are real (mutation-tested) and it is solvable at all.
3. **Graded difficulty as an explicit parameter** (`relation_difficulty`) — matches the easy-to-hard curriculum
   that [[self-improvement-fragility]] says is a prerequisite, and makes it a knob rather than an accident.
4. **Step-level credit.** Their semantic attribution needs an LLM judge; ours is free and objective — **which
   gate failed, at which attempt**. Same signal, no judge. Adopt.
5. **Report avg@k and best@k**, not a single number, for our frozen benchmark.
6. **Experience injection as a measured ratio**, with the option to strip it from the training sample. Prevents
   the model learning "the answer was in the context" instead of the skill.

## What to leave
- The whole verl/Ray/vLLM training pipeline — wrong scale for one 3060.
- LLM-judged step attribution — we have tests; a judge would reintroduce the bias the survey warns about.
- Self-questioning as *unbounded* environment exploration: our environment is a project with a human-owned
  spec, so generated tasks must stay inside the contract, not wander.

## Honest caveat
The report calls these "preliminary experiments", results are on 7B/14B models with API-scale infrastructure,
and both benchmarks (AppWorld, BFCL) are tool-use rather than software construction. Treat the *mechanisms* as
validated ideas, the *numbers* as not transferable to 1.5B local models.

Related: [[evoagentx]], [[self-evolving-agents-survey]], [[open-objections]], [[small-model-capability]]
