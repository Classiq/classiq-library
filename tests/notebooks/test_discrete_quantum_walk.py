from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("discrete_quantum_walk", timeout_seconds=90)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod_1"))
    validate_quantum_model(tb.ref("qmod_2"))
    validate_quantum_model(tb.ref("qmod_3"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_1"),
        expected_width=18,  # actual width: 8
        expected_depth=800,  # actual depth: 177
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_2"),
        expected_width=18,  # actual width: 8
        expected_depth=800,  # actual depth: 177
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_3"),
        expected_width=8,  # actual width: 6
        expected_depth=60,  # actual depth: 46
    )

    # test notebook content
    pass  # Todo
