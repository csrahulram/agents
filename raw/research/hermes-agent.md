---
title: Hermes Agent
type: prior-art
tags: [memory, skills, safety]
updated: 2026-09-23
---

# Hermes Agent (Nous Research, Feb 2026, MIT)

A single large-model tool-calling loop with persistent memory and self-written "skills".
[site](https://hermes-agent.nousresearch.com/) · [GitHub](https://github.com/nousresearch/hermes-agent)
**Direct user experience: it entered a bad loop after long use and could not recover.** That failure is the reason
for [[wiki-memory]]'s human-owned RAW layer.

## Worth copying
| Mechanism | Detail |
|---|---|
| Hard memory caps | `MEMORY.md` 2,200 chars, `USER.md` 1,375; a write that overflows **errors** instead of silently dropping |
| Frozen snapshot | Memory is captured at session start and never changes mid-session |
| Write approval | `memory.write_approval`, `skills.write_approval` stage writes for review |
| Skill linting | Rejects oversized skills (~24k chars), reference sprawl (>60 files), incident-log-shaped bodies |
| Progressive disclosure | Names and descriptions first (~3k tokens), full text only on demand |
| Curator | Tracks which skills are used, skipped or erroring; suggests merges and deletions |
| Injection scanning | Memory writes and downloaded skills are scanned before use |
| Never self-edits code | Fine-tuning is never self-triggered; the agent does not modify its own source |

## Not worth copying
- **`agent.max_turns` is unlimited by default** ([config](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)).
- No ratchet, no test-decided transitions, no rollback of project files; verification is left to the model.
- Skill quality is unverified until a curator reviews it; library growth has no documented bound.
- Its own docs warn that **models under 30B claim tool use without calling the tool** — assume this happens.

Related: [[wiki-memory]], [[self-improvement-fragility]], [[agent-loop-failures]]
