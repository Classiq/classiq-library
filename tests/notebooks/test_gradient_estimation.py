from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("gradient_estimation", timeout_seconds=200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_ancilla"),
        expected_width=16,  # Expected 8
        expected_depth=63,  # Expected 42
        expected_cx_count=41,  # Expected 27
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_linear"),
        expected_width=6,  # Expected 3
        expected_depth=23,  # Expected 15
        expected_cx_count=18,  # Expected 9
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_linear_2"),
        expected_width=6,  # Expected 3
        expected_depth=23,  # Expected 15
        expected_cx_count=18,  # Expected 9
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_quadratic"),
        expected_width=6,  # Expected 3
        expected_depth=35,  # Expected 23
        expected_cx_count=23,  # Expected 15
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_quadratic_2"),
        expected_width=6,  # Expected 3
        expected_depth=36,  # Expected 24
        expected_cx_count=23,  # Expected 15
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2d"),
        expected_width=12,  # Expected 6
        expected_depth=68,  # Expected 45
        expected_cx_count=72,  # Expected 48
    )

    # test notebook content
    pass  # Todo
