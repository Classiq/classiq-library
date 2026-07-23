#!/usr/bin/env python3
"""Rename a variable in a notebook's CODE CELLS ONLY (whole-word), json-aware.

    python3 rename_var.py <notebook.ipynb> <old_var> <new_var> [--in-cells-with=SUBSTR]

- Whole-word `old_var` -> `new_var` in code cells only (markdown untouched).
- `--in-cells-with=SUBSTR` scopes the rename (and the collision check) to code
  cells whose source contains SUBSTR — for a name overloaded across cells (e.g.
  `res` is an execution result in one cell and a register param in another).
- Refuses (collision) if `new_var` already appears as a word in the code cells,
  so two distinct variables are never merged.
- Reports the replacement count; NO-OP (exit 1) if `old_var` isn't found.

Writes JSON-aware (indent=1, ensure_ascii=False) for a minimal diff; pre-commit
canonicalises afterward.
"""

import json
import re
import sys


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--in-cells-with=")]
    marker = next(
        (a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--in-cells-with=")),
        None,
    )
    path, old, new = args[0], args[1], args[2]
    nb = json.load(open(path))
    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    # `--in-cells-with=SUBSTR` scopes the rename (and its collision check) to code
    # cells containing SUBSTR — used when a name is overloaded (e.g. `res` is both an
    # execution result and a quantum-register param in a different cell).
    if marker is not None:
        code_cells = [c for c in code_cells if marker in "".join(c["source"])]
    joined = "\n".join("".join(c["source"]) for c in code_cells)

    # A real collision is `new` used as an identifier. Ignore attribute access
    # (`.result()`), line comments, and string literals, so a bare `.result()`
    # method call or the word in a comment/string isn't a false positive.
    collision_scan = re.sub(r"#[^\n]*", "", joined)  # drop line comments
    collision_scan = re.sub(
        r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'", "", collision_scan
    )  # drop strings
    if re.search(rf"(?<![\w.]){re.escape(new)}\b", collision_scan):
        print(f"COLLISION: '{new}' already appears in code cells — pick another name.")
        return 1

    pat = re.compile(rf"\b{re.escape(old)}\b")
    n = 0
    for cell in code_cells:
        text = "".join(cell["source"])
        text, k = pat.subn(new, text)
        if k:
            n += k
            cell["source"] = text.splitlines(keepends=True)

    if n == 0:
        print(f"NO-OP: '{old}' not found in code cells.")
        return 1

    with open(path, "w") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"renamed {n}x  {old} -> {new}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
