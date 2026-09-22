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

The always-on models total about 5.5 GB, and about 8 GB with escalation, which leaves room within 12 GB.
The GUI actions model would only run when those others aren't running.

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
bench/             model benchmark tasks
tests/chaos/       worst-case fake-model tests (the stability proof)
models/            downloaded GGUF files (git-ignored)
workspace/<p>/     project code + tape/ + CONTRACT.md + LOG.md
```

---

## Phases (each ends with a checkpoint that must pass before moving on)

### Phase 0: Runtime setup
- Download the llama.cpp Windows CUDA build into `tools/llama.cpp/`.
- `scripts/fetch_models.py`: download the GGUF files from Hugging Face into `models/` and check their checksums.
- **Checkpoint:** each model answers a request on its port, and `nvidia-smi` shows total use under 9 GB.

### Phase 1: Serving layer
- `serve.py`: start servers from `agents.toml`, check they're up, restart any that crash, start the escalation model on demand.
- `llm.py`: chat through the OpenAI-compatible endpoint, with an optional grammar or JSON schema, fixed seed and timeouts, plus embeddings.
- **Checkpoint:** the grammar-forced output always parses (100 calls), and 4 parallel requests to the coder work.

### Phase 2: Model benchmark (decides the models)
- `bench/`: 20 function-sized coding cards with tests, 10 structured-output/planning tasks, 5 screenshot questions.
- Run every candidate model and measure: pass rate on the first try, pass rate with 4 candidates, speed, and how often the format breaks.
- **Checkpoint:** a table of results, and the final models are recorded in `agents.toml`.

### Phase 3: The tape
- Cards are markdown files with a metadata header: id, state, role, parent, depends, attempts, files, owner.
- Atomic writes (write to a temporary file, then rename), locks that expire, and one owner per file.
- A git commit on every accepted change, and a revert on every rejected one.
- **Checkpoint:** kill the process at random points 100 times, and the tape is never corrupted.

### Phase 4: Gates
- Format → permissions (only the card's own files, only allowed state changes) → sanity (compiles, imports resolve, no placeholders) → the card's test → no previously passing test now fails.
- **Checkpoint:** unit tests cover each gate with bad input.

### Phase 5: Runner + RULES.md
- The state machine: `goal → todo → spec → coding → testing → done`, plus `split`, `waiting`, `integrate`, `research` and `blocked`.
- The ratchet (the progress score never goes down), the no-progress watchdog, and overall limits on steps and time.
- **Checkpoint:** a scripted fake model builds a 5-card project and halts in `done`.

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
- 3 sample projects: a CLI tool, a small library, and a static web page (checked with a Playwright screenshot plus the vision model).
- Measure: percentage of cards done, steps per card, how often escalation is needed, and total time.
- **Checkpoint:** at least 2 of the 3 projects finish with no manual help.

### Phase 10: Lessons with probation (off by default)
- Lessons attach to specific rules, go on probation, are compared over several runs, and are removed automatically if they don't help. Instruction size is capped.
- **Checkpoint:** switching lessons on does not lower the Phase 9 results over 3 runs.

### Phase 11: Extras
- Audio through faster-whisper, video through sampled frames sent to the vision model, and GUI-Actor-2B as an optional Python service.

---

## Current code
| Keep | Rewrite | Remove |
|---|---|---|
| `memory.py`, `tools.py` (file safety, running commands) | `llm.py` (OpenAI-compatible, grammars), `agents.py` becomes rule-driven | `orchestrator.py` (the central orchestrator is replaced by `runner.py` and `RULES.md`) |

## Open decisions
1. Initial target language: Python only, or Python plus HTML/JS?
2. Is git fine for checkpoints? It's needed for the ratchet.
3. Should the escalation 3B model be allowed? It's about 2.5 GB, started on demand.
