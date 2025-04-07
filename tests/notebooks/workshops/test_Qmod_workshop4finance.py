from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("Qmod_workshop4finance", timeout_seconds=400)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # warning: the `qmod` and `qprog` are being overriden too many times

    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=None,
        expected_depth=None,
    )

    # test notebook content
    pass  # Todo
