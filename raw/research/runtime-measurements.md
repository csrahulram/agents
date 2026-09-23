---
title: Runtime measurements
type: measurement
tags: [hardware, llama.cpp, performance]
updated: 2026-09-23
---

# Runtime measurements (this machine)

**Machine:** RTX 3060 12 GB · 32 GB RAM · Ryzen 5 5600G · Windows 11 · Python 3.12 · Node 24
**Drives:** C: NVMe (34 GB free) · D: HDD (project) · E: SATA SSD (`E:\models\gguf`)
**Runtime:** llama.cpp `llama-server` build **11105**, CUDA 12.4, in `tools/llama.cpp`. Not Ollama — chosen for
grammars, parallel slots and explicit process control.

## Measured 2026-09-23 (median of 3 warm runs, model fully on GPU)
| Model | File | Load | GPU | First request |
|---|---|---|---|---|
| Qwen2.5-Coder-1.5B (8K ctx, 4 slots) | 1,117 MB | 1.4 s | 1,347 MB | 0.05 s |
| MiniCPM5-1B (8K ctx) | 688 MB | 2.8 s | 905 MB | 0.07 s |
| MiniCPM-V 4.6 + projector | 1,638 MB | 2.6 s | 1,892 MB | 0.09 s |
| nomic-embed-text-v1.5 | 146 MB | 0.5 s | 255 MB | 0.01 s |
| Qwen2.5-Coder-3B | 2,105 MB | 1.9 s | 2,335 MB | 0.06 s |

**Four core models: 4.4 GB GPU.** With the 3B: 6.7 GB. Desktop already uses ~1.1 GB. Headroom on 12 GB is ample.

## Containerised, measured 2026-09-23 (Docker 29.7.2, `ghcr.io/ggml-org/llama.cpp:server-cuda`, GPU passthrough)
All four model services healthy, **6.3 GB GPU total** (includes ~1.1 GB desktop; coder at 32K context, 4 slots).

| Measurement | Result |
|---|---|
| Coder, single request | 156 tokens in 1.2 s = **126 tok/s** |
| General, single request | 300 tokens in 1.2 s = **247 tok/s** |
| **Coder, 4 candidates in parallel** | 693 tokens in **1.7 s** = 399 tok/s aggregate |
| Embeddings | 16 texts in 0.11 s |
| Cold start of all four services | ~90 s (image already pulled) |

**Consequence:** one card's four candidates cost **under 2 seconds**. A 30-card project is minutes of model time,
so wall-clock cost is dominated by running tests in sandboxes, not by inference. Objection #6 in
[[open-objections]] is therefore about *your attention*, not about compute.

**Also observed:** the sample answer looked plausible and was wrong — `re.match` on `'2h30m'` parses only the first
component. Exactly the failure mode [[test-quality]] describes: only a real test catches it.

## Caveats
- These are **warm** loads; the files were already in the Windows cache. True cold loads could not be measured —
  even a 2-month-old file read at 2,000 MB/s, above SATA speed, and `winsat` needs admin. Estimated cold from
  E: is ~6 s for all four core models. To measure properly, run `bench/load_time.py` immediately after a reboot.
- **Not yet measured:** tokens/second under 4 parallel slots, end-to-end time per card, tokens per project.
  These decide whether the loop is practical — see [[open-objections]] #6.

Related: [[model-lineup]]
