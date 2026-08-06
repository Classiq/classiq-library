#!/usr/bin/env python3

import re

import latex2mathml.converter

from _common import get_cell_source, iter_cells, load_notebook, report, run_precommit

_LATEX_PATTERN = re.compile("(?<!\\\\)(\\${1,2})(.*?)\\1", re.DOTALL)


def validate_latex(filepath: str) -> bool:
    nb = load_notebook(filepath)

    result = True
    for cell_idx, cell in iter_cells(nb, "markdown"):
        source = get_cell_source(cell)
        for match in _LATEX_PATTERN.finditer(source):
            math_str = match.group(2)
            if not math_str.strip():
                continue

            try:
                latex2mathml.converter.convert(math_str)
            except Exception as e:
                result = False
                report(filepath, f"invalid LaTeX: {e}", cell_idx, math_str)

    return result


if __name__ == "__main__":
    run_precommit(validate_latex)
