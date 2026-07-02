#!/usr/bin/env python3
"""Corpus statistics for heading levels: for each (normalized) heading text that
recurs across notebooks, what markdown level does it usually appear at?

Produces soft guidelines for the heading-hierarchy agent — e.g. "References is
H2 in 90/95 notebooks". It only describes EXISTING headers (never suggests
adding any) and is advisory: a notebook may legitimately differ.
"""

import glob
import json
import re
from collections import Counter, defaultdict

MIN_NOTEBOOKS = 4  # only report headers common enough to generalize
_ROOT = (
    "classiq-library" if __import__("pathlib").Path("classiq-library").is_dir() else "."
)


def normalize(text: str) -> str:
    # drop markdown emphasis/code, lowercase, keep words
    text = re.sub(r"[`*_]", "", text)
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def real_headings(nb: dict) -> list[tuple[int, str]]:
    out, in_fence = [], False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        for line in "".join(cell.get("source", [])).splitlines():
            if re.match(r"^\s*```", line):
                in_fence = not in_fence
                continue
            if not in_fence and (m := re.match(r"^(#{1,6})\s+(\S.*?)\s*$", line)):
                out.append((len(m.group(1)), m.group(2)))
    return out


# normalized header -> {level: occurrences}, plus notebook set and a display name
levels: dict[str, Counter] = defaultdict(Counter)
notebooks: dict[str, set] = defaultdict(set)
display: dict[str, Counter] = defaultdict(Counter)

for path in sorted(glob.glob(_ROOT + "/**/*.ipynb", recursive=True)):
    nb = json.load(open(path))
    for level, text in real_headings(nb):
        key = normalize(text)
        if not key:
            continue
        levels[key][level] += 1
        notebooks[key].add(path)
        display[key][text.strip()] += 1

rows = []
for key, level_counts in levels.items():
    n_nb = len(notebooks[key])
    if n_nb < MIN_NOTEBOOKS:
        continue
    dominant_level, dominant_n = level_counts.most_common(1)[0]
    total = sum(level_counts.values())
    name = display[key].most_common(1)[0][0]
    dist = " ".join(f"H{lvl}:{n}" for lvl, n in sorted(level_counts.items()))
    rows.append((n_nb, name, dominant_level, 100 * dominant_n // total, dist))

print(f"common headers (in >= {MIN_NOTEBOOKS} notebooks), by frequency:\n")
print(f"  {'#nb':>3}  {'recommend':>9}  {'agree':>5}  header  [level distribution]")
for n_nb, name, dom, pct, dist in sorted(rows, key=lambda r: -r[0]):
    print(f"  {n_nb:>3}  {'H'+str(dom):>9}  {pct:>4}%  {name!r}  [{dist}]")
