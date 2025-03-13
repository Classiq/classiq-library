from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("QMOD_Workshop_Part_3", timeout_seconds=80)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # warning: the `qmod` and `qprog` are being overriden too many times

    # test models
    validate_quantum_model(tb.ref("qmod"))
    validate_quantum_model(tb.ref("qmod_iqae"))

    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=None,
        expected_depth=None,
    )
    validate_quantum_program_size(
        tb.ref("qprog_iqae"),
        expected_width=None,
        expected_depth=None,
    )

    # test notebook content
    pass  # Todo
