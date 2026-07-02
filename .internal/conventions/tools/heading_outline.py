#!/usr/bin/env python3
"""Minimal pre-processing for the notebook-heading-hierarchy agent.

Prints the markdown heading outline of a notebook — a fence-aware `grep ^#`.
Lines inside ``` fenced code blocks ``` are skipped (they are code comments,
not headings). Each heading is shown with its markdown cell index, so the agent
can locate it to edit.

Usage:  python3 heading_outline.py <path-to.ipynb>
The path may be given relative to here or to the classiq-library/ repo.
"""

import json
import re
import sys
from pathlib import Path


def resolve(arg: str) -> Path:
    for candidate in (Path(arg), Path("classiq-library") / arg):
        if candidate.is_file():
            return candidate
    sys.exit(f"notebook not found: {arg}")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = resolve(sys.argv[1])
    nb = json.loads(path.read_text())

    in_fence = False
    found = False
    for cell_index, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue
        for line in "".join(cell.get("source", [])).splitlines():
            if re.match(r"^\s*```", line):
                in_fence = not in_fence
                continue
            if not in_fence and (m := re.match(r"^(#{1,6})\s+(\S.*?)\s*$", line)):
                found = True
                print(f"cell {cell_index:>3}  {m.group(1)} {m.group(2)}")
    if not found:
        print("(no markdown headings found)")


if __name__ == "__main__":
    main()
