from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_operations", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=15,  # actual width: 11
        expected_depth=150,  # actual depth: 96
    )

    # test notebook content
    pass  # Todo
