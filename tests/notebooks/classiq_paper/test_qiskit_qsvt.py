from tests.utils_for_testbook import (
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qiskit_qsvt", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # the notebook is empty, there's nothing to test
    pass  # TODO
