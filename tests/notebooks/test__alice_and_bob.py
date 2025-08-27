from tests.utils_for_testbook import wrap_testbook
from testbook.client import TestbookNotebookClient


@wrap_testbook(
    "logical_qubits_by_alice_and_bob", timeout_seconds=5 * 60 * 60
)  # 5 hours
def test_notebook(tb: TestbookNotebookClient) -> None:
    pass
