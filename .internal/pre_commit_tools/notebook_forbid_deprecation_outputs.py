#!/usr/bin/env python3

import re

from _common import iter_cells, load_notebook, report, run_precommit

# Also matches subclasses, e.g. `ClassiqDeprecationWarning` and `PendingDeprecationWarning`
DEPRECATION_WARNING = re.compile(r"\w*(DeprecationWarning|FutureWarning|SyntaxWarning)")


def forbid_deprecation_outputs(notebook_path: str) -> bool:
    nb = load_notebook(notebook_path)

    result = True
    for cell_idx, cell in iter_cells(nb, "code"):
        for output in cell.get("outputs", []):
            if output.get("output_type") != "stream":
                continue
            if match := DEPRECATION_WARNING.search(output.get("text", "")):
                result = False
                report(
                    notebook_path,
                    "deprecation warning in the outputs - replace the deprecated call, and re-run the notebook",
                    cell_idx,
                    match.string[match.start() :].splitlines()[0],
                )

    return result


if __name__ == "__main__":
    run_precommit(forbid_deprecation_outputs)
