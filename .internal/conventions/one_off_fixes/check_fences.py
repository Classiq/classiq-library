"""Re-count H1s while ignoring lines inside ``` fenced code blocks ```.
Reveals which 'headings' are actually code comments (false positives)."""

import glob
import json
import re


def real_headings(md: str) -> list[tuple[int, str]]:
    out, in_fence = [], False
    for line in md.splitlines():
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if m := re.match(r"^(#{1,6})\s+(\S.*)$", line):
            out.append((len(m.group(1)), m.group(2).strip()))
    return out


for path in sorted(glob.glob("**/*.ipynb", recursive=True)):
    nb = json.load(open(path))
    md = "\n".join(
        "".join(c.get("source", []))
        for c in nb.get("cells", [])
        if c.get("cell_type") == "markdown"
    )
    naive = len(re.findall(r"(?m)^#\s+\S", md))
    real = sum(1 for lvl, _ in real_headings(md) if lvl == 1)
    if naive != real:
        print(f"FENCE FALSE-POSITIVE: {path}")
        print(f"    naive H1 count={naive}  real H1 count={real}")
    elif real > 1:
        print(f"genuine multi-H1 ({real}): {path}")
