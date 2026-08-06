#!/usr/bin/env python3
"""Auto-create a placeholder test for each new CI-tested notebook.

The generated test asserts on `tb.ref_pydantic("qprog")`; it is a *starting
point* the notebook author is expected to fill in (a notebook without a `qprog`
will fail until the author writes a real test — that is intentional).
"""

from pathlib import Path

from _common import PROJECT_ROOT, is_tested, report, run_precommit

DEFAULT_TIMEOUTS_SECONDS = 60


def check_and_create_test(notebook_path: str) -> bool:
    path = Path(notebook_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if does_test_exist(path):
        return True
    auto_create_test(path)
    return False


def does_test_exist(notebook_file_path: Path) -> bool:
    expected_test_name = f"test_{notebook_file_path.stem}.py"
    return bool(list(PROJECT_ROOT.rglob(expected_test_name)))


def auto_create_test(notebook_file_path: Path) -> None:
    test_file_name = (
        PROJECT_ROOT / "tests" / "notebooks" / f"test_{notebook_file_path.stem}.py"
    )
    if test_file_name.is_file():
        report(
            str(notebook_file_path),
            f"collision — test '{test_file_name}' already exists, skipping",
        )
        return

    report(
        str(notebook_file_path),
        f"created test '{test_file_name.relative_to(PROJECT_ROOT)}'",
        fixed=True,
    )
    with open(test_file_name, "w") as f:
        f.write(create_test_content(notebook_file_path))


def create_test_content(notebook_file_path: Path) -> str:
    return f"""from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("{notebook_file_path.stem}", timeout_seconds={DEFAULT_TIMEOUTS_SECONDS})
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=None,
        expected_depth=None,
        expected_cx_count=None,
    )

    # test notebook content
    pass  # Todo
"""


if __name__ == "__main__":
    run_precommit(check_and_create_test, filter_file=is_tested)
