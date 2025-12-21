from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("value_at_risk", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models

    # test notebook content
    pass  # Todo
