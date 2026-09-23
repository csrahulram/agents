---
title: Awesome-Self-Evolving-Agents (the curated corpus)
type: prior-art
tags: [corpus, index, self-evolution, safety]
source: https://github.com/ANative-Lab/Awesome-Self-Evolving-Agents
read: full README (367 entries), section by section, plus abstracts of the entries new to us, 2026-09-23
updated: 2026-09-23
---

# Awesome-Self-Evolving-Agents

The companion reading list to [[self-evolving-agents-survey]], maintained by the same group.
367 linked entries, last updated **May 2026** — nine months newer than the survey, so its value is what has
appeared *since*. It follows the survey's taxonomy exactly (single-agent → multi-agent → domain → evaluation →
safety), which makes the additions easy to spot.

## The entry that argues against our design
**Darwin Gödel Machine** (arXiv 2505.22954, [code](https://github.com/jennyzzt/dgm)) — an agent that
**iteratively modifies its own code**, including the code that does the modifying.
- SWE-bench **20.0 → 50.0%**; Polyglot 14.2 → 30.7%.
- It abandons proving changes are beneficial (impractical) in favour of **empirical validation on benchmarks**.
- Its safety story is exactly our two mechanisms: **sandboxing and human oversight**.

This is the strongest published counter to our rule that the kernel is permanently off-limits. Read carefully it
supports the rule rather than breaking it: the validation harness is the fixed point, self-modification happens
**inside a sandbox, under human oversight, judged by a benchmark it does not control**. Our staging → promotion
pipeline is the same structure. The open question it poses honestly: *we* forbid kernel edits outright; DGM shows
the boundary could instead be drawn at "anything may change if the frozen benchmark and human both approve."
Worth revisiting only after the loop is stable — and note DGM used frontier models, not 1.5B ones.

Related: **AlphaEvolve** (2506.13131, DeepMind — evolutionary coding agent with automated evaluators) and
**OpenEvolve**, its open-source reimplementation. **Live-SWE-agent** (2511.13646) asks whether software agents
can self-evolve *on the fly*, mid-task.

## The entry closest to our architecture
**MetaAgent** (ICML'25, 2507.22606) — builds multi-agent systems **as finite state machines**: the FSM controls
the agent's actions and state transitions at deployment, generated from a task description and then polished by
an optimiser. Auto-generated systems matched human-designed ones.
Our tape machine *is* an FSM (`RULES.md`), with two differences: ours is human-written and frozen, and our
transitions are decided by tests rather than by a model. Useful confirmation that FSM-as-control is a sound
substrate; useful warning that others get value from *generating* the FSM.

## Safety section additions worth tracking
- **AGrail** (ACL'25, 2502.11448) — a **lifelong guardrail** that separates **task-specific risks** (defined by an
  administrator) from **systemic risks** (design flaws affecting confidentiality, integrity, availability), and
  **adapts its safety checks over time**, with transferability across agents. The closest published analogue to a
  gate layer that evolves. If our gates ever need to grow, this is the reference design.
- **AutoDAN-Turbo** (ICLR'25 Spotlight) — a lifelong agent that self-explores jailbreak strategies. The adversary
  is also self-evolving; useful as a red-team model for our chaos suite.
- **Accuracy Paradox in LLMs** (2509.13345) — regulating hallucination risk when accuracy metrics look fine.
  Echoes the survey's warning that correctness metrics conceal epistemic risk ([[test-quality]]).
- Otherwise the same set we already hold: AgentHarm, RedCode, MobileSafetyBench, MACHIAVELLI, R-Judge, SafeLawBench.

## Memory additions since the survey
- **ReasoningBank** (2509.25140) — memory of *reasoning strategies* rather than facts or episodes.
- **Memento** (2508.16153) — "fine-tuning LLM agents **without** fine-tuning LLMs": adaptation stored in memory
  instead of weights. Directly relevant to us — a cheaper alternative to the model station's adapters.
- **Memory-R1** (2508.19828) — RL to decide what to store, update and forget.
- **Agent KB** (2507.06229) — cross-domain experience reuse with teacher-student retrieval.
- **M3-Agent** (2508.09736) — multimodal long-term memory, ByteDance.

## Other things we did not have
- **MASLab** (2505.16988) — a unified codebase of LLM multi-agent methods; a comparison harness rather than a framework.
- **R&D-Agent** (Microsoft, 2505.14738) — automated research → development → evolution for data-driven AI.
- **CORAL** (2026, 2604.01658) — autonomous multi-agent evolution for open-ended discovery.
- **ELL-StuLife** (2508.19005) — experience-driven lifelong learning, framework **plus benchmark**.
- **rSDE-Bench** / *Self-Evolving Multi-Agent Collaboration Networks for Software Development* (ICLR'25) —
  a benchmark for self-evolving software teams. The nearest existing benchmark to what we are building; worth
  examining before we write our own frozen benchmark.
- **Chain-of-Agents** (2508.13167) — distilling a multi-agent system into a single model. The logical end point
  if our station ever works: the loop's behaviour folded into the weights.

## How to use this note
As an index, not evidence. Three follow-ups, in order of value to us:
1. **rSDE-Bench** — an existing benchmark for self-evolving software teams (Phase 2 and Phase 12 both need one).
2. **Memento** — adaptation without training; potentially replaces or delays the whole model station.
3. **AGrail** — the design to copy if gates must become adaptive.

Related: [[self-evolving-agents-survey]], [[evoagentx]], [[agentevolver]], [[mase-mapping]]
