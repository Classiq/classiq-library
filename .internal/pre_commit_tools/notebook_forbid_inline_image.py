#!/usr/bin/env python3

import re
import sys
import json

from _common import is_tested

NO_ERROR = ""


def main() -> bool:
    result = True
    for file in filter(is_tested, sys.argv[1:]):
        result &= forbid_inline_image(file)
    return result


def _iterate_markdown_cells(notebook: dict):
    return filter(
        lambda cell: cell.get("cell_type", "") == "markdown", notebook.get("cells", [])
    )


def _does_cell_has_image_error(cell) -> str:
    if isinstance(cell["source"], str):
        source_lines = [cell["source"]]
    elif isinstance(cell["source"], list):
        source_lines = cell["source"]
    else:
        raise ValueError(f"Invalid markdown source detected: {type(cell['source'])}")

    for line in source_lines:
        # IF there is a src image, AND it's pointing to a file, THEN make sure the path has '/'

        # IF there is a src image, AND it's base64, THEN don't allow
        if (
            ('<img src="data:image/png;base64,' in line)
            or ('<img src="data:image/jpg;base64,' in line)
            or ('<img src="data:image/jpeg;base64,' in line)
            or ("<img" in line and "src=" in line and ";base64," in line)
        ):
            return "Inline base64 image found - Please attach the image as a separate file (e.g. 'something.png' in the same folder as that notebook)"

        if "<img src=" in line:
            if path_match := re.search("<img\\s+[^>]*?src=(['\"])(.*?)\\1", line):
                path = path_match.group(2)
                if "/" not in path:
                    return "Relative img-src paths need to start with './'"

    return NO_ERROR


def forbid_inline_image(notebook_path: str) -> bool:
    with open(notebook_path) as f:
        notebook = json.load(f)

    result = True
    for index, cell in enumerate(_iterate_markdown_cells(notebook)):
        if error := _does_cell_has_image_error(cell):
            result = False
            print(
                f"Error in notebook '{notebook_path}' in markdown cell number {index} : {error}"
            )

    return result


if __name__ == "__main__":
    sys.exit(not main())
