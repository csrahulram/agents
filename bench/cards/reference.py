"""Correct implementations of the bench cards, hand-written.

Used only as the mutation base: mutants are generated from these, and a mutant counts as a real bug
only if the hidden tests kill it. Never shown to any model.
"""
import re


def parse_duration(text: str) -> int:
    if not text:
        raise ValueError("empty")
    if not re.fullmatch(r"(\d+[hms])+", text):
        raise ValueError(f"bad duration: {text}")
    factors = {"h": 3600, "m": 60, "s": 1}
    total = 0
    for value, unit in re.findall(r"(\d+)([hms])", text):
        total += int(value) * factors[unit]
    return total


def chunk_list(items: list, size: int) -> list:
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i:i + size] for i in range(0, len(items), size)]


def normalise_whitespace(text: str) -> str:
    return " ".join(text.split())


def roman_to_int(s: str) -> int:
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    if not s or any(ch not in values for ch in s):
        raise ValueError(f"bad roman numeral: {s}")
    total = 0
    for i, ch in enumerate(s):
        value = values[ch]
        if i + 1 < len(s) and value < values[s[i + 1]]:
            total -= value
        else:
            total += value
    return total


def merge_intervals(intervals: list) -> list:
    for start, end in intervals:
        if start > end:
            raise ValueError(f"bad interval: ({start}, {end})")
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def word_frequencies(text: str) -> dict:
    counts = {}
    for word in re.findall(r"[\w']+", text.lower()):
        counts[word] = counts.get(word, 0) + 1
    return counts


def flatten_dict(d: dict, sep: str = ".") -> dict:
    out = {}
    for key, value in d.items():
        if isinstance(value, dict):
            for inner_key, inner_value in flatten_dict(value, sep).items():
                out[f"{key}{sep}{inner_key}"] = inner_value
        else:
            out[key] = value
    return out


def is_balanced(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def format_bytes(n: int) -> str:
    if n < 0:
        raise ValueError("negative")
    units = ["B", "KB", "MB", "GB", "TB"]
    if n < 1024:
        return f"{n} B"
    value = float(n)
    for unit in units[1:]:
        value /= 1024
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
    return f"{value:.1f} TB"


def diff_lines(a: str, b: str) -> list:
    left, right = a.split("\n"), b.split("\n")
    out = []
    for i in range(max(len(left), len(right))):
        old = left[i] if i < len(left) else None
        new = right[i] if i < len(right) else None
        if old == new:
            continue
        if old is None:
            out.append((i + 1, "added", new))
        elif new is None:
            out.append((i + 1, "removed", old))
        else:
            out.append((i + 1, "changed", new))
    return out
