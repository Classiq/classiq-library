#!/usr/bin/env python3
"""Replace simple stray unicode (smart quotes, dashes) with ASCII equivalents.

Processes ALL markdown cells, including references. This handles the ~80% of
unicode issues that are mechanical replacements. Complex cases (math-italic
letters, symbols needing LaTeX wrapping) require the agent.

    python3 fix_unicode_simple.py                     # dry-run, show what would change
    python3 fix_unicode_simple.py --apply             # apply changes
    python3 fix_unicode_simple.py path/to/nb.ipynb    # single notebook

Replacements:
    Smart quotes:  " " → "    ' ' → '
    Dashes:        — (em) → -    – (en) → -
    Minus sign:    − (U+2212) → -
"""

import json
import re
import sys
from pathlib import Path

REPLACEMENTS = {
    "“": '"',  # left double quote
    "”": '"',  # right double quote
    "‘": "'",  # left single quote
    "’": "'",  # right single quote
    "—": "-",  # em dash
    "–": "-",  # en dash
    "−": "-",  # minus sign
}

REPO_ROOT = Path(__file__).resolve().parents[3]
APPLY = "--apply" in sys.argv


def fix_outside_fences(text: str) -> tuple[str, int]:
    """Replace unicode outside fenced code blocks. Returns (new_text, count)."""
    fence_re = re.compile(r"```.*?```|`[^`\n]*`", re.S)
    last, out, total = 0, [], 0
    for m in fence_re.finditer(text):
        seg = text[last : m.start()]
        for old, new in REPLACEMENTS.items():
            count = seg.count(old)
            if count:
                total += count
                seg = seg.replace(old, new)
        out.append(seg)
        out.append(m.group(0))  # code span verbatim
        last = m.end()
    tail = text[last:]
    for old, new in REPLACEMENTS.items():
        count = tail.count(old)
        if count:
            total += count
            tail = tail.replace(old, new)
    out.append(tail)
    return "".join(out), total


def process_notebook(path: Path) -> tuple[int, bool]:
    """Process a single notebook. Returns (replacement_count, modified)."""
    nb = json.loads(path.read_text())
    total_replacements = 0
    modified = False

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        source = cell.get("source", [])
        text = "".join(source) if isinstance(source, list) else source
        new_text, count = fix_outside_fences(text)
        if count:
            total_replacements += count
            modified = True
            if isinstance(source, list):
                cell["source"] = new_text.splitlines(keepends=True)
                if new_text and not new_text.endswith("\n") and cell["source"]:
                    cell["source"][-1] = cell["source"][-1].rstrip("\n")
            else:
                cell["source"] = new_text

    if modified and APPLY:
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")

    return total_replacements, modified


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        paths = [Path(a) for a in args]
    else:
        paths = sorted(REPO_ROOT.glob("**/*.ipynb"))
        paths = [p for p in paths if ".ipynb_checkpoints" not in str(p)]

    total_files = 0
    total_replacements = 0

    for path in paths:
        count, modified = process_notebook(path)
        if count:
            rel = (
                path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
            )
            action = "fixed" if APPLY else "would fix"
            print(f"{rel}: {action} {count} replacement(s)")
            total_files += 1
            total_replacements += count

    print(
        f"\n{'Applied' if APPLY else 'Would apply'}: {total_replacements} replacements in {total_files} files"
    )
    if not APPLY and total_replacements:
        print("Run with --apply to make changes.")


if __name__ == "__main__":
    main()
