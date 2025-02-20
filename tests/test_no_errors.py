import os

import nbformat

from utils_for_tests import iterate_notebook_names, resolve_notebook_path


def test_no_errors_in_notebooks() -> None:
    for notebook in iterate_notebook_names():
        with open(resolve_notebook_path(notebook)) as f:
            notebook_data = nbformat.read(f, nbformat.NO_CONVERT)

        for index, cell in enumerate(notebook_data["cells"]):
            outputs = cell.get("outputs")
            if outputs is None:
                continue

            assert not any(
                output.get("output_type") == "error" for output in cell["outputs"]
            ), f"Cell #{index} in {notebook} has an output error"
