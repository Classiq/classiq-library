from tests.utils_for_testbook import (
    validate_quantum_program_size,
    validate_quantum_model,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("adapt_vqe", timeout_seconds=1800)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=8,  # actual expected width: 4
        expected_depth=50,  # actual expected depth: 26
    )

    # test notebook content
    pass  # Todo
