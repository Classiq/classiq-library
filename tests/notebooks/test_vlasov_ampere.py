from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("vlasov_ampere", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test notebook content
    pass  # Todo
