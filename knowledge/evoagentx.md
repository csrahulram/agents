---
title: EvoAgentX
type: prior-art
tags: [self-evolution, framework, codebase, hitl]
source: https://github.com/ANative-Lab/EvoAgentX
paper: https://arxiv.org/abs/2507.03616
read: README, paper abstract, and the optimizers / hitl / memory / workflow / benchmark modules of the cloned repo, 2026-09-23
updated: 2026-09-23
---

# EvoAgentX

The reference implementation of the survey's vision ([[self-evolving-agents-survey]] names it as the first
open-source MASE framework). MIT licence, ~70k lines of Python, ~3.4k stars, active (last commit Aug 2026).
Paper: *EvoAgentX: An Automated Framework for Evolving Agentic Workflows* (arXiv 2507.03616).

## Architecture
Five layers: basic components → agent → workflow → **evolving** → evaluation.
Package modules: `agents`, `workflow`, `optimizers`, `evaluators`, `benchmark`, `memory`, `rag`, `tools`,
`storages`, `models`, `prompts`, `hitl`, `frameworks/multi_agent_debate`.

A workflow is generated **from a natural-language goal**, then executed and optimised:
```python
workflow_graph = WorkFlowGenerator(llm=llm).generate_workflow(goal)
agent_manager.add_agents_from_workflow(workflow_graph, llm_config=config)
WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm).execute()
```

## The optimisers (`evoagentx/optimizers/`)
`aflow`, `mipro`, `textgrad`, `evoprompt`, `sew`, `map_elites`, plus an `engine/` with a parameter registry.
The base `Optimizer` is small and worth copying verbatim in spirit:

| Field | Default | Meaning |
|---|---|---|
| `max_steps` | 5 | hard budget on optimisation steps |
| `eval_every_n_steps` | 1 | how often to score |
| `eval_rounds` | 1 | **run evaluation N times and average** — their admission that one run is noise |
| `convergence_threshold` | 5 | stop after N steps without improvement |

`optimize()`, `step()`, `evaluate()`, `convergence_check()`. Every optimiser is a search over a graph with an
evaluator and a budget — the same shape as our promotion pipeline, with a model in the loop instead of a human.

**MAP-Elites** (`map_elites_optimizer.py`) is the interesting outlier: quality-diversity search that keeps an
**archive of the best configuration per feature cell**, not a single best. `feature_dimensions`, `feature_bins`,
`exploration_ratio=0.2`, `n_iterations=200`. Preserving diverse-but-good configurations is a direct counter to
benchmark overfitting ([[open-objections]] #7).

**SEW** (`sew_optimizer.py`, paper arXiv 2505.18646) converts the workflow into one of five representations —
`python`, `yaml`, `code`, `core`, `bpmn` — and evolves it with mutation prompts and thinking styles. Their point:
**the representation you evolve in changes the result**, up to 12% on LiveCodeBench. Our `RULES.md` markdown
table is such a representation choice, made for human readability rather than searchability.

## Human-in-the-loop (`evoagentx/hitl/`) — the closest thing to our supervision model
A first-class module, not an afterthought:
- `HITLDecision`: **approve / reject / modify / continue**
- `HITLInteractionType`: approve_reject, collect_user_input, review_edit_state, **review_tool_calls**,
  multi_turn_conversation
- `HITLMode`: **pre_execution** (intercept before it runs) or **post_execution** (intercept the result)
- `HITLManager` holds pending requests as futures with a **1800 s timeout**, CLI and GUI front ends,
  plus an `interceptor_agent` and a `workflow_editor`.

Their taxonomy is better than ours: we have approve/reject, they also have **modify** (edit before accepting)
and a distinction between intercepting *before* and *after* execution.

## Memory and retrieval
`memory/`: short-term `memory.py`, `long_term_memory.py` (add / get / update / delete / search / save / load over
chunked messages), `context_manager.py`. A full `rag/` stack: chunkers, embeddings, indexings, retrievers,
postprocessors, FAISS-backed. More machinery than our files-plus-SQLite index, and correspondingly more to go wrong.

## Benchmarks (`evoagentx/benchmark/`)
Ready-made harnesses for **HumanEval, MBPP, LiveCodeBench**, GSM8K, MATH, HotPotQA, NQ, BigBenchHard, WorfBench —
with `measures.py`. Directly reusable as a model of how to structure our frozen benchmark.

## Reported results
| Benchmark | Gain |
|---|---|
| HotPotQA | +7.44 F1 |
| MBPP | +10.00 pass@1 |
| MATH | +10.00 accuracy |
| GAIA | up to +20.00 accuracy |

**Read these carefully:** they are gains from optimising a workflow around **API models** (OpenAI, Claude,
Qwen, DeepSeek, Kimi via LiteLLM), not 1B local models. Nothing here shows the same lift at our scale, and
[[small-model-capability]] gives reason to expect less.

## What to take, and what not to
| Take | Why |
|---|---|
| `eval_rounds` averaging and `convergence_threshold` | their budget/noise discipline matches our promotion rules |
| **MAP-Elites archive** | keep diverse good adapters/configs instead of one champion; guards against overfitting one benchmark |
| The **HITL taxonomy**: modify as a third decision, pre- vs post-execution interception | our proposal review should allow "approve with edits", and our gates are pre-execution interception by another name |
| Benchmark module layout | a template for our frozen benchmark harness |
| The SEW insight that representation matters | worth testing whether cards-as-markdown is the right substrate |
| Leave | Why |
| Workflow generation from a natural-language goal | topology search is precisely what we forbid — the system could route around its own gates ([[mase-mapping]]) |
| TextGrad / MIPRO / EvoPrompt automatic prompt rewriting | prompts live in RAW; drift risk ([[self-improvement-fragility]]) |
| The RAG stack | files-as-truth plus a rebuildable index is smaller and recoverable ([[wiki-memory]]) |
| API-model assumptions | everything local here |

Related: [[self-evolving-agents-survey]], [[mase-mapping]], [[open-objections]]
