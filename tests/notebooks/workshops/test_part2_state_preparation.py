from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("part2_state_preparation", timeout_seconds=30)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        allow_zero_size=True,  # it's an empty `main`
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_solution"),
        expected_width=7,  # actual width: 5
        expected_depth=400,  # actual depth: 325
    )

    # test notebook content
    pass  # Todo
