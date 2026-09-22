"""The orchestrator: research -> plan -> execute -> verify -> improve, looped until the goal passes.

Every phase prompt comes from instructions/ORCHESTRATOR.md, so changing the markdown changes behaviour.
Project data lives in workspace/<project>/ (code) and workspace/<project>/.agents/ (plans, logs).
"""
import json
import re
import time
import tomllib
from pathlib import Path

from .agents import Agent, Instructions, Pool
from .llm import LLM
from .memory import Memory
from . import tools

ROOT = Path(__file__).resolve().parent.parent


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "project"


def _norm_tasks(tasks, prefix=""):
    out = []
    for i, t in enumerate(tasks or [], 1):
        if not isinstance(t, dict):
            t = {"title": str(t)}
        t["id"] = f"{prefix}{t.get('id', i)}" if prefix else t.get("id", i)
        t["type"] = "task" if t.get("type") == "task" else "code"
        files = t.get("files") or []
        t["files"] = [files] if isinstance(files, str) else list(files)
        out.append(t)
    return out


class Orchestrator:
    def __init__(self, config_path=ROOT / "agents.toml", log=print):
        self.cfg = tomllib.loads(Path(config_path).read_text(encoding="utf-8"))
        self.log = log
        o = self.cfg["ollama"]
        mk = lambda c: LLM(o["host"], c["model"], c.get("temperature", 0.3), o["num_ctx"], o["keep_alive"])
        hist = ROOT / "data" / "instruction_history"
        self.instr = {n: Instructions(ROOT / "instructions" / f"{n.upper()}.md", hist)
                      for n in ("orchestrator", "coder", "task", "research", "verifier")}
        self.brain = Agent("orchestrator", "orchestrator", mk(self.cfg["orchestrator"]), self.instr["orchestrator"])
        self.pools = {
            role: Pool([Agent(c["name"], role, mk(c), self.instr[role]) for c in self.cfg[role]])
            for role in ("coder", "task", "research")
        }
        # The task models double as verifiers, with their own instruction file.
        self.verifiers = Pool([Agent(c["name"] + "-verify", "verifier", mk(c), self.instr["verifier"])
                               for c in self.cfg["task"]])
        embedder = LLM(o["host"], o["embed_model"]) if o.get("embed_model") else None
        (ROOT / "data").mkdir(exist_ok=True)
        self.mem = Memory(ROOT / "data" / "memory.db", embedder)
        self.loop = self.cfg["loop"]

    # ------------------------------------------------------------------ helpers
    def _dirs(self, project):
        code = ROOT / "workspace" / project
        meta = code / ".agents"
        meta.mkdir(parents=True, exist_ok=True)
        return code, meta

    def _event(self, project, who, msg):
        self.log(f"[{who}] {msg}")
        self.mem.add_short(project, who, msg)
        _, meta = self._dirs(project)
        with open(meta / "LOG.md", "a", encoding="utf-8") as f:
            f.write(f"- {time.strftime('%Y-%m-%d %H:%M:%S')} **{who}**: {msg}\n")
        self._compact(project)

    def _compact(self, project):
        """Move old short-term memory into a long-term summary once the window is full."""
        window = self.loop["short_term_window"]
        if self.mem.short_count(project) <= window:
            return
        old = self.mem.pop_oldest_short(project, keep=window // 2)
        text = "\n".join(f"{a}: {c}" for a, c in old)
        try:
            summary = self.brain.run("Summarise these events.", text[:6000], phase="SUMMARISE")
        except Exception:
            summary = text[:1500]
        self.mem.remember(project, "summary", summary)

    def _context(self, project, query):
        """Short-term events + relevant long-term memories (this and past projects)."""
        recent = "\n".join(f"- {a}: {c[:300]}" for a, c in self.mem.recent(project, 8))
        recalled = "\n".join(f"- ({p}/{k}) {c[:400]}" for p, k, c in self.mem.recall(query, k=5))
        goal = self.mem.get_state(project, "goal", "")
        return f"## Goal\n{goal}\n\n## Recent events\n{recent or '-'}\n\n## Relevant memory\n{recalled or '-'}"

    # ------------------------------------------------------------------ phases
    def research(self, project, goal):
        r = self.brain.run(goal, self._context(project, goal), phase="RESEARCH_QUESTIONS", json_mode=True)
        questions = [str(q) for q in (r.get("questions") or [goal])][:4]
        self._event(project, "orchestrator", f"research questions: {questions}")

        def ask(agent, q):
            web = tools.web_search(q) if self.loop["web_research"] else ""
            ctx = self._context(project, q) + (f"\n\n## Web results\n{web}" if web else "")
            return f"### {q}\n_{agent.name}_\n\n{agent.run(q, ctx)}"

        notes = "\n\n".join(self.pools["research"].map(ask, questions))
        _, meta = self._dirs(project)
        (meta / "RESEARCH.md").write_text(f"# Research\n\n{notes}\n", encoding="utf-8")
        self.mem.remember(project, "research", notes[:3000])
        return notes

    def plan(self, project, goal, research):
        code, meta = self._dirs(project)
        ctx = (self._context(project, goal) + f"\n\n## Research\n{research[:4000]}"
               f"\n\n## Existing files\n{tools.list_files(code)}")
        plan = self.brain.run(goal, ctx, phase="PLAN", json_mode=True)
        plan["tasks"] = _norm_tasks(plan.get("tasks"))
        plan["verify"] = [str(v) for v in plan.get("verify") or []]
        if not plan["tasks"]:
            plan["tasks"] = _norm_tasks([{"title": goal, "details": goal}])
        self._write_plan(meta, goal, plan)
        self.mem.set_state(project, "plan", plan)
        return plan

    def _write_plan(self, meta, goal, plan, done=()):
        lines = [f"# Plan\n\n**Goal:** {goal}\n\n## Tasks"]
        for t in plan["tasks"]:
            mark = "x" if t["id"] in done else " "
            lines.append(f"- [{mark}] {t['id']}. ({t['type']}) **{t.get('title', '')}** — "
                         f"{t.get('details', '')} files: {', '.join(t['files'])}")
        lines.append("\n## Verify\n" + "\n".join(f"- `{v}`" for v in plan["verify"]))
        (meta / "PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def execute(self, project, tasks):
        code, meta = self._dirs(project)

        def do(agent, t):
            ctx = (self._context(project, t.get("title", "")) +
                   f"\n\n## Project files\n{tools.list_files(code)}\n\n## Relevant file contents\n"
                   f"{tools.read_files(code, t['files'])}")
            task = f"{t.get('title', '')}\n\n{t.get('details', '')}\n\nFiles to produce: {t['files']}"
            out = agent.run(task, ctx)
            return t, agent.name, out, tools.write_files(code, tools.parse_files(out))

        futures = [self.pools["coder" if t["type"] == "code" else "task"].submit(lambda a, t=t: do(a, t))
                   for t in tasks]
        results = []
        for f in futures:
            t, who, out, written = f.result()
            if not written and t["type"] == "task":
                note = meta / f"task-{t['id']}.md"
                note.write_text(f"# {t.get('title', '')}\n\n{out}\n", encoding="utf-8")
                written = [str(note.relative_to(code)).replace("\\", "/")]
            self._event(project, who, f"task {t['id']} '{t.get('title', '')}' -> {written or 'NO FILES'}")
            results.append({"task": t, "agent": who, "written": written})
        return results

    def verify(self, project, goal, plan, results):
        code, _ = self._dirs(project)
        checks = []
        if self.loop["allow_shell"]:
            for cmd in plan.get("verify", [])[:5]:
                rc, out = tools.run_cmd(cmd, code, self.loop["command_timeout"])
                checks.append({"cmd": cmd, "rc": rc, "output": out})
                self._event(project, "verify", f"`{cmd}` exit {rc}")
        missing = [r["task"]["id"] for r in results if not r["written"]]
        files = tools.list_files(code)
        ctx = (f"## Goal\n{goal}\n\n## Files\n{files}\n\n## Contents\n{tools.read_files(code, files, 5000)}\n\n"
               f"## Command results\n{json.dumps(checks, indent=1)[:3000]}\n\n## Tasks without output\n{missing}")
        review = self.verifiers.submit(
            lambda a: a.run("Does the project meet the goal?", ctx, json_mode=True)).result()
        issues = [str(i) for i in review.get("issues") or []]
        issues += [f"`{c['cmd']}` failed (exit {c['rc']}): {c['output'][-500:]}" for c in checks if c["rc"]]
        issues += [f"task {m} produced no files (use ```file:path blocks)" for m in missing]
        passed = (bool(review.get("pass")) and all(c["rc"] == 0 for c in checks)
                  and not missing and bool(files))
        if not passed and not issues:
            issues = ["verifier rejected the result without details; re-check the goal"]
        return {"pass": passed, "issues": issues, "checks": checks}

    def improve(self, project, goal, verdict):
        """Reflect on failures: write lessons into the instruction markdown and plan fix tasks."""
        code, _ = self._dirs(project)
        ctx = (self._context(project, goal) + f"\n\n## Files\n{tools.list_files(code)}\n\n## Issues\n"
               + "\n".join(f"- {i}" for i in verdict["issues"])[:4000])
        r = self.brain.run(goal, ctx, phase="IMPROVE", json_mode=True)
        lessons = r.get("lessons") if isinstance(r.get("lessons"), dict) else {}
        for role, items in lessons.items():
            role = role.lower()
            if role in self.instr and isinstance(items, list):
                items = [str(i) for i in items]
                self.instr[role].add_lessons(items, self.loop["max_lessons"])
                self._event(project, "improve", f"{len(items)} lesson(s) -> {role.upper()}.md")
                for i in items:
                    self.mem.remember(project, f"lesson:{role}", i)
        fixes = _norm_tasks(r.get("fix_tasks"), prefix="fix") or _norm_tasks(
            [{"title": "Fix verification issues", "details": "\n".join(verdict["issues"])}], prefix="fix")
        new_verify = [str(v) for v in r.get("verify") or []]
        return fixes, new_verify

    # ------------------------------------------------------------------ main loop
    def run(self, goal=None, project=None, max_cycles=None):
        project = project or slug(goal)
        if goal and goal != self.mem.get_state(project, "goal"):
            self.mem.set_state(project, "plan", None)  # new goal on an existing project: re-plan
            self.mem.set_state(project, "pending", None)
        goal = goal or self.mem.get_state(project, "goal")
        if not goal:
            raise ValueError(f"no goal stored for project '{project}'")
        code, meta = self._dirs(project)
        (meta / "GOAL.md").write_text(f"# Goal\n\n{goal}\n", encoding="utf-8")
        self.mem.set_state(project, "goal", goal)
        self.mem.set_state(project, "status", "running")
        max_cycles = max_cycles or self.loop["max_cycles"]

        plan = self.mem.get_state(project, "plan")
        if plan:
            pending = self.mem.get_state(project, "pending") or plan["tasks"]
            self._event(project, "orchestrator", f"resuming with {len(pending)} pending task(s)")
        else:
            self._event(project, "orchestrator", "phase: research")
            notes = self.research(project, goal)
            self._event(project, "orchestrator", "phase: plan")
            plan = self.plan(project, goal, notes)
            pending = plan["tasks"]

        done = []
        for cycle in range(1, max_cycles + 1):
            self._event(project, "orchestrator", f"cycle {cycle}: executing {len(pending)} task(s)")
            self.mem.set_state(project, "pending", pending)
            results = self.execute(project, pending)
            done += [r["task"]["id"] for r in results if r["written"]]
            verdict = self.verify(project, goal, plan, results)
            self.mem.set_state(project, "last_verdict", verdict)
            if verdict["pass"]:
                self._write_plan(meta, goal, plan, done)
                self._event(project, "orchestrator", f"PASSED on cycle {cycle}")
                self.mem.remember(project, "success", f"Goal '{goal}' completed in {cycle} cycle(s). "
                                                      f"Files: {tools.list_files(code)}")
                self.mem.set_state(project, "status", "done")
                self.mem.set_state(project, "pending", [])
                return True
            self._event(project, "orchestrator", f"cycle {cycle} failed: {verdict['issues'][:3]}")
            pending, new_verify = self.improve(project, goal, verdict)
            if new_verify:
                plan["verify"] = new_verify
            plan["tasks"] = plan["tasks"] + pending
            self.mem.set_state(project, "plan", plan)
            self._write_plan(meta, goal, plan, done)
        self.mem.set_state(project, "pending", pending)
        self.mem.set_state(project, "status", "incomplete")
        self._event(project, "orchestrator", "stopped: max cycles reached (run `resume` to continue)")
        return False
