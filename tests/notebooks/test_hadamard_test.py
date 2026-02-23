from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hadamard_test", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # actual width 5
        expected_depth=140,  # actual depth 107
        expected_cx_count=80,  # actual 68
    )

    # test notebook content
    pass  # Todo
