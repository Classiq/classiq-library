from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("phase_kickback", timeout_seconds=1000)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # warning: the notebook overrides the `qmod` and `qprog` parameter

    # test models
    validate_quantum_model(tb.ref("qmod"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=7,  # actual width: 5
        expected_depth=80,  # actual depth: 64
    )

    # test notebook content
    pass  # Todo
