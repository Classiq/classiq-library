from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hadamard_test", timeout_seconds=44)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # warning: the notebook overrides the `qmod` and `qprog` parameter

    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_with_execution_preferences"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=7,  # actual width: 5
        expected_depth=130,  # actual depth: 97
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_with_execution_preferences"),
        expected_width=7,  # actual width: 5
        expected_depth=130,  # actual depth: 97
    )

    # test notebook content
    pass  # Todo
