"""File writing, command execution and optional web search used by the agents."""
import html
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

# Coders emit files as:  ```file:path/to/name.py\n<content>\n```
FILE_BLOCK = re.compile(r"```(?:file:|[a-zA-Z0-9_+-]*\s+file:)\s*([^\n`]+)\n(.*?)```", re.S)
SKIP_DIRS = {".agents", ".git", "__pycache__", "node_modules", ".venv", "venv"}


def parse_files(text):
    return [(p.strip(), body) for p, body in FILE_BLOCK.findall(text)]


def safe_path(root, rel):
    root = Path(root).resolve()
    target = (root / rel.lstrip("/\\")).resolve()
    if root != target and root not in target.parents:
        raise ValueError(f"path escapes project: {rel}")
    return target


def write_files(root, files):
    written = []
    for rel, body in files:
        try:
            path = safe_path(root, rel)
        except ValueError:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        written.append(str(path.relative_to(Path(root).resolve())).replace("\\", "/"))
    return written


def list_files(root):
    root = Path(root)
    return sorted(
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )


def read_files(root, rels, limit=6000):
    out, budget = [], limit
    for rel in rels:
        try:
            text = safe_path(root, rel).read_text(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            continue
        chunk = text[:budget]
        out.append(f"```file:{rel}\n{chunk}\n```")
        budget -= len(chunk)
        if budget <= 0:
            break
    return "\n".join(out)


def run_cmd(cmd, cwd, timeout=120):
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        out = (p.stdout + "\n" + p.stderr).strip()
        return p.returncode, out[-3000:]
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"


def web_search(query, n=5):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        page = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")
    except Exception as e:
        return f"(web search failed: {e})"
    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', page, re.S)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', page, re.S)
    clean = lambda s: html.unescape(re.sub("<.*?>", "", s)).strip()
    return "\n".join(f"- {clean(t)}: {clean(s)}" for t, s in list(zip(titles, snippets))[:n])
