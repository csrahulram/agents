"""Can a small model write tests that catch real bugs?

The load-bearing assumption of the whole design: tests decide truth, and a 1B model writes them.

Method:
  1. Take a hand-written correct implementation of each card (never shown to any model).
  2. Generate mutants of it (operator swaps, constant tweaks, removed guards, off-by-one).
  3. Keep a mutant only if our own hidden tests kill it - that proves it is a real bug.
  4. Ask the model to write tests from the spec alone.
  5. Score: do its tests pass the correct implementation (no false alarms), and how many real bugs do they kill?

  python bench/test_writer.py                 # general model (MiniCPM5-1B)
  python bench/test_writer.py --port 18001    # the coder model instead
"""
import argparse
import ast
import json
import random
import re
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = {c["id"]: c for c in json.loads((ROOT / "bench" / "cards" / "cards.json").read_text(encoding="utf-8"))}
REFERENCE = (ROOT / "bench" / "cards" / "reference.py").read_text(encoding="utf-8")
SANDBOX_IMAGE = "python:3.12-slim"

SYSTEM = """You write Python tests. Given a function specification, write tests that would catch a buggy
implementation.

Rules:
- Output ONLY a ```python code block.
- Write plain `assert` statements at module level, one per line, calling the function directly.
- For errors expected, use: try/except with `assert False` if no error is raised.
- Cover the examples, the edge cases named in the specification, and boundary values.
- Do not define the function. Do not import it. Assume it already exists.
- At least 8 assertions."""


def reference_source(name):
    """Just the one function, plus the imports it needs."""
    tree = ast.parse(REFERENCE)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return "import re\n\n" + ast.unparse(fn)


class Mutator(ast.NodeTransformer):
    """One small, plausible bug per mutant."""
    SWAP_CMP = {ast.LtE: ast.Lt, ast.GtE: ast.Gt, ast.Lt: ast.LtE, ast.Gt: ast.GtE,
                ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
    SWAP_OP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv}

    def __init__(self, target):
        self.target, self.count = target, 0

    def _hit(self):
        self.count += 1
        return self.count == self.target

    def visit_Compare(self, node):
        self.generic_visit(node)
        op = type(node.ops[0])
        if op in self.SWAP_CMP and self._hit():
            node.ops[0] = self.SWAP_CMP[op]()
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        op = type(node.op)
        if op in self.SWAP_OP and self._hit():
            node.op = self.SWAP_OP[op]()
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, int) and not isinstance(node.value, bool) and self._hit():
            return ast.Constant(value=node.value + 1)
        return node

    def visit_Raise(self, node):
        if self._hit():
            return ast.Pass()
        return node


def make_mutants(source, limit=12):
    out = []
    for target in range(1, 40):
        try:
            mutated = ast.unparse(ast.fix_missing_locations(Mutator(target).visit(ast.parse(source))))
        except Exception:
            continue
        if mutated != source and mutated not in out:
            out.append(mutated)
        if len(out) >= limit:
            break
    return out


def run_checks(code, checks, name, timeout=60):
    """Run a list of assertion lines against an implementation, in a container. True = all passed."""
    helper = (
        "def raises(exc, *args, **kwargs):\n"
        f"    try:\n        {name}(*args, **kwargs)\n"
        "    except exc:\n        return\n"
        "    except Exception as e:\n        raise AssertionError('wrong error: ' + type(e).__name__)\n"
        "    raise AssertionError('no error raised')\n"
    )
    body = "\n".join(f"try:\n    {c}\nexcept Exception as e:\n    failures.append({c!r})" for c in checks)
    script = f"{code}\n\n{helper}\nfailures = []\n{body}\nprint('FAIL' if failures else 'OK')\n" \
             f"import sys; sys.exit(1 if failures else 0)"
    with tempfile.TemporaryDirectory(dir=ROOT / "bench") as d:
        p = Path(d) / "check.py"
        p.write_text(script, encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
               "-v", f"{d}:/work:ro", "-w", "/work", SANDBOX_IMAGE, "python", "check.py"]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).returncode == 0
        except subprocess.TimeoutExpired:
            return False


ALLOWED_IMPORTS = {"re", "math", "string", "collections", "itertools", "json", "datetime"}


def sanitise(test_code, name):
    """A format gate for model-written tests: keep the checks, drop everything that cannot run.

    Model test blocks fail mechanically far more often than they fail on judgement - `import pytest`,
    a re-definition of the function under test, or runaway generation that ends mid-string. All of that
    is cheap for code to remove or reject.
    """
    test_code = test_code.strip()
    if test_code.startswith("```"):                       # nested fence
        test_code = re.sub(r"^```(?:python)?\n|```$", "", test_code).strip()
    try:
        tree = ast.parse(test_code)
    except SyntaxError:                                    # usually truncated / degenerate output
        lines, kept = test_code.splitlines(), []
        for line in lines:                                 # salvage the statements that do parse
            try:
                ast.parse(line)
                kept.append(line)
            except SyntaxError:
                continue
        try:
            tree = ast.parse("\n".join(kept))
        except SyntaxError:
            return ""
    body = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue                                       # re-definitions and helper classes
        if isinstance(node, ast.Import):
            names = [n.name.split(".")[0] for n in node.names]
            if not set(names) <= ALLOWED_IMPORTS:
                continue                                   # pytest, unittest, the function's own module
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
            continue
        body.append(node)
    return ast.unparse(ast.Module(body=body, type_ignores=[]))


# kept for compatibility with earlier runs
strip_definitions = sanitise


def run_test_block(code, test_code, timeout=60):
    """Run a model-written test block as a whole. True = it passed."""
    with tempfile.TemporaryDirectory(dir=ROOT / "bench") as d:
        (Path(d) / "check.py").write_text(code + "\n\n" + test_code + "\nprint('OK')\n", encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
               "-v", f"{d}:/work:ro", "-w", "/work", SANDBOX_IMAGE, "python", "check.py"]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).returncode == 0
        except subprocess.TimeoutExpired:
            return False


def ask(port, card, temperature=0.3, seed=1):
    spec = (f"{card['signature']}\n\n{card['description']}\n\nExamples:\n"
            + "\n".join(f"  {e}" for e in card["examples"]))
    payload = {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": spec}],
               "temperature": temperature, "seed": seed, "max_tokens": 2500,
               "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                 data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        msg = json.loads(r.read())["choices"][0]["message"]
    text = msg.get("content") or msg.get("reasoning_content") or ""
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    return (blocks[0] if blocks else text).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=18002, help="18002 general, 18001 coder, 18005 the 3B")
    a = ap.parse_args()
    random.seed(0)

    rows = []
    print(f"test writer: port {a.port}")
    print(f"{'card':<22} {'mutants':<8} {'ours kill':<10} {'model kills':<12} {'false alarm':<12} asserts")
    for name, card in CARDS.items():
        src = reference_source(name)
        mutants = make_mutants(src)
        # a mutant is a real bug only if our own hidden tests kill it
        real_bugs = [m for m in mutants if not run_checks(m, card["hidden_tests"], name)]
        sane = run_checks(src, card["hidden_tests"], name)  # sanity: reference must pass its own tests

        tests = strip_definitions(ask(a.port, card), name)
        n_asserts = tests.count("assert")
        false_alarm = not run_test_block(src, tests)          # do the model's tests reject correct code?
        killed = sum(1 for m in real_bugs if not run_test_block(m, tests))

        rows.append({"card": name, "reference_ok": sane, "mutants": len(mutants), "real_bugs": len(real_bugs),
                     "model_killed": killed, "false_alarm": false_alarm, "asserts": n_asserts})
        print(f"{name:<22} {len(mutants):<8} {len(real_bugs):<10} "
              f"{(str(killed) + '/' + str(len(real_bugs))):<12} {str(false_alarm):<12} {n_asserts}")

    total_bugs = sum(r["real_bugs"] for r in rows)
    killed = sum(r["model_killed"] for r in rows)
    alarms = sum(r["false_alarm"] for r in rows)
    print("\n" + "=" * 70)
    print(f"reference passes its own tests: {sum(r['reference_ok'] for r in rows)}/{len(rows)}")
    print(f"real bugs (mutants our tests kill): {total_bugs}")
    print(f"model-written tests killed:         {killed}/{total_bugs} = {100*killed/max(total_bugs,1):.0f}%")
    print(f"cards where model tests falsely rejected correct code: {alarms}/{len(rows)}")
    out = ROOT / "bench" / f"test_writer_{a.port}.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
