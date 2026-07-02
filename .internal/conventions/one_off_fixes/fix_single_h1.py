#!/usr/bin/env python3
"""Point 6: exactly one H1 per notebook (the title).

For each target notebook: keep the first real H1 (the title) and demote every
later real H1 to H2. "Real" = not inside a ``` fenced code block ``` (such lines
are code comments, not headings, and must be left alone).

`arithmetic_expressions` is special: its second 'H1' is an instructional
sentence, not a section title, so we strip the `# ` to make it normal prose.

Dry-run by default; pass --apply to write (json; pre-commit canonicalises later).
"""

import json
import re
import sys

DEMOTE_FILES = [
    "applications/CFD/heat_eq_qsvt/heat_eq_qsvt.ipynb",
    "applications/chemistry/tensor_hypercontraction/tensor_hypercontraction.ipynb",
    "applications/cybersecurity/whitebox_fuzzing/whitebox_fuzzing.ipynb",
    "applications/finance/brownian_chebyshev_polynomials/brownian_chebyshev_polynomials.ipynb",
    "applications/optimization/adapt_qaoa/adapt_qaoa.ipynb",
    "applications/optimization/robust_posture_optimization/robust_posture_optimization.ipynb",
    "applications/telecom/resiliency_planning/resiliency_planning_AMD.ipynb",
    "community/Hackathons/iQuHack_2025/Challenge/classiq_iQuHack_2025_final.ipynb",
    "community/Hackathons/iQuHack_2025/Challenge_solution/our_solution/classiq_iQuHack_2025_final_sol.ipynb",
    "community/Hackathons/iQuHack_2025/Challenge_solution/winning_solution/classiq_iQuHack_2025_quantum_tree_sol.ipynb",
    "community/basic_examples/hw_aware_synthesis/hw_aware_synthesis.ipynb",
    "tutorials/workshops/algo_design_QCE_tutorial/algo_design_QCE_tutorial_part_I.ipynb",
    "tutorials/workshops/finance_workshops/rainbow_options_workshop_bruteforce.ipynb",
    "tutorials/workshops/oracle_workshop/oracles_workshop.ipynb",
]
SENTENCE_FILE = "tutorials/technology_demonstrations/arithmetic_expressions/arithmetic_expressions.ipynb"

APPLY = "--apply" in sys.argv


def lines_of(cell: dict) -> list[str]:
    src = cell.get("source", [])
    return src if isinstance(src, list) else src.splitlines(keepends=True)


def transform(cell: dict, fn) -> list[str]:
    """Apply fn(line, in_fence) -> new_line over a cell's lines, tracking fences."""
    out, in_fence = [], False
    for line in lines_of(cell):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            out.append(line)
            continue
        out.append(line if in_fence else fn(line))
    return out


def demote_later_h1s(path: str) -> list[str]:
    nb = json.load(open(path))
    changes, seen_first = [], False

    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue

        def fn(line: str) -> str:
            nonlocal seen_first
            if not (m := re.match(r"^#\s+(\S.*?)\s*$", line)):
                return line
            if not seen_first:
                seen_first = True
                return line  # keep the title
            changes.append(m.group(1)[:60])
            return "#" + line  # H1 -> H2

        cell["source"] = transform(cell, fn)

    if APPLY:
        _write(path, nb)
    return changes


def strip_sentence_h1(path: str) -> list[str]:
    nb = json.load(open(path))
    changes, seen_first = [], False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue

        def fn(line: str) -> str:
            nonlocal seen_first
            if not (m := re.match(r"^#\s+(\S.*?)\s*$", line)):
                return line
            if not seen_first:
                seen_first = True
                return line
            changes.append("(strip) " + m.group(1)[:60])
            return re.sub(r"^#\s+", "", line)  # heading -> prose

        cell["source"] = transform(cell, fn)
    if APPLY:
        _write(path, nb)
    return changes


def _write(path: str, nb: dict) -> None:
    with open(path, "w") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main() -> None:
    print(f"{'APPLY' if APPLY else 'DRY-RUN'}\n")
    for path in DEMOTE_FILES:
        changes = demote_later_h1s(path)
        print(f"{path}\n    demoted to H2: {changes}")
    print()
    changes = strip_sentence_h1(SENTENCE_FILE)
    print(f"{SENTENCE_FILE}\n    {changes}")


if __name__ == "__main__":
    main()
