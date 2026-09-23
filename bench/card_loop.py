"""Measure the loop mechanisms that are supposed to make small models survive long runs.

Four conditions on the same card-sized tasks, using the real coder model and hidden tests:

  pass@1            one candidate                       - the naive baseline
  pass@4            four candidates in parallel          - "candidates beat repair"
  repair-fresh      retry with ONLY spec + extracted error
  repair-carry      retry with the failed attempts still in context (self-conditioning)

Every test runs in an ephemeral container with no network.

  python bench/card_loop.py            # all cards, all conditions
  python bench/card_loop.py --cards 3  # quick run
"""
import argparse
import json
import re
import statistics
import subprocess
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = json.loads((ROOT / "bench" / "cards" / "cards.json").read_text(encoding="utf-8"))
CODER_URL = "http://127.0.0.1:18001/v1/chat/completions"
SANDBOX_IMAGE = "python:3.12-slim"
MAX_REPAIRS = 2

SYSTEM = """You are a Python coder. Write one function, exactly as specified.

Rules:
- Output ONLY a ```python code block containing the complete function and any imports it needs.
- Use the exact function name and signature given.
- Standard library only. No explanation, no tests, no example usage.
- Raise the errors the specification asks for."""

TEST_RUNNER = r'''
import sys, traceback
sys.path.insert(0, "/work")
from solution import {name} as _f

def raises(exc, *args, **kwargs):
    try:
        _f(*args, **kwargs)
    except exc:
        return
    except Exception as e:
        raise AssertionError(f"expected {{exc.__name__}}, got {{type(e).__name__}}: {{e}}")
    raise AssertionError(f"expected {{exc.__name__}}, no error raised for args={{args}}")

{name} = _f
failures = []
{checks}
if failures:
    print("FAILED " + str(len(failures)))
    print(failures[0])
    sys.exit(1)
print("OK")
'''


def build_checks(tests):
    out = []
    for t in tests:
        out.append("try:\n    " + t + "\nexcept Exception as e:\n"
                   "    failures.append(" + repr(t) + " + '  ->  ' + type(e).__name__ + ': ' + str(e))")
    return "\n".join(out)


def chat(messages, temperature, seed, max_tokens=700):
    payload = {"messages": messages, "temperature": temperature, "seed": seed,
               "max_tokens": max_tokens, "top_p": 0.95}
    req = urllib.request.Request(CODER_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.loads(r.read())
    return (body["choices"][0]["message"]["content"], time.perf_counter() - t0,
            body.get("usage", {}).get("completion_tokens", 0))


def extract_code(text):
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.S)
    return (blocks[0] if blocks else text).strip()


def run_in_sandbox(card, code, timeout=60):
    """Write the candidate and the hidden tests into a temp dir, run them in a network-less container."""
    with tempfile.TemporaryDirectory(dir=ROOT / "bench") as d:
        work = Path(d)
        (work / "solution.py").write_text(code, encoding="utf-8")
        runner = TEST_RUNNER.format(name=card["id"], checks=build_checks(card["hidden_tests"]))
        (work / "run_tests.py").write_text(runner, encoding="utf-8")
        cmd = ["docker", "run", "--rm", "--network", "none", "--memory", "512m", "--cpus", "1",
               "-v", f"{work}:/work:ro", "-w", "/work", SANDBOX_IMAGE, "python", "run_tests.py"]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, "timeout"
        out = (p.stdout + p.stderr).strip()
        return p.returncode == 0, out[-600:]


def feedback(error):
    """What code extracts and hands back - never the model's own words about its mistake."""
    return f"The function failed this check:\n{error}\nFix the function."


def split_tests(card):
    """Tests the coder may see, and the held-out ones that score it (the reward-hacking guard)."""
    tests = card["hidden_tests"]
    cut = max(1, round(len(tests) * 0.6))
    return tests[:cut], tests[cut:]


def solve_card(card, runs, tdd=False):
    spec = (f"{card['signature']}\n\n{card['description']}\n\n"
            f"Examples:\n" + "\n".join(f"  {e}" for e in card["examples"]))
    if tdd:
        visible = card["_visible"]
        spec += ("\n\nYour function must satisfy these checks exactly "
                 "(`raises(ValueError, x)` means calling it with x raises ValueError):\n"
                 + "\n".join(f"  {t}" for t in visible))
    base = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": spec}]
    result = {"card": card["id"]}

    # four candidates in parallel, differing only by seed and temperature
    settings = [(0.2, 1), (0.4, 2), (0.6, 3), (0.8, 4)]
    with ThreadPoolExecutor(4) as ex:
        gen = list(ex.map(lambda s: chat(base, s[0], s[1]), settings))
    t_gen = max(g[1] for g in gen)
    tokens = sum(g[2] for g in gen)
    checked = [run_in_sandbox(card, extract_code(g[0])) for g in gen]

    result["pass@1"] = checked[0][0]
    result["pass@4"] = any(ok for ok, _ in checked)
    result["gen_s"] = round(t_gen, 1)
    result["tokens"] = tokens

    # repair conditions start from the same failed first candidate
    if checked[0][0]:
        result["repair_fresh"] = result["repair_carry"] = True
        result["repairs_needed"] = 0
        return result

    for mode in ("fresh", "carry"):
        code, ok, err = extract_code(gen[0][0]), False, checked[0][1]
        history = list(base)
        for attempt in range(MAX_REPAIRS):
            if mode == "fresh":
                messages = base + [{"role": "user", "content": feedback(err)}]
            else:  # carry the failed attempts forward, as a naive agent loop does
                history = history + [{"role": "assistant", "content": code},
                                     {"role": "user", "content": feedback(err)}]
                messages = history
            text, _, tok = chat(messages, 0.3, 10 + attempt)
            tokens += tok
            code = extract_code(text)
            ok, err = run_in_sandbox(card, code)
            if ok:
                result[f"repairs_{mode}"] = attempt + 1
                break
        result[f"repair_{mode}"] = ok
    result["tokens"] = tokens
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", type=int, default=len(CARDS))
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--tdd", action="store_true",
                    help="show the coder 60%% of the checks; score only on the held-out 40%%")
    ap.add_argument("--holdout-score", action="store_true",
                    help="score on the held-out 40%% WITHOUT showing any checks (fair baseline for --tdd)")
    a = ap.parse_args()
    cards = CARDS[:a.cards]
    if a.tdd or a.holdout_score:  # score on held-out checks: hardcoding the visible ones cannot pass
        cards = [{**c, "_visible": split_tests(c)[0], "hidden_tests": split_tests(c)[1]} for c in cards]

    rows = []
    for card in cards:
        t0 = time.perf_counter()
        r = solve_card(card, a.runs, tdd=a.tdd)
        r["wall_s"] = round(time.perf_counter() - t0, 1)
        rows.append(r)
        print(f"{r['card']:<22} pass@1 {str(r['pass@1']):<5} pass@4 {str(r['pass@4']):<5} "
              f"repair-fresh {str(r.get('repair_fresh', '-')):<5} repair-carry {str(r.get('repair_carry', '-')):<5} "
              f"{r['wall_s']:>5}s")

    n = len(rows)
    pct = lambda key: 100 * sum(bool(r.get(key)) for r in rows) / n
    print("\n" + "=" * 70)
    print(f"cards: {n}")
    print(f"pass@1                      {pct('pass@1'):5.0f}%")
    print(f"pass@4 (parallel candidates){pct('pass@4'):5.0f}%")
    print(f"pass@1 + repair, fresh ctx  {pct('repair_fresh'):5.0f}%")
    print(f"pass@1 + repair, carried ctx{pct('repair_carry'):5.0f}%")
    print(f"median wall clock per card  {statistics.median(r['wall_s'] for r in rows):5.1f}s")
    print(f"total completion tokens     {sum(r['tokens'] for r in rows)}")
    out = ROOT / "bench" / "card_loop_results.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"saved {out}")


if __name__ == "__main__":
    main()
