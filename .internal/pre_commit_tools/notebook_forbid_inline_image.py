#!/usr/bin/env python3

import re

from _common import (
    get_cell_source,
    is_tested,
    iter_cells,
    load_notebook,
    report,
    run_precommit,
)

NO_ERROR = ""


def _cell_image_error(cell: dict) -> tuple[str, str]:
    for line in get_cell_source(cell).splitlines(keepends=True):
        if (
            '<img src="data:image/png;base64,' in line
            or '<img src="data:image/jpg;base64,' in line
            or '<img src="data:image/jpeg;base64,' in line
            or ("<img" in line and "src=" in line and ";base64," in line)
        ):
            return line, (
                "Inline base64 image found — attach the image as a separate file"
                " (e.g. 'something.png' in the same folder as the notebook)"
            )

        if "<img src=" in line:
            if path_match := re.search("<img\\s+[^>]*?src=(['\"])(.*?)\\1", line):
                path = path_match.group(2)
                if "/" not in path:
                    return line, "Relative img-src paths need to start with './'"

    return NO_ERROR, NO_ERROR


def forbid_inline_image(notebook_path: str) -> bool:
    nb = load_notebook(notebook_path)

    result = True
    for cell_idx, cell in iter_cells(nb, "markdown"):
        line, error = _cell_image_error(cell)
        if error:
            result = False
            report(notebook_path, error, cell_idx, line)

    return result


if __name__ == "__main__":
    run_precommit(forbid_inline_image, filter_file=is_tested)
