#!/usr/bin/env python3

import json
import re
import sys

import latex2mathml.converter

_LATEX_PATTERN = re.compile("(?<!\\\\)(\\${1,2})(.*?)\\1", re.DOTALL)


def main() -> bool:
    result = True
    for filepath in sys.argv[1:]:
        if filepath.endswith(".ipynb"):
            result &= validate_latex(filepath)
    return result


def validate_latex(filepath: str) -> bool:
    with open(filepath, encoding="utf-8") as f:
        notebook = json.load(f)

    result = True
    for cell_idx, cell in enumerate(notebook.get("cells", [])):
        if cell.get("cell_type") != "markdown":
            continue

        source = "".join(cell.get("source", []))
        for match in _LATEX_PATTERN.finditer(source):
            math_str = match.group(2)
            if not math_str.strip():
                continue

            try:
                latex2mathml.converter.convert(math_str)
            except Exception as e:
                result = False
                snippet = math_str.strip()[:50]
                print(f"{filepath} | cell {cell_idx}: invalid LaTeX: {snippet}...")
                print(f"  {e}")

    return result


if __name__ == "__main__":
    sys.exit(not main())
