from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("task_scheduling_problem", timeout_seconds=840)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_large"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=8,  # actual width: 6
        expected_depth=160,  # actual depth: 139
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_large"),
        expected_width=30,  # actual width: 24
        expected_depth=500,  # actual depth: 428
    )

    # test notebook content
    pass  # todo
