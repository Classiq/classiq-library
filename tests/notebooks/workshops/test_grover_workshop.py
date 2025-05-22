from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("grover_workshop", timeout_seconds=1000)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # warning: the `qmod` and `qprog` are being overriden too many times

    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=30,  # actual width: 19
        expected_depth=250,  # actual depth: 143
    )

    # test notebook content
    pass  # Todo
