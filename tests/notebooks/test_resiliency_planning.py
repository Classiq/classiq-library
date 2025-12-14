from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("resiliency_planning", timeout_seconds=1801)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=24,
        expected_depth=1000,  # Actual is 586
        expected_cx_count=None,
    )

    # test notebook content
    pass  # Todo
