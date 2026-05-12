from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("arithmetic_expressions", timeout_seconds=40)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=tb.ref("NUM_QUBITS_1"),
        expected_depth=300,  # actual depth: 222
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=tb.ref("NUM_QUBITS_2"),
        expected_depth=270,  # actual depth: 200
    )

    # test notebook content
    pass  # TODO
