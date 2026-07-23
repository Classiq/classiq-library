#!/usr/bin/env python3
"""Audit non-ASCII (>0x7F) characters in notebook MARKDOWN cells.

A `grep [^\\x00-\\x7f]`-style sweep, but notebook-aware: it separates
- prose/math markdown text  (where leftover math unicode would be a miss), from
- inline `code` / ``` fenced ``` spans (where unicode is allowed),
and groups by character with name, counts, and an example — so we can see what
remains and decide what's fine vs. what to also normalize.
"""

import glob, json, re, sys, unicodedata
from collections import defaultdict

MAIN = ("algorithms/", "applications/", "tutorials/")
CODE_SPAN = re.compile(r"```.*?```|`[^`\n]*`", re.S)

# char -> {"text": n, "code": n, "nbs": set, "ex": "..."}
stats = defaultdict(lambda: {"text": 0, "code": 0, "nbs": set(), "ex": ""})


def audit(path: str) -> None:
    for c in json.load(open(path)).get("cells", []):
        if c.get("cell_type") != "markdown":
            continue
        src = "".join(c["source"])
        code_ranges = [(m.start(), m.end()) for m in CODE_SPAN.finditer(src)]

        def in_code(i):
            return any(a <= i < b for a, b in code_ranges)

        for i, ch in enumerate(src):
            if ord(ch) < 128:
                continue
            s = stats[ch]
            s["code" if in_code(i) else "text"] += 1
            s["nbs"].add(path)
            if not s["ex"]:
                line = src[max(0, i - 30) : i + 30].replace("\n", " ")
                s["ex"] = line


paths = [
    p for p in sorted(glob.glob("**/*.ipynb", recursive=True)) if p.startswith(MAIN)
]
for p in paths:
    audit(p)


def cat(ch):
    name = unicodedata.name(ch, "?")
    g = unicodedata.category(ch)
    if "GREEK" in name:
        return "Greek letter"
    if g.startswith("Z") or "SPACE" in name:
        return "space/separator"
    if ch in "‘’“”":
        return "smart quote"
    if ch in "–—":
        return "dash"
    if g == "So" or ord(ch) >= 0x1F000 or "️" == ch:
        return "symbol/emoji"
    if g.startswith("P"):
        return "punctuation"
    if g.startswith("L"):
        return "letter (accented?)"
    if g.startswith("S"):
        return "math/other symbol"
    return g


groups = defaultdict(list)
for ch, s in stats.items():
    groups[cat(ch)].append((ch, s))

print(f"scanned {len(paths)} main notebooks — non-ASCII in markdown cells\n")
print(f"{'char':>6} {'U+':>7} {'text':>5} {'code':>5} {'#nb':>4}  name / example")
for gname in sorted(
    groups, key=lambda g: -sum(s["text"] + s["code"] for _, s in groups[g])
):
    tot = sum(s["text"] + s["code"] for _, s in groups[gname])
    print(f"\n## {gname}  (total {tot})")
    for ch, s in sorted(groups[gname], key=lambda kv: -(kv[1]["text"] + kv[1]["code"])):
        nm = unicodedata.name(ch, "?")
        flag = "  <-- in TEXT (not code)" if s["text"] else ""
        print(
            f"  {ch!r:>6} {ord(ch):>7X} {s['text']:>5} {s['code']:>5} {len(s['nbs']):>4}  {nm}{flag}"
        )
        if s["text"]:
            print(f"            e.g. …{s['ex']}…")
