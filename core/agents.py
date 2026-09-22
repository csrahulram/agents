"""Agents are an LLM plus a markdown instruction file. Pools run two agents in parallel."""
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle
from pathlib import Path


class Instructions:
    """A markdown file split into `## Section` blocks. Lessons are appended by the improve loop."""

    def __init__(self, path, history_dir):
        self.path = Path(path)
        self.history = Path(history_dir)
        self.lock = threading.Lock()

    def text(self):
        return self.path.read_text(encoding="utf-8")

    def sections(self):
        parts = re.split(r"^## +(.+)$", self.text(), flags=re.M)
        return {parts[i].strip().upper(): parts[i + 1].strip() for i in range(1, len(parts), 2)}

    def section(self, name, default=""):
        return self.sections().get(name.upper(), default)

    def system_prompt(self, *names):
        """Role + Rules + Lessons, plus any named phase section."""
        s = self.sections()
        keep = ["ROLE", "RULES", *[n.upper() for n in names], "LESSONS"]
        return "\n\n".join(f"## {k}\n{s[k]}" for k in keep if s.get(k))

    def add_lessons(self, lessons, max_lessons=25):
        lessons = [l.strip().lstrip("-* ").strip() for l in lessons if l and l.strip()]
        if not lessons:
            return
        with self.lock:
            self.history.mkdir(parents=True, exist_ok=True)
            shutil.copy(self.path, self.history / f"{self.path.stem}.{int(time.time())}.md")
            text = self.text()
            if "## Lessons" not in text:
                text = text.rstrip() + "\n\n## Lessons\n"
            head, _, body = text.partition("## Lessons")
            existing = [l[2:].strip() for l in body.splitlines() if l.startswith("- ")]
            merged = existing + [l for l in lessons if l not in existing]
            merged = merged[-max_lessons:]
            self.path.write_text(head + "## Lessons\n" + "".join(f"- {l}\n" for l in merged),
                                 encoding="utf-8")


class Agent:
    def __init__(self, name, role, llm, instructions):
        self.name, self.role, self.llm, self.instructions = name, role, llm, instructions

    def run(self, task, context="", phase=None, json_mode=False):
        messages = [
            {"role": "system", "content": self.instructions.system_prompt(*([phase] if phase else []))},
            {"role": "user", "content": (f"# Context\n{context}\n\n" if context else "") + f"# Task\n{task}"},
        ]
        return self.llm.chat_json(messages) if json_mode else self.llm.chat(messages)


class Pool:
    """Round-robins work across agents of one role, with one worker thread per agent."""

    def __init__(self, agents):
        self.agents = agents
        self._next = cycle(agents)
        self._lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=len(agents))

    def submit(self, fn):
        with self._lock:
            agent = next(self._next)
        return self.executor.submit(fn, agent)

    def map(self, fn, items):
        futures = [self.submit(lambda a, it=it: fn(a, it)) for it in items]
        return [f.result() for f in futures]
