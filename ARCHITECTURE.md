# Architecture

```
                         ┌──────────────────────────────┐
   goal ───────────────► │ Orchestrator (qwen2.5:1.5b)  │ ◄── instructions/ORCHESTRATOR.md
                         └──────┬───────────────────────┘      (one ## section per phase)
        ┌───────────────────────┼────────────────────────┬─────────────────────┐
        ▼                       ▼                        ▼                     ▼
  Research pool (2)       Coder pool (2)           Task pool (2)        Verifier (task models)
  qwen2.5:1.5b            qwen2.5-coder:1.5b       llama3.2:1b          + real commands
  gemma3:1b               deepseek-coder:1.3b      gemma3:1b              (unittest, etc.)
        │                       │                        │                     │
        └───────────────┬───────┴────────────────────────┴─────────────────────┘
                        ▼
      Memory (data/memory.db)  +  Project data (workspace/<project>/.agents/*.md)
```

## The loop
1. **Research**: orchestrator asks 2–4 questions → both researchers answer in parallel → `RESEARCH.md`.
2. **Plan** (instructions): orchestrator writes tasks and verify commands as JSON → `PLAN.md`.
3. **Execute**: code tasks go to the coder pool, other tasks go to the task pool, 2 at a time per pool.
   Agents emit ```` ```file:path ```` blocks and the system writes them into the project folder (paths can't escape the folder).
4. **Verify**: runs the verify commands, then a verifier model reviews the files against the goal.
   It passes only when every command exits 0, the verifier says yes, and every task produced files.
5. **Improve**: on failure, the orchestrator turns the issues into fix tasks **and** lessons.
   Lessons are appended to the `## Lessons` section of the relevant role's `.md` file (the old version is backed up
   to `data/instruction_history/`) and stored in long-term memory. The next cycle runs only the fix tasks.
6. Repeat until it passes or `max_cycles` is reached. `resume` continues from the saved state.

## Memory
| Layer | Storage | Contents |
|---|---|---|
| Short-term | `short_term` table | Recent events per project; when the window fills, the oldest half is summarised into long-term memory |
| Long-term | `long_term` table + `nomic-embed-text` vectors | Research, lessons, summaries, successes, searchable **across projects** |
| Project state | `project_state` table | Goal, plan, pending tasks, last verdict, status (used for resume) |
| Project data | `workspace/<p>/.agents/` | `GOAL.md`, `PLAN.md`, `RESEARCH.md`, `LOG.md`, task notes |
| Instructions | `instructions/*.md` | Role prompts that improve over time |

## Changing behaviour
- Swap models: edit `agents.toml`, then run `python run.py setup`.
- Change a phase: edit that `## Section` in `instructions/ORCHESTRATOR.md`. The code reads it on every call.
- Add a phase: add a `## Section` to the markdown and call `self.brain.run(..., phase="SECTION")` in `core/orchestrator.py`.
