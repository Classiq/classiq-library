from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("classiq_overview_tutorial", timeout_seconds=500)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=20,  # actual width: 16
        expected_depth=300,  # actual depth: 225
    )

    # test notebook content
    pass  # Todo
