from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("second_quantized_hamiltonian", timeout_seconds=44)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=4,  # actual width: 4
        expected_depth=15,  # actual depth: 13
    )

    # test notebook content
    pass  # Todo
