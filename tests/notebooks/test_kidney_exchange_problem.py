from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("kidney_exchange_problem", timeout_seconds=300)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    validate_quantum_model(str(tb.ref("qmod")))
    # test quantum programs
    validate_quantum_program_size(
        tb.ref("qprog"),  # type: ignore
        expected_width=10,
        expected_depth=100,
    )

    # test notebook content
    # Based on the notebook output, the best solution should be:
    # donor1 -> patient1 (1,0,0), donor2 -> patient3 (0,0,1), donor3 -> patient2 (0,1,0)
    # This gives: [1,0,0, 0,0,1, 0,1,0] (flattened 3x3 matrix)
    expected_solution = [1, 0, 0, 0, 0, 1, 0, 1, 0]
    actual_solution = tb.ref("best_solution.solution")

    assert (
        actual_solution == expected_solution
    ), f"The solution {actual_solution} is not optimal. Expected {expected_solution}."
