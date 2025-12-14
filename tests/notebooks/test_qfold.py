from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qfold", timeout_seconds=120)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=7,  # actual width: 5
        expected_depth=150,  # actual depth: 134
        expected_cx_count=None,
    )

    # test notebook content
    pass  # Todo
