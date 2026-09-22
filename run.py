"""CLI for the local agent team.

  python run.py setup                      pull every model in agents.toml
  python run.py new "build a todo CLI"     start a project from a goal
  python run.py resume <project>           continue an incomplete project
  python run.py status                     list projects
  python run.py recall "query"             search long-term memory
"""
import argparse
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def models_in_config():
    cfg = tomllib.loads((ROOT / "agents.toml").read_text(encoding="utf-8"))
    names = {cfg["orchestrator"]["model"], cfg["ollama"]["embed_model"]}
    for role in ("coder", "task", "research"):
        names |= {c["model"] for c in cfg[role]}
    return cfg, sorted(names)


def setup():
    cfg, names = models_in_config()
    from core.llm import list_local_models
    have = list_local_models(cfg["ollama"]["host"])
    for m in names:
        if m in have or f"{m}:latest" in have:
            print(f"ok      {m}")
        else:
            print(f"pulling {m}")
            subprocess.run(["ollama", "pull", m], check=False)


def main():
    p = argparse.ArgumentParser(description="Local multi-agent project builder")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    n = sub.add_parser("new")
    n.add_argument("goal")
    n.add_argument("--name", help="project folder name (default: from goal)")
    n.add_argument("--cycles", type=int)
    r = sub.add_parser("resume")
    r.add_argument("project")
    r.add_argument("--cycles", type=int)
    sub.add_parser("status")
    q = sub.add_parser("recall")
    q.add_argument("query")
    a = p.parse_args()

    if a.cmd == "setup":
        return setup()

    from core.orchestrator import Orchestrator, slug
    orch = Orchestrator()
    if a.cmd == "new":
        ok = orch.run(goal=a.goal, project=a.name or slug(a.goal), max_cycles=a.cycles)
        print(f"\n{'DONE' if ok else 'INCOMPLETE'} -> workspace/{a.name or slug(a.goal)}")
        return 0 if ok else 1
    if a.cmd == "resume":
        ok = orch.run(project=a.project, max_cycles=a.cycles)
        print(f"\n{'DONE' if ok else 'INCOMPLETE'} -> workspace/{a.project}")
        return 0 if ok else 1
    if a.cmd == "status":
        for project, status in orch.mem.projects():
            print(f"{status.strip(chr(34)):<11} {project}")
    if a.cmd == "recall":
        for project, kind, content in orch.mem.recall(a.query, k=8):
            print(f"[{project}/{kind}] {content[:300]}\n")


if __name__ == "__main__":
    sys.exit(main())
