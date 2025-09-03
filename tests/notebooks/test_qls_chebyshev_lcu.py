from tests.utils_for_testbook import (
    validate_quantum_program_size,
    wrap_testbook,
)
from testbook.client import TestbookNotebookClient


@wrap_testbook("qls_chebyshev_lcu", timeout_seconds=60)
def test_notebook(tb: TestbookNotebookClient) -> None:
    # test models
    # test quantum programs
    validate_quantum_program_size(
        tb.ref_pydantic("qprog"),
        expected_width=None,
        expected_depth=None,
    )

    # test notebook content
    pass  # Todo
