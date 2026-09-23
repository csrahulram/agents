---
title: Our design in the MASE framework
type: analysis
tags: [design, self-evolution, gaps]
updated: 2026-09-23
---

# Our design mapped onto the MASE framework

Using the four components from [[self-evolving-agents-survey]] to locate what we are building, what we borrow,
and where we deliberately differ.

## The mapping
| MASE component | Ours |
|---|---|
| **System inputs** `I` | The goal, `CONTRACT.md`, and the card's input→output examples. Task-level, with instance-level refinement per card. |
| **Agent system** `A` | Coder, general and vision models; prompts in `raw/instructions/`; memory as an Obsidian-style wiki; tools fixed by the seed; "topology" = the `RULES.md` state machine. |
| **Environment** | The **sandbox container**: interpreter, test runner, Playwright, health checks. Exactly the survey's canonical code environment, plus isolation. |
| **Optimiser** `P` | Split in three, deliberately: **(a)** code — gates, ratchet, escalation ladder (rule-based heuristics over a tiny search space); **(b)** the model station — LoRA/DPO on our own verified trajectories; **(c)** the human — the only writer of RAW. |

## What the survey validates in our design
1. **Verifier-as-environment.** CodeT, LEVER and NExT all use compilers and unit tests as the verifier, and NExT
   filters self-generated trajectories by unit-test correctness before training — our Phase 12 dataset rule,
   already published practice.
2. **Parallel small models beat one big call.** Verga et al. and Zhang et al.: parallel generation with small
   LLMs can match or outperform a single large LLM, and aggregation reduces error bounds. Our 4-candidate design.
3. **Role separation in code agents.** AgentCoder and CodeAgent split coder / reviewer / tester, as we split
   coder from test-writer.
4. **Typed, statically verified topology.** MermaidFlow explores "only semantically valid regions" via
   safety-constrained operators — the same idea as our structure gate and one-function-per-file rule.
5. **Step-level over outcome-level feedback.** Outcome-only feedback produces *unfaithful reasoning* — right
   answer, wrong process. Our per-card gates are step-level by construction.
6. **Restricting the search space is the safety lever.** The optimiser is defined by `(S, H)`; we keep `S`
   deliberately tiny — no prompt rewriting, no topology search, only adapters and human-approved RAW.

## Where we deliberately diverge
| Survey norm | Ours | Why |
|---|---|---|
| The optimiser rewrites prompts automatically (OPRO, ProTeGi, Promptbreeder) | Prompts live in RAW; agents may only **propose** changes with evidence | Prompt self-rewriting is the drift path; [[self-improvement-fragility]] |
| Topology is searched (AFlow, GPTSwarm, MaAS) | `RULES.md` is fixed and human-written | Search over control flow means the system can route around its own gates |
| LLM-as-a-Judge / Agent-as-a-Judge decides quality | Tests decide; a model may only **rank** candidates that already passed | Judge bias and prompt sensitivity are documented in the survey itself |
| Tool creation by the agent (CREATOR, LATM, Alita) | Tools are seed code; the system may build **plugins behind a fixed API**, gated | Tool creation is arbitrary code execution by another name |
| Evaluation is snapshot-based | Staging stack + frozen benchmark + chaos suite + canary + auto-rollback | The survey names longitudinal safety evaluation as the open problem |

## What the survey says we are missing
1. **No step-level reward model.** Process reward models beat outcome-only feedback. Our gates are binary
   pass/fail per card. A cheap approximation: record *which gate* failed and at which attempt, so the trajectory
   data carries step-level signal for the station. **Adopt.**
2. **Curriculum learning** (Confucius: easy-to-difficult exposure) matches our dependency-layer build order, but
   we have not applied it to *training* data ordering. Given the task-order fragility finding in
   [[self-improvement-fragility]], order the station's training data easy-to-hard. **Adopt.**
3. **Agent-as-a-Judge for the whole trajectory.** Too expensive at 1B and it would re-introduce a model judge.
   **Reject**, but keep the idea for a human-facing summary of *why* a card was blocked.
4. **Transferability is poor across backbones.** Lessons and adapters must be stamped with the model version
   they were learned on, and re-validated when a model changes. **Adopt** — add to `promotion.toml`.
5. **Reward-model instability** ("small perturbations in update rules can undermine trustworthiness") argues
   against our later RL/GRPO ambition at 1B scale. Treat Phase 13 method 3 as research, not a plan. **Adopt.**
6. **Multi-agent structure must earn its keep** — a single well-prompted large model matches many MAS designs.
   Our justification is not capability but privacy, cost, offline operation and stability, per
   [[open-objections]] #6. Keep that honest.

Related: [[self-evolving-agents-survey]], [[open-objections]], [[../../PLAN|PLAN]]
