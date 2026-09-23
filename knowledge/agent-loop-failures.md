---
title: How agent loops fail
type: evidence
tags: [loops, stability, failure-modes]
updated: 2026-09-23
---

# How agent loops fail

## Failures are structural, not just model weakness
**MAST** (UC Berkeley, 2025) annotated 1,600+ traces across 7 multi-agent frameworks and found **14 failure modes**
in three groups: system design, agents misunderstanding each other, and **weak verification of results**. Multi-agent
systems often gained little over a single agent. Coordination, not capability, was the bottleneck.
[paper](https://arxiv.org/abs/2503.13657)

## Loops that never stop
A 2026 study scanned **6,549 agent repositories** and confirmed **68 infinite-loop failures across 47 projects**.
The cause is a feedback path with no enforced bound. [paper](https://arxiv.org/abs/2607.01641)
Standard defences: a hard step limit, fingerprinting repeated actions, and detecting no state change in k steps.
[overview](https://futureagi.com/glossary/infinite-loop-agent/)

## Coherence collapse
Agents sometimes **reach correct code and then fail to submit or apply it** — a failure of the surrounding
mechanics rather than of code generation. [paper](https://arxiv.org/pdf/2603.24631)
This is why format, permissions and application of file writes are gates in their own right.

## Design consequences
- Every loop has a limit written in code, and the chaos suite proves each one fires.
- State transitions are decided by code and tests, never by a model's claim of success.
- Repeated identical output counts as a failure immediately.
- No-progress watchdog: if the progress score does not rise in N steps, roll back and block.

Related: [[error-compounding]], [[hermes-agent]], [[blackboard-and-tape]]
