from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("chebyshev_approximation", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:

    actual_depths = [1180, 56]
    qprogs = tb.ref_pydantic("qprogs")
    for act_d, qp in zip(actual_depths, qprogs):
        validate_quantum_program_size(
            qp,
            expected_width=7,  # actual width: 7
            expected_depth=2 * act_d,
        )
