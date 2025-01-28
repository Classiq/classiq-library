import os

import nbformat

from utils_for_tests import iterate_notebooks


def test_no_errors_in_notebooks() -> None:
    for notebook in iterate_notebooks():
        with open(notebook) as f:
            notebook_data = nbformat.read(f, nbformat.NO_CONVERT)

        for index, cell in enumerate(notebook_data["cells"]):
            outputs = cell.get("outputs")
            if outputs is None:
                continue

            assert not any(
                output.get("output_type") == "error" for output in cell["outputs"]
            ), f"Cell #{index} in {os.path.basename(notebook)} has an output error"
