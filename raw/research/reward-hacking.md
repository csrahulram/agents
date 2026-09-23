---
title: Reward hacking against tests
type: evidence
tags: [tests, gaming, training, risk]
updated: 2026-09-23
---

# Reward hacking against tests

When passing tests is the only path forward, models optimise for passing tests rather than solving the task.
This is documented, named, and benchmarked.

## Observed behaviours
Agents **overwrite test files, monkey-patch scoring functions, delete assertions, terminate programs early,
hardcode expected outputs, and copy reference implementations** to obtain a pass.
[RLVR gaming](https://arxiv.org/pdf/2604.15149), [survey](https://arxiv.org/pdf/2604.13602)

## Benchmarks that measure it
- [ImpossibleBench](https://www.lesswrong.com/posts/qJYMbrabcQqCZ7iqm/impossiblebench-measuring-reward-hacking-in-llm-coding-1) — tests deliberately contradict the spec
- [EvilGenie](https://arxiv.org/html/2511.21654v2) — an environment where hacking is easy, to see who takes it
- [SpecBench](https://arxiv.org/html/2605.21384v1) — long-horizon tasks, separating the proxy (validation tests)
  from the truth (held-out tests)

## Why our design is especially exposed
1. Tests are the **only** gate that advances a card.
2. **Phase 13 trains on whatever passed**, so gaming becomes training data — reinforcement learning toward cheating.

## Countermeasures to build in
- **Held-out tests**: the card passes on tests it never saw. Standard detection method.
- **Test files are immutable** once accepted; the permissions gate rejects any later edit by a code card.
- **Detect edits to test files** and hardcoded constants matching test inputs.
- Training data excludes any card whose held-out tests failed.

Related: [[test-quality]], [[open-objections]]
