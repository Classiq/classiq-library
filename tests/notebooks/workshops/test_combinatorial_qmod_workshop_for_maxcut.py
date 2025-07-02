from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("combinatorial_qmod_workshop_for_maxcut", timeout_seconds=250)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=10,  # actual width: 5
        expected_depth=80,  # actual depth: 53
    )

    # test notebook content
    pass  # Todo
