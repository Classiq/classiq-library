#!/usr/bin/env python3
"""Apply literal text replacements to a notebook's MARKDOWN CELLS ONLY.

An agent decides the edits, writes them to a JSON spec, and this helper applies
them safely so code cells can never be touched:

    python3 md_replace.py <notebook.ipynb> <spec.json> [--skip=1,5,9]

spec.json: [{"old": "...", "new": "..."}, ...]   (applied in order)
--skip=...: comma-separated markdown-cell indices to leave untouched (e.g. the
            References section, so citation dashes/quotes are preserved).

Guarantees:
  - only `cell_type == "markdown"` cells are modified;
  - within a markdown cell, text inside inline `code` spans and ``` fenced
    blocks ``` is left untouched (so code references like `μ` are safe);
  - skipped cell indices are never modified.

Lenient: applies every spec that matches and reports any spec that matched
nothing (so you can spot a stale `old`); writes if at least one replacement was
made, exits 1 (no write) only if nothing matched at all.

Writes JSON-aware (indent=1, ensure_ascii=False) so the diff stays minimal and
unicode is preserved literally; pre-commit canonicalises afterward.
"""

import json
import re
import sys

CODE_SPAN = re.compile(r"```.*?```|`[^`\n]*`", re.S)  # fenced or inline code


def replace_outside_code(text: str, old: str, new: str) -> tuple[str, int]:
    last, out, n = 0, [], 0
    for m in CODE_SPAN.finditer(text):
        seg = text[last : m.start()]
        n += seg.count(old)
        out.append(seg.replace(old, new))
        out.append(m.group(0))  # code span verbatim
        last = m.end()
    tail = text[last:]
    n += tail.count(old)
    out.append(tail.replace(old, new))
    return "".join(out), n


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    skip = set()
    for a in sys.argv[1:]:
        if a.startswith("--skip="):
            skip = {int(x) for x in a.split("=", 1)[1].split(",") if x.strip()}
    nb_path, spec_path = args[0], args[1]
    specs = json.load(open(spec_path))
    nb = json.load(open(nb_path))

    counts = {i: 0 for i in range(len(specs))}
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "markdown" or idx in skip:
            continue
        text = "".join(cell["source"])
        for i, s in enumerate(specs):
            text, c = replace_outside_code(text, s["old"], s["new"])
            counts[i] += c
        cell["source"] = text.splitlines(keepends=True)

    total = sum(counts.values())
    misses = [specs[i]["old"] for i, c in counts.items() if c == 0]
    if total == 0:
        print(
            "NO-OP (notebook unchanged) — nothing matched outside code/skipped cells."
        )
        return 1

    with open(nb_path, "w") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(
        f"applied: "
        + ", ".join(f"{counts[i]}x {specs[i]['old']!r}" for i in range(len(specs)))
    )
    if misses:
        print("  (note: matched nothing — " + ", ".join(repr(m) for m in misses) + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
