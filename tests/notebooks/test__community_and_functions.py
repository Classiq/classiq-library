import os
import pytest
from contextlib import contextmanager

from testbook import testbook  # type: ignore[import]
from tests.utils_for_tests import (
    iterate_notebooks,
    ROOT_DIRECTORY,
    resolve_notebook_path,
)

TIMEOUT: int = 60 * 15  # 15 minutes


def _should_test_notebook(notebook_path: str) -> bool:
    if notebook_path.endswith("/logical_qubits_by_alice_and_bob.ipynb"):
        pytest.skip("Skipping 'logical_qubits_by_alice_and_bob'")
        return False

    return "/functions/" in notebook_path or "/community/" in notebook_path


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(ROOT_DIRECTORY)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


@pytest.mark.parametrize(
    "notebook_path", filter(_should_test_notebook, iterate_notebooks())
)
def test_notebooks(notebook_path: str) -> None:
    with cwd(os.path.dirname(notebook_path)):
        with testbook(
            os.path.basename(notebook_path),
            execute=True,
            timeout=TIMEOUT,
        ):
            pass  # we simply wish it to run without errors
