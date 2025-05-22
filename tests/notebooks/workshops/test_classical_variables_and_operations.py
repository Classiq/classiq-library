from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("classical_variables_and_operations", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=15,  # actual width: 10
        expected_depth=1,  # actual depth: 1
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=30,  # actual width: 24
        expected_depth=1,  # actual depth: 1
    )

    # test notebook content
    pass  # Todo
