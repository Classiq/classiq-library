from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hadamard_test_tutorial", timeout_seconds=44)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=7,  # actual width: 5
        expected_depth=130,  # actual depth: 97
    )

    # test notebook content
    pass  # Todo
