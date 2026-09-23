"""Measure generation speed of the containerised models, alone and with 4 requests at once.

  python bench/throughput.py

Answers the practical question: how long does one card take, and what does a project cost in wall-clock time.
"""
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PORTS = {"coder": 18001, "general": 18002, "embed": 18004}
PROMPT = ("Write a Python function `parse_duration(text: str) -> int` that converts strings like "
          "'2h30m', '45s' or '1h' into seconds. Raise ValueError on invalid input. Return only the code.")


def chat(port, prompt, max_tokens=300):
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps({"messages": [{"role": "user", "content": prompt}],
                         "max_tokens": max_tokens, "temperature": 0.2, "seed": 1}).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=300) as r:
        body = json.loads(r.read())
    dt = time.perf_counter() - t0
    usage = body.get("usage", {})
    return dt, usage.get("completion_tokens", 0), body["choices"][0]["message"]["content"]


def main():
    print("single request")
    for name, port in (("coder", PORTS["coder"]), ("general", PORTS["general"])):
        dt, tokens, text = chat(port, PROMPT)
        print(f"  {name:<8} {tokens:4d} tokens in {dt:5.1f} s = {tokens / dt:5.1f} tok/s")

    print("4 candidates in parallel (one card's worth of coder work)")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(4) as ex:
        out = list(ex.map(lambda _: chat(PORTS["coder"], PROMPT), range(4)))
    wall = time.perf_counter() - t0
    total = sum(t for _, t, _ in out)
    print(f"  {total} tokens in {wall:5.1f} s = {total / wall:5.1f} tok/s aggregate, "
          f"slowest candidate {max(d for d, _, _ in out):.1f} s")

    t0 = time.perf_counter()
    req = urllib.request.Request(f"http://127.0.0.1:{PORTS['embed']}/v1/embeddings",
                                 data=json.dumps({"input": ["hello world"] * 16}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        n = len(json.loads(r.read())["data"])
    print(f"embeddings: {n} texts in {time.perf_counter() - t0:.2f} s")

    print("\nsample coder output (first 10 lines):")
    print("\n".join(out[0][2].splitlines()[:10]))


if __name__ == "__main__":
    main()
