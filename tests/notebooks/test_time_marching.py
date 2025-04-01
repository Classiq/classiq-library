from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("time_marching", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    pass  # TODO
