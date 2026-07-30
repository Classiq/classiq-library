#!/usr/bin/env python3

import re
import sys
import json

from _common import is_tested


def main() -> bool:
    result = True
    for file in filter(is_tested, sys.argv[1:]):
        result &= forbid_inline_image(file)
    return result


def _iterate_markdown_cells(notebook: dict):
    return filter(
        lambda cell: cell.get("cell_type", "") == "markdown", notebook.get("cells", [])
    )


def _does_cell_has_inline_image(cell) -> bool:
    if isinstance(cell["source"], str):
        source_lines = [cell["source"]]
    elif isinstance(cell["source"], list):
        source_lines = cell["source"]
    else:
        raise ValueError(f"Invalid markdown source detected: {type(cell['source'])}")

    for line in source_lines:
        if '<img src="data:image/png;base64,' in line:
            return True
        if '<img src="data:image/jpg;base64,' in line:
            return True
        if '<img src="data:image/jpeg;base64,' in line:
            return True
        if "<img" in line and "src=" in line and ";base64," in line:
            return True

        # if re.search(".*\\b<img\\b[^>]+\\bsrc=[^>]+\\bbase64\\b", line):
        #     return True

    return False


def forbid_inline_image(notebook_path: str) -> bool:
    with open(notebook_path) as f:
        notebook = json.load(f)

    result = True
    for index, cell in enumerate(_iterate_markdown_cells(notebook)):
        if _does_cell_has_inline_image(cell):
            result = False
            print(
                f"Inline base64 image found in notebook '{notebook_path}' in markdown cell number {index}.\nPlease attach the image as a separate file (e.g. 'something.png' in the same folder as that notebook)"
            )

    return result


if __name__ == "__main__":
    sys.exit(not main())
