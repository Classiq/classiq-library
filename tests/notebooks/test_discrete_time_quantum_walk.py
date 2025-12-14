from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("discrete_time_quantum_walk", timeout_seconds=2000)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1d"),
        expected_width=14,
        expected_depth=500,
    )

    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2d"),
        expected_width=18,
        expected_depth=1200,
    )

    # test notebook content
    pass  # Todo
