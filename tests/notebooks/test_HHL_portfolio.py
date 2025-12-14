from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("HHL_portfolio", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=18,
        expected_depth=25000,
    )

    # test notebook content
    pass  # Todo
