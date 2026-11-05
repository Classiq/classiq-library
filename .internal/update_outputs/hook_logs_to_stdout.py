#!/usr/bin/env python3
"""
usage: hook_logs_to_stdout.py add|remove <notebook...>

adds a first cell that makes classiq log to stdout, then removes it after the execution
classiq logs "Submitting job to ..." and "Job: <url>" to stderr, which notebooks render like errors
"""

import json
import sys
from typing import Callable

LOGS_TO_STDOUT_CELL = {
    "cell_type": "code",
    "execution_count": None,
    "id": "logs-to-stdout",
    "metadata": {},
    "outputs": [],
    "source": [
        "import logging\n",
        "import sys\n",
        "\n",
        "import classiq\n",
        "\n",
        'for handler in logging.getLogger("classiq.execution.functions.util._logging").handlers:\n',
        "    handler.setStream(sys.stdout)",
    ],
}

# cells have an "id" only from nbformat 4.5
NBFORMAT_VERSION_WITH_CELL_ID = (4, 5)


def _read_notebook(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def _write_notebook(path: str, notebook: dict) -> None:
    with open(path, "w") as f:
        json.dump(notebook, f, indent=1)


def add_logs_to_stdout(notebook_path: str) -> None:
    notebook = _read_notebook(notebook_path)

    cell = dict(LOGS_TO_STDOUT_CELL)
    nbformat_version = notebook["nbformat"], notebook["nbformat_minor"]
    if nbformat_version < NBFORMAT_VERSION_WITH_CELL_ID:
        cell.pop("id")

    notebook["cells"].insert(0, cell)
    _write_notebook(notebook_path, notebook)


# does nothing if there's no such cell, so it's safe to call more than once
def remove_logs_to_stdout(notebook_path: str) -> None:
    notebook = _read_notebook(notebook_path)

    cells = notebook["cells"]
    if not cells or cells[0].get("source") != LOGS_TO_STDOUT_CELL["source"]:
        return
    cell = cells.pop(0)

    # if the cell was executed, it was counted first, so the rest are counted from 2
    if cell.get("execution_count") is not None:
        for other_cell in cells:
            if type(other_cell.get("execution_count")) is int:
                other_cell["execution_count"] -= 1

    _write_notebook(notebook_path, notebook)


ACTIONS: dict[str, Callable[[str], None]] = {
    "add": add_logs_to_stdout,
    "remove": remove_logs_to_stdout,
}


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print(f"usage: {sys.argv[0]} add|remove <notebook...>", file=sys.stderr)
        sys.exit(1)

    action = ACTIONS[sys.argv[1]]
    for path in sys.argv[2:]:
        action(path)
