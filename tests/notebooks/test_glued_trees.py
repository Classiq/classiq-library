from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("glued_trees", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # everything in this test is inside a function, storing results in a file
    pass  # TODO: need to rewrite the notebook in order to test it
