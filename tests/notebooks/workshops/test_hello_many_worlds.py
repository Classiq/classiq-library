from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("hello_many_worlds", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog_1"),
        expected_width=25,  # actual width: 12
        expected_depth=450,  # actual depth: 390
    )
    validate_quantum_program_size(
        tb.ref("qprog_2"),
        expected_width=25,  # actual width: 21
        expected_depth=500,  # actual depth: 420
    )

    # test notebook content
    pass  # Todo
