import pytest

from testbook import testbook  # type: ignore[import]
from tests.utils_for_tests import iterate_notebooks
from tests.utils_for_testbook import NotebookEdit, _build_cd_decorator

TIMEOUT: int = 60 * 15  # 15 minutes


def _should_test_notebook(notebook_path: str) -> bool:
    if notebook_path.endswith("/logical_qubits_by_alice_and_bob.ipynb"):
        return False

    return "/functions/" in notebook_path or "/community/" in notebook_path


def noop(*args, **kwargs):
    pass


@pytest.mark.parametrize(
    "notebook_path", list(filter(_should_test_notebook, iterate_notebooks()))
)
def test_notebooks(notebook_path: str) -> None:
    test = noop  # we simply wish it to run without errors
    with NotebookEdit(notebook_path) as nr:
        test = testbook(notebook_path, execute=True, timeout=TIMEOUT)(test)
        test = _build_cd_decorator(notebook_path)(test)
    test()
