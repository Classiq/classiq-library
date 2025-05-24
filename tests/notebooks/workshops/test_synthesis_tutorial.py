from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("synthesis_tutorial", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_opt_depth"),
        expected_width=20,  # actual width: 16
        expected_depth=250,  # actual depth: 171
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_opt_width"),
        expected_width=20,  # actual width: 9
        expected_depth=250,  # actual depth: 199
    )

    # test notebook content
    pass  # Todo
