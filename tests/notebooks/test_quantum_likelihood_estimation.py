from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("quantum_likelihood_estimation", timeout_seconds=1200)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    qprogs = tb.ref_pydantic("qprogs")
    for qprog in qprogs:
        validate_quantum_program_size(
            qprog,
            expected_width=1,  # actual 1
            expected_depth=12,  # actual 6
        )
