from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("tket_qsvt_example", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # the notebook is empty, there's nothing to test
    pass  # TODO
