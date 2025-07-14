#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Iterable
import subprocess

PROJECT_ROOT = Path(subprocess.getoutput("git rev-parse --show-toplevel"))  # noqa: S605

DEFAULT_TIMEOUTS_SECONDS = 60


def main() -> bool:
    if len(sys.argv) == 1:
        print(
            f"Usage: `{sys.argv[0]} <file path> <file path> ...` or `{sys.argv[0]} --all-files`"
        )
        sys.exit(1)

    result = True
    for notebook_file_path in _get_all_notebooks():
        if not does_test_exist(notebook_file_path) and should_notebook_be_tested(
            notebook_file_path
        ):
            result = False
            auto_create_test(notebook_file_path)
    return result


def _get_all_notebooks() -> Iterable[Path]:
    all_notebooks: Iterable[Path]

    if "--all-files" in sys.argv:
        all_notebooks = PROJECT_ROOT.rglob("*.ipynb")
    else:
        all_notebooks = [
            Path(file)
            for file in sys.argv[1:]
            if (file.endswith(".ipynb") and (".ipynb_checkpoint" not in file))
        ]

        all_notebooks = [
            p if p.is_absolute() else PROJECT_ROOT / p for p in all_notebooks
        ]

    return all_notebooks


def does_test_exist(notebook_file_path: Path) -> bool:
    expected_test_name = f"test_{notebook_file_path.stem}.py"
    return bool(list(PROJECT_ROOT.rglob(expected_test_name)))


def should_notebook_be_tested(notebook_file_path: Path) -> bool:
    return not (
        "functions" in notebook_file_path.parts
        or "community" in notebook_file_path.parts
    )


def auto_create_test(notebook_file_path: Path) -> None:
    test_file_name = (
        PROJECT_ROOT / "tests" / "notebooks" / f"test_{notebook_file_path.stem}.py"
    )
    if test_file_name.is_file():
        print(
            f"There's a collision - the test `{test_file_name}` already exists, somehow. Automatic creation will skip it"
        )
        return

    print(
        f"Adding test '{notebook_file_path.name}' in file '{test_file_name.relative_to(PROJECT_ROOT)}'"
    )
    with open(test_file_name, "w") as f:
        f.write(create_test_content(notebook_file_path))


def create_test_content(notebook_file_path: Path) -> str:
    return f"""from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("{notebook_file_path.stem}", timeout_seconds={DEFAULT_TIMEOUTS_SECONDS})
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=None,
        expected_depth=None,
    )

    # test notebook content
    pass  # Todo
"""


if __name__ == "__main__":
    if not main():
        sys.exit(1)
