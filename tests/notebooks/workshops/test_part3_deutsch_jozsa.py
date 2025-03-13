from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("part3_deutsch_jozsa", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
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
        expected_width=15,  # actual width: 11
        expected_depth=180,  # actual depth: 142
    )

    # test notebook content
    pass  # Todo
