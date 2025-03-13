from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("part1_arithmetic", timeout_seconds=30)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_example"),
        expected_width=10,  # actual width: 7
        expected_depth=50,  # actual depth: 31
    )
    validate_quantum_program_size(
        tb.ref("qprog"),
        allow_zero_size=True,  # it's an empty `main`
    )
    validate_quantum_program_size(
        tb.ref("qprog_solution"),
        expected_width=15,  # actual width: 12
        expected_depth=200,  # actual depth: 160
    )

    # test notebook content
    pass  # Todo
