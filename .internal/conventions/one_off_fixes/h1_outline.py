"""For every notebook with >1 H1, print its heading outline + the markdown cell
index of each heading, so we can decide per-notebook how to demote extra H1s."""

import glob
import json
import re

for path in sorted(glob.glob("**/*.ipynb", recursive=True)):
    nb = json.load(open(path))
    headings = []  # (cell_index, level, text, is_first_line_of_cell)
    for ci, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue
        src = "".join(cell.get("source", []))
        for li, line in enumerate(src.splitlines()):
            if m := re.match(r"^(#{1,6})\s+(\S.*)$", line):
                headings.append((ci, len(m.group(1)), m.group(2).strip(), li == 0))

    h1s = [h for h in headings if h[1] == 1]
    if len(h1s) <= 1:
        continue

    print(f"\n{'='*78}\n{path}   ({len(h1s)} H1s)")
    for ci, level, text, first in headings:
        marker = "  <-- H1" if level == 1 else ""
        pos = "" if first else " (mid-cell)"
        print(f"   cell{ci:>3} {'#'*level} {text[:70]}{marker}{pos}")
