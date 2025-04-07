from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("part5_grover", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_grover"))
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_solution"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_grover"),
        expected_width=13,  # actual width: 10
        expected_depth=400,  # actual depth: 341
    )
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        allow_zero_size=True,  # it's an empty `main`
    )
    validate_quantum_program_size(
        tb.ref("qprog_2"),
        allow_zero_size=True,  # it's an empty `main`
    )
    validate_quantum_program_size(
        tb.ref("qprog_solution"),
        expected_width=13,  # actual width: 11
        expected_depth=400,  # actual depth: 283
    )

    # test notebook content
    pass  # Todo
