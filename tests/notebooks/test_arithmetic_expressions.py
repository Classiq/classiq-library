from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("arithmetic_expressions", timeout_seconds=40)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=tb.ref("NUM_QUBITS_1"),
        expected_depth=380,  # actual depth: 321
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=tb.ref("NUM_QUBITS_2"),
        expected_depth=270,  # actual depth: 228
    )

    # test notebook content
    pass  # TODO
