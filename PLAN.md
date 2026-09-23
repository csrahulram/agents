# Build Plan: Tape-Machine Agent System (no Ollama)

**Principle:** models propose, code decides. The tape (cards + markdown + memory) holds all state;
a dumb runner applies the rules in `RULES.md`; small models do one step per card; tests decide transitions.

**Hardware:** RTX 3060 12 GB · 32 GB RAM · Ryzen 5 5600G · Windows 11 · Python 3.12

---

## Runtime stack
| Component | Runtime | Model file (GGUF from Hugging Face) | Approx. GPU memory |
|---|---|---|---|
| Coder | `llama-server` (CUDA), `--parallel 4` | Qwen2.5-Coder-1.5B-Instruct Q4_K_M | ~1.5 GB |
| General | `llama-server` | MiniCPM5-1B Q4_K_M (fallback: Qwen3-1.7B) | ~1.2 GB |
| Vision | `llama-server` + vision projector file | MiniCPM-V 4.6 (fallback: Qwen3.5-0.8B) | ~2.5 GB |
| Embeddings | `llama-server --embedding` | nomic-embed-text-v1.5 | ~0.3 GB |
| Escalation (on demand) | `llama-server`, started only when needed | Qwen2.5-Coder-3B-Instruct Q4_K_M | ~2.5 GB |
| Speech to text | `faster-whisper` (Python) | whisper small | ~1 GB |
| GUI actions (later, optional) | Python + Transformers | GUI-Actor-2B | ~5 GB |
| Training (model station) | `trainer` container (CUDA, GPU passthrough verified) | trains adapters on our own runs | the full 12 GB, model services stopped |

The always-on models total about 5.5 GB, and about 8 GB with escalation, which leaves room within 12 GB.
The GUI actions model would only run when those others aren't running.

## The seed, and what may never be self-built
**The seed is the hand-written kernel.** It is small, boring, and off-limits to agents — it is the thing that decides
what is true, so nothing that a model writes may ever change it:

| Seed component | Why it must be hand-written |
|---|---|
| `core/llm.py` | speaks to the models; if it is wrong, every measurement is wrong |
| `core/tape.py` | atomic writes, locks, git checkpoints — the ratchet lives here |
| `core/gates.py` | the five gates; a model editing its own judge is the bad loop |
| `core/runner.py` + `RULES.md` | the loop and its limits |
| `compose.yaml` + `sandbox/` | isolation and resource limits |
| `web/seed/` | a read-only view: cards, logs, proposals, approve/reject |

Everything **above** the kernel is fair game for the system to build: the full web interface, project templates,
Dockerfiles for generated projects, extra gates as plugins behind a fixed API, and its own benchmark cards.
Recursion means *the system extends its periphery*, never *the system rewrites its own judge*.

## Docker Compose runtime (verified on this machine: Docker 29.7.2, Compose v5.5.0, GPU passthrough works)
| Service | Image | Role |
|---|---|---|
| `llm-coder`, `llm-general`, `llm-vision`, `llm-embed` | llama.cpp CUDA | one model each, `--parallel 4` on the coder; `llm-escalate` is a profile started on demand |
| `runner` | python:3.12-slim | the loop; mounts `raw/` read-only, `wiki/`, `workspace/`; spawns sandboxes via the Docker socket |
| `web` | python:3.12-slim | dashboard and API; the seed version is read-only, the full one is built by the system |
| `sandbox` (ephemeral, one per test run) | our image: python + node + Playwright | **`network_mode: none`**, read-only except `/work`, CPU/memory caps, hard timeout, killed after each run |
| `proxy` | caddy | serves deployed projects on local ports/hostnames |
| `trainer` (profile) | CUDA + PyTorch | the model station; no separate WSL install needed |

The sandbox closes the hole where model-written commands ran directly on the host. Nothing generated ever executes
outside it, and with no network it cannot download anything or reach your machine.

## Staging → main promotion (RAW changes and the kernel itself)
Two identical Compose stacks from the same files, different project names, ports and volumes:

| Stack | Runs on | Purpose |
|---|---|---|
| `main` | `raw/` at the approved version | normal work; never runs an unapproved RAW |
| `staging` | `proposals/raw-v{N+1}/` merged over RAW | proves a change before it is allowed near main |

**Promotion pipeline** — a proposal reaches main only by passing, in order:
1. The stack starts and every service is healthy.
2. The **frozen benchmark**, scored against main's numbers.
3. The **chaos suite**, in full.
4. One **real project end to end**, deployed and serving.
5. No regression on held-out projects.

Then `promote` (human command, one word): tag `raw/v{N+1}`, merge to `main` in git, restart the main stack, and
record the evidence. `rollback` returns to `raw/vN` and the previous images. Staging is disposable — delete and
rebuild it from files at any time. Kernel changes (which only a human writes) go through the same pipeline.

## Local deploy loop
A project reaching `done` gets: a generated `Dockerfile` and `compose.yaml` (written as ordinary cards, gated like
any code), a build, a start behind `proxy` on an assigned port, and a **health check plus the acceptance tests run
against the live service**. Only then is it marked `deployed`. Failure rolls back to the previous image tag, and the
previous version keeps serving. Everything stays local; nothing is published.

## Three layers (Karpathy's LLM Wiki pattern, with a human-owned ground truth)
| Layer | Contents | Who writes | Properties |
|---|---|---|---|
| **RAW** | goal/spec, acceptance tests, `RULES.md`, instruction files, approved lessons, setup facts, **the benchmark, the chaos suite, `promotion.toml`** | **Human only.** The permissions gate rejects every agent write. | Versioned `raw/v1, v2…` with git tags. Frozen during a run. |
| **Proposals** | `proposals/raw-v{N+1}/`: suggested RAW changes, each with evidence (failed cards, metrics, log lines) and an automatic before/after test | Agents suggest; the human approves or rejects | Rejections are recorded so the same idea can't return |
| **WIKI** | tape cards, memory notes, summaries, the search index, generated code, `models.toml` | Agents, through the gates and the ratchet | **Disposable:** can always be rebuilt from RAW + logs |

Everything is Obsidian-compatible markdown: metadata headers and `[[links]]`, so the whole project can be browsed
as a graph. Files are the source of truth; the SQLite index (text search + embeddings) is rebuilt from them.
Maintenance — link checks, contradictions, stale notes, size limits — is done by code, never by a model.

**Why this stops the long-term bad loop:** the agents' ground truth cannot drift on its own, and there is always a
clean baseline. Delete the WIKI, rebuild from RAW vN, and any corrupted memory or confused tape is gone.

## Layout
```
agents.toml        models, ports, limits
RULES.md           the state machine (the only "orchestration")
instructions/      one prompt file per rule/role
core/
  serve.py         start/stop/health-check llama-server processes
  llm.py           OpenAI-compatible client: grammar, json_schema, seed
  tape.py          cards: read/write, atomic writes, locks with expiry, git checkpoints
  gates.py         format → permissions → sanity → card test → no breakage
  runner.py        the loop, ratchet, watchdog, limits
  escalate.py      candidates, escalation ladder, repeated-output detection
  feedback.py      turns test failures into precise error feedback
  context.py       builds each card's context: contract signatures + retrieved code + memory
  memory.py        short-term / long-term / project state (kept from the current code)
raw/               human-owned ground truth: RULES.md, instructions, benchmark, chaos suite, promotion.toml
proposals/         agent-suggested RAW changes, awaiting human review
bench/             model benchmark tasks (frozen: the same tasks score every model version)
station/           model station: dataset.py, train.py, eval.py, registry.py, configs/
data/trajectories/ every model call with its gate result — the training data
adapters/          trained LoRA adapters, one folder per role and version (git-ignored)
tests/chaos/       worst-case fake-model tests (the stability proof)
models/            downloaded GGUF files (git-ignored)
workspace/<p>/     project code + tape/ + CONTRACT.md + LOG.md
```

---

## Phases (each ends with a checkpoint that must pass before moving on)

### Phase 0: Runtime setup
- ✅ llama.cpp Windows CUDA build in `tools/llama.cpp/` (b11105), models in `E:\models\gguf`, load times measured.
- `compose.yaml` with the model services, and the sandbox image (python + node + Playwright).
- Playwright inside the sandbox image, not on the host.
- `scripts/fetch_models.py`: download the GGUF files from Hugging Face into `models/` and check their checksums.
- **Checkpoint:** each model answers a request on its port, and `nvidia-smi` shows total use under 9 GB.

### Phase 1: Serving layer
- `serve.py`: start servers from `agents.toml`, check they're up, restart any that crash, start the escalation model on demand.
- `llm.py`: chat through the OpenAI-compatible endpoint, with an optional grammar or JSON schema, fixed seed and timeouts, plus embeddings.
- **Checkpoint:** the grammar-forced output always parses (100 calls), and 4 parallel requests to the coder work.

### Phase 2: Model benchmark (decides the models)
- `bench/`: 20 function-sized coding cards with tests (12 Python, 8 JavaScript), 5 small HTML page cards with Playwright tests, 10 structured-output/planning tasks, 5 screenshot questions.
- Run every candidate model and measure: pass rate on the first try, pass rate with 4 candidates, speed, and how often the format breaks.
- **Checkpoint:** a table of results, and the final models are recorded in `agents.toml`.

### Phase 3: The tape
- Cards are markdown files with a metadata header: id, state, role, parent, depends, attempts, files, owner.
- Atomic writes (write to a temporary file, then rename), locks that expire, and one owner per file.
- A git commit on every accepted change, and a revert on every rejected one.
- **Checkpoint:** kill the process at random points 100 times, and the tape is never corrupted.

### Phase 4: Gates
- Format → permissions (only the card's own files, only allowed state changes) → **structure** (one public function
  per file, name matches the file, signature matches `CONTRACT.md`) → sanity (compiles, imports resolve, no
  placeholders) → the card's test → no previously passing test now fails.
- Every command runs in an **ephemeral sandbox container**: no network, read-only except `/work`, CPU/memory caps,
  hard timeout, destroyed afterwards.
- Checks for each language:
  | Language | Sanity check | Card test | Whole-project check |
  |---|---|---|---|
  | Python | `py_compile`, imports resolve | `unittest` | all tests + an end-to-end test |
  | JavaScript | `node --check` | `node --test` (built into Node 24, no packages) | all tests |
  | HTML/CSS | the HTML parses, linked files exist | Playwright loads the page: no console errors, the required elements are present, and clicks/inputs behave as specified | a screenshot checked by the vision model with specific yes/no questions |
- The vision model is only a final check on how the page looks. A page passes on the Playwright tests, never on the vision model alone.
- **Checkpoint:** unit tests cover each gate with bad input, for all three languages.

### Phase 5: Runner + RULES.md
- The state machine: `goal → todo → spec → coding → testing → done`, plus `split`, `waiting`, `integrate`, `research` and `blocked`.
- The ratchet (the progress score never goes down), the no-progress watchdog, and overall limits on steps and time.
- **Trajectory logging starts here** (the training data for the model station): every model call is written to
  `data/trajectories/*.jsonl` as {rule, model, prompt, output, gate results, tests passed, time, card id, project,
  raw version}. Every call, accepted or rejected, because the rejected ones are the negative examples.
- **Checkpoint:** a scripted fake model builds a 5-card project and halts in `done`, and its trajectories are logged.

### Phase 6: Candidates, feedback, escalation
- 4 parallel candidates per card, and the first to pass all gates wins.
- Tests are written from the card's examples, by a different model from the coder, before any code is written.
- `feedback.py` extracts the failing check, expected vs. actual values, and the line number.
- Escalation ladder: retry (at most 2–3) → the other model → research note → split → the 3B model → `blocked`.
- Repeated-output detection, and suspecting the test when every candidate fails the same check.
- **Checkpoint:** a fake model that only succeeds on the 3B model still reaches `done` through escalation.

### Phase 7: Worst-case tests (stability proof, must pass before real models)
- Fake models that return: empty output, broken blocks, writes outside the project, faked state changes, the same broken output repeated, endless split requests, huge outputs, code that hangs, contradictory edits.
- **Checkpoint:** every scenario ends in `done` or `blocked`, the tape is never corrupted, no card reaches `done` without real passing tests, and every run stops within its limits. Runs in CI from now on.

### Phase 8: Context and memory
- `CONTRACT.md`: signatures and data types written first, and each card sees only its own lines plus those of what it calls.
- Relevant code is retrieved through embeddings, and memory is carried over from the current code.
- **Checkpoint:** every model call stays under 3K tokens on a 30-card project.

### Phase 9: Real models, end to end
- Before anything else, the four **falsification tests** from `raw/research/open-objections.md`:
  decomposition pilot, mutation test (catch 8 of 10 injected bugs), gaming probe, blocked-card rate.
  If these fail, the design changes here — not after months of building.
- 3 sample projects: a CLI tool, a small library, and a static web page (Playwright plus a vision check).
- Measure: cards done, steps per card, escalation rate, blocked cards, tokens and wall-clock time per project.
- **Checkpoint:** at least 2 of the 3 finish with no manual help, and the four probes have numbers.

### Phase 9.5: Deploy pipeline
- Card types for `Dockerfile` and `compose.yaml`, gated like any other code.
- `deploy`: build → start behind `proxy` on an assigned port → health check → acceptance tests against the live
  service → mark `deployed`. Any failure rolls back to the previous image tag; the old version keeps serving.
- **Checkpoint:** the static web page project deploys, serves locally, and rolls back cleanly when a bad build is forced.

### Phase 9.6: The system builds its own web interface (first dogfood project)
The seed UI is read-only. The full interface is the system's **first real project**, chosen because it is HTML/JS,
fully testable with Playwright, and its failures are visible rather than silent.
- Goal handed to the loop: live card board, logs, progress score, start/pause, proposal review, blocked-card triage.
- It talks to the runner through a **fixed, hand-written API** in the seed. The UI may not reach the tape directly.
- **Checkpoint:** the interface is built by the loop, passes its Playwright tests, deploys locally, and is good enough
  to run the next project from. If the loop cannot build it, that is a real result about the design, not a detour.

### Phase 10: Proposals and review (replaces free self-editing of instructions)
- Agents never edit RAW. They write a proposal: a small diff plus evidence, tested automatically against the
  benchmark and chaos suite before you ever see it. Proposals without evidence, or that don't improve results, are
  rejected by code.
- Proposals are batched into one review per run, with a cap on how many, so reviewing stays meaningful.
  Rejections are recorded in RAW with the reason, so the same suggestion can't come back.
- Runs continue on RAW vN while proposals wait; nothing stalls on a review.
- **Checkpoint:** an approved proposal becomes `raw/v2`, and rebuilding the WIKI from RAW reproduces the same result.

### Phase 11: Extras
- Audio through faster-whisper, video through sampled frames sent to the vision model, and GUI-Actor-2B as an optional Python service.

### Phase 12: Model station — data and evaluation
The station turns the loop's own runs into training data, trains adapters for our exact tasks, and promotes a new
model only when it beats the current one on a frozen benchmark. Weights are treated like RAW: **a new model is a
version you approve, never a silent self-update.**

- `station/dataset.py`: build datasets from `data/trajectories/`, one per role:
  | Dataset | Positive example | Negative example |
  |---|---|---|
  | coder | the candidate that passed every gate | candidates that failed, with the error |
  | test-writer | tests that were kept and caught a real bug | tests that were wrong (every candidate failed them) |
  | splitter/planner | splits whose children all reached `done` | splits that led to `blocked` |
  | proposal writer | proposals that were approved and improved the benchmark | rejected ones |
- Hygiene: remove duplicates, cap how many examples come from one project, split train/test **by project** so nothing
  leaks, drop anything from a `blocked` card, and record which RAW version produced each example.
- `station/eval.py`: the frozen benchmark from Phase 2 plus the chaos suite, scoring pass rate on the first try,
  pass rate with 4 candidates, format errors, tokens, and speed. Every model version is scored the same way.
- **Checkpoint:** a dataset built from 3 real projects, with a leak check and a scored baseline for each current model.

### Phase 13: Model station — training
- Environment: the **`trainer` container** (CUDA + PyTorch). GPU passthrough is verified on this machine, so no
  separate WSL distro is needed. Training runs while the model services are stopped, so it has the full 12 GB.
- Methods, cheapest first:
  1. **LoRA fine-tuning** on the winning outputs. Biggest gains on format, structure and house style.
     A 1.5B model with LoRA fits comfortably in 12 GB.
  2. **Preference training (DPO/ORPO)** on passed-vs-failed candidate pairs for the same card. The loop produces these
     pairs for free, and it teaches the model which of its own plausible outputs actually passes.
  3. **Reinforcement learning from the tests (GRPO)** where the reward is the gate result. It's the most powerful
     and the most expensive, and is only worth trying at 0.5–1.5B once the first two are exhausted.
  4. **Learning from a stronger model** (optional): a larger local model solves the cards the small one failed, and its
     solutions, after passing the gates, become training data. Check the licence of the teacher model first.
- Serving: llama.cpp can load a LoRA adapter next to the base model (`--lora`), so adapters can be swapped and
  reverted without re-downloading anything. Merging and re-quantising to GGUF is the alternative when speed matters.
- **Checkpoint:** one trained adapter beats the base model on the frozen benchmark, and the loop runs end to end with it.

### Phase 14: Model station — automatic promotion, manual RAW
**Weights promote themselves; the yardstick never does.** A new adapter can take over automatically once it proves
itself, because everything it is measured against — the benchmark tasks, the chaos suite, the thresholds below,
`RULES.md` and the instruction files — lives in RAW and only a human changes it. The system can change how well it
plays, never what counts as winning.

- `station/registry.py`: `wiki/models.toml` records, per role, the active adapter, its scores, the date and the
  promotion decision. It is working state, not RAW, because promotion is automatic. RAW holds only
  `raw/promotion.toml`: the thresholds, the benchmark hash and the chaos suite.
- **Automatic promotion requires all of:**
  1. **Effectiveness:** beats the active model on the frozen benchmark over 3 seeds, by more than 2× the measured
     run-to-run variation — not a single lucky run.
  2. **Robustness:** the entire chaos suite passes, the format-error rate is no worse, and latency is within 20%.
  3. **Generalisation:** no worse (within noise) on held-out projects it never trained on.
  4. **Real use:** one full real project completes end to end with it.
  5. **Integrity:** the benchmark hash matches RAW, and the leak check shows no benchmark task in the training data.
  Fail any one and the adapter is archived with the reason. No partial credit, no manual override to promote.
- **Canary and automatic rollback:** after promotion the new adapter runs the next 50 cards while the metrics are
  watched. If the first-try pass rate drops below the previous baseline beyond the noise band, or the chaos suite
  starts failing, the system **rolls back on its own**, quarantines the adapter and writes the evidence to the log.
  Two failed canaries for one role pause training for that role until a human looks.
- **Always reversible:** the base model is never deleted, the last 5 adapters are kept, and rollback is one line.
- **You are told, not asked:** every promotion and rollback is logged and summarised in the run report.
- **Known risks and their handling:** training on its own output can narrow the model (guard: the held-out set and
  the "learning from a stronger model" data); a model can forget general ability (guard: the benchmark includes
  general tasks); and the benchmark can become the target (guard: refresh it with new cards each quarter, keeping
  the old one for comparison).
- **Checkpoint:** a promotion and a rollback both work, with the loop stable before and after.

---

## Current code
| Keep | Rewrite | Remove |
|---|---|---|
| `memory.py`, `tools.py` (file safety, running commands) | `llm.py` (OpenAI-compatible, grammars), `agents.py` becomes rule-driven | `orchestrator.py` (the central orchestrator is replaced by `runner.py` and `RULES.md`) |

## Decisions
1. **Target languages: Python plus HTML/JS.** No frameworks and no build tools, ever — plain HTML, CSS and
   JavaScript, and the Python standard library. Decided.
2. **One function per file, everywhere in generated code.** No clubbing several functions into one file, so two
   agents never contend for the same file and a fix touches exactly one file.
   - `lib/<function_name>.py` exports exactly one public function of the same name; `tests/test_<name>.py` beside it.
   - Shared data shapes live in one `types.py`; `main.py` is wiring only, with no logic.
   - Imports follow one fixed pattern: `from lib.<name> import <name>`.
   - `CONTRACT.md` lists every function's signature, description and dependencies **before any code is written**.
   - A gate enforces all of this: one public function per file, the name matches the file, the signature matches the
     contract, and no file outside the card's own.
   - Build order is by dependency layer: functions with no dependencies first, each layer tested before the next.
3. **Docker everything.** Models, runner, web, sandboxes, proxy and trainer all run as Compose services. Accepted
   cost: a little inference overhead versus running llama-server on Windows directly, in exchange for one
   reproducible environment, clean staging/main separation and real isolation.
4. **The kernel is human-written and permanently off-limits to agents.** Decided.

## Open decisions
1. Is git fine for checkpoints? It's needed for the ratchet.
2. Escalation model: Qwen2.5-Coder-3B is under a **research-only licence**. Keep it (fine for personal/research use),
   or swap to the 7B (Apache 2.0, ~4.7 GB, loaded on demand) if the work may ever be commercial.
3. ~~WSL2 for training~~ — resolved: the `trainer` container works, GPU passthrough verified 2026-09-23.

## Measured on this machine (2026-09-23)
llama.cpp build 11105, CUDA 12.4, RTX 3060 12 GB. Warm load / GPU memory / first request:
coder-1.5B 1.4 s / 1,347 MB / 0.05 s · general-1B 2.8 s / 905 MB / 0.07 s · vision 2.6 s / 1,892 MB / 0.09 s ·
embeddings 0.5 s / 255 MB / 0.01 s · coder-3B 1.9 s / 2,335 MB / 0.06 s.
Four core models: **4.4 GB**, or 6.7 GB with the 3B. Models live in `E:\models\gguf`.
