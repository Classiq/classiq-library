from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qpe_for_matrix", timeout_seconds=748)
def test_notebook(tb: TestbookNotebookClient) -> None:
    """
    A notebook for a qpe for matrix.
    """
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_exact"),
        expected_width=9,  # actual width: 9
        expected_depth=500,  # actual depth: 384
    )
    validate_quantum_program_size(
        tb.ref_pydantic("qprog_approx"),
        expected_width=9,  # actual width: 9
        expected_depth=8000,  # actual depth: 6276
    )

    # test notebook content
    w = tb.ref_pydantic("w")
    width = tb.ref_pydantic("energy_resolution")
    for s in tb.ref_pydantic("solution_exact"):
        assert any(abs(s - wi) <= width for wi in w)
    for s in tb.ref_pydantic("solution_approx"):
        assert any(abs(s - wi) <= width for wi in w)
