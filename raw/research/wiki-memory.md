---
title: Wiki-style memory
type: prior-art
tags: [memory, obsidian, raw]
updated: 2026-09-23
---

# Wiki-style memory (markdown + wikilinks)

The 2026 trend: agent memory as a folder of linked markdown notes — the format Obsidian reads.

| Work | Contribution | Evidence |
|---|---|---|
| [Karpathy, LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (Apr 2026) | Three layers: `raw/` never changed, `wiki/` maintained by the model, a schema file; operations **ingest, query, lint** | Pattern, not a paper; widely adopted |
| [A-MEM](https://arxiv.org/abs/2502.12110) (NeurIPS 2025) | Zettelkasten notes the model links and revises | 2–6× on multi-hop questions, 85–93% fewer tokens per operation |
| [Knowledge Compounding](https://arxiv.org/abs/2604.11243) | Wiki vs retrieval-augmented baseline | 47K vs 305K tokens over 4 queries (−84.6%) |
| [Memory as Metabolism](https://arxiv.org/abs/2604.12034) | Triage, decay, contextualise, consolidate, **audit**; a path for contradicting evidence to overturn beliefs | Design proposal, partial safety analysis |
| [Agent-native memory benchmark](https://arxiv.org/abs/2606.24775) | 12 systems compared | **No architecture wins everywhere**; local incremental maintenance beats global reorganisation; weak points are update correctness and long-run stability |

## What we take, and the one thing we change
Format: metadata headers, wiki-style links, one fact per note, files as the source of truth, SQLite only as a
rebuildable index.

**Change: the model does not maintain the ground truth.** RAW (rules, instructions, benchmark, chaos suite,
thresholds) is human-only; agents submit proposals with evidence. The WIKI layer is disposable and rebuildable
from RAW plus logs — which is precisely the recovery path Hermes lacked ([[hermes-agent]]).
Lint — broken links, contradictions, stale notes, size caps — runs in code, never in a model.

Related: [[self-improvement-fragility]], [[hermes-agent]]
