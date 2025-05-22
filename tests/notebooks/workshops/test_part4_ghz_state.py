from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("part4_ghz_state", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        allow_zero_size=True,  # it's an empty `main`
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_solution"),
        expected_width=10,  # actual width: 6
        expected_depth=10,  # actual depth: 6
    )

    # test notebook content
    pass  # Todo
