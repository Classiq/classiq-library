from tests.utils_for_testbook import (
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("vlasov_ampere_qiskit", timeout_seconds=600)
def test_notebook(tb: TestbookNotebookClient) -> None:
    pass
