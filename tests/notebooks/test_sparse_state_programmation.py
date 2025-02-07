from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("sparse_state_preparation", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # everything in this test is inside a function, storing results in a file
    pass  # TODO: Not sure how to test a notebook
