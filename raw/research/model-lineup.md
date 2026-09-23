---
title: Model line-up
type: decision-input
tags: [models, licences, benchmarks]
updated: 2026-09-23
---

# Model line-up

All open-weight, all local. Licences checked on Hugging Face 2026-09-23.

| Role | Model | Size (Q4) | Licence | Evidence |
|---|---|---|---|---|
| Coder | Qwen2.5-Coder-1.5B-Instruct | 1,117 MB | Apache-2.0 | HumanEval+ 66.5, best at this size |
| General (split, tests, research, proposals) | MiniCPM5-1B | 688 MB | Apache-2.0 | Vendor claims 1B-class SOTA (42.57 avg vs 35.61); **unverified by us** |
| Vision | MiniCPM-V 4.6 (1.3B) + projector | 1,638 MB | Apache-2.0 | OmniDocBench 84.6 vs Gemma4-E2B 47.0 |
| Memory search | nomic-embed-text-v1.5 | 146 MB | Apache-2.0 | Already in use, works |
| Escalation | Qwen2.5-Coder-3B-Instruct | 2,105 MB | ⚠️ **Qwen Research** (non-commercial) | HumanEval+ 80.5 |
| Speech (later) | Whisper small | ~0.5 GB | Apache-2.0 | — |
| Screen control (optional) | GUI-Actor-2B | ~4–5 GB | MIT | 2B beats many 7B models at locating screen elements; **Python/CUDA only, not llama.cpp** |

## Rejected
- **Qwen3.5-0.8B / Gemma 4 E2B** — multimodal; images cost size we would rather spend on coding ability.
  Gemma 4 E2B is also a 7.2 GB download.
- **Llama-3.2-1B** — scores 10.8 on the Berkeley tool-calling leaderboard (frontier ~75); superseded.
- **Mify-Coder** — strong, but 2.5B and above our size target.

## Open
- Second coder from another family (`yi-coder:1.5b`, HumanEval+ 64.0) for more varied candidates — decide from the
  Phase 2 benchmark.
- Escalation licence: keep the 3B (research/personal use only) or move to the Apache-2.0 7B (~4.7 GB, on demand).

Related: [[small-model-capability]], [[runtime-measurements]]
