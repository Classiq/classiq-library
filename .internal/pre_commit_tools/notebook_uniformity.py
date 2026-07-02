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
  - execution results are parsed via .result_value(), not .result()[0].value.
  - a circuit is shown via show(qprog), not the qprog.show() method form.
  - a notebook opens with an H1 title (optionally after a logo/banner cell).
  - a notebook has exactly one H1 (later H1 headings are demoted to H2).
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


_OLD_RESULT_PARSE = re.compile(r"\.result\(\)\s*\[\s*0\s*\]\s*\.value")


def results_use_result_value(nb: nbformat.NotebookNode, auto_fix: bool) -> str:
    """Parse execution results via `.result_value()`, not `.result()[0].value`."""
    count = 0
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        if not (hits := len(_OLD_RESULT_PARSE.findall(cell.source))):
            continue
        count += hits
        if auto_fix:
            cell.source = _OLD_RESULT_PARSE.sub(".result_value()", cell.source)
    if not count:
        return NO_ERROR
    return f".result()[0].value should be .result_value() ({count} occurrence(s))"


_CIRCUIT_SHOW_METHOD = re.compile(r"\b(qprog\w*|quantum_program\w*|qp)\.show\(\)")


def show_uses_function_form(nb: nbformat.NotebookNode, auto_fix: bool) -> str:
    """Show a circuit with show(qprog), not the qprog.show() method form."""
    count = 0
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        if not (hits := _CIRCUIT_SHOW_METHOD.findall(cell.source)):
            continue
        count += len(hits)
        if auto_fix:
            cell.source = _CIRCUIT_SHOW_METHOD.sub(r"show(\1)", cell.source)
    if not count:
        return NO_ERROR
    return f"qprog.show() should be show(qprog) ({count} occurrence(s))"


_H1_HEADING = re.compile(r"^\s*#[ \t]+\S")


def _is_h1_cell(cell: nbformat.NotebookNode) -> bool:
    return cell.cell_type == "markdown" and bool(_H1_HEADING.match(cell.source))


def _is_logo_cell(cell: nbformat.NotebookNode) -> bool:
    """A banner/logo cell: an <img> (or other html) with no prose text of its own."""
    if cell.cell_type != "markdown" or "<img" not in cell.source:
        return False
    return not re.search(r"[A-Za-z0-9]", re.sub(r"<[^>]+>", "", cell.source))


def opens_with_h1_title(nb: nbformat.NotebookNode, auto_fix: bool) -> str:
    """A notebook opens with an H1 title, optionally after one logo/banner cell.

    Not auto-fixable (a missing title can't be invented) — reports only.
    """
    cells = nb.cells
    opens_ok = bool(cells) and (
        _is_h1_cell(cells[0])
        or (_is_logo_cell(cells[0]) and len(cells) > 1 and _is_h1_cell(cells[1]))
    )
    if opens_ok:
        return NO_ERROR
    return (
        "does not open with an H1 title "
        "('# Title' in the first cell, optionally after a logo/banner cell)"
    )


def single_h1_title(nb: nbformat.NotebookNode, auto_fix: bool) -> str:
    """Exactly one H1 (the title); demote any later H1 headings to H2.

    The first H1 encountered is kept as the title; every subsequent `# ` heading
    is demoted to `## `. Fenced code blocks are skipped so a `#` comment inside
    ``` ``` ``` isn't mistaken for a heading.
    """
    seen_h1 = False
    demoted: list[str] = []
    for cell in nb.cells:
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.split("\n")
        in_fence = False
        for i, line in enumerate(lines):
            if re.match(r"^\s*```", line):
                in_fence = not in_fence
                continue
            if in_fence or not re.match(r"^#[ \t]+\S", line):
                continue
            if seen_h1:
                demoted.append(line.strip())
                if auto_fix:
                    lines[i] = "#" + line  # H1 -> H2
            else:
                seen_h1 = True
        if auto_fix:
            cell.source = "\n".join(lines)
    if not demoted:
        return NO_ERROR
    return f"multiple H1 headings — demoted {len(demoted)} to H2 (keep one H1 title): {demoted}"


UNIFORMITY_RULES: list[UniformityRule] = [
    references_heading_is_plural,
    results_use_result_value,
    show_uses_function_form,
    opens_with_h1_title,
    single_h1_title,
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
