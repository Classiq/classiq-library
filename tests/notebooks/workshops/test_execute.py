from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("execute", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_with_execution_preferences"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_with_execution_preferences"),
        expected_width=30,  # actual width: 12
        expected_depth=500,  # actual depth: 390
    )

    # test notebook content
    pass  # Todo
