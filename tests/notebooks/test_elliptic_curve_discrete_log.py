from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("elliptic_curve_discrete_log", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_shor_ecdlp"),
        expected_width=25,
        expected_depth=100000,
    )

    # test notebook content
    pass  # Todo
