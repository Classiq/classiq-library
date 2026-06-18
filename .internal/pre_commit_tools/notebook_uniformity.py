#!/usr/bin/env python3
"""Pre-commit hook: auto-fix simple notebook-uniformity conventions.

This is the enforcement counterpart to the read-only audit in
``.internal/notebook_uniformity_report.py`` — a home for the uniformity rules
that are simple and safe enough to fix automatically.

Each rule edits the notebook in place when ``auto_fix`` is set and returns a
short message describing the violation (or ``NO_ERROR`` when the notebook already
conforms). Add a rule by writing such a function and appending it to
``UNIFORMITY_RULES``.

Currently enforced:
  - a references section heading is plural ("References", not "Reference").
"""

import re
import sys
from collections.abc import Callable, Iterable

import nbformat

NO_ERROR = ""

# Edits `nb` in place when `auto_fix`; returns a message describing the
# violation/fix, or NO_ERROR when the notebook already conforms.
UniformityRule = Callable[[nbformat.NotebookNode, bool], str]


class Config:
    # if True, the hook does nothing (safety switch)
    IS_DISABLED: bool = False
    # if True, fix notebooks in place; if False, only report violations
    SHOULD_AUTO_FIX: bool = True


_SINGULAR_REFERENCES_HEADING = re.compile(
    r"^(#{1,6}[ \t]+)([Rr])eference([ \t]*)$", re.MULTILINE
)


def references_heading_is_plural(nb: nbformat.NotebookNode, auto_fix: bool) -> str:
    """A references section heading should read "References", never "Reference"."""
    found: list[str] = []

    def to_plural(match: re.Match) -> str:
        found.append(match.group(0).strip())
        return f"{match.group(1)}{match.group(2)}eferences{match.group(3)}"

    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        fixed_source = _SINGULAR_REFERENCES_HEADING.sub(to_plural, cell.source)
        if auto_fix:
            cell.source = fixed_source

    if not found:
        return NO_ERROR
    return f"singular heading {found} — use the plural 'References'"


UNIFORMITY_RULES: list[UniformityRule] = [
    references_heading_is_plural,
]


def main(full_file_paths: Iterable[str], auto_fix: bool) -> bool:
    if Config.IS_DISABLED:
        return True
    result = True
    for path in full_file_paths:
        result &= check_notebook(path, auto_fix)
    return result


def check_notebook(notebook_path: str, auto_fix: bool) -> bool:
    nb = nbformat.read(notebook_path, as_version=4)
    messages = [msg for rule in UNIFORMITY_RULES if (msg := rule(nb, auto_fix))]
    if not messages:
        return True

    if auto_fix:
        nbformat.write(nb, notebook_path)
    header = "auto-fixed (please `git add`)" if auto_fix else "violations"
    print(f"{notebook_path}: {header}")
    for message in messages:
        print(f"\t{message}")
    return False


if __name__ == "__main__":
    sys.exit(not main(sys.argv[1:], Config.SHOULD_AUTO_FIX))
