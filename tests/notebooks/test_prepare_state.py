from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("prepare_state", timeout_seconds=20)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=7,  # actual width: 6
        expected_depth=350,  # actual depth: 278
    )
    validate_quantum_program_size(
        tb.ref("qprog_simulator"),
        compare_to=tb.ref("qprog"),
    )

    # test notebook content
    pass  # Todo
