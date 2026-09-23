---
title: Survey of Self-Evolving AI Agents (Fang et al. 2025)
type: prior-art
tags: [self-evolution, taxonomy, safety, optimisation]
source: https://arxiv.org/abs/2508.07407
read: pages 1-33 in full (34-55 are references), 2026-09-23
updated: 2026-09-23
---

# A Comprehensive Survey of Self-Evolving AI Agents

Fang, Peng, Zhang, Wang et al. (Glasgow, Sheffield, MBZUAI, NUS, Cambridge, UCL, Aberdeen, Leiden),
arXiv 2508.07407v2, Aug 2025. The reference map for the field our project sits in.
Companion repo: `EvoAgentX/Awesome-Self-Evolving-Agents`.

## Definition and the Three Laws
> Self-evolving AI agents are autonomous systems that continuously and systematically optimise their internal
> components through interaction with environments, with the goal of adapting to changing tasks, contexts and
> resources **while preserving safety and enhancing performance**.

Modelled on Asimov, strictly hierarchical — a later law may never override an earlier one:
| Law | Name | Requirement |
|---|---|---|
| I | **Endure** (safety adaptation) | maintain safety and stability **during any modification** |
| II | **Excel** (performance preservation) | subject to I, preserve or enhance existing task performance |
| III | **Evolve** (autonomous evolution) | subject to I and II, autonomously optimise internal components |

This ordering is the paper's central normative claim, and it is exactly the ordering of our design:
gates and rollback first, benchmark-beating second, autonomy last. See [[mase-mapping]].

## Four paradigms
**MOP** (offline pretraining, frozen) → **MOA** (online adaptation: SFT, LoRA, RLHF) → **MAO** (multi-agent
orchestration: message passing, debate, tool calling, no weight changes) → **MASE** (multi-agent self-evolving:
agents refine prompts, memory, tools and topology from environment feedback and meta-rewards).
Our system is MAO + a constrained MOA loop (the model station), deliberately stopping short of full MASE.

## The unified framework
Four components in a closed loop: **System Inputs** → **Agent System** → **Environment** → **Optimiser** → back.
- **System inputs** `I`: task-level (`{task, D_train}`, optionally synthesised when no labels exist) or
  instance-level (`{x, y, context}`).
- **Agent system** `A`: LLM, prompts, memory, tools; or multi-agent with topology and communication.
- **Environment**: the operating context **and the source of feedback**. For code this is "compilers,
  interpreters and test cases" — our sandbox is textbook-correct here.
- **Optimiser** `P`: `A* = argmax_{A∈S} O(A; I)`, defined by a **search space S** and an **algorithm H**
  (rule-based heuristics, gradient descent, Bayesian, MCTS, RL, evolutionary, learned policies).
  Restricting `S` is the main safety lever, and the one we use most.

## What gets optimised (with the named methods)
**Single-agent**
| Target | Approaches |
|---|---|
| LLM behaviour, training | SFT on own correct rollouts (STaR; **NExT — self-generated trajectories filtered by unit-test correctness**), teacher trajectories; RL with DPO/GRPO, verifiable rewards (Tülu 3, DeepSeek-R1), self-proposing tasks (Absolute Zero, R-Zero) |
| LLM behaviour, test time | Outcome-level verifiers (**CodeT, LEVER — compiler/tests as the verifier**), step-level process reward models (unfaithful reasoning is the reason outcome-only feedback is not enough), search (CoT-SC best-of-N, Tree/Graph/Forest-of-Thoughts) |
| Prompts | Edit-based (GRIPS, TEMPERA), generative (APE, OPRO, PromptAgent+MCTS, MIPRO+Bayesian, StraGo, Retroformer), text-gradient (ProTeGi, TextGrad), evolutionary (EvoPrompt, Promptbreeder) |
| Memory | Short-term: recursive summarisation, MemoryBank (Ebbinghaus-style forgetting), Reflexion, COMEDY, ReadAgent. Long-term: A-MEM, Mem0, AWM, MEM1 (RL-consolidated), MIRIX, Agent KB (teacher-student transfer) |
| Tools | SFT (ToolLLM, Gorilla, Confucius curriculum), RL (ReTool, ToolRL, Tool-N1), inference-time (EASYTOOL, DRAFT, PLAY2PROMPT), **tool creation** (CREATOR, LATM, CRAFT, AgentOptimizer, Alita) |

**Multi-agent**
- Manual patterns: parallel + vote, hierarchical/SOP (MetaGPT), debate.
- Topology as the optimisation target: code-level workflows (AutoFlow, **AFlow** = MCTS over typed operator
  graphs, ScoreFlow, MAS-GPT), communication graphs (GPTSwarm, G-Designer, DyLAN, Captain Agent),
  **MermaidFlow — typed declarative graphs with static verification, exploring only semantically valid regions
  via safety-constrained evolutionary operators**, pruning (AgentPrune, AGP) and safety pruning (G-Safeguard, NetSafe).
- Unified prompt+topology: ADAS, FlowReasoner, EvoAgent, EvoFlow, MASS (local prompts → topology → global
  prompts), MAS-ZERO (inference-time only), MaAS (agentic supernet), ANN (layered, textual back-prop).
- Backbone: multi-agent finetuning on debate trajectories, Sirius, MALT, COPPER, OPTIMA, MaPoRL.

**Programming domain:** Self-Refine, AgentCoder and CodeAgent (**coder / reviewer / tester role split**),
CodeCoR, OpenHands; debugging with execution traces (Self-Debugging, Self-Edit, PyCapsule, RGD).

## Two findings that cut against complexity
1. **Parallel generation with small LLMs can match or outperform a single large LLM**, and multi-layer
   aggregation further reduces error bounds (Verga et al. 2024; Wang et al. 2025a; Zhang et al. 2025d).
   This is the strongest published support for our 4-candidates-per-card design.
2. **A single large LLM with well-crafted prompts can match complex multi-agent discussion frameworks**
   (Pan et al. 2025a), while handcrafted multi-agent workflows carry high build and maintenance cost.
   Multi-agent structure must earn its keep — it is not free performance.

## Evaluation
Benchmarks per agent type (ToolBench, API-Bank, GTA, AppWorld; WebArena, BrowseComp; MultiAgentBench,
GAIA; OSWorld, AndroidWorld; SWE-bench, DataSciBench). Evaluation is reframed as **a feedback mechanism that
drives optimisation**, not an endpoint.
- **LLM-as-a-Judge**: scalable, correlates with humans at times, but **sensitive to prompt design, biased, and
  output-only** — it misses reasoning quality in multi-step work.
- **Agent-as-a-Judge**: judges the whole trajectory, not the final answer; on DevAI it aligned better with human
  experts and cut evaluation time and cost. Harder to generalise beyond code generation.

## Safety (Section 7.3) — the part most relevant to us
- Risk benchmarks: **AgentHarm** (will an agent carry out malicious multi-step requests), **RedCode** (code
  security), **MobileSafetyBench**, **MACHIAVELLI** (does reward optimisation produce power-seeking behaviour),
  **R-Judge**, **SafeLawBench**.
- Safety is "not a one-off certification but an ongoing requirement: **every evolution step, from prompt updates
  to topology changes, must be assessed** for unintended or malicious behaviours" — requiring continuous,
  granular, scalable evaluation.
- **Their headline gap: most evaluation is snapshot-based.** Longitudinal, evolution-aware benchmarks that track
  safety across a system's lifetime "remain an open and urgent challenge". This is precisely the failure the user
  experienced with [[hermes-agent]], and what our staging → promotion pipeline is built to cover.
- Over-reliance on correctness metrics "can conceal epistemic risks and systemic biases" — an argument for our
  held-out tests and mutation testing rather than a single pass/fail number ([[test-quality]]).

## Open challenges, grouped by law
- **Endure:** optimisation pipelines prioritise task metrics over safety; evolving systems break legal frameworks
  that assume static models; learned reward models are unstable under scarce, noisy supervision — "even small
  perturbations in inputs or update rules can undermine the trustworthiness of an evolving workflow".
- **Excel:** no reliable ground truth in some domains; efficiency vs effectiveness in multi-agent optimisation;
  **optimised prompts and topologies are brittle and transfer poorly across backbones** — so our lessons and
  adapters are tied to a specific model version.
- **Evolve:** text-only optimisation ignores multimodal/spatial settings; most work assumes a fixed toolset.
- Future directions: simulation environments for closed-loop evolution, tool creation, real-world longitudinal
  benchmarks, explicit effectiveness-efficiency trade-offs, domain-aware evolution.

Related: [[mase-mapping]], [[self-improvement-fragility]], [[reward-hacking]], [[wiki-memory]]
