from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("linear_combination_of_unitaries", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=5,  # actual width: 4
        expected_depth=500,  # actual depth: 372
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=5,  # actual width: 4
        expected_depth=500,  # actual depth: 372
    )

    # test notebook content
    pass  # Todo
