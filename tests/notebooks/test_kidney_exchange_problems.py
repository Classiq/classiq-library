from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("kidney_exchange_problems", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(tb.ref("qmod"))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),
        expected_width=10,
        expected_depth=100,
    )

    # test notebook content
    assert tb.ref("best_solution.solution") == [
        1,
        0,
        0,
        0,
        0,
        1,
        0,
        1,
        0,
    ], "The solution is not optimal."
    pass
