#!/usr/bin/env python3
"""
usage: injected_cells.py add|remove <notebook...>

adds cells at the beginning of the notebook, so that they run before its own cells
then, removes them after the execution
"""

import json
import sys
from typing import Callable

RANDOM_SEED = 8

INJECTED_CELLS = [
    # set the random seeds, so that executing the notebook gives reproducible outputs
    #   numpy: https://stackoverflow.com/questions/58544946/how-to-set-the-fixed-random-seed-in-numpy
    #   torch: https://pytorch.org/docs/stable/notes/randomness.html
    f"""\
import random

import numpy as np
import torch

random.seed({RANDOM_SEED})
np.random.seed({RANDOM_SEED})
torch.manual_seed({RANDOM_SEED})""",
    # classiq logs "Submitting job to ..." and "Job: <url>" to stderr, which notebooks render like errors
    """\
import logging
import sys

import classiq

for handler in logging.getLogger("classiq.execution.functions.util._logging").handlers:
    handler.setStream(sys.stdout)""",
]

# cells have an "id" only from nbformat 4.5
NBFORMAT_VERSION_WITH_CELL_ID = (4, 5)


def _read_notebook(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_notebook(path: str, notebook: dict) -> None:
    # the same format as `nbformat.write` - unescaped unicode, and a trailing newline
    # so that rewriting a notebook changes only what we've edited
    with open(path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write("\n")


def _make_cell(index: int, source: str, with_id: bool) -> dict:
    cell = {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }
    if with_id:
        cell["id"] = f"injected-cell-{index}"
    return cell


def add_cells(notebook_path: str) -> None:
    notebook = _read_notebook(notebook_path)

    nbformat_version = notebook["nbformat"], notebook["nbformat_minor"]
    with_id = nbformat_version >= NBFORMAT_VERSION_WITH_CELL_ID
    cells = [
        _make_cell(index, source, with_id)
        for index, source in enumerate(INJECTED_CELLS)
    ]

    notebook["cells"][:0] = cells
    _write_notebook(notebook_path, notebook)


# does nothing if the cells aren't there, so it's safe to call more than once
def remove_cells(notebook_path: str) -> None:
    notebook = _read_notebook(notebook_path)

    cells = notebook["cells"]
    injected = cells[: len(INJECTED_CELLS)]
    if ["".join(cell["source"]) for cell in injected] != INJECTED_CELLS:
        return
    del cells[: len(INJECTED_CELLS)]

    # the injected cells ran first, so the notebook's own cells were counted after them
    # (they didn't run if, e.g., the execution was interrupted)
    num_executed = sum(cell.get("execution_count") is not None for cell in injected)
    for cell in cells:
        if type(cell.get("execution_count")) is int:
            cell["execution_count"] -= num_executed

    _write_notebook(notebook_path, notebook)


ACTIONS: dict[str, Callable[[str], None]] = {
    "add": add_cells,
    "remove": remove_cells,
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print(f"usage: {sys.argv[0]} add|remove <notebook...>", file=sys.stderr)
        sys.exit(1)

    action = ACTIONS[sys.argv[1]]
    for path in sys.argv[2:]:
        action(path)
