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

## Caveats
- These are **warm** loads; the files were already in the Windows cache. True cold loads could not be measured —
  even a 2-month-old file read at 2,000 MB/s, above SATA speed, and `winsat` needs admin. Estimated cold from
  E: is ~6 s for all four core models. To measure properly, run `bench/load_time.py` immediately after a reboot.
- **Not yet measured:** tokens/second under 4 parallel slots, end-to-end time per card, tokens per project.
  These decide whether the loop is practical — see [[open-objections]] #6.

Related: [[model-lineup]]
